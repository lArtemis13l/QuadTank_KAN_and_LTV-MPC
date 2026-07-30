# Simulation and training environment

This directory holds two generations of work. Read the distinction before using
anything in it.

## Current — `revision/`

The pipeline behind the present manuscript. Numbered stage scripts regenerate every
dataset, model, result file, figure and table it reports. See
[`revision/README.md`](revision/README.md).

**This is the only part that produces current results.**

## Superseded — everything else in this directory

The notebooks and their outputs belong to an earlier version of the work, submitted
elsewhere and not accepted. They are retained for provenance, because the present
manuscript diagnoses two defects in that version and a reader may want to reproduce the
diagnosis. They are **not** refactored, and their results are **not** current.

| File | What it was | Status |
|---|---|---|
| `01_ProjectInitialization_HILSim.ipynb` | Hardware-in-the-loop interface to the STM32; symbolic law inlined in the loop | Superseded. The hardware campaign has been removed from the paper. |
| `02a_KAN_Training_NMP.ipynb` | KAN training, non-minimum phase | Superseded by `revision/s02_train_models.py` |
| `02b_KAN_Training_SafetyAudit.ipynb` | The "positive feedback" sign inversion, found by inspection | Superseded by `revision/s03_signflip_analysis.py`, which reproduces the anomaly from the rank structure of the training design instead of noticing it by eye |
| `03_CodeGen_MPC.ipynb`, `Nucleo_MPC_GenFinal/` | CVXPYgen → OSQP C solver for the STM32 | Superseded; no current result depends on it |
| `04_Paper_Plot_Generator.ipynb` | Figures for the earlier paper | Superseded by `revision/s06_make_figures.py` |
| `Data/`, `*_Test.csv`, `KAN_Unstable.csv`, `Fig_*.pdf` | Logs and plots of the earlier campaign | Superseded |
| `model/`, `figures/` | PyKAN scratch (checkpoints, activation plots) | Untracked; regenerated on training |
| **`quad_tank_golden_reference_P_minus.csv`** | The original single-trajectory distillation set | **Keep.** `revision/s03_signflip_analysis.py` reads it — it is the dataset whose rank deficiency explains the sign anomaly. |

## Why the earlier results were withdrawn

Two defects, either of which alone prevents the closed loop from converging:

* the commanded target `[10, 10, 2, 2]` is not an equilibrium of the plant, so no
  controller could drive its cost to zero; and
* the MPC's prediction horizon was 3 s against a right-half-plane zero with a 69 s time
  constant, which makes the teacher itself move in the wrong direction.

The hardware benchmark is also gone from the paper: its latency and flash figures were
measured for a different symbolic law than the one now deployed, and the board was not
available for re-measurement. Computational cost is now reported as an exact
multiply–accumulate count. Any speed-up figure quoted in earlier versions of this file
is withdrawn.

Everything here remains under the Apache-2.0 licence, "AS IS".
