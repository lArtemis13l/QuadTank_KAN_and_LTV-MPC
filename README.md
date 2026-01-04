# Symbolic KAN vs. MPC on Embedded Hardware (STM32H7)

**Author:** Adilkhan Salkimbayev

**Status:** Submitted to IEEE ICCA 2026

## Overview
This repository contains the source code and experimental data for benchmarking **Symbolic Kolmogorov-Arnold Networks (KAN)** against **Certainty Equivalence MPC** on a Non-Minimum Phase Quad-Tank system.

**Key Result:** KAN achieves a **~6000x speedup** (3µs vs 19ms) while maintaining control stability under disturbance.

## Hardware Setup
![Setup](figures/setup_photo.jpg) 
- **MCU:** STM32H753ZI (Cortex-M7 @ 480MHz)
- **Method:** Hardware-in-the-Loop (HIL) via UART (921.6 kbps)
- **Solver:** OSQP (for MPC) vs. Symbolic Inference (for KAN)

## Results
| Controller | Avg Latency | Worst-Case | CPU Load |
|:----------:|:-----------:|:----------:|:--------:|
| MPC (OSQP) | 19 ms       | 81 ms      | ~100%    |
| Symbolic KAN| 3.4 µs     | 3.4 µs     | <0.1%    |

## Folder Structure
- `Firmware/`: C code for STM32 (System Workbench / CubeIDE).
- `Simulation/`: Python Plant model (ODE), Training scripts (PyKAN), and Data Logs.
- `Paper/`: LaTeX source and high-res figures.
