#include "arm_math.h"
#include "model_calc.h"
#include "config.h"

void KAN_Solve_Active(float64_t *x_ref, float64_t *x_est, float64_t *u_out);

void KAN_Solve_Minimum_Phase(float64_t *x_ref, float64_t *x_est, float64_t *u_out);

void KAN_Solve_Non_Minimum_Phase(float64_t *x_ref, float64_t *x_est, float64_t *u_out);