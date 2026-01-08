# Symbolic KAN vs. MPC on Embedded Hardware (STM32H7)

**Author:** Adilkhan Salkimbayev

**Status:** Submitted to IEEE ICCA 2026

## Overview
This repository contains the source code and experimental data for benchmarking **Symbolic Kolmogorov-Arnold Networks (KAN)** against **Certainty Equivalence MPC** on a Non-Minimum Phase Quad-Tank system.

**Key Result:** KAN achieves a **~19500x speedup** average case (0.99µs vs 19.3ms) and **~80294x speedup** (1.02µs vs 81.9ms) worst-case while maintaining control stability under disturbance.

## Hardware Setup
![Setup](setup_photo.jpg) 
- **MCU:** STM32H753ZI (Cortex-M7 @ 480MHz)
- **Laptop:** Acer Nitro 16 AN16-41 (AMD Ryzen 7 7840HS, RTX 4060, 16GB DDR5 RAM)
- **Method:** Hardware-in-the-Loop (HIL) via UART (921600 Baud)
- **Solver:** OSQP (for MPC) vs. Symbolic Inference (for KAN)

## Results
| Controller | Avg Latency | Worst-Case | CPU Load |
|:----------:|:-----------:|:----------:|:--------:|
| MPC (OSQP) | 19 ms       | 81 ms      | ~100%    |
| Symbolic KAN| 1.0 µs     | 1.02 µs     | 0.033%    |

## Folder Structure
- `Firmware/` (QT_HIL_Clean): C code for STM32 (System Workbench / CubeIDE).
- `Simulation/` (Diploma_Johansson_KAN_MPC_EKF): Python Plant model (ODE), Training scripts (PyKAN), and Data Logs.
- `Paper/`: PDF of my IEEE ICCA submission. (Draft, v1.0.5)
