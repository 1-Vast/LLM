# Cancer Stem Cells Drug-induced Plasticity

This repository contains the MATLAB scripts of the experiments presented in the article Inferring Drug-induced Plasticity via Drug Screen Data. In particular, this repository contains the following directories:

- CSC_DIP_base: This directory contains all the scripts necessary to generate in silico base experiment (Section 2.2). main_Point_Estimation.m and main_Confidence_Interval.m can generate the point estimation and confidence interval respectively in the base experiment.

- CSC_DIP_AIC: This directory contains all the scripts necessary to generate in silico AIC model selection experiment (Section 2.4). main_DIP_base_AIC.m can generate the AIC results for all different model assumptions in the manuscript.

- CSC_Robustness_relaxed_drug_assumption: This directory contains all the scripts necessary to generate the relaxed drug effect assumption experiment (Section 2.3). Please run the main_Point_Estimation.m script in this directory to reproduce the corresponding results.

- CSC_Robustness_relaxed_initial_condition: This directory contains all the scripts necessary to generate the relaxed initial proportion assumption experiment (Section 2.3). Please run the main_Point_Estimation.m script in this directory to reproduce the corresponding results.

- CSC_Robustness_limited_division: This directory contains all the scripts necessary to generate the limited division CNSC dynamics assumption experiment (Section 2.3). Please run the main_Point_Estimation.m script in this directory to reproduce the corresponding results.

- In silico experiment analysis: This directory contains all the scripts and results necessary to generate Figures 2,3,4,5,6,7,8,10. The script 'Plot_Figure*.m' can reproduce the target figure, where * denotes its index.

- In vitro experiment analysis: This directory contains all the script necessary to generate the in vitro experiment results (Section 2.5 and Section 2.6). 

    - main_in_vitro_Gastric_AIC/main_in_vitro_Gastric_TD_AIC: main script for generating AIC value of the AGS--CPX-O experiment.
    - main_in_vitro_COLO858_AIC: main script for generating AIC value of the COLO858--Vemurafenib experiment.


 
