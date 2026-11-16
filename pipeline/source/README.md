# BlueFood R source

This directory contains the active R scripts for the US PFOA and PFOS physiologically based kinetic (PBK) model, package setup, and certificate checks. The paths match those in the portable release.

- [r_runner.R](research/r_runner.R) runs the PBK workflow.
- [PBK model](research/assets/r/code/PFAS_PBK_US_2003_2016_Fabrega_2015.R) and [fast ODE solver](research/assets/r/code/ode_fast.R) implement the model.
- [R package setup](research/setup_R.R) and [R certificate check](research/check_R_CA.R) support installation.

Use the [portable pipeline ZIP](../BlueFood%20Portable%20Pipeline.zip?raw=1) to run the model with its inputs and environment setup. See the [pipeline guide](../README.md) for the input and script inventory.
