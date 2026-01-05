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
 * mpc_runner.h
 */

#ifndef MPC_RUNNER_H
#define MPC_RUNNER_H

void Run_MPC_Step(double *x_est, double *x_ref, double *u_opt_out,
                  double *A_flat, double *B_flat, double *d_vec);

#endif
