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
Stage 1 -- generation of the policy-distillation dataset.

Design (documented in the manuscript, Sec. "Dataset design"):

  * Two datasets, one per operating regime (MP / NMP), because the deployed
    controller is gain-scheduled.
  * Reference set-points are drawn as *reachable* equilibria: (h1r, h2r) is
    sampled uniformly from a box and the remaining two levels and the steady
    inputs follow from the exact equilibrium map (qtlib.equilibrium).  The
    original submission commanded [10,10,2,2], which is NOT an equilibrium of
    the plant; that inconsistency is removed here.
  * Two sample sources:
      (a) on-policy closed-loop LTV-MPC trajectories  -> covers the manifold
          the controller actually visits;
      (b) off-policy i.i.d. samples of (x, ref) from a box, each labelled by a
          single MPC solve -> covers states never visited on-policy and, most
          importantly, decorrelates the individual level errors e_i.
    The commanded lower-tank references of source (b) are additionally jittered
    off the equilibrium manifold.  This is not cosmetic: on the equilibrium
    manifold h3_eq and h4_eq are each of the form a*h1 + b*h2 + c*sqrt(h1*h2),
    so one fixed linear combination of (h1,h2,h3,h4) is constant for every
    reachable reference.  Without the jitter the 8-D regressor therefore stays
    rank-8 (of 9 with the intercept) and one coefficient direction of any
    linear symbolic read-out remains unidentifiable.
  * Split is by *trajectory / block*, never by row, so that no test sample is
    temporally adjacent to a training sample.

Outputs data/dataset_{MP,NMP}.npz and data/dataset_summary.json.
"""

from __future__ import annotations

import json
import os
import time

import numpy as np

import qtlib as Q

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

DT = 0.1            # sampling period used for distillation data
T_TRAJ = 60.0       # s per closed-loop trajectory
N_TRAJ = 24         # closed-loop trajectories per regime
N_RANDOM = 6000     # off-policy i.i.d. samples per regime
REF_BOX = (7.0, 15.0)     # cm, sampled independently for h1_ref and h2_ref
REF_JITTER34 = 1.5        # cm, off-manifold jitter of commanded h3_ref, h4_ref
X0_BOX = (1.0, 18.0)      # cm, initial levels for tanks 1..2
X0_BOX_LOW = (0.5, 9.0)   # cm, initial levels for tanks 3..4
SPLIT = (0.70, 0.15, 0.15)  # train / val / test, applied at trajectory level


def sample_ref(rng, reg):
    for _ in range(200):
        h1r = rng.uniform(*REF_BOX)
        h2r = rng.uniform(*REF_BOX)
        try:
            return Q.equilibrium(h1r, h2r, reg)
        except ValueError:
            continue
    raise RuntimeError("no feasible reference found")


def sample_x0(rng):
    return np.array([rng.uniform(*X0_BOX), rng.uniform(*X0_BOX),
                     rng.uniform(*X0_BOX_LOW), rng.uniform(*X0_BOX_LOW)])


def collect_regime(reg, seed):
    rng = np.random.default_rng(seed)
    mpc = Q.LTVMPC()
    X, REF, U, GRP, SRC = [], [], [], [], []
    grp = 0

    # ---- (a) on-policy closed-loop trajectories --------------------------
    t0 = time.time()
    for j in range(N_TRAJ):
        x_eq, u_eq = sample_ref(rng, reg)
        x0 = sample_x0(rng)
        u_prev = np.zeros(2)
        ekf = Q.EKF(x0=np.array([12.0, 12.0, 1.0, 1.0]))
        x = x0.copy()
        for k in range(int(T_TRAJ / DT)):
            x_est = ekf.x
            u, ok = mpc.solve(x_est, x_eq, u_prev, DT, reg)
            if ok:
                X.append(x_est.copy()); REF.append(x_eq.copy()); U.append(u.copy())
                GRP.append(grp); SRC.append(0)
            u_prev = u
            x = Q.step_plant(x, u, DT, reg)
            z = x + rng.normal(0.0, np.sqrt(2.37), 4)
            ekf.step(u, z, DT, reg)
        grp += 1
        if (j + 1) % 6 == 0:
            print(f"  [{reg.name}] trajectory {j+1}/{N_TRAJ}  ({time.time()-t0:.0f} s)")

    # ---- (b) off-policy i.i.d. coverage samples -------------------------
    n_blocks = 12
    per_block = N_RANDOM // n_blocks
    for b in range(n_blocks):
        for _ in range(per_block):
            x_eq, u_eq = sample_ref(rng, reg)
            ref = x_eq.copy()
            ref[2:] = np.maximum(ref[2:] + rng.uniform(-REF_JITTER34, REF_JITTER34, 2), 0.2)
            x = sample_x0(rng)
            u_prev = rng.uniform(Q.U_MIN, Q.U_MAX, 2)
            u, ok = mpc.solve(x, ref, u_prev, DT, reg)
            if ok:
                X.append(x.copy()); REF.append(ref.copy()); U.append(u.copy())
                GRP.append(grp); SRC.append(1)
        grp += 1
        print(f"  [{reg.name}] random block {b+1}/{n_blocks}  ({time.time()-t0:.0f} s)")

    X = np.array(X); REF = np.array(REF); U = np.array(U)
    GRP = np.array(GRP); SRC = np.array(SRC)

    # ---- split by group -------------------------------------------------
    groups = np.unique(GRP)
    rng.shuffle(groups)
    n_tr = int(round(SPLIT[0] * len(groups)))
    n_va = int(round(SPLIT[1] * len(groups)))
    g_tr, g_va, g_te = groups[:n_tr], groups[n_tr:n_tr + n_va], groups[n_tr + n_va:]
    split = np.empty(len(GRP), dtype="<U5")
    split[np.isin(GRP, g_tr)] = "train"
    split[np.isin(GRP, g_va)] = "val"
    split[np.isin(GRP, g_te)] = "test"

    F = Q.features(X, REF)              # 8-D policy input
    Y = U / Q.NORM_U                    # normalised policy output
    return dict(x=X, ref=REF, u=U, feat=F, y=Y, group=GRP, source=SRC, split=split)


def main():
    summary = {}
    for reg, seed in ((Q.MP, 20260701), (Q.NMP, 20260702)):
        print(f"=== generating dataset for regime {reg.name} ===")
        d = collect_regime(reg, seed)
        np.savez_compressed(os.path.join(DATA, f"dataset_{reg.name}.npz"), **d)
        F, split, src = d["feat"], d["split"], d["source"]
        summary[reg.name] = {
            "n_total": int(len(F)),
            "n_train": int((split == "train").sum()),
            "n_val": int((split == "val").sum()),
            "n_test": int((split == "test").sum()),
            "n_on_policy": int((src == 0).sum()),
            "n_off_policy": int((src == 1).sum()),
            "n_groups": int(len(np.unique(d["group"]))),
            "dt": DT, "T_traj": T_TRAJ,
            "ref_box_cm": list(REF_BOX),
            "feature_ranges": [[float(F[:, i].min()), float(F[:, i].max())] for i in range(8)],
            "corr_e1_e2_all": float(np.corrcoef(F[:, 4], F[:, 5])[0, 1]),
            "corr_e1_e2_onpolicy": float(np.corrcoef(F[src == 0, 4], F[src == 0, 5])[0, 1]),
            "cond_regressor": float(np.linalg.cond(np.hstack([F, np.ones((len(F), 1))]))),
            "effective_rank": int((np.linalg.svd(
                np.hstack([F, np.ones((len(F), 1))]) - np.hstack([F, np.ones((len(F), 1))]).mean(0),
                compute_uv=False) > 1e-8).sum()) + 1,
            "u_saturation_low_frac": float((d["u"] <= Q.U_MIN + 1e-6).mean()),
            "u_saturation_high_frac": float((d["u"] >= Q.U_MAX - 1e-6).mean()),
        }
        print(json.dumps(summary[reg.name], indent=2))
    with open(os.path.join(DATA, "dataset_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("saved ->", DATA)


if __name__ == "__main__":
    main()
