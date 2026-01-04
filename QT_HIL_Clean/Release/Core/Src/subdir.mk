################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (12.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/Src/algebra_libs.c \
../Core/Src/arm_mat_cholesky_f64.c \
../Core/Src/arm_mat_init_f64.c \
../Core/Src/arm_mat_inverse_f64.c \
../Core/Src/arm_mat_mult_f64.c \
../Core/Src/arm_mat_qr_f64.c \
../Core/Src/arm_mat_solve_lower_triangular_f64.c \
../Core/Src/arm_mat_solve_upper_triangular_f64.c \
../Core/Src/arm_mat_sub_f64.c \
../Core/Src/arm_mat_trans_f64.c \
../Core/Src/auxil.c \
../Core/Src/cpg_solve.c \
../Core/Src/cpg_workspace.c \
../Core/Src/csc_math.c \
../Core/Src/csc_utils.c \
../Core/Src/ekf.c \
../Core/Src/error.c \
../Core/Src/kan_solver.c \
../Core/Src/kkt.c \
../Core/Src/main.c \
../Core/Src/matrix.c \
../Core/Src/model_calc.c \
../Core/Src/mpc_runner.c \
../Core/Src/osqp_api.c \
../Core/Src/qdldl.c \
../Core/Src/qdldl_interface.c \
../Core/Src/scaling.c \
../Core/Src/stm32h7xx_hal_msp.c \
../Core/Src/stm32h7xx_it.c \
../Core/Src/syscalls.c \
../Core/Src/sysmem.c \
../Core/Src/system_stm32h7xx.c \
../Core/Src/util.c \
../Core/Src/vector.c \
../Core/Src/workspace.c 

OBJS += \
./Core/Src/algebra_libs.o \
./Core/Src/arm_mat_cholesky_f64.o \
./Core/Src/arm_mat_init_f64.o \
./Core/Src/arm_mat_inverse_f64.o \
./Core/Src/arm_mat_mult_f64.o \
./Core/Src/arm_mat_qr_f64.o \
./Core/Src/arm_mat_solve_lower_triangular_f64.o \
./Core/Src/arm_mat_solve_upper_triangular_f64.o \
./Core/Src/arm_mat_sub_f64.o \
./Core/Src/arm_mat_trans_f64.o \
./Core/Src/auxil.o \
./Core/Src/cpg_solve.o \
./Core/Src/cpg_workspace.o \
./Core/Src/csc_math.o \
./Core/Src/csc_utils.o \
./Core/Src/ekf.o \
./Core/Src/error.o \
./Core/Src/kan_solver.o \
./Core/Src/kkt.o \
./Core/Src/main.o \
./Core/Src/matrix.o \
./Core/Src/model_calc.o \
./Core/Src/mpc_runner.o \
./Core/Src/osqp_api.o \
./Core/Src/qdldl.o \
./Core/Src/qdldl_interface.o \
./Core/Src/scaling.o \
./Core/Src/stm32h7xx_hal_msp.o \
./Core/Src/stm32h7xx_it.o \
./Core/Src/syscalls.o \
./Core/Src/sysmem.o \
./Core/Src/system_stm32h7xx.o \
./Core/Src/util.o \
./Core/Src/vector.o \
./Core/Src/workspace.o 

C_DEPS += \
./Core/Src/algebra_libs.d \
./Core/Src/arm_mat_cholesky_f64.d \
./Core/Src/arm_mat_init_f64.d \
./Core/Src/arm_mat_inverse_f64.d \
./Core/Src/arm_mat_mult_f64.d \
./Core/Src/arm_mat_qr_f64.d \
./Core/Src/arm_mat_solve_lower_triangular_f64.d \
./Core/Src/arm_mat_solve_upper_triangular_f64.d \
./Core/Src/arm_mat_sub_f64.d \
./Core/Src/arm_mat_trans_f64.d \
./Core/Src/auxil.d \
./Core/Src/cpg_solve.d \
./Core/Src/cpg_workspace.d \
./Core/Src/csc_math.d \
./Core/Src/csc_utils.d \
./Core/Src/ekf.d \
./Core/Src/error.d \
./Core/Src/kan_solver.d \
./Core/Src/kkt.d \
./Core/Src/main.d \
./Core/Src/matrix.d \
./Core/Src/model_calc.d \
./Core/Src/mpc_runner.d \
./Core/Src/osqp_api.d \
./Core/Src/qdldl.d \
./Core/Src/qdldl_interface.d \
./Core/Src/scaling.d \
./Core/Src/stm32h7xx_hal_msp.d \
./Core/Src/stm32h7xx_it.d \
./Core/Src/syscalls.d \
./Core/Src/sysmem.d \
./Core/Src/system_stm32h7xx.d \
./Core/Src/util.d \
./Core/Src/vector.d \
./Core/Src/workspace.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Src/%.o Core/Src/%.su Core/Src/%.cyclo: ../Core/Src/%.c Core/Src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=gnu11 -DUSE_PWR_LDO_SUPPLY -DUSE_HAL_DRIVER -DSTM32H753xx -c -I../Core/Inc -I../Drivers/STM32H7xx_HAL_Driver/Inc -I../Drivers/STM32H7xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32H7xx/Include -I../Drivers/CMSIS/Include -Os -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv5-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Core-2f-Src

clean-Core-2f-Src:
	-$(RM) ./Core/Src/algebra_libs.cyclo ./Core/Src/algebra_libs.d ./Core/Src/algebra_libs.o ./Core/Src/algebra_libs.su ./Core/Src/arm_mat_cholesky_f64.cyclo ./Core/Src/arm_mat_cholesky_f64.d ./Core/Src/arm_mat_cholesky_f64.o ./Core/Src/arm_mat_cholesky_f64.su ./Core/Src/arm_mat_init_f64.cyclo ./Core/Src/arm_mat_init_f64.d ./Core/Src/arm_mat_init_f64.o ./Core/Src/arm_mat_init_f64.su ./Core/Src/arm_mat_inverse_f64.cyclo ./Core/Src/arm_mat_inverse_f64.d ./Core/Src/arm_mat_inverse_f64.o ./Core/Src/arm_mat_inverse_f64.su ./Core/Src/arm_mat_mult_f64.cyclo ./Core/Src/arm_mat_mult_f64.d ./Core/Src/arm_mat_mult_f64.o ./Core/Src/arm_mat_mult_f64.su ./Core/Src/arm_mat_qr_f64.cyclo ./Core/Src/arm_mat_qr_f64.d ./Core/Src/arm_mat_qr_f64.o ./Core/Src/arm_mat_qr_f64.su ./Core/Src/arm_mat_solve_lower_triangular_f64.cyclo ./Core/Src/arm_mat_solve_lower_triangular_f64.d ./Core/Src/arm_mat_solve_lower_triangular_f64.o ./Core/Src/arm_mat_solve_lower_triangular_f64.su ./Core/Src/arm_mat_solve_upper_triangular_f64.cyclo ./Core/Src/arm_mat_solve_upper_triangular_f64.d ./Core/Src/arm_mat_solve_upper_triangular_f64.o ./Core/Src/arm_mat_solve_upper_triangular_f64.su ./Core/Src/arm_mat_sub_f64.cyclo ./Core/Src/arm_mat_sub_f64.d ./Core/Src/arm_mat_sub_f64.o ./Core/Src/arm_mat_sub_f64.su ./Core/Src/arm_mat_trans_f64.cyclo ./Core/Src/arm_mat_trans_f64.d ./Core/Src/arm_mat_trans_f64.o ./Core/Src/arm_mat_trans_f64.su ./Core/Src/auxil.cyclo ./Core/Src/auxil.d ./Core/Src/auxil.o ./Core/Src/auxil.su ./Core/Src/cpg_solve.cyclo ./Core/Src/cpg_solve.d ./Core/Src/cpg_solve.o ./Core/Src/cpg_solve.su ./Core/Src/cpg_workspace.cyclo ./Core/Src/cpg_workspace.d ./Core/Src/cpg_workspace.o ./Core/Src/cpg_workspace.su ./Core/Src/csc_math.cyclo ./Core/Src/csc_math.d ./Core/Src/csc_math.o ./Core/Src/csc_math.su ./Core/Src/csc_utils.cyclo ./Core/Src/csc_utils.d ./Core/Src/csc_utils.o ./Core/Src/csc_utils.su ./Core/Src/ekf.cyclo ./Core/Src/ekf.d ./Core/Src/ekf.o ./Core/Src/ekf.su ./Core/Src/error.cyclo ./Core/Src/error.d ./Core/Src/error.o ./Core/Src/error.su ./Core/Src/kan_solver.cyclo ./Core/Src/kan_solver.d ./Core/Src/kan_solver.o ./Core/Src/kan_solver.su ./Core/Src/kkt.cyclo ./Core/Src/kkt.d ./Core/Src/kkt.o ./Core/Src/kkt.su ./Core/Src/main.cyclo ./Core/Src/main.d ./Core/Src/main.o ./Core/Src/main.su ./Core/Src/matrix.cyclo ./Core/Src/matrix.d ./Core/Src/matrix.o ./Core/Src/matrix.su ./Core/Src/model_calc.cyclo ./Core/Src/model_calc.d ./Core/Src/model_calc.o ./Core/Src/model_calc.su ./Core/Src/mpc_runner.cyclo ./Core/Src/mpc_runner.d ./Core/Src/mpc_runner.o ./Core/Src/mpc_runner.su ./Core/Src/osqp_api.cyclo ./Core/Src/osqp_api.d ./Core/Src/osqp_api.o ./Core/Src/osqp_api.su ./Core/Src/qdldl.cyclo ./Core/Src/qdldl.d ./Core/Src/qdldl.o ./Core/Src/qdldl.su ./Core/Src/qdldl_interface.cyclo ./Core/Src/qdldl_interface.d ./Core/Src/qdldl_interface.o ./Core/Src/qdldl_interface.su ./Core/Src/scaling.cyclo ./Core/Src/scaling.d ./Core/Src/scaling.o ./Core/Src/scaling.su ./Core/Src/stm32h7xx_hal_msp.cyclo ./Core/Src/stm32h7xx_hal_msp.d ./Core/Src/stm32h7xx_hal_msp.o ./Core/Src/stm32h7xx_hal_msp.su ./Core/Src/stm32h7xx_it.cyclo ./Core/Src/stm32h7xx_it.d ./Core/Src/stm32h7xx_it.o ./Core/Src/stm32h7xx_it.su ./Core/Src/syscalls.cyclo ./Core/Src/syscalls.d ./Core/Src/syscalls.o ./Core/Src/syscalls.su ./Core/Src/sysmem.cyclo ./Core/Src/sysmem.d ./Core/Src/sysmem.o ./Core/Src/sysmem.su ./Core/Src/system_stm32h7xx.cyclo ./Core/Src/system_stm32h7xx.d ./Core/Src/system_stm32h7xx.o ./Core/Src/system_stm32h7xx.su ./Core/Src/util.cyclo ./Core/Src/util.d ./Core/Src/util.o ./Core/Src/util.su ./Core/Src/vector.cyclo ./Core/Src/vector.d ./Core/Src/vector.o ./Core/Src/vector.su ./Core/Src/workspace.cyclo ./Core/Src/workspace.d ./Core/Src/workspace.o ./Core/Src/workspace.su

.PHONY: clean-Core-2f-Src

