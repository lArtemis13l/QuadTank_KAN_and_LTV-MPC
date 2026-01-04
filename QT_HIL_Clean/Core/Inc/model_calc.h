/* Core/Inc/model_calc.h */
#ifndef MODEL_CALC_H
#define MODEL_CALC_H

void Get_Nonlinear_Model(double *x, double *u, double dt, double *x_next);
void Get_Jacobian_F(double *x, double dt, double *F_matrix_data);
void Get_Linear_Model_Affine(double *x_op, double *u_op, double dt,
                             double *A_flat, double *B_flat, double *d_vec);

#endif
