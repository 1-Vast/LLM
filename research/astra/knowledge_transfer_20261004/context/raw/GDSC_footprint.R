library(readr)
library(dplyr)
library(decoupleR)
library(reshape2)
library(readxl)

GDSC_rnaseq_tpm_20220624 <- as.data.frame(
  read_csv("data/cellmodelpassport/rnaseq_tpm_20220624.csv"))[,-1]
names(GDSC_rnaseq_tpm_20220624)[1] <- "GENE_SYMBOLS"

GDSC_rnaseq_tpm_20220624 <- GDSC_rnaseq_tpm_20220624 %>% group_by(GENE_SYMBOLS) %>% summarise_each(mean)
GDSC_rnaseq_tpm_20220624 <- as.data.frame(GDSC_rnaseq_tpm_20220624)
GDSC_rnaseq_tpm_20220624 <- GDSC_rnaseq_tpm_20220624[!is.na(GDSC_rnaseq_tpm_20220624$GENE_SYMBOLS),]

row.names(GDSC_rnaseq_tpm_20220624) <- GDSC_rnaseq_tpm_20220624$GENE_SYMBOLS

GDSC_rnaseq_tpm_20220624 <- GDSC_rnaseq_tpm_20220624[,-1]
GDSC_rnaseq_tpm_20220624 <- GDSC_rnaseq_tpm_20220624[complete.cases(GDSC_rnaseq_tpm_20220624),]

#to match the CCLE dataset
GDSC_rnaseq_tpm_20220624_logp1 <- log2(GDSC_rnaseq_tpm_20220624+1)

#obtained from https://depmap.org/portal/download/all/ -- OmicsExpressionProteinCodingGenesTPMLogp1.csv
#to have roughly the same genes as CCLE
CCLE_coding_genes <- as.data.frame(
  read.table("support/CCLE_coding_genes.txt", quote="\"", comment.char=""))

GDSC_rnaseq_tpm_20220624_logp1 <- GDSC_rnaseq_tpm_20220624_logp1[CCLE_coding_genes[,1],]
GDSC_rnaseq_tpm_20220624_logp1 <- GDSC_rnaseq_tpm_20220624_logp1[complete.cases(GDSC_rnaseq_tpm_20220624_logp1 ),]
### progeny

progeny_model <- decoupleR::get_progeny(top = 100)

progeny_activities <- run_ulm(GDSC_rnaseq_tpm_20220624_logp1, progeny_model)

progeny_activities_wf <- reshape2::dcast(progeny_activities[,c(2,3,4)], source~condition)

write_csv(progeny_model, file = "support/progeny_model.csv")
write_csv(progeny_activities_wf, file = "results/GDSC_progeny_activities.csv")

### collectrI

collectrI <- decoupleR::get_collectri()

TF_activities <- run_ulm(GDSC_rnaseq_tpm_20220624_logp1, collectrI)

TF_activities_df <- reshape2::dcast(TF_activities[,c(2,3,4)], source~condition)

write_csv(collectrI, file = "support/collectrI.csv")
write_csv(TF_activities_df, file = "results/GDSC_TF_activities.csv")

##### 

#Obsolete, mapping can now be found in the header file in support folder

# GDSC1_fitted_dose_response <- as.data.frame(
#   read_excel("data/GDSC1_fitted_dose_response_24Jul22.xlsx"))
# 
# cell_name_mapping <- unique(GDSC1_fitted_dose_response[,c(4,5)])
# cell_name_mapping$COSMIC_ID <- paste("DATA.",cell_name_mapping$COSMIC_ID, sep = "")
# 
# cell_name_mapping <- cell_name_mapping[cell_name_mapping$COSMIC_ID %in% names(progeny_activities_wf),]
# 
# write_csv(cell_name_mapping, file = "results/cell_name_mapping.csv")
