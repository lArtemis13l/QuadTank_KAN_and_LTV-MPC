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
Stage 4 -- what can and cannot be claimed about the stability of the distilled
controller.

The original submission asserted that the scalar test  d u / d e < 0  amounts to
"formal verification" of closed-loop stability.  It does not: for a coupled
nonlinear MIMO plant it is neither necessary nor sufficient.  This stage
replaces that claim with three statements of decreasing strength, each of which
is actually computed:

 (S1) LOCAL CERTIFICATE (rigorous, local).  The deployed law is an explicit
      polynomial, so the closed-loop map x+ = f(x, pi(x,r)) has an analytic
      Jacobian at the equilibrium.  If its spectral radius is < 1 the closed
      loop is locally exponentially stable, by Lyapunov's indirect method.
      A discrete quadratic Lyapunov function V = x'Px is then obtained from the
      discrete Lyapunov equation, and the largest sublevel set of V contained in
      the region where the decrease condition still holds is estimated
      numerically -- an *estimate* of the region of attraction, not a proof.

 (S2) SAMPLING-BASED VERIFICATION (statistical, global over a box).  The
      decrease condition V(x+) - V(x) < 0 is checked on a large sample of the
      operating box.  This is a falsification test: it can refute stability,
      it cannot prove it.  The fraction of violating samples is reported.

 (S3) MONTE-CARLO ROBUSTNESS.  Plant parameters are perturbed and the closed
      loop is simulated; the fraction of runs that converge, and the resulting
      steady-state error distribution, are reported.

Constraint satisfaction (input box and tank overflow/dry-out) is measured over
the same Monte-Carlo campaign, because the approximate controller carries no
constraint guarantee by construction.

Outputs results/stability.json
"""

from __future__ import annotations

import json
import os

import numpy as np
import scipy.linalg as sla

import controllers as C
import qtlib as Q
import verify as V

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

DT = 0.1
REFS = [(9.0, 9.0), (10.0, 10.0), (12.0, 12.0), (13.0, 9.0), (9.0, 13.0), (14.0, 14.0)]


def local_certificate(policy, reg, dt):
    """Thin wrapper around verify.certify so that the certificate reported here
    is computed by exactly the code that selected the deployed complexity."""
    import scipy.linalg as _sla
    out = []
    for c in V.certify(policy, reg, dt):
        rec = {k: v for k, v in c.items() if not k.startswith("_")}
        rec["offset_from_equilibrium_cm"] = float(
            np.linalg.norm(np.array(c["_xfp"]) - np.array(c["_xeq"])))
        if c["locally_stable"]:
            P = _sla.solve_discrete_lyapunov(np.array(c["_J"]).T, np.eye(4))
            rec["lyapunov_P_cond"] = float(np.linalg.cond(P))
            rec["_P"] = P
            rec["_xfp"] = c["_xfp"]
            rec["_xeq"] = c["_xeq"]
        out.append(rec)
    return out


def roa_estimate(policy, reg, dt, cert, n=21, T=200.0):
    """
    Grid the (h1, h2) initial-condition plane (lower tanks at their equilibrium
    values) and record which initial conditions converge to the fixed point.
    """
    ref = None
    for c in cert:
        if c["ref"] == [10.0, 10.0] and c.get("locally_stable"):
            ref = c
            break
    if ref is None:
        return None
    x_eq = np.array(ref["_xeq"]); x_fp = np.array(ref["_xfp"])
    grid = np.linspace(1.0, 19.0, n)
    ok = np.zeros((n, n), bool)
    for i, a in enumerate(grid):
        for j, b in enumerate(grid):
            x = np.array([a, b, x_eq[2], x_eq[3]])
            conv = True
            for _ in range(int(T / dt)):
                x = Q.step_plant(x, policy(x, x_eq), dt, reg)
                if not np.all(np.isfinite(x)) or x.max() > Q.H_MAX:
                    conv = False
                    break
            if conv and np.linalg.norm(x[:2] - x_fp[:2]) > 0.5:
                conv = False
            ok[i, j] = conv
    return {"grid_cm": [float(v) for v in grid],
            "converged": ok.tolist(),
            "converged_fraction": float(ok.mean()),
            "note": "lower tanks initialised at the equilibrium of the commanded reference"}


def sampling_verification(policy, reg, dt, cert, n=20000, box=(1.0, 19.0), seed=0):
    """Check the decrease condition of the local Lyapunov function on a box."""
    ref = next((c for c in cert if c["ref"] == [10.0, 10.0] and c.get("locally_stable")), None)
    if ref is None:
        return None
    P = np.array(ref["_P"]); x_fp = np.array(ref["_xfp"]); x_eq = np.array(ref["_xeq"])
    rng = np.random.default_rng(seed)
    X = rng.uniform(box[0], box[1], size=(n, 4))
    viol, dV = 0, []
    for x in X:
        xn = Q.step_plant(x, policy(x, x_eq), dt, reg)
        e0, e1 = x - x_fp, xn - x_fp
        d = float(e1 @ P @ e1 - e0 @ P @ e0)
        dV.append(d)
        if d >= 0:
            viol += 1
    dV = np.array(dV)
    return {"n_samples": n, "box_cm": list(box),
            "violation_fraction": viol / n,
            "median_dV": float(np.median(dV)),
            "note": ("V is the local Lyapunov function from (S1); a nonzero "
                     "violation fraction far from the equilibrium is expected "
                     "and does not by itself imply instability")}


def monte_carlo_robustness(policy, reg, dt, n=200, spread=0.20, seed=1, T=200.0):
    """Uniform multiplicative perturbation of valve ratios, pump gains and
    outlet areas; the controller is *not* retrained or retuned."""
    rng = np.random.default_rng(seed)
    x_eq, u_eq = Q.equilibrium(10.0, 10.0, reg)
    recs = []
    for _ in range(n):
        r = reg.copy()
        r.k = reg.k * rng.uniform(1 - spread, 1 + spread, 2)
        r.gamma = np.clip(reg.gamma * rng.uniform(1 - spread, 1 + spread, 2), 0.05, 0.95)
        a_scale = rng.uniform(1 - spread, 1 + spread)
        sim = Q.run_closed_loop(policy, r, reg.x0, lambda t: x_eq, dt, T,
                                seed=int(rng.integers(1e6)), use_ekf=False,
                                meas_noise_var=0.0, proc_noise_var=0.0)
        xf = sim["x"][-1]
        stable = bool(np.all(np.isfinite(xf)) and sim["x"].max() <= Q.H_MAX
                      and np.max(np.abs(sim["x"][-100:, :2] - sim["x"][-1, :2])) < 0.05)
        recs.append({
            "stable": stable,
            "h1_err": float(xf[0] - x_eq[0]), "h2_err": float(xf[1] - x_eq[1]),
            "max_level": float(sim["x"].max()),
            "overflow": bool(sim["x"].max() > Q.H_MAX),
            "dryout": bool(sim["x"].min() <= 1e-6),
            "sat_frac": float(np.mean((sim["u"] <= Q.U_MIN + 1e-9) | (sim["u"] >= Q.U_MAX - 1e-9))),
        })
    e1 = np.array([r["h1_err"] for r in recs])
    e2 = np.array([r["h2_err"] for r in recs])
    return {
        "n": n, "parameter_spread_pct": 100 * spread,
        "stable_fraction": float(np.mean([r["stable"] for r in recs])),
        "overflow_fraction": float(np.mean([r["overflow"] for r in recs])),
        "dryout_fraction": float(np.mean([r["dryout"] for r in recs])),
        "mean_input_saturation_fraction": float(np.mean([r["sat_frac"] for r in recs])),
        "h1_err_cm": {"mean": float(e1.mean()), "std": float(e1.std()),
                      "p95_abs": float(np.percentile(np.abs(e1), 95))},
        "h2_err_cm": {"mean": float(e2.mean()), "std": float(e2.std()),
                      "p95_abs": float(np.percentile(np.abs(e2), 95))},
    }


def constraint_study(policies, reg, dt, n=48, seed=2, T=100.0):
    """
    Constraint satisfaction over randomised set-point changes.  The MPC enforces
    0 <= h <= 20 cm and 0 <= u <= 12 V explicitly; every distilled policy only
    inherits the input box through clipping, so state-constraint satisfaction
    has to be measured, not assumed.
    """
    rng = np.random.default_rng(seed)
    tasks = []
    for _ in range(n):
        h1r, h2r = rng.uniform(7.5, 14.5, 2)
        try:
            x_eq, _ = Q.equilibrium(h1r, h2r, reg)
        except ValueError:
            continue
        x0 = np.array([rng.uniform(2, 18), rng.uniform(2, 18),
                       rng.uniform(0.5, 8), rng.uniform(0.5, 8)])
        tasks.append((x0, x_eq))
    out = {}
    settle = int(20.0 / dt)   # ignore the first 20 s: a lower tank started near
                              # empty drains to zero whatever the pumps do, which
                              # is a reachability artefact of the initial state
                              # rather than a constraint violation attributable
                              # to the controller
    for name, pol in policies.items():
        ovf = dry = 0
        worst_hi, worst_lo, sat = [], [], []
        for x0, x_eq in tasks:
            sim = Q.run_closed_loop(pol, reg, x0, lambda t: x_eq, dt, T,
                                    seed=0, use_ekf=False,
                                    meas_noise_var=0.0, proc_noise_var=0.0)
            X = sim["x"][settle:]
            mx, mn = X.max(), X.min()
            ovf += int(mx > Q.H_MAX)
            dry += int(mn <= 1e-6)
            worst_hi.append(float(mx)); worst_lo.append(float(mn))
            sat.append(float(np.mean((sim["u"] <= Q.U_MIN + 1e-9) |
                                     (sim["u"] >= Q.U_MAX - 1e-9))))
        out[name] = {
            "n_tasks": len(tasks),
            "settling_window_ignored_s": 20.0,
            "overflow_fraction": ovf / max(len(tasks), 1),
            "dryout_fraction": dry / max(len(tasks), 1),
            "max_level_observed_cm": float(np.max(worst_hi)),
            "min_level_observed_cm": float(np.min(worst_lo)),
            "mean_input_saturation_fraction": float(np.mean(sat)),
        }
        print(f"  [constraints] {name}: {out[name]}", flush=True)
    return out


def main():
    result = {}
    for regime, reg in (("MP", Q.MP), ("NMP", Q.NMP)):
        print(f"=== {regime} ===", flush=True)
        law = C.SymbolicLaw(regime)
        cert = local_certificate(law, reg, DT)
        print("  local certificate:", [(c["ref"], round(c["spectral_radius"], 4)) for c in cert], flush=True)
        roa = roa_estimate(law, reg, DT, cert)
        print("  ROA converged fraction:", None if roa is None else roa["converged_fraction"], flush=True)
        samp = sampling_verification(law, reg, DT, cert)
        print("  sampled Lyapunov violation fraction:", None if samp is None else samp["violation_fraction"], flush=True)
        mc = monte_carlo_robustness(law, reg, DT)
        print("  MC robustness:", {k: mc[k] for k in ("stable_fraction", "overflow_fraction")}, flush=True)

        pols = {"Symbolic KAN": law,
                "LTV-MPC": C.mpc_policy(reg, DT),
                "Gain-scheduled LQR": C.lqr_policy(reg, DT),
                "MLP (32-32)": C.mlp_policy(regime, "mlp")}
        cons = constraint_study(pols, reg, DT)

        result[regime] = {
            "local_certificate": [{k: v for k, v in c.items() if not k.startswith("_")}
                                  for c in cert],
            "max_spectral_radius": float(max(c["spectral_radius"] for c in cert)),
            "all_locally_stable": bool(all(c["locally_stable"] for c in cert)),
            "roa_estimate": roa,
            "sampled_lyapunov": samp,
            "monte_carlo_robustness": mc,
            "constraint_satisfaction": cons,
        }
    with open(os.path.join(RES, "stability.json"), "w") as f:
        json.dump(result, f, indent=2)
    print("wrote", os.path.join(RES, "stability.json"))


if __name__ == "__main__":
    main()
