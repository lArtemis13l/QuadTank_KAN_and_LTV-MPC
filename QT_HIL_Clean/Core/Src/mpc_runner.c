#include "mpc_runner.h"
#include "cpg_solve.h"      // Solver functions (cpg_solve)
#include "cpg_workspace.h"  // Solver structures (cpg_params, cpg_info)
#include "config.h"
#include <string.h>         // For memset (safety)

// Adjust loop horizon if different from Python, but usually it's fixed
#define MPC_HORIZON 30
#define CLAMP(x, low, high)  (((x) > (high)) ? (high) : (((x) < (low)) ? (low) : (x)))

void Run_MPC_Step(double *x_est, double *x_ref, double *u_opt_out,
                  double *A_flat, double *B_flat, double *d_vec) {

    // 1. Safety Clamp x_est (The "Anti-Crash" layer)
    cpg_float x0_safe[4];
    for(int i=0; i<4; i++) x0_safe[i] = (cpg_float)(x_est[i] < 0.0 ? 0.0 : x_est[i]);

    // 2. Transpose A (Row-Major C -> Column-Major OSQP)
    for (int r = 0; r < 4; r++) {
        for (int c = 0; c < 4; c++) {
            cpg_update_A(c * 4 + r, (cpg_float)A_flat[r * 4 + c]);
        }
    }

    // 3. Transpose B (Row-Major C -> Column-Major OSQP)
    for (int r = 0; r < 4; r++) {
        for (int c = 0; c < 2; c++) {
            cpg_update_B(c * 4 + r, (cpg_float)B_flat[r * 2 + c]);
        }
    }

    // 4. Update Vectors
    for (int i = 0; i < 4; i++) {
        cpg_update_d(i, (cpg_float)d_vec[i]);
        cpg_update_x0(i, x0_safe[i]);
        cpg_update_ref(i, (cpg_float)x_ref[i]);
    }

    // 5. SOLVE
    cpg_solve();

    // 6. RETRIEVE RESULT
    u_opt_out[0] = CLAMP((double)CPG_Prim.u[0], 0.0, 12.0);
    u_opt_out[1] = CLAMP((double)CPG_Prim.u[1], 0.0, 12.0);
}
