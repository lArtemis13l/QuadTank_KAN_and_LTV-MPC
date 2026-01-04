/* Core/Inc/config.h */
#ifndef CONFIG_H
#define CONFIG_H

// --- 1. Dimensions ---
#define N_STATES    4
#define N_INPUTS    2
#define N_MEAS      2  // We only measure h1, h2
//#define USE_MINIMUM_PHASE  // <--- Comment this out for Minimum Phase (P-)
#define USE_NON_MINIMUM_PHASE     // <--- Keep this for Non-Minimum Phase (P+)

// --- 2. Timing ---
// 1. The Hardware Cycle (Fast)
// This is for the EKF and the actual Loop Timer
#define DT_SECONDS      0.003   // 3ms
#define SAMPLING_MS     3       // For HAL_Delay or Timers

// 2. The MPC Prediction Step (Slow / Far-Sighted)
// This allows the MPC to see 30 * 0.1 = 3.0 seconds into the future
// even though we are updating the control every 3ms.
#define DT_MPC_HORIZON  0.1     // 100ms steps for prediction

// --- 3. Physical Constraints ---
#define MAX_VOLTAGE 12.0f
#define MIN_VOLTAGE 0.0f
#define MAX_LEVEL   40.0f
#define MIN_LEVEL   0.0f

// --- 4. Tuning (Golden Reference) ---
// These match python "Grand Unification" cell
// We use 'static const' so they are burnt into flash memory
static const double AREAS[4]  = {28.0, 32.0, 28.0, 32.0};
static const double HOLES[4]  = {0.071, 0.057, 0.071, 0.057};
static const double GAMMA_MINUS[2]  = {0.7, 0.6};
static const double GAMMA_PLUS[2] = {0.43, 0.34};
static const double K_PUMP_MINUS[2] = {3.33, 3.35};
static const double K_PUMP_PLUS[2] = {3.14, 3.29};
static const double G_CONST   = 981.0;

// EKF Tuning
// Note: We will define the matrices in ekf.c, but scalars go here
static const double R_EKF_VAL = 100.0; // dt reduced from 0.1s to 0.003 s, thus the change
static const double Q_EKF_VAL = 1e-4; // Trust the Johansson model!

#endif // CONFIG_H
