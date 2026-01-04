/*
 * mpc_runner.h
 */

#ifndef MPC_RUNNER_H
#define MPC_RUNNER_H

void Run_MPC_Step(double *x_est, double *x_ref, double *u_opt_out,
                  double *A_flat, double *B_flat, double *d_vec);

#endif
