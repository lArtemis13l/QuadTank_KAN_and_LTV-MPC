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
Uniform closed-loop interface for every controller compared in the paper.

Each factory returns a callable  u = pi(x_est, ref)  with u already clipped to
the actuator box, so that all controllers are simulated by exactly the same
closed-loop driver (qtlib.run_closed_loop).
"""

from __future__ import annotations

import functools
import os

import numpy as np
import torch

import policyform as PF
import qtlib as Q
import symbolic as SY

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models")


# ------------------------------------------------------- symbolic KAN law
class SymbolicLaw:
    """The deployed closed-form controller: a fixed multiply-accumulate chain."""

    def __init__(self, regime):
        d = np.load(os.path.join(MODELS, f"symbolic_law_{regime}.npz"))
        self.coef = [d["coef0"], d["coef1"]]
        self.sup = [[tuple(int(v) for v in m) for m in d["sup0"]],
                    [tuple(int(v) for v in m) for m in d["sup1"]]]
        self.regime = regime
        self.reg = PF.REGIMES[regime]

    def __call__(self, x, ref):
        f = Q.features(x, ref)
        fc = PF.clip_features(f, self.regime)   # never extrapolate the polynomial
        y = np.array([SY.design(fc, self.sup[j]) @ self.coef[j] for j in range(2)]).ravel()
        return PF.decode(y, x, ref, self.regime).ravel()

    def flops(self):
        """Multiply-accumulate operations per call, core included."""
        return sum(SY.flops(s) for s in self.sup) + PF.CORE_FLOPS

    def n_terms(self):
        return [len(s) for s in self.sup]

    def jacobian(self, x, ref):
        """Analytic d u / d phi of the deployed law (used by the safety audit)."""
        f = Q.features(x, ref)
        J = np.zeros((2, 8))
        for j in range(2):
            for v in range(8):
                J[j, v] = float(SY.d_design(f, self.sup[j], v) @ self.coef[j])
        return J * Q.NORM_U / Q.NORM_X   # chain rule through the normalisation


def gain_scheduled(law_mp, law_nmp):
    """Switches on the valve ratios, as in the deployed firmware."""
    def pi(x, ref, gamma_sum):
        return law_mp(x, ref) if gamma_sum >= 1.0 else law_nmp(x, ref)
    return pi


# ------------------------------------------------------------- neural nets
def _torch_policy(model, regime):
    model.eval()

    def pi(x, ref):
        f = torch.tensor(Q.features(x, ref), dtype=torch.float32)
        with torch.no_grad():
            y = model(f).numpy()
        return PF.decode(y, x, ref, regime).ravel()
    return pi


def mlp_policy(regime, tag="mlp"):
    from s02_train_models import MLP
    hid = (32, 32) if tag == "mlp" else (8,)
    m = MLP(hid)
    m.load_state_dict(torch.load(os.path.join(MODELS, f"{tag}_{regime}.pt")))
    return _torch_policy(m, regime)


def deeponet_policy(regime):
    from s02_train_models import DeepONet
    m = DeepONet()
    m.load_state_dict(torch.load(os.path.join(MODELS, f"deeponet_{regime}.pt")))
    return _torch_policy(m, regime)


def poly_policy(regime, degree):
    d = np.load(os.path.join(MODELS, f"poly{degree}_{regime}.npz"))
    coef, inter, powers = d["coef"], d["intercept"], d["powers"]
    sup = [tuple(int(v) for v in p) for p in powers]

    def pi(x, ref):
        f = Q.features(x, ref)
        fc = PF.clip_features(f, regime)        # same guard as the symbolic law
        y = (SY.design(fc, sup) @ coef.T).ravel() + inter
        return PF.decode(y, x, ref, regime).ravel()
    return pi


# --------------------------------------------------------------- baselines
def lqr_policy(reg, dt):
    """
    Gain-scheduled LQR: at every reference the equilibrium (x_eq, u_eq) is
    computed in closed form and the discrete LQR gain is solved about it.
    Gains are cached, so online cost is one matrix-vector product.

    The input weight is the same detuned R = I used by the core of the deployed
    law (policyform.R_CORE), selected because the teacher's own R = 1e-3 makes
    the unconstrained LQR saturate on any appreciable error; this makes the
    baseline as strong as we could make it.
    """
    cache = {}

    def pi(x, ref):
        key = (round(float(ref[0]), 4), round(float(ref[1]), 4))
        if key not in cache:
            try:
                x_eq, u_eq = Q.equilibrium(key[0], key[1], reg)
                K, _ = Q.gs_lqr_gain(reg, x_eq, dt, R=PF.R_CORE)
            except Exception:
                x_eq, u_eq = np.asarray(ref, float), np.zeros(2)
                K = np.zeros((2, 4))
            cache[key] = (x_eq, u_eq, K)
        x_eq, u_eq, K = cache[key]
        u = u_eq - K @ (np.asarray(x, float) - x_eq)
        return np.clip(u, Q.U_MIN, Q.U_MAX)
    return pi


def mpc_policy(reg, dt, mpc=None):
    mpc = mpc or Q.LTVMPC()
    state = {"u": np.zeros(2)}

    def pi(x, ref):
        u, _ = mpc.solve(x, ref, state["u"], dt, reg)
        state["u"] = u
        return u
    return pi


def build_all(reg, dt, regime_name):
    """Every controller for a given regime, ready for closed-loop simulation."""
    return {
        "LTV-MPC": mpc_policy(reg, dt),
        "Symbolic KAN": SymbolicLaw(regime_name),
        "MLP (32-32)": mlp_policy(regime_name, "mlp"),
        "MLP (8)": mlp_policy(regime_name, "mlp_small"),
        "DeepONet": deeponet_policy(regime_name),
        "Poly ridge (deg 2)": poly_policy(regime_name, 2),
        "Poly ridge (deg 3)": poly_policy(regime_name, 3),
        "Gain-scheduled LQR": lqr_policy(reg, dt),
    }
