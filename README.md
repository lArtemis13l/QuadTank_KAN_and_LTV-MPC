# Certifiable approximation of model predictive control laws

**Author:** Adilkhan Salkimbayev — **Licence:** Apache-2.0

Code and data for a study of what can and cannot be certified about an offline
approximation of a linear time-varying MPC law, on the Johansson quadruple-tank
benchmark in both its minimum-phase (MP) and non-minimum-phase (NMP) configurations.

Everything reported in the accompanying manuscript is produced by the numbered stage
scripts in [`QuadTank_Project/revision/`](QuadTank_Project/revision). Start there.

---

## What the study finds

The deployed controller is

```
u = sat[ u_eq(r)  +  K e  +  w(e) * U_max * f(phi(x, r)) ]
     feed-forward   LQR core   learned correction
```

with a gate `w(e) = min(||e||^2 / s^2, 1)` that vanishes quadratically at the set-point.

| Finding | Evidence |
|---|---|
| The **symbolic read-out**, not the network, is a dominant error source | MP: a 2.43 % imitation error becomes 7.85 % under off-the-shelf `auto_symbolic`; a convex refit recovers it to 5.51 %. NMP: 4.45 % → 10.97 % → 9.11 % |
| An unconstrained read-out **violates negative feedback** on up to 30 % of the operating box | Driven to 0 % (MP) / 0.4 % (NMP) by an affine inequality inside a convex least-squares fit, for ≤ 0.2 pp of accuracy — and in NMP the constraint *improves* accuracy |
| The gate makes **zero steady-state offset and local stability structural** | Substituting random coefficients (σ up to 100) leaves the closed-loop spectral radius unchanged to ~1e-10 |
| KAN support selection is **not measurably better** than direct sparse regression | Across 11 term budgets × 2 regimes the two curves sit within a few tenths of a percentage point of each other; neither dominates |
| The benchmark **cannot justify distillation** | With a correct horizon the MPC beats a well-tuned gain-scheduled LQR by only 7–9 %, so there is little for any approximator to lose |

Deployed law: **4 terms/pump (MP, 30 multiply–accumulates)** and **48 terms/pump
(NMP, 203)**, certified locally exponentially stable (ρ ≤ 0.9988) at every set-point
tested, 97–100 % stable under ±20 % parameter perturbation.

### Two defects in the earlier version of this work, reported rather than quietly fixed

* **The commanded target was not an equilibrium.** With two pumps the equilibrium set is
  two-dimensional: fixing `(h1, h2)` determines `h3, h4`. In the NMP regime the
  equilibrium at (10, 10) is `[10, 10, 4.16, 3.44]` cm, so `[10, 10, 2, 2]` is
  unreachable and *no* controller — the MPC included — could drive its cost to zero.
* **The prediction horizon was ~20x shorter than the inverse response.** The
  right-half-plane zero has a 69 s time constant; the original MPC used N = 30 at
  Δt_p = 0.1 s — a **3-second** horizon. A myopic controller on a non-minimum-phase
  plant moves in the wrong direction. The revision uses Δt_p = 4 s, with the control
  loop still at 0.1 s.

Either alone prevents the closed loop from converging.

---

## Repository layout

| Path | Status |
|---|---|
| `QuadTank_Project/revision/` | **Current.** The pipeline behind the manuscript — see its [README](QuadTank_Project/revision/README.md). |
| `QuadTank_Project/quad_tank_golden_reference_P_minus.csv` | **Current dependency.** The original single-trajectory dataset whose rank deficiency the sign-flip analysis diagnoses; `s03` reads it. |
| `QuadTank_Project/*.ipynb`, `Data/`, `Nucleo_MPC_GenFinal/`, other `*.csv` and `*.pdf` | **Superseded.** Retained for provenance only. |
| `legacy_photos/` | **Legacy.** Photographs of the hardware-in-the-loop bench and IDE from the earlier version. Kept as a record that the work was carried out; no result in the current paper depends on it. |

### On the superseded material

The notebooks, the generated OSQP C solver and the hardware-in-the-loop logs belong to
an earlier version of this work. They are kept because the manuscript diagnoses that
version's defects and a reader may want to reproduce the diagnosis — not because they
produce any current result. Nothing under `revision/` imports them, with the single
exception noted in the table above.

The STM32 firmware (`QT_HIL_Clean/`) has been deleted outright: with the hardware
campaign gone from the paper, nothing referenced it. It remains recoverable from the
git history if ever needed (`git log --all -- QT_HIL_Clean`).

The hardware campaign has been removed from the paper. Its latency and flash figures
were measured for a different symbolic law than the one now deployed, and the
microcontroller was not available for re-measurement, so retaining them would have
mixed measured numbers with carried-over ones. Computational cost is now reported as an
exact multiply–accumulate count, which is a property of the control law rather than of
a processor. **Any speed-up figure appearing in the git history of this file is
withdrawn.**

---

## Reproducing

```bash
cd QuadTank_Project/revision
pip install -r ../../requirements.txt
python s01_generate_dataset.py     # ~7 min   datasets, both regimes
python s02_train_models.py         # ~20 min  KAN, MLP, DeepONet, polynomial baselines
python s02b_sparsify.py            # ~10 min  term-budget sweep, certified selection
python s03_signflip_analysis.py    # ~2 min   root cause of the sign anomaly
python s04_stability.py            # ~12 min  certificate, ROA, Monte-Carlo, constraints
python s04b_invariance.py          # ~1 min   structural properties (P1), (P2)
python s05_scenarios.py            # ~12 min  closed-loop scenario campaign
python s06_make_figures.py         # ~1 min   figures
python s07_make_tables.py          # <1 min   LaTeX tables
python s08_key_numbers.py          # <1 min   every number quoted in the prose
```

Results land in `revision/results/`; `key_numbers.json` collects every quantity the
manuscript states in text.

Questions and issues: open a GitHub issue, or contact **@lArtemis13l**.
