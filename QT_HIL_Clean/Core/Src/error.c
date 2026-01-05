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

#include "glob_opts.h"
#include "error.h"
#include "printing.h"
#include "osqp_api_constants.h"

const char *OSQP_ERROR_MESSAGE[] = {
  "Problem data validation.",
  "Solver settings validation.",
  /* "Linear system solver not available.\nTried to obtain it from shared library.", */
  "Linear system solver initialization.",
  "KKT matrix factorization.\nThe problem seems to be non-convex.",
  "Memory allocation.",
  "Solver workspace not initialized.",
  "Algebra libraries not loaded.",
  "Unable to open file for writing.",
  "Invalid defines for codegen",
  "Vector/matrix not initialized.",
  "Function not implemented.",

  /* This must always be the last item in the list */
  "Unknown error code."
};


OSQPInt _osqp_error(enum osqp_error_type error_code,
		                const char*          function_name) {

  /* Don't print anything if there was no error */
  if (error_code != OSQP_NO_ERROR)
    c_print("ERROR in %s: %s\n", function_name, OSQP_ERROR_MESSAGE[error_code-1]);

  return (OSQPInt)error_code;
}

OSQPInt _osqp_error_line(enum osqp_error_type error_code,
                         const char*          function_name,
                         const char*          filename,
                         OSQPInt              line_number) {

  /* Don't print anything if there was no error */
  if (error_code != OSQP_NO_ERROR)
    c_print("ERROR in %s (%s:%" OSQP_INT_FMT "): %s\n", function_name, filename, line_number, OSQP_ERROR_MESSAGE[error_code-1]);

  return (OSQPInt)error_code;
}
