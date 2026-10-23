# Set directory and load libraries --------------------------------------------
path <- dirname(rstudioapi::getActiveDocumentContext()$path)
setwd(path)

library(openxlsx)
library(ggplot2)
library(ggthemes)
library(ggridges)
library(dplyr)
library(caret)
library(ggpattern)

# Cleaning data  -----------------------------------
cleanData <- function(raw_data, cytokines_lst, 
                      concentrations){
  clean_data <- data.frame(matrix(nrow=0, ncol=ncol(raw_data)))
  colnames(clean_data) <- colnames(raw_data)
  
  for (cyt in cytokines_lst){
    for (conc in concentrations){
      current_group <- raw_data[raw_data$Cytokine==cyt & 
                                  raw_data$`Cytokine concentration`==conc,]
      quartiles <- quantile(current_group$`Fluorescent intensity`, probs=c(.25, .75), na.rm = FALSE)
      IQR <- IQR(current_group$`Fluorescent intensity`)
      Lower <- quartiles[1] - 1.5*IQR
      Upper <- quartiles[2] + 1.5*IQR 
      
      print(paste(IQR, Lower, Upper, cyt, conc, median(current_group$`Fluorescent intensity`)))
      
      
      current_group <- current_group[
        current_group$`Fluorescent intensity` > Lower &
          current_group$`Fluorescent intensity` < Upper,
      ]
      
      clean_data <- rbind(clean_data, current_group)
    }
  }
  
  return(clean_data)
}

# Plotting --------------------------------------------------------------------
base_breaks <- function(n = 10){
  function(x) {
    axisTicks(log10(range(x, na.rm = TRUE)), log = TRUE, n = n)
  }
}


# Normalization ---------------------------------------------------------------
min_max_norm <- function(data, col){
  process <- preProcess(as.data.frame(data[col]), method=c("range"))
  temp <- predict(
    process,
    as.data.frame(data[col]))
  colnames(temp) <- c('data')
  temp$data
}


# Loading data for MPSA -----------------------------------------------------
getMPSAdata <- function(pathway, folder, MPSA_par, nrSamples,
                        iteration){
  allKS_data <- data.frame(matrix(nrow=0, ncol=4,))
  colnames(allKS_data) <- c('Parameter', 'KS statistic', 'Pathway',
                            'alpha')
  for (pathway in pathways){
    load(paste('../output/', pathway, folder, '/', MPSA_par, '/Nsamples=', nrSamples,
               '/Iteration', iteration, '/SavedVariables.RData', sep=""))
    
    temp_data <- merge(KS_df, annot, by=c('Parameter'))  
    temp_data[nrow(temp_data)+1,] <- c('Dummy', 
                                       mean(KS_df[nrow(KS_df)-nrDummies:
                                                    nrow(KS_df),]$`KS statistic`),
                                       pathway)
    
    temp_data$`KS statistic` <- as.numeric(temp_data$`KS statistic`)
    allKS_data <- rbind(allKS_data, temp_data)
  }
  
  return(allKS_data)
}






