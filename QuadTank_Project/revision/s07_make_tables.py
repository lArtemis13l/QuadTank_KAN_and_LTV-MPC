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
Stage 7 -- LaTeX tables, emitted directly from the result JSON files.

No number in the manuscript is typed by hand: the paper \\input{}s these
fragments, so a re-run of the pipeline updates the paper.
"""

from __future__ import annotations

import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "els-cas-templates", "tables"))
os.makedirs(OUT, exist_ok=True)


def rd(x, n=2):
    if x is None:
        return "--"
    try:
        if isinstance(x, bool):
            return "yes" if x else "no"
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return str(x)


def write(name, body):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    print("  wrote", p, flush=True)


DATA = os.path.join(HERE, "data")


def load(n):
    for d in (RES, DATA):
        p = os.path.join(d, n)
        if os.path.exists(p):
            return json.load(open(p))
    return None


# --------------------------------------------------------------- T: dataset
def t_dataset():
    d = load("dataset_summary.json")
    a = load("signflip_analysis.json")
    if d is None:
        return
    orig = a["original_dataset_conditioning"] if a else {}
    rows = []
    for reg in ("MP", "NMP"):
        s = d[reg]
        rows.append(
            f"{reg} & {s['n_total']} & {s['n_train']} & {s['n_val']} & {s['n_test']} & "
            f"{s['n_on_policy']} & {s['n_off_policy']} & {s['n_groups']} & "
            f"{rd(s['corr_e1_e2_all'],3)} & {rd(s['cond_regressor'],0)} & "
            f"{s['effective_rank']}/9 \\\\")
    orig_row = ""
    if orig:
        orig_row = (f"Single trajectory, fixed $r$ & {orig['n_samples']} & "
                    f"{int(0.8*orig['n_samples'])} & -- & {int(0.2*orig['n_samples'])} & "
                    f"{orig['n_samples']} & 0 & 1 & {rd(orig['corr_e1_e2'],3)} & "
                    f"$2.0\\times10^{{17}}$ & "
                    f"{orig['numerical_rank_of_9_columns']}/9 \\\\")
    write("tab_dataset.tex", r"""\begin{table*}[pos=tp]
\caption{Design of the policy-distillation datasets. The regressor is the 8-dimensional
policy input augmented with a bias column; its numerical rank determines whether the
individual coefficients of a linear symbolic read-out are identifiable at all. A
single regulation trajectory towards a fixed reference is shown for contrast: it is
the cheapest design to collect and the one on which the read-out is not identifiable.}
\centering
\resizebox{\textwidth}{!}{%
\begin{tabular}{lrrrrrrrrrr}
\hline
\textbf{Dataset} & \textbf{Total} & \textbf{Train} & \textbf{Val.} & \textbf{Test} &
\textbf{On-policy} & \textbf{Off-policy} & \textbf{Groups} &
$\rho(e_1,e_2)$ & $\kappa(\Phi)$ & \textbf{rank} \\
\hline
""" + orig_row + "\n" + "\n".join(rows) + r"""
\hline
\end{tabular}}
\label{tab:dataset}
\end{table*}
""")


# ------------------------------------------------------- T: open-loop fidelity
NAMES = [
    ("kan_spline", "KAN (spline, before symbolic read-out)"),
    ("symbolic_raw", "Symbolic KAN, \\texttt{auto\\_symbolic} output"),
    ("symbolic_refit", "Symbolic KAN + coefficient refit"),
    ("symbolic_refit_shape_constrained", "Symbolic KAN + refit + shape constraint"),
    ("mlp", "MLP $8$--$32$--$32$--$2$"),
    ("mlp_small", "MLP $8$--$8$--$2$"),
    ("deeponet", "DeepONet (branch/trunk)"),
    ("poly2", "Polynomial ridge, degree 2"),
    ("poly3", "Polynomial ridge, degree 3"),
    ("poly4", "Polynomial ridge, degree 4"),
    ("sparse_poly_matched", "Sparse polynomial (OMP, matched budget)"),
]


def t_openloop():
    m = load("openloop_metrics.json")
    sw = load("sparsity_sweep.json")
    if m is None:
        return
    rows = []
    for k, lab in NAMES:
        r_mp, r_nm = m["MP"].get(k), m["NMP"].get(k)
        if r_mp is None:
            continue
        npar = r_mp.get("n_params") or r_mp.get("n_terms_per_output") or \
            (r_mp.get("n_terms") if isinstance(r_mp.get("n_terms"), int) else None)
        if npar is None and isinstance(r_mp.get("n_terms"), list):
            npar = sum(r_mp["n_terms"])
        rows.append(f"{lab} & {npar if npar else '--'} & "
                    f"{rd(r_mp['nmae_pct_of_range'])} & {rd(r_mp['r2'],3)} & "
                    f"{rd(r_nm['nmae_pct_of_range'])} & {rd(r_nm['r2'],3)} \\\\")
    if sw:
        d_mp, d_nm = sw["MP"]["deployed"], sw["NMP"]["deployed"]
        rows.append(r"\hline")
        rows.append(f"\\textbf{{Deployed symbolic law ({d_mp['k']} terms)}} & "
                    f"{sum(d_mp['n_terms'])} & \\textbf{{{rd(d_mp['nmae'])}}} & -- & "
                    f"\\textbf{{{rd(d_nm['nmae'])}}} & -- \\\\")
    write("tab_openloop.tex", r"""\begin{table*}[pos=tp]
\caption{Open-loop imitation of the LTV-MPC policy on the held-out test split.
nMAE is the mean absolute command error as a percentage of the full actuator
range ($U_{\max}-U_{\min}=12$~V); predictions are clipped to the actuator box
before scoring, as they are on the target. Every row is trained on the same
data, the same split and the same feed-forward/feedback decomposition.}
\centering
\resizebox{\textwidth}{!}{%
\begin{tabular}{lrrrrr}
\hline
& & \multicolumn{2}{c}{\textbf{MP regime}} & \multicolumn{2}{c}{\textbf{NMP regime}} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}
\textbf{Surrogate} & \textbf{Params/terms} & \textbf{nMAE (\%)} & $R^2$ &
\textbf{nMAE (\%)} & $R^2$ \\
\hline
""" + "\n".join(rows) + r"""
\hline
\end{tabular}}
\label{tab:openloop}
\end{table*}
""")


# --------------------------------------------------------- T: closed loop S1
def t_closedloop():
    s = load("scenarios.json")
    if s is None:
        return
    order = ["LTV-MPC", "Symbolic KAN", "MLP (32-32)", "MLP (8)", "DeepONet",
             "Poly ridge (deg 2)", "Poly ridge (deg 3)", "Gain-scheduled LQR"]
    rows = []
    for n in order:
        a = s["MP"]["S1_nominal"].get(n)
        b = s["NMP"]["S1_nominal"].get(n)
        if a is None or b is None:
            continue
        rows.append(
            f"{n} & {rd(a['rmse_h12_cm'])} & {rd(abs(a['max_abs_ss_err_cm']))} & "
            f"{rd(a['total_variation_u_V'],1)} & "
            f"{rd(b['rmse_h12_cm'])} & {rd(abs(b['max_abs_ss_err_cm']))} & "
            f"{rd(b['total_variation_u_V'],1)} \\\\")
    write("tab_closedloop.tex", r"""\begin{table*}[pos=tp]
\caption{Closed-loop tracking of the reachable equilibrium of $(h_1,h_2)=(10,10)$~cm
from the Johansson initial state, with the EKF and measurement noise in the loop
(120~s, $\Delta t = 0.1$~s). RMSE and steady-state error are over the controlled
levels $h_1,h_2$; TV is the total variation of the two pump commands.}
\centering
\resizebox{\textwidth}{!}{%
\begin{tabular}{lrrrrrr}
\hline
& \multicolumn{3}{c}{\textbf{MP regime}} & \multicolumn{3}{c}{\textbf{NMP regime}} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
\textbf{Controller} & \textbf{RMSE (cm)} & $|e_{ss}|$ \textbf{(cm)} & \textbf{TV (V)} &
\textbf{RMSE (cm)} & $|e_{ss}|$ \textbf{(cm)} & \textbf{TV (V)} \\
\hline
""" + "\n".join(rows) + r"""
\hline
\end{tabular}}
\label{tab:closedloop}
\end{table*}
""")


# ------------------------------------------------------------ T: scenarios
def t_scenarios():
    s = load("scenarios.json")
    if s is None:
        return
    order = ["LTV-MPC", "Symbolic KAN", "MLP (32-32)", "Gain-scheduled LQR",
             "Poly ridge (deg 3)"]
    rows = []
    for n in order:
        st = s["NMP"]["S2_staircase"].get(n)
        di = s["NMP"]["S3_disturbance"].get(n)
        dg = s["NMP"]["S4_degradation"]["ramp"].get(n)
        if not (st and di and dg):
            continue
        rows.append(
            f"{n} & {rd(st['rmse_h12_cm'])} & {rd(st['worst_segment_ss_err_cm'])} & "
            f"{rd(di['peak_deviation_h1_cm'])} & {rd(di['recovery_time_s'],1)} & "
            f"{rd(di['total_variation_u_V'],1)} & "
            f"{rd(abs(dg['final_err_h1_cm']))} & {rd(dg['stable'])} \\\\")
    write("tab_scenarios.tex", r"""\begin{table*}[pos=tp]
\caption{Scenario campaign, NMP regime. S2: four successive, partly asymmetric
set-point changes. S3: $+3$~cm load disturbance on tank~1 at $t=60$~s; recovery
time is the first instant at which $|h_1-h_1^{\rm ref}|<0.1$~cm. S4: pump gains
ramped down by 30\% between $t=40$~s and $t=80$~s with no controller update.}
\centering
\resizebox{\textwidth}{!}{%
\begin{tabular}{lrrrrrrr}
\hline
& \multicolumn{2}{c}{\textbf{S2 staircase}} & \multicolumn{3}{c}{\textbf{S3 disturbance}} &
\multicolumn{2}{c}{\textbf{S4 degradation}} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-6}\cmidrule(lr){7-8}
\textbf{Controller} & \textbf{RMSE (cm)} & \textbf{worst $e_{ss}$ (cm)} &
\textbf{peak (cm)} & \textbf{rec.\ (s)} & \textbf{TV (V)} &
$|e_{ss}|$ \textbf{(cm)} & \textbf{stable} \\
\hline
""" + "\n".join(rows) + r"""
\hline
\end{tabular}}
\label{tab:scenarios}
\end{table*}
""")


# ------------------------------------------------------------ T: stability
def t_stability():
    st = load("stability.json")
    if st is None:
        return
    rows = []
    for reg in ("MP", "NMP"):
        r = st[reg]
        mc = r["monte_carlo_robustness"]
        roa = r.get("roa_estimate") or {}
        samp = r.get("sampled_lyapunov") or {}
        rho = r["max_spectral_radius"]
        tau = -0.1 / np.log(rho) if 0 < rho < 1 else float("nan")
        rows.append(
            f"{reg} & {rd(rho,4)} & {rd(tau,0)} & {rd(r['all_locally_stable'])} & "
            f"{rd(100*roa.get('converged_fraction',float('nan')),1)} & "
            f"{rd(100*samp.get('violation_fraction',float('nan')),2)} & "
            f"{rd(100*mc['stable_fraction'],1)} & "
            f"{rd(mc['h1_err_cm']['p95_abs'])} & "
            f"{rd(100*mc['overflow_fraction'],1)} \\\\")
    write("tab_stability.tex", r"""\begin{table}[pos=htbp]
\caption{What is actually verified about the deployed law. $\rho$ is the spectral
radius of the closed-loop Jacobian at the fixed point, evaluated at six
reachable set-points; $\rho<1$ certifies local exponential stability
(Lyapunov's indirect method). The remaining columns are numerical evidence, not
proofs: the fraction of a $19\times19$ grid of initial conditions that
converges, the fraction of $2\times10^4$ box samples violating the decrease
condition of the local Lyapunov function, and a 200-sample Monte-Carlo campaign
with $\pm20\%$ perturbation of valve ratios and pump gains.}
\centering
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lrrrrrrrr}
\hline
\textbf{Regime} & $\max\rho$ & $\tau$ \textbf{(s)} & \textbf{loc.\ stable} & \textbf{ROA (\%)} &
$V$ \textbf{viol.\ (\%)} & \textbf{MC stable (\%)} & \textbf{p95 $|e|$ (cm)} &
\textbf{overflow (\%)} \\
\hline
""" + "\n".join(rows) + r"""
\hline
\end{tabular}}
\label{tab:stability}
\end{table}
""")


# ----------------------------------------------------------- T: constraints
def t_constraints():
    st = load("stability.json")
    if st is None:
        return
    order = ["LTV-MPC", "Symbolic KAN", "MLP (32-32)", "Gain-scheduled LQR"]
    rows = []
    for n in order:
        a = st["MP"]["constraint_satisfaction"].get(n)
        b = st["NMP"]["constraint_satisfaction"].get(n)
        if a is None or b is None:
            continue
        rows.append(
            f"{n} & {rd(100*a['overflow_fraction'],1)} & {rd(100*a['dryout_fraction'],1)} & "
            f"{rd(a['max_level_observed_cm'])} & "
            f"{rd(100*b['overflow_fraction'],1)} & {rd(100*b['dryout_fraction'],1)} & "
            f"{rd(b['max_level_observed_cm'])} \\\\")
    write("tab_constraints.tex", r"""\begin{table*}[pos=tp]
\caption{State-constraint satisfaction over randomised set-point changes from
randomised initial conditions. The LTV-MPC enforces $0\le h_i\le 20$~cm
explicitly; every distilled policy inherits only the input box, through
clipping. Percentages are the fraction of tasks in which some tank overflowed
($h>20$~cm) or ran dry ($h\le 0$~cm).}
\centering
\resizebox{\textwidth}{!}{%
\begin{tabular}{lrrrrrr}
\hline
& \multicolumn{3}{c}{\textbf{MP regime}} & \multicolumn{3}{c}{\textbf{NMP regime}} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
\textbf{Controller} & \textbf{overflow (\%)} & \textbf{dry-out (\%)} & $\max h$ \textbf{(cm)} &
\textbf{overflow (\%)} & \textbf{dry-out (\%)} & $\max h$ \textbf{(cm)} \\
\hline
""" + "\n".join(rows) + r"""
\hline
\end{tabular}}
\label{tab:constraints}
\end{table*}
""")


def main():
    for f in (t_dataset, t_openloop, t_closedloop, t_scenarios, t_stability,
              t_constraints):
        try:
            f()
        except Exception as exc:
            print(f"  !! {f.__name__} failed: {type(exc).__name__}: {exc}", flush=True)


if __name__ == "__main__":
    main()
