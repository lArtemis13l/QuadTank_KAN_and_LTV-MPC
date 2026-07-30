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
Stage 5 -- closed-loop benchmarks.

Every controller is driven through the same set of scenarios by the same
simulator.  Reference set-points are always *reachable equilibria* computed in
closed form, so that a converging controller really does drive the tracking
error to zero; the original submission commanded [10,10,2,2], which is not an
equilibrium of the plant, which is why its cost never reached zero.

Scenarios (deliberately chosen so that no two produce similar trajectories):
  S1 nominal      -- step to the equilibrium of (10,10) from the Johansson
                     initial state, both regimes
  S2 staircase    -- four successive, partly asymmetric set-point changes
  S3 disturbance  -- +3 cm load disturbance on tank 1 at t = 60 s
  S4 degradation  -- pump gains ramped down to -30 % between t = 40 s and 80 s
  S5 handover     -- valve ratios moved from the NMP to the MP configuration
                     over a 10 s ramp (a physically realisable transition)
  S6 noise sweep  -- measurement-noise variance swept with the EKF in the loop

Outputs results/scenarios.json and results/traj_*.npz
"""

from __future__ import annotations

import json
import os

import numpy as np

import controllers as C
import qtlib as Q

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
TRAJ = os.path.join(RES, "traj")
os.makedirs(TRAJ, exist_ok=True)

DT = 0.1


def score(sim, x_eq, tail=0.2):
    """Tracking metrics on the controlled outputs h1, h2."""
    x, u, t = sim["x"], sim["u"], sim["t"]
    n_tail = max(1, int(tail * len(t)))
    e = x[:, :2] - x_eq[:2]
    return {
        "rmse_h12_cm": float(np.sqrt(np.mean(e ** 2))),
        "iae_h12_cm_s": float(np.sum(np.abs(e)) * DT),
        "steady_state_err_h1_cm": float(np.mean(x[-n_tail:, 0]) - x_eq[0]),
        "steady_state_err_h2_cm": float(np.mean(x[-n_tail:, 1]) - x_eq[1]),
        "max_abs_ss_err_cm": float(np.max(np.abs(x[-n_tail:, :2] - x_eq[:2]))),
        "settling_time_h1_s": Q.settling_time(t, x[:, 0], x_eq[0], band=0.02, scale=x_eq[0]),
        "total_variation_u_V": Q.total_variation(u),
        "input_saturation_frac": float(np.mean((u <= Q.U_MIN + 1e-9) | (u >= Q.U_MAX - 1e-9))),
        "max_level_cm": float(x.max()),
        "min_level_cm": float(x.min()),
        "overflow": bool(x.max() > Q.H_MAX),
        "dryout": bool(x.min() <= 1e-6),
    }


def run(pol, reg, x0, ref_fn, T, **kw):
    return Q.run_closed_loop(pol, reg, x0, ref_fn, DT, T, **kw)


def s1_nominal(pols, reg, regime, out):
    x_eq, _ = Q.equilibrium(10.0, 10.0, reg)
    res = {}
    for name, p in pols.items():
        sim = run(p, reg, reg.x0, lambda t: x_eq, 120.0, seed=11)
        res[name] = score(sim, x_eq)
        np.savez(os.path.join(TRAJ, f"S1_{regime}_{name.replace(' ','_').replace('(','').replace(')','')}.npz"),
                 t=sim["t"], x=sim["x"], u=sim["u"], ref=sim["ref"])
        print(f"  S1 {regime} {name:20s} RMSE={res[name]['rmse_h12_cm']:.3f} "
              f"ss=({res[name]['steady_state_err_h1_cm']:+.3f},{res[name]['steady_state_err_h2_cm']:+.3f}) "
              f"TV={res[name]['total_variation_u_V']:.1f}", flush=True)
    out["S1_nominal"] = res
    return x_eq


def s2_staircase(pols, reg, regime, out):
    segs = [(0.0, 10.0, 10.0), (60.0, 13.0, 9.0), (120.0, 9.0, 13.0), (180.0, 12.0, 12.0)]
    eqs = [(t0, *Q.equilibrium(a, b, reg)) for t0, a, b in segs]

    def ref_fn(t):
        cur = eqs[0][1]
        for t0, xe, ue in eqs:
            if t >= t0:
                cur = xe
        return cur

    res = {}
    for name, p in pols.items():
        sim = run(p, reg, reg.x0, ref_fn, 240.0, seed=12)
        e = sim["x"][:, :2] - sim["ref"][:, :2]
        # per-segment steady-state error, measured in the last 5 s of each hold
        seg_err = []
        for t0, xe, _ in eqs:
            m = (sim["t"] >= t0 + 55.0) & (sim["t"] < t0 + 60.0)
            if m.sum() == 0:
                m = sim["t"] >= sim["t"][-1] - 5.0
            seg_err.append(float(np.max(np.abs(sim["x"][m][:, :2] - xe[:2]))))
        res[name] = {
            "rmse_h12_cm": float(np.sqrt(np.mean(e ** 2))),
            "iae_h12_cm_s": float(np.sum(np.abs(e)) * DT),
            "per_segment_max_ss_err_cm": seg_err,
            "worst_segment_ss_err_cm": float(np.max(seg_err)),
            "total_variation_u_V": Q.total_variation(sim["u"]),
            "overflow": bool(sim["x"].max() > Q.H_MAX),
            "dryout": bool(sim["x"].min() <= 1e-6),
        }
        np.savez(os.path.join(TRAJ, f"S2_{regime}_{name.replace(' ','_').replace('(','').replace(')','')}.npz"),
                 t=sim["t"], x=sim["x"], u=sim["u"], ref=sim["ref"])
        print(f"  S2 {regime} {name:20s} RMSE={res[name]['rmse_h12_cm']:.3f} "
              f"worst-seg={res[name]['worst_segment_ss_err_cm']:.3f}", flush=True)
    out["S2_staircase"] = res


def s3_disturbance(pols, reg, regime, out):
    x_eq, _ = Q.equilibrium(10.0, 10.0, reg)
    res = {}
    for name, p in pols.items():
        rng = np.random.default_rng(13)
        x = reg.x0.copy()
        ekf = Q.EKF(x0=np.array([12.0, 12.0, 1.0, 1.0]))
        X, U = [], []
        n = int(400.0 / DT)
        kdist = int(60.0 / DT)
        for k in range(n):
            if k == kdist:
                x[0] += 3.0
            u = np.clip(np.asarray(p(ekf.x, x_eq), float).ravel(), Q.U_MIN, Q.U_MAX)
            x = Q.step_plant(x, u, DT, reg)
            z = x + rng.normal(0, np.sqrt(2.37), 4)
            ekf.step(u, z, DT, reg)
            X.append(x.copy()); U.append(u.copy())
        X, U = np.array(X), np.array(U)
        t = np.arange(n) * DT
        post = X[kdist:]
        # Recovery is measured against the level the controller was actually
        # holding just before the step, not against the reference: every
        # controller (the MPC included) carries the same small estimator-induced
        # standing error, and a threshold below it would never be met.
        h_pre = float(np.mean(X[kdist - 50:kdist, 0]))
        sd_pre = float(np.std(X[kdist - 50:kdist, 0]))
        peak = float(np.max(np.abs(post[:, 0] - h_pre)))
        # Recovery is measured on a 5 s moving average of h1.  Without the
        # filter a controller whose command chatters (the MPC does, because the
        # solver switches active set under estimator noise) never settles
        # permanently inside any fixed band, and the metric would report its
        # ripple rather than its disturbance rejection.  The ripple itself is
        # recorded separately below.
        win = int(5.0 / DT)
        pad = np.pad(post[:, 0], (win // 2, win - win // 2 - 1), mode="edge")
        h_f = np.convolve(pad, np.ones(win) / win, mode="valid")
        band = max(0.1 * peak, 3.0 * sd_pre)
        inside = np.abs(h_f - h_pre) < band
        rec = float("nan")
        for i in range(len(inside)):
            if inside[i:].all():
                rec = i * DT
                break
        res[name] = {
            "pre_disturbance_level_cm": h_pre,
            "peak_deviation_h1_cm": peak,
            "pre_disturbance_std_cm": sd_pre,
            "post_recovery_ripple_std_cm": float(np.std(X[-int(60.0 / DT):, 0])),
            "recovery_band_cm": band,
            "recovery_time_s": float(rec),
            "residual_err_h1_cm": float(abs(X[-1, 0] - h_pre)),
            "total_variation_u_V": Q.total_variation(U),
            "iae_after_disturbance_cm_s": float(np.sum(np.abs(post[:, :2] - x_eq[:2])) * DT),
        }
        np.savez(os.path.join(TRAJ, f"S3_{regime}_{name.replace(' ','_').replace('(','').replace(')','')}.npz"),
                 t=t, x=X, u=U, ref=np.tile(x_eq, (n, 1)))
        print(f"  S3 {regime} {name:20s} peak={res[name]['peak_deviation_h1_cm']:.3f} "
              f"rec={res[name]['recovery_time_s']:.1f}s TV={res[name]['total_variation_u_V']:.1f}", flush=True)
    out["S3_disturbance"] = res


def s4_degradation(pols, reg, regime, out):
    """Pump gains ramp down by up to 30 % between t=40 s and t=80 s, plus a
    sweep of the final degradation level."""
    x_eq, _ = Q.equilibrium(10.0, 10.0, reg)
    res = {"ramp": {}, "sweep": {}}
    for name, p in pols.items():
        rng = np.random.default_rng(14)
        x = reg.x0.copy()
        ekf = Q.EKF(x0=np.array([12.0, 12.0, 1.0, 1.0]))
        X, U = [], []
        n = int(160.0 / DT)
        for k in range(n):
            t = k * DT
            frac = 0.0 if t < 40 else min(1.0, (t - 40) / 40.0)
            r = reg.copy(); r.k = reg.k * (1 - 0.30 * frac)
            u = np.clip(np.asarray(p(ekf.x, x_eq), float).ravel(), Q.U_MIN, Q.U_MAX)
            x = Q.step_plant(x, u, DT, r)
            z = x + rng.normal(0, np.sqrt(2.37), 4)
            ekf.step(u, z, DT, r)
            X.append(x.copy()); U.append(u.copy())
        X, U = np.array(X), np.array(U)
        res["ramp"][name] = {
            "final_err_h1_cm": float(X[-1, 0] - x_eq[0]),
            "final_err_h2_cm": float(X[-1, 1] - x_eq[1]),
            "max_err_after_ramp_cm": float(np.max(np.abs(X[int(80 / DT):, :2] - x_eq[:2]))),
            "final_u_V": [float(v) for v in U[-1]],
            "stable": bool(np.all(np.isfinite(X[-1])) and X.max() <= Q.H_MAX),
        }
        np.savez(os.path.join(TRAJ, f"S4_{regime}_{name.replace(' ','_').replace('(','').replace(')','')}.npz"),
                 t=np.arange(n) * DT, x=X, u=U, ref=np.tile(x_eq, (n, 1)))
        # static sweep
        sw = []
        for d in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
            r = reg.copy(); r.k = reg.k * (1 - d)
            sim = run(p, r, reg.x0, lambda t: x_eq, 200.0, seed=15,
                      meas_noise_var=0.0, proc_noise_var=0.0, use_ekf=False)
            sw.append({"degradation": d,
                       "ss_err_h1_cm": float(sim["x"][-1, 0] - x_eq[0]),
                       "ss_err_h2_cm": float(sim["x"][-1, 1] - x_eq[1]),
                       "stable": bool(sim["x"].max() <= Q.H_MAX)})
        res["sweep"][name] = sw
        print(f"  S4 {regime} {name:20s} ramp final err=({res['ramp'][name]['final_err_h1_cm']:+.3f},"
              f"{res['ramp'][name]['final_err_h2_cm']:+.3f})  "
              f"sweep@30% err={sw[6]['ss_err_h1_cm']:+.3f}", flush=True)
    out["S4_degradation"] = res


def s5_handover(law_mp, law_nmp, out):
    """
    Valve ratios are moved from the NMP to the MP configuration by a 10 s linear
    ramp -- a physically realisable manoeuvre for motorised three-way valves.
    The scheduler reads the commanded valve position, which is an actuator
    set-point known to the controller, not an unmeasured plant parameter.
    """
    x_eq_nmp, _ = Q.equilibrium(10.0, 10.0, Q.NMP)
    x_eq_mp, _ = Q.equilibrium(10.0, 10.0, Q.MP)
    rng = np.random.default_rng(16)
    x = Q.NMP.x0.copy()
    ekf = Q.EKF(x0=np.array([12.0, 12.0, 1.0, 1.0]))
    n = int(200.0 / DT)
    t0, tr = 90.0, 10.0
    X, U, G, REF = [], [], [], []
    for k in range(n):
        t = k * DT
        s = 0.0 if t < t0 else min(1.0, (t - t0) / tr)
        r = Q.NMP.copy()
        r.gamma = (1 - s) * Q.NMP.gamma + s * Q.MP.gamma
        r.k = (1 - s) * Q.NMP.k + s * Q.MP.k
        gsum = float(r.gamma.sum())
        ref = x_eq_mp if gsum >= 1.0 else x_eq_nmp
        law = law_mp if gsum >= 1.0 else law_nmp
        u = np.clip(np.asarray(law(ekf.x, ref), float).ravel(), Q.U_MIN, Q.U_MAX)
        x = Q.step_plant(x, u, DT, r)
        z = x + rng.normal(0, np.sqrt(2.37), 4)
        ekf.step(u, z, DT, r)
        X.append(x.copy()); U.append(u.copy()); G.append(gsum); REF.append(ref.copy())
    X, U = np.array(X), np.array(U)
    np.savez(os.path.join(TRAJ, "S5_handover.npz"), t=np.arange(n) * DT,
             x=X, u=U, ref=np.array(REF), gamma_sum=np.array(G))
    kh = int((t0 + tr) / DT)
    out["S5_handover"] = {
        "switch_time_s": t0, "ramp_duration_s": tr,
        "max_transient_after_switch_cm": float(np.max(np.abs(X[kh:kh + int(20 / DT), :2] - x_eq_mp[:2]))),
        "final_err_h1_cm": float(X[-1, 0] - x_eq_mp[0]),
        "final_err_h2_cm": float(X[-1, 1] - x_eq_mp[1]),
        "max_level_cm": float(X.max()),
        "input_jump_at_switch_V": float(np.max(np.abs(np.diff(U[kh - 5:kh + 5], axis=0)))),
        "stable": bool(X.max() <= Q.H_MAX),
    }
    print("  S5 handover:", out["S5_handover"], flush=True)


def s6_noise(pols, reg, regime, out):
    x_eq, _ = Q.equilibrium(10.0, 10.0, reg)
    res = {}
    for name, p in pols.items():
        row = []
        for var in (0.0, 0.5, 2.37, 5.0, 10.0):
            errs = []
            for s in range(3):
                sim = run(p, reg, reg.x0, lambda t: x_eq, 120.0, seed=100 + s,
                          meas_noise_var=var)
                errs.append(float(np.max(np.abs(sim["x"][-200:, :2] - x_eq[:2]))))
            row.append({"meas_noise_var": var, "max_ss_err_cm": float(np.mean(errs))})
        res[name] = row
        print(f"  S6 {regime} {name:20s} " +
              " ".join(f"{r['meas_noise_var']}:{r['max_ss_err_cm']:.2f}" for r in row), flush=True)
    out["S6_noise"] = res


def main():
    result = {}
    for regime, reg in (("NMP", Q.NMP), ("MP", Q.MP)):
        print(f"================ {regime} ================", flush=True)
        pols = C.build_all(reg, DT, regime)
        out = {}
        s1_nominal(pols, reg, regime, out)
        s2_staircase(pols, reg, regime, out)
        s3_disturbance(pols, reg, regime, out)
        fast = {k: v for k, v in pols.items() if k != "LTV-MPC"}
        fast["LTV-MPC"] = pols["LTV-MPC"]
        s4_degradation(fast, reg, regime, out)
        s6_noise({k: pols[k] for k in ("LTV-MPC", "Symbolic KAN", "MLP (32-32)",
                                       "Gain-scheduled LQR")}, reg, regime, out)
        result[regime] = out

    print("================ handover ================", flush=True)
    result["handover"] = {}
    s5_handover(C.SymbolicLaw("MP"), C.SymbolicLaw("NMP"), result["handover"])

    with open(os.path.join(RES, "scenarios.json"), "w") as f:
        json.dump(result, f, indent=2)
    print("wrote", os.path.join(RES, "scenarios.json"))


if __name__ == "__main__":
    main()
