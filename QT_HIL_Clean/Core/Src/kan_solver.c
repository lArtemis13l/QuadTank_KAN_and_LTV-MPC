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

/*
 * kan_solver.c
 */

#include "arm_math.h"
#include "model_calc.h"
#include "kan_solver.h"
#include "config.h"

extern double active_gamma[2];
extern double active_k_pump[2];

static inline float64_t sq(float64_t x) {
    return x * x;
}

// The Master Function: Decides which KAN to use and passes the data along
void KAN_Solve_Active(float64_t *x_ref, float64_t *x_est, float64_t *u_out) {

    // 1. Check the active physics configuration
    double g1 = active_gamma[0];
    double g2 = active_gamma[1];

    // 2. Route the data to the correct solver
    // Logic: If sum of gammas < 1, it is Non-Minimum Phase (The "Hard" Mode)
    if ((g1 + g2) < 1.0) {
        KAN_Solve_Non_Minimum_Phase(x_ref, x_est, u_out);
    }
    else {
        KAN_Solve_Minimum_Phase(x_ref, x_est, u_out);
    }
}

void KAN_Solve_Non_Minimum_Phase(float64_t *x_ref, float64_t *x_est, float64_t *u_out) {
	// declarations
	double x_1 = x_est[0] / 20;
	double x_2 = x_est[1] / 20;
	double x_3 = x_est[2] / 20;
	double x_4 = x_est[3] / 20;
	double x_5 = (x_ref[0] - x_est[0]) / 20;
	double x_6 = (x_ref[1] - x_est[1]) / 20;
	double x_7 = (x_ref[2] - x_est[2]) / 20;
	double x_8 = (x_ref[3] - x_est[3]) / 20;

	// calculations
	double u1_raw = -0.0968267150455004*x_1 - 11.5522264852875*x_2 + 0.24044993223655*x_3 - 1.44435744660287*x_4 + 3.84138434219758*x_5 + 0.391351450674539*x_7 - 0.0423460680693187*x_8 + 0.025617322294888*sq(-10.0001583099365*x_1 - 9.9999303817749) - 0.0544665046036243*sq(-1.67091600341674*x_1 + 3.95226181130601*x_3 - 3.95791483032078*x_4 + 0.0593229825848618*x_8 - 1.27748664741404) + 1.17289172290718;
	double u2_raw = 0.255779834040008*x_1 - 2.6622473754427*x_2 + 0.507210095953869*x_3 - 0.526471928427408*x_4 + 0.555851813772936*x_5 + 0.0940461332965534*x_7 - 0.0233986858247011*x_8 + 0.00577475079669435*sq(-10.0001583099365*x_1 - 9.9999303817749) + 0.0999103412032127*sq(-1.67086166413561*x_1 + 3.95213328116732*x_3 - 3.9577861163422*x_4 + 0.0593210533626737*x_8 - 1.27916169855622) - 0.470107100576432;

	u_out[0] = u1_raw * 12;
	u_out[1] = u2_raw * 12;

	// --- ADD THIS SAFETY LAYER ---
	if (u_out[0] < 0.0) u_out[0] = 0.0; // Pumps can't suck
	if (u_out[0] > 12.0) u_out[0] = 12.0; // Max voltage

	if (u_out[1] < 0.0) u_out[1] = 0.0;
	if (u_out[1] > 12.0) u_out[1] = 12.0;
}

void KAN_Solve_Minimum_Phase(float64_t *x_ref, float64_t *x_est, float64_t *u_out) {
	// declarations
	double x_1 = x_est[0] / 20;
	double x_2 = x_est[1] / 20;
	double x_3 = x_est[2] / 20;
	double x_4 = x_est[3] / 20;
	double x_5 = (x_ref[0] - x_est[0]) / 20;
	double x_6 = (x_ref[1] - x_est[1]) / 20;
	double x_7 = (x_ref[2] - x_est[2]) / 20;
	double x_8 = (x_ref[3] - x_est[3]) / 20;

	// calculations
	double u1_raw = -7.51353229127572*x_1 + 1.67695980545613*x_2 + 1.380334825995*x_3 + 1.41885837254108*x_4 + 13.5659177492177*x_5 + 12.9515220240303*x_6 + 0.00379216831156005*x_7 - 1.86035150507028*x_8 - 0.0111200432541076*sq(-9.99997997283936*x_7 - 10.0) + 4.32878089027349;
	double u2_raw = 29.5483484887791*x_1 - 6.28340398110346*x_2 - 5.79130579228489*x_3 - 6.12823903142176*x_4 + 53.3293360232067*x_5 + 50.5462118426809*x_6 - 0.326246124210953*x_7 + 9.99471715160938*x_8 + 0.0438193227065643*sq(-9.99997997283936*x_7 - 10.0) - 16.1091995441476;

	u_out[0] = u1_raw * 12;
	u_out[1] = u2_raw * 12;

	// --- ADD THIS SAFETY LAYER ---
	if (u_out[0] < 0.0) u_out[0] = 0.0; // Pumps can't suck
	if (u_out[0] > 12.0) u_out[0] = 12.0; // Max voltage

	if (u_out[1] < 0.0) u_out[1] = 0.0;
	if (u_out[1] > 12.0) u_out[1] = 12.0;
}

