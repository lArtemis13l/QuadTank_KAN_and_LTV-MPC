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

#ifndef  OSQP_EXPORT_DEFINE_H
#define  OSQP_EXPORT_DEFINE_H

// Define the function attributes that are needed to mark functions as being
// visible for linking in the shared library version of OSQP
#if defined(_WIN32)
#  if defined(BUILDING_OSQP)
#    define OSQP_API_EXPORT __declspec(dllexport)
#  else
#    define OSQP_API_EXPORT __declspec(dllimport)
#  endif
#else
#  if defined(BUILDING_OSQP)
#    define OSQP_API_EXPORT __attribute__((visibility("default")))
#  else
#    define OSQP_API_EXPORT
#  endif
#endif

// Only define API export parts when using the shared library
#if defined(OSQP_SHARED_LIB)
#  define OSQP_API OSQP_API_EXPORT
#else
#  define OSQP_API
#endif

#endif /* OSQP_EXPORT_DEFINE_H */
