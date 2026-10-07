
To reproduce, Download all RNA-Seq processed data from https://cellmodelpassports.sanger.ac.uk/downloads (rnaseq_all_20220624.zip) and decompress it in data/cellmodelpassport folder. Install the decoupleR, reshape2 and dplyr packages, and run scripts/GDSC_footprint.R

You can find the progeny pathway activity estimate with up-to-date version of the decoupleR package in results/GDSC_progeny_activities.csv (estimated with the ULM method, top 100 model weight)

You can find the TF activity estimate with up-to-date version of the decoupleR package in results/GDSC_TF_activities.csv (estimated with the ULM method, collectrI regulons, minimum 5 targets/TF)

You can find the mapping between GDSC cell IDs and cell line names in support/rnaseq_tpm_20220624_header

See https://saezlab.github.io/decoupleR/articles/pw_bk.html for more info on progeny/TF pathway activity
