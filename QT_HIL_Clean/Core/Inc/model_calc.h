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

/* Core/Inc/model_calc.h */
#ifndef MODEL_CALC_H
#define MODEL_CALC_H

void Get_Nonlinear_Model(double *x, double *u, double dt, double *x_next);
void Get_Jacobian_F(double *x, double dt, double *F_matrix_data);
void Get_Linear_Model_Affine(double *x_op, double *u_op, double dt,
                             double *A_flat, double *B_flat, double *d_vec);

#endif
