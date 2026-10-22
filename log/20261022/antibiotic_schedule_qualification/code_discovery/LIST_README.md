# LIST (Large-scale Integrated System for Testing)
Ultra-multiplexed Microfluidic Platform for 3D Microbial Culture and Antibiotic Susceptibility Testing


## Overview
This platform is an ultra-multiplexed microfluidic system designed for high-throughput 3D bacterial culturing and antibiotic susceptibility testing (AST). This repository contains the operational code, design files, and analysis tools for the platform. The platform supports automated control, real-time colony tracking, and synergy analysis for antibiotic combinations, addressing challenges like antimicrobial resistance (AMR) in microfludics.

This repository contains a collection of folders related to a software project, including:
- **AutoCAD Design**: Files and resources for AutoCAD designs, featuring architectural and engineering outlines.
- **GUI Code with Operational File**: Codebase for the graphical user interface components to operate the LIST platform
- **Operational File for GUI**: Operational files supporting the GUI functionality, including configuration settings and run-time data.
- **Colony Tracking**: Tools and scripts for tracking colony and segmentation are aimed at monitoring and analyzing colony behavior.
- **Graphvis plot code**: Scheme for colony tracking and segmentation pipelines.
- **hydrogel diffusion modeling**: not be updated yet.
  
## File folders


**1.1 AutoCAD_Design**

Purpose: This folder contains original design files for the ultra-multiplexed microfluidic chip, made by two layers, created in AutoCAD or similar CAD software. 

![](images/chip.png)
**[Chip Images]**


These files define the physical layout of microfluidic channels, chambers, and sensors on the chip (AutoCAD v.2025) 

Contents:
Design Files: .dwg or .dxf files for microfluidic chip layouts, specifying dimensions, flow paths, and integration points for actuators, made by two layers.
CAD Templates: Reusable templates for standard microfluidic components (e.g., valves, jucntion, chambers, input and output) to streamline design.
Documentation: Guides for best practices in microfluidic design, including material selection (e.g., PDMS, glass) and fabrication techniques (e.g., soft lithography).
Sample Projects: Example designs for specific experiments for 3D microbial culturomics.
Operational Role: These files are used to fabricate the physical microfluidic chip. 


**1.2 GUI_Code (run by MATLAB v2016b)**

Purpose: This folder contains the source code for the GUI, which serves as the primary interface for users to control the microfluidic platform and visualize data.

Contents:
Source Code: The code is modular, with components for 
Control Panel: Interfaces to adjust parameters valve states (80 solenoids)
Setup Instructions: A README.md or similar file detailing dependencies, installation steps, and how to run the GUI locally (MATLAB v.2016)
**IMPORTANT: NEED INSTRUMENTAION SETTING** (See in details, https://www.nature.com/articles/nprot.2014.120)
Potential Code Integration: Scripts (in MATLAB, v.2025) parse CAD files to extract channel geometries or cahmbers locations, enabling the software to align control logic with the physical layout.


![](images/gui.png)
**[GUI view]**

Operational Code:
The GUI communicates with the microfluidic hardware SETUP that interfaces with functions.
Example workflow: A user adjusts a slider to set valve acuation. The GUI sends this command to the backend, which translates it into a hardware signal.


**1.3 Operational_File_for_GUI**

Purpose: This folder contains configuration files and runtime data to support the GUI’s functionality.


![](images/control.png)
**[Operational File view]**

Contents:
Configuration Files: EXCEL files, each colunmn defining settings like:

Operational Role:
The GUI reads these files at startup to initialize settings and during runtime to update configurations dynamically.

For exmample, the "Combinatorial Inputs.xlsx" file (Extended Data Fig 1a) supports GUI control for antibiotic testing. 
(A) An excerpt of the Excel file displays the first 10 rows, detailing 512 unique experimental conditions for testing combinations of nine antibiotics (amikacin, cefepime, clindamycin, levofloxacin, nitrofurantoin, rifampicin, sulfamethoxazole, tetracycline, and trimethoprim). The "Combinatorial input" column specifies active antibiotics (e.g., "1" for amikacin, "1,2" for amikacin + cefepime), with columns A–I listing corresponding valve states (e.g., [2, 3, 5, 7, 9, 11, 13, 15, 17] for Condition 1). 
(B) A diagram illustrates the full factorial design, covering individual and pairwise antibiotic interactions. 
(C) A workflow schematic shows the integration of the Excel file with a custom GUI, mapping valve states to 18 valve controls (multiplexed across 80 total valves) for precise delivery of antibiotic combinations to the 512 chambers. 
(D) A schematic of the microfluidic chip’s layout illustrates how the 512 chambers receive unique antibiotic combinations via 18 valve controls, with fluid routing indicated by color-coded channels. 
(E) A flowchart details the GUI’s role in importing the Excel file and translating sequences into real-time valve operations, ensuring accurate antibiotic delivery to each chamber.



**1.4 Colony_Tracking (run by MATLAB v2024b)**

Purpose: This folder contains tools for tracking and analyzing biological colonies (e.g., bacterial cultures) within the microfluidic chip.

Contents:
Tracking Scripts: Likely written in MATLAB (v.2024b) to detect and track colonies in images or video feeds.
Data Analysis Tools: Scripts for quantifying dynamic colony growth, segmentation with detection criteria.
Visualization Assets: Code for generating plots or export raw data to colony analysis data.
Sample Datasets: Example images testing tracking results.
Integration Guide: Instructions for connecting tracking tools to external systems, such as ImageJ FIJI plug-in tools

![](images/colony.png)
**[Results with description]**

Operational Code:
Example: A Matlab script from a microscope, applies image segmentation to identify colonies, and tracks their positions over time. Results are saved as CSV files or visualized in the GUI (Figure set).
Analytical models might be used for advanced segmentation or anomaly detection to improve detection accucary.
Real-time tracking may involve multithreading to process image streams without delaying GUI responsiveness.
Integration with GUI: The tracking scripts likely send processed data (e.g., colony counts, growth rates) to the GUI via APIs or file-based communication (e.g., writing to a shared database).

% Microbial Growth Curve Analysis for Antibiotic Synergy
% Analyzes simultaneous (A+B) and sequential (A-B, B-A) antibiotic dosing
% Uses Loewe Additivity Model to calculate Combination Index (CI) with a 4PL model


 **1.5 Graphvis plot code**: Scheme for colony tracking and segmentation pipelines.

![](images/scheme.png)
 **[Graphvis schemes]**


Note : Additional image data are available at DOI:10.5281/zenodo.18362221. 

## Contributions
Feel free to fork this repository and submit pull requests. Please ensure to follow the coding standards, include appropriate documentation, and test your changes thoroughly.

## License
This project is licensed under the License - see the [LICENSE](LICENSE) file for details.

## Contact
For any questions or suggestions, please contact the lead maintainer (yoonj@uchicago.edu).

*Last updated: Aug, 17  2026
