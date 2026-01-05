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

/* Header file defining printing functions */
#ifndef PRINTING_H_
#define PRINTING_H_

/* cmake generated compiler flags */
#include "osqp_configure.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Format specifier to use for the OSQP integers */
# ifdef OSQP_USE_LONG            /* Long integers */
#define OSQP_INT_FMT "lld"
# else                           /* Standard integers */
#define OSQP_INT_FMT "d"
# endif

/* Error printing function */
/* Always define this, and let implementations undefine if they want to change it */
# if __STDC_VERSION__ >= 199901L
/* The C99 standard gives the __func__ macro, which is preferred over __FUNCTION__ */
# define c_eprint(...) c_print("ERROR in %s: ", __func__); \
         c_print(__VA_ARGS__); c_print("\n");
#else
# define c_eprint(...) c_print("ERROR in %s: ", __FUNCTION__); \
         c_print(__VA_ARGS__); c_print("\n");
#endif

#ifdef OSQP_CUSTOM_PRINTING
/* Use user-provided printing functions */
# include OSQP_CUSTOM_PRINTING

#elif defined(OSQP_ENABLE_PRINTING)
/* Use standard printing routine */
# include <stdio.h>
# include <string.h>

# define c_print printf

#else
/* No printing is desired, so turn the two functions into NOPs */
# undef c_eprint
# define c_print(...)
# define c_eprint(...)

#endif  /* OSQP_CUSTOM_PRINTING */

#ifdef __cplusplus
}
#endif

#endif /* PRINTING_H_ */
