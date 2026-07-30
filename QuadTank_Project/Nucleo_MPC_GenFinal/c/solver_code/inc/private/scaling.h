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

#ifndef SCALING_H
#define SCALING_H


// Functions to scale problem data
#include "osqp.h"
#include "types.h"
#include "lin_alg.h"

#ifdef __cplusplus
extern "C" {
#endif

// Enable data scaling if OSQP_EMBEDDED_MODE is disabled or if OSQP_EMBEDDED_MODE == 2
# if OSQP_EMBEDDED_MODE != 1

/**
 * Scale problem matrices
 * @param  solver OSQP solver
 * @return      exitflag
 */
OSQPInt scale_data(OSQPSolver* solver);
# endif // if OSQP_EMBEDDED_MODE != 1


/**
 * Unscale problem matrices
 * @param  solver OSQP solver
 * @return      exitflag
 */
OSQPInt unscale_data(OSQPSolver* solver);


/**
 * Unscale solution
   @param  usolx unscaled x result
   @param  usoly unscaled y result
   @param  solx  x solution to be unscaled
   @param  solx  y solution to be unscaled
 * @param  work Workspace
 * @return      exitflag
 */
OSQPInt unscale_solution(OSQPVectorf*       usolx,
                         OSQPVectorf*       usoly,
                         const OSQPVectorf* solx,
                         const OSQPVectorf* soly,
                         OSQPWorkspace*     work);

#ifdef __cplusplus
}
#endif

#endif /* ifndef SCALING_H */
