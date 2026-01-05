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

#ifndef TIMING_H_
#define TIMING_H_

#include "osqp_configure.h"
#include "types.h"

/**
 * Timer Methods
 */

#ifdef __cplusplus
extern "C" {
#endif

#ifdef OSQP_ENABLE_PROFILING

/**
 * Create a new timer.
 * @return the timer
 */
OSQPTimer* OSQPTimer_new();

/**
 * Free an existing timer.
 * @param t Timer object to destroy
 */
void OSQPTimer_free(OSQPTimer* t);

/**
 * Start timer
 * @param t Timer object
 */
void osqp_tic(OSQPTimer* t);

/**
 * Report time
 * @param  t Timer object
 * @return   Reported time
 */
OSQPFloat osqp_toc(OSQPTimer* t);

#endif /* #ifdef OSQP_ENABLE_PROFILING */

#ifdef __cplusplus
}
#endif

#endif /* #ifdef TIMING_H_ */
