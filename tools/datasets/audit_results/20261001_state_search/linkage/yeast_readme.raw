[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4627227.svg)](https://doi.org/10.5281/zenodo.4627227)

# Cycloop

`Cycloop` is the repository containing the MATLAB code that supports the findings of the study: 'Automatic synchronisation of the cell cycle in budding yeast through closed-loop feedback control.'


# Repo Contents
+ [Computational_Analysis](./Computational_Analysis)
+ [Illustrative_Platform_Code](./Illustrative_Platform_Code)
+ [Simulator](./Simulator)
+ [Supplementary_Data_1](./Supplementary_Data_1)

# System Requirements
## Hardware Requirements
`Cycloop` requires only a standard computer with enough RAM to run the code in the MATLAB environment.

## OS Requirements
This package is supported for macOS Catalina and Windows 10. The package has been tested on the following systems:
+ macOS Catalina
+ Windows 10


## Software Dependencies
+ MATLAB R2019a
+ Additional MATLAB toolboxes (e.g. Signal Processing Toolbox, Image Processing Toolbox, etc.)

# Installation Guide
1. Download the repository from https://github.com/dibbelab/Cycloop .
2. Unpack the files.
3. Start MATLAB and navigate to the `Cycloop` folder.


# Demo
See the [Instructions for Use](#instructions-for-use) section.

# Instructions for Use
## Simulator
Set the working directory to `./Simulator/`. 

+ Run the script `main_code.m` to generate the simulations shown in Fig. 3b-e and Fig. 4b-e.
+ Run the script `make_SFIG2_bd.m` to generate the analysis shown in Supplementary Fig. 2b, d.
+ Run the script `make_SFIG2_ce.m` to generate the analysis shown in Supplementary Fig. 2c, e.


## Computational Analysis
### Non-Cycling Strain
Set the working directory to `./Computational_Analysis/NonCycling/`.

+ Run the script `Main.m` to generate the outputs related to the microfluidics experiments shown in Fig. 2, Fig. 3f-t, Supplementary Fig. 3, Supplementary Fig. 5, and Supplementary Fig. 6.
+ Run the script `make_SuppFig1_abc.m` to generate the outputs related to the microfluidics experiment shown in Supplementary Fig. 1a-c.
+ Run the script `make_SuppFig1_def.m` to generate the single-cell traces shown in Supplementary Fig. 1d-f.
+ Run the script `make_SuppFig4.m` to generate the quantitative analysis shown in Supplementary Fig. 4a, c, e, g.

#### Single-cell traces
To regenerate the single-cell traces, follow these steps:
1. Download the raw images from https://zenodo.org/record/4516319/files/Raw_images%28NonCycling%29.zip .
2. Unpack the raw images in the folder `./Computational_Analysis/NonCycling/Raw_images/`.
3. Delete the `*.mat` files located in the folder `./Computational_Analysis/NonCycling/Cell_traces/`.
4. Run the script `Main.m`.

### Cycling Strain
Set the working directory to `./Computational_Analysis/Cycling/`.
+ Run the script `main_script.m` to generate the outputs related to the microfluidics experiments shown in Fig. 4f-t, Supplementary Fig. 7 and Supplementary Fig. 8.
+ Run the script `make_SFIG4.m` to generate the quantitative analysis shown in Supplementary Fig. 4b, d, f, h.
+ Run the script `make_SFIG9.m` to generate the correlation analysis shown in Supplementary Fig. 9.

#### Single-cell traces
To regenerate the single-cell traces, follow these steps:
1. Download the raw images from https://zenodo.org/record/4516319/files/Raw_images%28Cycling%29.zip .
2. Unpack the raw images in the folder `./Computational_Analysis/Cycling/Raw_images/`.
3. Delete the `*.mat` files located in the folder `./Computational_Analysis/Cycling/Cell_traces/`.
4. Run the script `main_script.m`.

# Illustrative Code
## Illustrative Platform Code
The folder `./Illustrative_Platform_Code` contains the illustrative code used to perform the microfluidics control experiments.

# License
This code is licensed under the **GNU General Public License v3.0**.
