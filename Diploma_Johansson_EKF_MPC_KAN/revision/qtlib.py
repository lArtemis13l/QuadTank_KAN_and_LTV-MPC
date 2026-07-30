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
Shared library for the quadruple-tank / LTV-MPC / KAN distillation study.

Everything the revision experiments need lives here so that every script uses
*exactly* the same plant, estimator and MPC formulation.

Plant parameters follow Johansson (2000), Table 1 ("P-" = minimum phase,
"P+" = non-minimum phase).  Note that the original submission's simulation code
used k = [2.826, 2.961]; the revision uses Johansson's published values so that
the paper's parameter table and the executable code agree.

"""

from __future__ import annotations

import numpy as np

G = 981.0  # cm/s^2

# --- geometry (identical in both regimes) ---------------------------------
A_TANK = np.array([28.0, 32.0, 28.0, 32.0])          # cm^2
A_OUT = np.array([0.071, 0.057, 0.071, 0.057])       # cm^2

U_MIN, U_MAX = 0.0, 12.0    # pump voltage limits (V)
H_MIN, H_MAX = 0.0, 20.0    # tank level limits (cm); 20 cm = overflow


class Regime:
    """Container for one operating regime of the quadruple-tank."""

    def __init__(self, name, gamma, k, x0):
        self.name = name
        self.gamma = np.asarray(gamma, float)
        self.k = np.asarray(k, float)
        self.x0 = np.asarray(x0, float)

    @property
    def is_nmp(self):
        return self.gamma.sum() < 1.0

    def copy(self, **kw):
        d = dict(name=self.name, gamma=self.gamma.copy(),
                 k=self.k.copy(), x0=self.x0.copy())
        d.update(kw)
        return Regime(**d)


# Johansson (2000) Table 1
MP = Regime("MP", gamma=[0.70, 0.60], k=[3.33, 3.35], x0=[12.4, 12.7, 1.8, 1.4])
NMP = Regime("NMP", gamma=[0.43, 0.34], k=[3.14, 3.29], x0=[12.6, 13.0, 4.8, 4.9])


# ---------------------------------------------------------------- dynamics
def f_cont(x, u, reg):
    """Continuous-time Johansson dynamics dx/dt."""
    h = np.maximum(np.asarray(x, float).ravel(), 1e-3)
    u = np.asarray(u, float).ravel()
    g1, g2 = reg.gamma
    k1, k2 = reg.k
    a, A = A_OUT, A_TANK
    return np.array([
        -a[0] / A[0] * np.sqrt(2 * G * h[0]) + a[2] / A[0] * np.sqrt(2 * G * h[2]) + g1 * k1 * u[0] / A[0],
        -a[1] / A[1] * np.sqrt(2 * G * h[1]) + a[3] / A[1] * np.sqrt(2 * G * h[3]) + g2 * k2 * u[1] / A[1],
        -a[2] / A[2] * np.sqrt(2 * G * h[2]) + (1 - g2) * k2 * u[1] / A[2],
        -a[3] / A[3] * np.sqrt(2 * G * h[3]) + (1 - g1) * k1 * u[0] / A[3],
    ])


def step_plant(x, u, dt, reg, rk4=True):
    """One integration step of the true (nonlinear) plant."""
    x = np.asarray(x, float).ravel()
    if rk4:
        k1 = f_cont(x, u, reg)
        k2 = f_cont(x + 0.5 * dt * k1, u, reg)
        k3 = f_cont(x + 0.5 * dt * k2, u, reg)
        k4 = f_cont(x + dt * k3, u, reg)
        x_next = x + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    else:
        x_next = x + dt * f_cont(x, u, reg)
    return np.maximum(x_next, 0.0)


def jac_A_cont(x, reg):
    """Continuous-time state Jacobian df/dx."""
    h = np.maximum(np.asarray(x, float).ravel(), 1.0)
    a, A = A_OUT, A_TANK
    J = np.zeros((4, 4))
    for i in range(4):
        J[i, i] = -a[i] / A[i] * np.sqrt(G / (2 * h[i]))
    J[0, 2] = a[2] / A[0] * np.sqrt(G / (2 * h[2]))
    J[1, 3] = a[3] / A[1] * np.sqrt(G / (2 * h[3]))
    return J


def B_cont(reg):
    g1, g2 = reg.gamma
    k1, k2 = reg.k
    A = A_TANK
    B = np.zeros((4, 2))
    B[0, 0] = g1 * k1 / A[0]
    B[3, 0] = (1 - g1) * k1 / A[3]
    B[1, 1] = g2 * k2 / A[1]
    B[2, 1] = (1 - g2) * k2 / A[2]
    return B


def affine_model(x_op, u_op, dt, reg):
    """Euler-discretised affine model x+ = A x + B u + d about (x_op, u_op)."""
    A = np.eye(4) + dt * jac_A_cont(x_op, reg)
    B = dt * B_cont(reg)
    x_nl = np.asarray(x_op, float) + dt * f_cont(x_op, u_op, reg)
    d = x_nl - (A @ np.asarray(x_op, float) + B @ np.asarray(u_op, float))
    return A, B, d


# ------------------------------------------------------------- equilibrium
def equilibrium(h1_ref, h2_ref, reg):
    """
    Exact steady state of the quadruple-tank for a commanded pair (h1, h2).

    Only two levels can be assigned independently: with two pumps the plant has
    a two-dimensional equilibrium manifold.  Given (h1, h2), the steady inputs
    and the *induced* levels h3, h4 are uniquely determined.  Returns
    (x_eq, u_eq) or raises ValueError when u_eq leaves the actuator box.
    """
    g1, g2 = reg.gamma
    k1, k2 = reg.k
    a = A_OUT
    M = np.array([[g1 * k1, (1 - g2) * k2],
                  [(1 - g1) * k1, g2 * k2]])
    rhs = np.array([a[0] * np.sqrt(2 * G * h1_ref),
                    a[1] * np.sqrt(2 * G * h2_ref)])
    u_eq = np.linalg.solve(M, rhs)
    h3 = ((1 - g2) * k2 * u_eq[1] / a[2]) ** 2 / (2 * G)
    h4 = ((1 - g1) * k1 * u_eq[0] / a[3]) ** 2 / (2 * G)
    x_eq = np.array([h1_ref, h2_ref, h3, h4])
    if not (U_MIN - 1e-9 <= u_eq.min() and u_eq.max() <= U_MAX + 1e-9):
        raise ValueError(f"setpoint ({h1_ref},{h2_ref}) needs u={u_eq}, outside [0,12] V")
    return x_eq, u_eq


def u_eq_of_ref(ref, reg):
    """
    Steady-state (feed-forward) input for a commanded reference, in closed form.

    Only the two controlled levels enter:
        [g1 k1  (1-g2) k2 ; (1-g1) k1  g2 k2] u_eq = [a1 sqrt(2 g h1r);
                                                      a2 sqrt(2 g h2r)]
    so u_eq = c1 sqrt(h1r) + c2 sqrt(h2r) with c1, c2 fixed per regime -- two
    square roots and four multiply-adds.  Splitting the policy as
    u = u_eq(r) + dpi(x, r) means the learned part only has to produce the
    *deviation* from steady state, and therefore only has to vanish (not match
    a large constant) at the set-point.  Any residual imitation error then
    enters the closed loop multiplied by the loop sensitivity instead of being
    added directly to the actuator command.
    """
    ref = np.asarray(ref, float).reshape(-1, 4)
    g1, g2 = reg.gamma
    k1, k2 = reg.k
    M = np.array([[g1 * k1, (1 - g2) * k2],
                  [(1 - g1) * k1, g2 * k2]])
    Minv = np.linalg.inv(M)
    rhs = np.stack([A_OUT[0] * np.sqrt(2 * G * np.maximum(ref[:, 0], 0.0)),
                    A_OUT[1] * np.sqrt(2 * G * np.maximum(ref[:, 1], 0.0))], axis=1)
    return rhs @ Minv.T


def transmission_zeros(reg, x_eq):
    """Continuous-time transmission zeros of the (h1,h2) output channel."""
    import scipy.linalg as sla
    A = jac_A_cont(x_eq, reg)
    B = B_cont(reg)
    C = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0]])
    n, m = A.shape[0], B.shape[1]
    p = C.shape[0]
    M = np.block([[A, B], [C, np.zeros((p, m))]])
    N = np.block([[np.eye(n), np.zeros((n, m))],
                  [np.zeros((p, n)), np.zeros((p, m))]])
    ev = sla.eig(M, N, right=False)
    return np.array([z for z in ev if np.isfinite(z)])


# ------------------------------------------------------------------- MPC
Q_MPC = np.diag([40.0, 40.0, 5.0, 5.0])
R_MPC = np.diag([1e-3, 1e-3])
HORIZON = 30
# The prediction model is discretised far more coarsely than the control loop.
# This matters: the plant's dominant time constants are 50-70 s and the NMP
# transmission zero sits at 0.0146 rad/s (69 s), so a horizon of N*dt_pred must
# span at least that.  The original study used dt_pred = 0.1 s, giving a 3 s
# horizon -- shorter than the inverse response it was supposed to anticipate,
# which makes the controller effectively myopic and, on a non-minimum-phase
# plant, drives it the wrong way.  N = 30 at dt_pred = 4 s spans 120 s, about
# 1.7 times the time constant of the right-half-plane zero.
DT_PRED = 4.0


class LTVMPC:
    """
    Affine LTV-MPC with input and state constraints, compiled once with CVXPY
    parameters so that repeated solves reuse the same canonicalised problem.
    """

    def __init__(self, horizon=HORIZON, Q=Q_MPC, R=R_MPC,
                 u_lim=(U_MIN, U_MAX), h_lim=(H_MIN, H_MAX), solver="OSQP"):
        import cvxpy as cp
        self.cp = cp
        self.N = horizon
        self.solver = solver
        self.Ap = cp.Parameter((4, 4), name="A")
        self.Bp = cp.Parameter((4, 2), name="B")
        self.dp = cp.Parameter(4, name="d")
        self.x0p = cp.Parameter(4, name="x0")
        self.refp = cp.Parameter(4, name="ref")
        x = cp.Variable((4, horizon + 1), name="x")
        u = cp.Variable((2, horizon), name="u")
        cost = 0
        cons = [x[:, 0] == self.x0p]
        for k in range(horizon):
            cost += cp.quad_form(x[:, k] - self.refp, Q, assume_PSD=True)
            cost += cp.quad_form(u[:, k], R, assume_PSD=True)
            cons += [x[:, k + 1] == self.Ap @ x[:, k] + self.Bp @ u[:, k] + self.dp]
            cons += [u[:, k] >= u_lim[0], u[:, k] <= u_lim[1]]
            cons += [x[:, k + 1] >= h_lim[0], x[:, k + 1] <= h_lim[1]]
        cost += cp.quad_form(x[:, horizon] - self.refp, Q, assume_PSD=True)
        self.prob = cp.Problem(cp.Minimize(cost), cons)
        self.x, self.u = x, u
        self.fail_count = 0

    def solve(self, x_est, ref, u_prev, dt, reg, dt_pred=None):
        """`dt` is the control period; `dt_pred` the prediction discretisation."""
        A, B, d = affine_model(np.maximum(x_est, 0.0), u_prev,
                               DT_PRED if dt_pred is None else dt_pred, reg)
        self.Ap.value = A
        self.Bp.value = B
        self.dp.value = d
        self.x0p.value = np.clip(np.asarray(x_est, float), H_MIN, H_MAX)
        self.refp.value = np.asarray(ref, float)
        try:
            self.prob.solve(solver=self.solver, warm_start=True)
        except Exception:
            self.fail_count += 1
            return np.clip(u_prev, U_MIN, U_MAX), False
        if self.u.value is None or not np.all(np.isfinite(self.u.value)):
            self.fail_count += 1
            return np.clip(u_prev, U_MIN, U_MAX), False
        return np.clip(self.u.value[:, 0], U_MIN, U_MAX), True


# --------------------------------------------------------------------- EKF
class EKF:
    """Canonical EKF with full-state measurement (H = I4)."""

    def __init__(self, x0, P0=1.0, q=1e-4, r=100.0):
        self.x = np.asarray(x0, float).copy()
        self.P = np.eye(4) * P0
        self.Q = np.eye(4) * q
        self.R = np.eye(4) * r
        self.H = np.eye(4)

    def step(self, u, z, dt, reg):
        x_pred = step_plant(self.x, u, dt, reg)
        F = np.eye(4) + dt * jac_A_cont(self.x, reg)
        P_pred = F @ self.P @ F.T + self.Q
        S = P_pred + self.R
        K = P_pred @ np.linalg.solve(S, np.eye(4))
        self.x = np.maximum(x_pred + K @ (z - x_pred), 0.0)
        self.P = (np.eye(4) - K) @ P_pred
        return self.x


# ---------------------------------------------------------- LQR baseline
def gs_lqr_gain(reg, x_eq, dt, Q=Q_MPC, R=R_MPC):
    """Discrete-time LQR gain about the equilibrium (gain-scheduled baseline)."""
    import scipy.linalg as sla
    Ad = np.eye(4) + dt * jac_A_cont(x_eq, reg)
    Bd = dt * B_cont(reg)
    P = sla.solve_discrete_are(Ad, Bd, Q, R)
    K = np.linalg.solve(R + Bd.T @ P @ Bd, Bd.T @ P @ Ad)
    return K, P


# --------------------------------------------------------------- metrics
def rmse(a, b, axis=None):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2, axis=axis)))


def nrmse_pct(pred, true, scale):
    """RMSE normalised by an explicit physical scale (documented, not implicit)."""
    return 100.0 * float(np.sqrt(np.mean((np.asarray(pred) - np.asarray(true)) ** 2))) / scale


def nmae_pct(pred, true, scale):
    return 100.0 * float(np.mean(np.abs(np.asarray(pred) - np.asarray(true)))) / scale


def total_variation(u):
    u = np.asarray(u)
    return float(np.sum(np.abs(np.diff(u, axis=0))))


def settling_time(t, y, ref, band=0.02, scale=None):
    """First time after which |y-ref| stays inside band*scale for the rest of the run."""
    y = np.asarray(y).ravel()
    t = np.asarray(t).ravel()
    s = abs(ref) if scale is None else scale
    tol = band * s
    ok = np.abs(y - ref) <= tol
    idx = len(ok)
    for i in range(len(ok) - 1, -1, -1):
        if not ok[i]:
            idx = i + 1
            break
        idx = i
    return float(t[idx]) if idx < len(t) else float("nan")


# -------------------------------------------------- generic closed loop
def run_closed_loop(policy, reg, x0, ref_fn, dt, T, seed=0,
                    meas_noise_var=2.37, proc_noise_var=1e-6, use_ekf=True):
    """
    Simulate the plant under an arbitrary policy u = policy(x_est, ref).

    Returns a dict of arrays: t, x, u, ref, x_est.
    """
    rng = np.random.default_rng(seed)
    n = int(round(T / dt))
    x = np.asarray(x0, float).copy()
    ekf = EKF(x0=np.array([12.0, 12.0, 1.0, 1.0]))
    u = np.zeros(2)
    X, U, Rf, Xe = [], [], [], []
    for k in range(n):
        t = k * dt
        ref = np.asarray(ref_fn(t), float)
        x_est = ekf.x if use_ekf else x
        u = np.clip(np.asarray(policy(x_est, ref), float).ravel(), U_MIN, U_MAX)
        x = step_plant(x, u, dt, reg)
        x = x + rng.normal(0.0, np.sqrt(proc_noise_var), 4) * dt
        x = np.maximum(x, 0.0)
        z = x + rng.normal(0.0, np.sqrt(meas_noise_var), 4)
        if use_ekf:
            ekf.step(u, z, dt, reg)
        else:
            ekf.x = x.copy()
        X.append(x.copy()); U.append(u.copy()); Rf.append(ref.copy()); Xe.append(x_est.copy())
    return dict(t=np.arange(n) * dt, x=np.array(X), u=np.array(U),
                ref=np.array(Rf), x_est=np.array(Xe))


# ------------------------------------------------------ feature encoding
NORM_X = 20.0   # cm  -- level normalisation constant
NORM_U = 12.0   # V   -- voltage normalisation constant


def features(x, ref):
    """The 8-dimensional policy input [h/20, (ref-h)/20] used by every learner."""
    x = np.asarray(x, float).reshape(-1, 4)
    ref = np.asarray(ref, float).reshape(-1, 4)
    return np.hstack([x / NORM_X, (ref - x) / NORM_X])
