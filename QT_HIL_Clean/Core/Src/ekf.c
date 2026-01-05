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

/* Core/Src/ekf.c */
#include "ekf.h"
#include "model_calc.h"
#include <string.h> 
#include <math.h>

// PATCH: Manual implementation of Matrix Addition (Missing in CMSIS 5.9.0)
void arm_mat_add_f64(const arm_matrix_instance_f64 *pSrcA, const arm_matrix_instance_f64 *pSrcB, arm_matrix_instance_f64 *pDst) {
    uint32_t numSamples = pSrcA->numRows * pSrcA->numCols;

    for (uint32_t i = 0; i < numSamples; i++) {
        pDst->pData[i] = pSrcA->pData[i] + pSrcB->pData[i];
    }
}

// Remove 'static inline' to avoid complexity, or keep 'static' and rename
static void Mat_Init(arm_matrix_instance_f64 *S, uint16_t nRows, uint16_t nCols, float64_t *pData) {
    S->numRows = nRows;
    S->numCols = nCols;
    S->pData = pData;
}

void EKF_Init(EKF_Handle_t *ekf, float64_t *initial_guess) {
    
    Mat_Init(&ekf->x, N_STATES, 1, ekf->x_data);
    Mat_Init(&ekf->P, N_STATES, N_STATES, ekf->P_data);
    Mat_Init(&ekf->Q, N_STATES, N_STATES, ekf->Q_data);
    Mat_Init(&ekf->R, N_STATES, N_STATES, ekf->R_data);
    Mat_Init(&ekf->F, N_STATES, N_STATES, ekf->F_data);

    // --- STEP 2: Set the actual Values ---
    
    // A. Set Initial State x (Copy from argument)
    // We treat the matrix as a simple array here
    for(int i=0; i<N_STATES; i++) {
        ekf->x_data[i] = initial_guess[i];
    }

    memset(ekf->P_data, 0, N_STATES * N_STATES * sizeof(float64_t));

    for (int i = 0; i < N_STATES; i++) {
        ekf->P_data[i * N_STATES + i] = 1.0; 
    }

    // C. Set Q and R (From your config.h constants)
    memset(ekf->Q_data, 0, N_STATES * N_STATES * sizeof(float64_t));
    memset(ekf->R_data, 0, N_STATES * N_STATES * sizeof(float64_t));

    // Fill diagonals
    for (int i = 0; i < N_STATES; i++) {
        ekf->Q_data[i * N_STATES + i] = Q_EKF_VAL; 
        ekf->R_data[i * N_STATES + i] = R_EKF_VAL; 
    }
}

void EKF_Predict(EKF_Handle_t *ekf, float64_t *u_volts) {
    
    Get_Nonlinear_Model(ekf->x_data, u_volts, DT_SECONDS, ekf->x_data);

    Get_Jacobian_F(ekf->x_data, DT_SECONDS, ekf->F_data);
    
    float64_t temp1_data[16]; 
    arm_matrix_instance_f64 Temp1;
    Mat_Init(&Temp1, 4, 4, temp1_data);
    
    float64_t temp2_data[16]; 
    arm_matrix_instance_f64 Temp2;
    Mat_Init(&Temp2, 4, 4, temp2_data);
    
    float64_t f_trans_data[16]; 
    arm_matrix_instance_f64 F_trans;
    Mat_Init(&F_trans, 4, 4, f_trans_data);

    // Temp1 = F * P
    arm_mat_mult_f64(&ekf->F, &ekf->P, &Temp1);
    // F_trans = F'
    arm_mat_trans_f64(&ekf->F, &F_trans);
    // Temp2 = Temp1 * F'
    arm_mat_mult_f64(&Temp1, &F_trans, &Temp2);
    // P = Temp2 + Q
    arm_mat_add_f64(&Temp2, &ekf->Q, &ekf->P);
}

void EKF_Update(EKF_Handle_t *ekf, float64_t *z_meas) {
    // --- SETUP TEMP MATRICES ---
    // We only need a few scratching pads, we can reuse them!
    float64_t temp1_data[16]; 
    arm_matrix_instance_f64 Temp1;
    Mat_Init(&Temp1, 4, 4, temp1_data);

    float64_t temp2_data[16]; 
    arm_matrix_instance_f64 Temp2;
    Mat_Init(&Temp2, 4, 4, temp2_data);

    float64_t temp_vec_data[4]; 
    arm_matrix_instance_f64 TempVec;
    Mat_Init(&TempVec, 4, 1, temp_vec_data);

    // --- STEP 1: INNOVATION (Residual) y = z - Hx ---
    // Since H is Identity, this is just y = z - x
    
    // Create Measurement Vector z
    float64_t z_data[4]; 
    arm_matrix_instance_f64 z;
    Mat_Init(&z, 4, 1, z_data);
    
    // Copy input array to matrix data
    memcpy(z_data, z_meas, 4 * sizeof(float64_t));

    // Calculate y = z - x
    // Reuse TempVec for y
    arm_matrix_instance_f64 y = TempVec; 
    arm_mat_sub_f64(&z, &ekf->x, &y);


    // --- STEP 2: SYSTEM UNCERTAINTY S = HPH' + R ---
    // Since H is Identity: S = P + R
    
    float64_t s_data[16]; arm_matrix_instance_f64 S;
    Mat_Init(&S, 4, 4, s_data);
    
    arm_mat_add_f64(&ekf->P, &ekf->R, &S);


    // --- STEP 3: KALMAN GAIN K = PH' * inv(S) ---
    // Since H is Identity: K = P * inv(S)
    
    float64_t s_inv_data[16]; 
    arm_matrix_instance_f64 S_inv;
    Mat_Init(&S_inv, 4, 4, s_inv_data);
    
    // Invert S
    arm_mat_inverse_f64(&S, &S_inv); // Note: Check for singularity return in real code!
    
    // Calculate K (We store K in the struct directly if defined there, or temp)
    float64_t k_data[16]; 
    arm_matrix_instance_f64 K;
    Mat_Init(&K, 4, 4, k_data);
    
    arm_mat_mult_f64(&ekf->P, &S_inv, &K);


    // --- STEP 4: UPDATE STATE x = x + Ky ---
    
    // TempVec = K * y
    arm_mat_mult_f64(&K, &y, &TempVec);
    
    // x = x + TempVec
    arm_mat_add_f64(&ekf->x, &TempVec, &ekf->x);


    // --- STEP 5: UPDATE COVARIANCE P = (I - KH)P ---
    // numerically more stable: P = P - KP since H is identity
    
    // Temp1 = K * P
    arm_mat_mult_f64(&K, &ekf->P, &Temp1);
    
    // P = P - Temp1
    arm_mat_sub_f64(&ekf->P, &Temp1, &ekf->P);
}

