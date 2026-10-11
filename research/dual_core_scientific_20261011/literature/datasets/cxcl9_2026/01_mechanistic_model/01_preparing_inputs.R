# Set directory and load libraries --------------------------------------------
path <- dirname(rstudioapi::getActiveDocumentContext()$path)
setwd(path)

library(ggplot2)
library(ggthemes)
library(ggridges)
library(dplyr)
library(openxlsx)
library(caret)

source('utils.R')

# Load data -------------------------------------------------------------------
experiment = 'AsPC1' # for output file save
experiment1 = 'E3DA'
experiment2 = 'E3DB'
nCond = 24 

inhibitors_lst <- c('None', 'Momelotinib', 'BMS-345541', 
                    'Salirasib', 'Trametinib', 'Taselisib')
cytokines_lst <- c('IFNG_TNFA',
                   'IFNG', 'TNFA', 'None')

# get FACS data
raw_data <- read.csv(paste('../data/cxcl9_assay/00_Raw_Data_', experiment1, '.csv', sep=''),
                     check.names = F)
raw_data[raw_data$Condition == 'Sample1',]$Condition = 'SampleA1'
raw_data[raw_data$Condition == 'Sample2',]$Condition = 'SampleA2'
temp <- read.csv(paste('../data/cxcl9_assay/00_Raw_Data_', experiment2, '.csv', sep=''),
                 check.names = F)
temp[temp$Condition == 'Sample1',]$Condition = 'SampleB1'
temp[temp$Condition == 'Sample2',]$Condition = 'SampleB2'
raw_data <- rbind(raw_data, temp)

# Data cleaning ---------------------------------------------------------------
# remove outliers using Q1, Q3 and IQR
clean_data <- data.frame(matrix(nrow=0, ncol=ncol(raw_data)))
colnames(clean_data) <- colnames(raw_data)

for (cyt in cytokines_lst){
  for (inh in inhibitors_lst){
    current_group <- raw_data[raw_data$Cytokines==cyt & 
                                raw_data$Inhibitors==inh,]
    quartiles <- quantile(current_group$`Fluorescent intensity`, probs=c(.25, .75), na.rm = FALSE)
    IQR <- IQR(current_group$`Fluorescent intensity`)
    Lower <- quartiles[1] - 1.5*IQR
    Upper <- quartiles[2] + 1.5*IQR 
    
    
    current_group <- current_group[
      current_group$`Fluorescent intensity` > Lower &
      current_group$`Fluorescent intensity` < Upper,
    ]
    
    clean_data <- rbind(clean_data, current_group)
  }
}

# Calculate some statistics (mean std, etc.) ---------------------------------
# Statistics of raw data 
raw_data_stats <- raw_data %>%
  group_by(Cytokines, Inhibitors) %>%
  summarise(
    n = n(),
    arithmetic_mean = mean(`Fluorescent intensity (PE)`),
    geometric_mean = exp(mean(log(`Fluorescent intensity (PE)`))),
    median = median(`Fluorescent intensity (PE)`),
    sd = sd(`Fluorescent intensity (PE)`),
  )

# Statistics of cleaned data 
clean_data_stats <- clean_data %>%
  group_by(Cytokines, Inhibitors) %>%
  summarise(
    n = n(),
    arithmetic_mean = mean(`Fluorescent intensity (PE)`),
    geometric_mean = exp(mean(log(`Fluorescent intensity (PE)`))),
    median = median(`Fluorescent intensity (PE)`),
    sd = sd(`Fluorescent intensity (PE)`),
  )

# Merge statistics of multiple repeats 
stats_per_sample <- clean_data %>%
  group_by(Cytokines, Inhibitors, Condition) %>%
  summarise(
    n=n(),
    arithmetic_mean = mean(`Fluorescent intensity (PE)`),
    geometric_mean = exp(mean(log(`Fluorescent intensity (PE)`))),
    median = median(`Fluorescent intensity (PE)`),
    sd = sd(`Fluorescent intensity (PE)`)
  )


# Normalization ---------------------------------------------------------------
clean_data_stats$`log10(arithmetic_mean)` <- log10(clean_data_stats$arithmetic_mean)

# Min-max normalization 
clean_data_stats$`normalized(log10(arithmetic_mean))` <- min_max_norm(clean_data_stats, 
                                                                       'log10(arithmetic_mean)')
# process per sample 
stats_per_sample$`log10(arithmetic_mean)` <- NA
stats_per_sample$`normalized(log10(arithmetic_mean))` <- NA

for (sample in unique(clean_data$Condition)){
  stats_per_sample[stats_per_sample$Condition==sample,]$`log10(arithmetic_mean)` <- 
    log10(stats_per_sample[stats_per_sample$Condition==sample,]$arithmetic_mean)
  
  stats_per_sample[stats_per_sample$Condition==sample,]$`normalized(log10(arithmetic_mean))` <-
    min_max_norm(stats_per_sample[stats_per_sample$Condition==sample,],
                 'log10(arithmetic_mean)')
}

# get statistics with normalized data 
stats_FINAL <- stats_per_sample %>%
  group_by(Cytokines, Inhibitors) %>%
  summarise(
    n=n(),
    arithmetic_mean = mean(`normalized(log10(arithmetic_mean))`),
    median = median(`normalized(log10(arithmetic_mean))`),
    sd = sd(`normalized(log10(arithmetic_mean))`)
  )

# save statistics
write.csv(clean_data_stats, file= paste('../output/assay_data/Raw_data_statistics_', 
                                        experiment, '.csv', sep=''),
          row.names=FALSE)
write.csv(stats_FINAL, file= paste('../output/assay_data/Optimization_statistics_', 
                                        experiment, '.csv', sep=''),
          row.names=FALSE)



