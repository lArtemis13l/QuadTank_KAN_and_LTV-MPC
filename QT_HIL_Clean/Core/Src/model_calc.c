#include "config.h"
#include <string.h>
#include <math.h>

// --- LINKING TO MAIN.C ---
// These variables are defined in main.c. We use 'extern' to access them here.
extern double active_gamma[2];
extern double active_k_pump[2];

double get_safe_h_gradient(double h) {
    return fmax(h, 0.1); // Limit denominator to equivalent of 2cm height
}

void Mat_Vec_Mult_4x4(double *A, double *x, double *y) {
    y[0] = A[0]*x[0] + A[1]*x[1] + A[2]*x[2] + A[3]*x[3];
    y[1] = A[4]*x[0] + A[5]*x[1] + A[6]*x[2] + A[7]*x[3];
    y[2] = A[8]*x[0] + A[9]*x[1] + A[10]*x[2] + A[11]*x[3];
    y[3] = A[12]*x[0] + A[13]*x[1] + A[14]*x[2] + A[15]*x[3];
}

// The "Accumulator" fix for B*u
void Mat_Vec_Mult_Add_4x2(double *B, double *u, double *y) {
    // Row 0
    y[0] += B[0]*u[0] + B[1]*u[1];
    // Row 1
    y[1] += B[2]*u[0] + B[3]*u[1];
    // Row 2
    y[2] += B[4]*u[0] + B[5]*u[1];
    // Row 3
    y[3] += B[6]*u[0] + B[7]*u[1];
}

void Get_Nonlinear_Model(double *x, double *u, double dt, double *x_next) {

    double h1 = x[0], h2 = x[1], h3 = x[2], h4 = x[3];
    double v1 = u[0], v2 = u[1];

    // --- DYNAMIC SWITCHING ---
    // Use the active configuration set by main.c
    double g1 = active_gamma[0];
    double g2 = active_gamma[1];
    double k1 = active_k_pump[0];
    double k2 = active_k_pump[1];
    // -------------------------

    double sqrt_h1 = sqrt(2 * G_CONST * fmax(h1, 0.001));
    double sqrt_h2 = sqrt(2 * G_CONST * fmax(h2, 0.001));
    double sqrt_h3 = sqrt(2 * G_CONST * fmax(h3, 0.001));
    double sqrt_h4 = sqrt(2 * G_CONST * fmax(h4, 0.001));

    double dh1 = -(HOLES[0]/AREAS[0]) * sqrt_h1 + (HOLES[2]/AREAS[0]) * sqrt_h3 + (g1 * k1 * v1) / AREAS[0];
    double dh2 = -(HOLES[1]/AREAS[1]) * sqrt_h2 + (HOLES[3]/AREAS[1]) * sqrt_h4 + (g2 * k2 * v2) / AREAS[1];
    double dh3 = -(HOLES[2]/AREAS[2]) * sqrt_h3 + ((1 - g2) * k2 * v2) / AREAS[2];
    double dh4 = -(HOLES[3]/AREAS[3]) * sqrt_h4 + ((1 - g1) * k1 * v1) / AREAS[3];

    x_next[0] = h1 + dh1 * dt;
    x_next[1] = h2 + dh2 * dt;
    x_next[2] = h3 + dh3 * dt;
    x_next[3] = h4 + dh4 * dt;

    for(int i=0; i<4; i++) if(x_next[i] < 0) x_next[i] = 0;
}

void Get_Jacobian_F(double *x, double dt, double *F_matrix_data) {

    memset(F_matrix_data, 0, N_STATES * N_STATES * sizeof(double));

    double h1 = x[0];
    double h2 = x[1];
    double h3 = x[2];
    double h4 = x[3];

    double grad_h1 = sqrt(2 * G_CONST * get_safe_h_gradient(h1));
    double grad_h2 = sqrt(2 * G_CONST * get_safe_h_gradient(h2));
    double grad_h3 = sqrt(2 * G_CONST * get_safe_h_gradient(h3));
    double grad_h4 = sqrt(2 * G_CONST * get_safe_h_gradient(h4));

    F_matrix_data[0*4 + 0] = 1.0 - dt * (HOLES[0]/AREAS[0]) * (G_CONST / grad_h1);
    F_matrix_data[1*4 + 1] = 1.0 - dt * (HOLES[1]/AREAS[1]) * (G_CONST / grad_h2);
    F_matrix_data[2*4 + 2] = 1.0 - dt * (HOLES[2]/AREAS[2]) * (G_CONST / grad_h3);
    F_matrix_data[3*4 + 3] = 1.0 - dt * (HOLES[3]/AREAS[3]) * (G_CONST / grad_h4);

    F_matrix_data[0*4 + 2] = dt * (HOLES[2]/AREAS[0]) * (G_CONST / grad_h3);
    F_matrix_data[1*4 + 3] = dt * (HOLES[3]/AREAS[1]) * (G_CONST / grad_h4);
}

void Get_Linear_Model_Affine(double *x_op, double *u_op, double dt, double *A_flat, double *B_flat, double *d_vec) {

    Get_Jacobian_F(x_op, dt, A_flat);

    memset(B_flat, 0, N_STATES * N_INPUTS * sizeof(double));

    // --- DYNAMIC SWITCHING ---
    double g1 = active_gamma[0];
    double g2 = active_gamma[1];
    double k1 = active_k_pump[0];
    double k2 = active_k_pump[1];
    // -------------------------

    // B Matrix Layout: 4 rows, 2 cols (Row Major)
    // Col 0 (Pump 1), Col 1 (Pump 2)

    // Row 0 (h1): Affected by Pump 1 via g1
    B_flat[0*2 + 0] = dt * ((g1 * k1) / AREAS[0]);
    // B_flat[0*2 + 1] = 0;

    // Row 1 (h2): Affected by Pump 2 via g2
    // B_flat[1*2 + 0] = 0;
    B_flat[1*2 + 1] = dt * ((g2 * k2) / AREAS[1]);

    // Row 2 (h3): Affected by Pump 2 via (1-g2)
    // B_flat[2*2 + 0] = 0;
    B_flat[2*2 + 1] = dt * (((1 - g2) * k2) / AREAS[2]);

    // Row 3 (h4): Affected by Pump 1 via (1-g1)
    B_flat[3*2 + 0] = dt * (((1 - g1) * k1) / AREAS[3]);
    // B_flat[3*2 + 1] = 0;

    double x_next_nonlin[4];
    Get_Nonlinear_Model(x_op, u_op, dt, x_next_nonlin);

    double x_next_lin[4] = {0};

    // 1. Calculate A * x
    Mat_Vec_Mult_4x4(A_flat, x_op, x_next_lin);

    // 2. Accumulate B * u (The Critical Fix)
    Mat_Vec_Mult_Add_4x2(B_flat, u_op, x_next_lin);

    for (int i = 0; i < 4; i++) {
        d_vec[i] = x_next_nonlin[i] - x_next_lin[i];
    }
}
