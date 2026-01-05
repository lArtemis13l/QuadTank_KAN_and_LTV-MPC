/*
 * Copyright 2026 Adilkhan Salkimbayev
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* Core/Inc/ekf.h */
#ifndef EKF_H
#define EKF_H

#include "arm_math.h"
#include "config.h"

// The EKF Object Structure
typedef struct {
    // State Vector x [4x1]
    float64_t x_data[N_STATES];
    arm_matrix_instance_f64 x;

    // Covariance P [4x4]
    float64_t P_data[N_STATES * N_STATES];
    arm_matrix_instance_f64 P;

    // Q, R, F...
    float64_t Q_data[N_STATES * N_STATES];
    arm_matrix_instance_f64 Q;

    float64_t R_data[N_STATES * N_STATES];
    arm_matrix_instance_f64 R;

    float64_t F_data[N_STATES * N_STATES];
    arm_matrix_instance_f64 F;
} EKF_Handle_t;

// --- Public Functions ---
// ONLY the declarations go here. No code!
void EKF_Init(EKF_Handle_t *ekf, float64_t *initial_guess);
void EKF_Predict(EKF_Handle_t *ekf, float64_t *u_volts);
void EKF_Update(EKF_Handle_t *ekf, float64_t *z_meas);

#endif // EKF_H
