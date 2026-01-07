# Simulation & Training Environment (Raw Artifacts)

**Warning:** This directory contains the raw Jupyter Notebooks used to generate the results for the IEEE ICCA submission. To preserve the scientific integrity of the experiments and the exact state that produced the figures, these files have **not** been refactored or sanitized.

## File Guide

While the codebase is raw, the following files represent the core workflow:

*   **`01_ProjectInitialization_HILSim.ipynb`**: The main hardware-in-the-loop interface that communicates with the STM32.
*   **`02a_KAN_Training_NMP.ipynb`**: The training pipeline that produced the final 3µs Symbolic KAN.
*   **`02b_KAN_Training_SafetyAudit.ipynb`**: Contains the forensic analysis of the "Positive Feedback" sign inversion (Safety Audit).
*   **`03_CodeGen_MPC.ipynb`**: The script generating the OSQP Quadratic Programming solver. **`Nucleo_MPC_GenFinal`** displays the resulting code. 
*   **`04_Paper_Plot_Generator.ipynb`**: Generates the vector PDFs used in the paper.

## Note on Code Style
These notebooks are effectively "Digital Laboratory Notes." They contain debug prints, experimental branches, and intermediate outputs. They are provided "AS IS" under the Apache 2.0 license to ensure transparency and reproducibility of the 3µs vs 19ms (stutters reaching 81ms) benchmark results.
