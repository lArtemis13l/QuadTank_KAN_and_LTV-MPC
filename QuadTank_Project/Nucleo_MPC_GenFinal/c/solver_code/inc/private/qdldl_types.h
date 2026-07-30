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
 * Fix the types that QDLDL uses for the generated code to match
 * the OSQP types and be C89 compliant.
 */

#ifndef QDLDL_TYPES_H
# define QDLDL_TYPES_H

#include "osqp_api_types.h"

# ifdef __cplusplus
extern "C" {
# endif /* ifdef __cplusplus */

#include <limits.h> //for the QDLDL_INT_TYPE_MAX

/* Set the QDLDL integer and float types the same as OSQP */
typedef OSQPInt    QDLDL_int;   /* for indices */
typedef OSQPFloat  QDLDL_float; /* for numerical values  */

/* Always use int for bool because we must be C89 compliant */
typedef int   QDLDL_bool;

/* Maximum value of the signed type QDLDL_int. */
#ifdef OSQP_USE_LONG
#define QDLDL_INT_MAX LLONG_MAX
#else
#define QDLDL_INT_MAX INT_MAX
#endif

# ifdef __cplusplus
}
# endif /* ifdef __cplusplus */

#endif /* ifndef QDLDL_TYPES_H */
