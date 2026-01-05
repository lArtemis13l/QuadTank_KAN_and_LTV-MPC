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

#include "arm_math.h"
#include "model_calc.h"
#include "config.h"

void KAN_Solve_Active(float64_t *x_ref, float64_t *x_est, float64_t *u_out);

void KAN_Solve_Minimum_Phase(float64_t *x_ref, float64_t *x_est, float64_t *u_out);

void KAN_Solve_Non_Minimum_Phase(float64_t *x_ref, float64_t *x_est, float64_t *u_out);