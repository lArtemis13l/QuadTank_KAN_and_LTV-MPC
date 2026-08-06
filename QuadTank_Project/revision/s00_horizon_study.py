# Copyright 2026 Adilkhan Salkimbayev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Stage 0 -- the teacher's prediction horizon must span the plant's inverse response.

This settles the LTV-MPC configuration that every later stage depends on, so it
runs first.  The prediction model is discretised at dt_pred while the control
loop runs at dt = 0.1 s; with N = 30 fixed, the horizon is N * dt_pred.  Sweeping
dt_pred over {0.1, 1, 2, 4} s gives horizons of {3, 30, 60, 120} s, bracketing
the 69 s time constant of the non-minimum-phase transmission zero.

The 3 s horizon is the configuration to reject: on a non-minimum-phase plant a
controller that cannot see past the inverse response moves in the wrong
direction, and it pays for that with heavy command chatter.  Both effects are
quantified here rather than asserted -- the final state after 200 s and the
total variation of the pump commands.

Outputs results/horizon_study.json.
"""

from __future__ import annotations

import json
import os
import time

import numpy as np

import controllers as C
import qtlib as Q

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

DT = 0.1            # control period, as everywhere else in the pipeline
T_SIM = 200.0       # long enough for the short-horizon loop to show it drifts
SEED = 11           # same seed as the S1 nominal scenario in stage 5
DT_PRED_SWEEP = [0.1, 1.0, 2.0, 4.0]


def staircase_ref(reg):
    """The stage-5 staircase reference profile, reused so the two agree."""
    segs = [(0.0, 10.0, 10.0), (60.0, 13.0, 9.0), (120.0, 9.0, 13.0), (180.0, 12.0, 12.0)]
    eqs = [(t0, Q.equilibrium(a, b, reg)[0]) for t0, a, b in segs]

    def ref_fn(t):
        cur = eqs[0][1]
        for t0, xe in eqs:
            if t >= t0:
                cur = xe
        return cur
    return ref_fn


def run_one(reg, dt_pred, x_eq, ref_fn=None, T=None):
    """One closed loop under an LTV-MPC whose prediction step is dt_pred."""
    mpc = Q.LTVMPC(horizon=Q.HORIZON)
    state = {"u": np.zeros(2)}

    def policy(x, ref):
        u, ok = mpc.solve(x, ref, state["u"], DT, reg, dt_pred=dt_pred)
        state["u"] = u
        return u

    sim = Q.run_closed_loop(policy, reg, reg.x0,
                            ref_fn if ref_fn is not None else (lambda t: x_eq),
                            dt=DT, T=T if T is not None else T_SIM, seed=SEED)
    xf = sim["x"][-1]
    # track against the commanded reference, so this works for a fixed set-point
    # and for the staircase alike
    err = sim["x"][:, :2] - sim["ref"][:, :2]
    x_eq = sim["ref"][-1] if x_eq is None else x_eq
    # drift: is the loop still moving away at the end?
    tail = sim["x"][int(0.9 * len(sim["x"])):, :2]
    drift = float(np.linalg.norm(tail[-1] - tail[0]))
    return {
        "dt_pred_s": dt_pred,
        "horizon_s": Q.HORIZON * dt_pred,
        "final_state_cm": [round(float(v), 2) for v in xf],
        "final_abs_err_h1_cm": round(float(abs(xf[0] - x_eq[0])), 3),
        "final_abs_err_h2_cm": round(float(abs(xf[1] - x_eq[1])), 3),
        "rmse_h12_cm": round(float(np.sqrt(np.mean(err ** 2))), 3),
        "total_variation_u_V": round(float(Q.total_variation(sim["u"])), 1),
        "tail_drift_cm": round(drift, 3),
        "mpc_solve_failures": int(mpc.fail_count),
    }


def main():
    out = {"config": {"N": Q.HORIZON, "dt_s": DT, "T_s": T_SIM, "seed": SEED,
                      "deployed_dt_pred_s": Q.DT_PRED}}
    for regime, reg in (("MP", Q.MP), ("NMP", Q.NMP)):
        x_eq, u_eq = Q.equilibrium(10.0, 10.0, reg)
        rows = []
        print(f"=== {regime}  reference {np.round(x_eq, 2).tolist()} cm ===", flush=True)
        for dt_pred in DT_PRED_SWEEP:
            t0 = time.time()
            r = run_one(reg, dt_pred, x_eq)
            rows.append(r)
            print(f"  dt_pred={dt_pred:>4} s  horizon={r['horizon_s']:>5.0f} s  "
                  f"final={r['final_state_cm']}  TV={r['total_variation_u_V']:>7.1f} V  "
                  f"drift={r['tail_drift_cm']:.2f} cm  ({time.time() - t0:.0f}s)",
                  flush=True)
        # Transmission zeros of the (h1,h2) channel at this equilibrium. They are
        # computed here, not taken from the benchmark's source: the inverse-response
        # time constant they imply is exactly what the horizon has to span, so they
        # belong with the horizon argument rather than with the plant parameters.
        z = sorted(float(np.real(v))
                   for v in Q.transmission_zeros(reg, x_eq))
        rhp = [v for v in z if v > 0]
        out[regime] = {"reference_cm": [round(float(v), 4) for v in x_eq],
                       "u_eq_V": [round(float(v), 4) for v in u_eq],
                       "transmission_zeros_per_s": [round(v, 6) for v in z],
                       "rhp_zero_per_s": round(rhp[0], 6) if rhp else None,
                       "inverse_response_tau_s": (round(1.0 / rhp[0], 1)
                                                  if rhp else None),
                       "sweep": rows}

    # Section 6.2 compares command activity against the stage-5 scenarios, so the
    # durations have to match those exactly (S1 nominal 120 s, S2 staircase 240 s)
    # or the totals are not comparable.
    tvc = {}
    for regime, reg in (("MP", Q.MP), ("NMP", Q.NMP)):
        x_eq, _ = Q.equilibrium(10.0, 10.0, reg)
        rows = []
        print(f"=== {regime} task-matched total variation ===", flush=True)
        for task, ref_fn, T in (("S1_nominal", (lambda t, xe=x_eq: xe), 120.0),
                                ("S2_staircase", staircase_ref(reg), 240.0)):
            for dt_pred in (0.1, Q.DT_PRED):
                r = run_one(reg, dt_pred, x_eq, ref_fn=ref_fn, T=T)
                rows.append({"task": task, "T_s": T,
                             "dt_pred_s": dt_pred,
                             "horizon_s": r["horizon_s"],
                             "total_variation_u_V": r["total_variation_u_V"]})
                print(f"  {task:<13} dt_pred={dt_pred:>4} s  "
                      f"horizon={r['horizon_s']:>5.0f} s  "
                      f"TV={r['total_variation_u_V']:>7.1f} V", flush=True)
        tvc[regime] = rows
    out["tv_comparison"] = tvc

    def tv_at(dtp):
        return [r["total_variation_u_V"] for k in ("MP", "NMP")
                for r in tvc[k] if r["dt_pred_s"] == dtp]

    tv3, tvd = tv_at(0.1), tv_at(Q.DT_PRED)
    out["summary"] = {
        "short_horizon_s": Q.HORIZON * 0.1,
        "short_horizon_tv_range_V": [min(tv3), max(tv3)],
        "deployed_horizon_s": Q.HORIZON * Q.DT_PRED,
        "deployed_tv_range_V": [min(tvd), max(tvd)],
        "tasks": ["S1_nominal (120 s)", "S2_staircase (240 s)"],
    }

    p = os.path.join(RES, "horizon_study.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nwrote", p, flush=True)
    print("3 s horizon total variation across regimes:",
          out["summary"]["short_horizon_tv_range_V"], "V", flush=True)


if __name__ == "__main__":
    main()
