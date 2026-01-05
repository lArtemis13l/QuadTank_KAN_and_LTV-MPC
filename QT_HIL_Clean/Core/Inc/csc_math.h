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

#ifndef CSC_MATH_H
# define CSC_MATH_H


# include "osqp_api_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/****************************************************************************
* CSC Matrix updates                                                        *
*****************************************************************************/

 /**
  * Update elements of a previously allocated csc matrix
  * without changing its sparsity structure.
  *
  *  If Mx_new_idx is OSQP_NULL, Mx_new is assumed to be as long as M->x
  *  and all matrix entries are replaced
  *
  *  The caller is responsible for ensuring that P_new_n is not greater
  *  the number of nonzeros in the matrix
  *
  * @param  M          csc matrix
  * @param  Mx_new     Vector of new elements in M->x
  * @param  Mx_new_idx Index mapping new elements to positions in M->x
  * @param  P_new_n    Number of new elements to be changed
  *
  */

void csc_update_values(OSQPCscMatrix*   M,
                       const OSQPFloat* Mx_new,
                       const OSQPInt*   Mx_new_idx,
                       OSQPInt          P_new_n);

/*****************************************************************************
* CSC Algebraic Operations                                                   *
******************************************************************************/

// A = sc*A
void csc_scale(OSQPCscMatrix* A, OSQPFloat sc);

// A = diag(L)*A
void csc_lmult_diag(OSQPCscMatrix* A, const OSQPFloat* L);

// A = A*diag(R)
void csc_rmult_diag(OSQPCscMatrix* A, const OSQPFloat* R);

// d = diag(At*diag(D)*A)
void csc_AtDA_extract_diag(const OSQPCscMatrix* A,
                           const OSQPFloat*     D,
                                 OSQPFloat*     d);

//y = alpha*A*x + beta*y, where A is symmetric and only triu is stored
void csc_Axpy_sym_triu(const OSQPCscMatrix* A,
                       const OSQPFloat*     x,
                             OSQPFloat*     y,
                             OSQPFloat      alpha,
                             OSQPFloat      beta);

//y = alpha*A*x + beta*y
void csc_Axpy(const OSQPCscMatrix* A,
              const OSQPFloat*     x,
                    OSQPFloat*     y,
                    OSQPFloat      alpha,
                    OSQPFloat      beta);

//y = alpha*A^T*x + beta*y
void csc_Atxpy(const OSQPCscMatrix* A,
               const OSQPFloat*     x,
                     OSQPFloat*     y,
                     OSQPFloat      alpha,
                     OSQPFloat      beta);

// // returns 1/2 x'*P*x
// OSQPFloat csc_quad_form(const csc *P, const OSQPFloat *x);

// E[i] = inf_norm(M(:,i))
void csc_col_norm_inf(const OSQPCscMatrix* M, OSQPFloat* E);

// E[i] = inf_norm(M(i,:))
void csc_row_norm_inf(const OSQPCscMatrix* M, OSQPFloat* E);

// E[i] = inf_norm(M(i,:)), where M stores triu part only
void csc_row_norm_inf_sym_triu(const OSQPCscMatrix* M, OSQPFloat* E);

#ifdef __cplusplus
}
#endif

#endif /* ifndef CSC_MATH_H */
