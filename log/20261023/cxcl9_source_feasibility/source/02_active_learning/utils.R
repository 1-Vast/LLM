init_pars_ssm <- function(lam, maxTime, maxSteps, bootstrap){
  paramsSSm=defaultParametersSSm()
  paramsSSm$local_solver = "DHC"
  paramsSSm$maxtime = maxTime;
  paramsSSm$maxeval = Inf;
  paramsSSm$atol=1e-6;
  paramsSSm$reltol=1e-6; 
  paramsSSm$nan_fac=1000;
  paramsSSm$dim_refset=30;
  paramsSSm$n_diverse=1000;
  paramsSSm$maxStepSize=Inf;
  paramsSSm$maxNumSteps=maxSteps;
  transferFun=4;
  paramsSSm$transfer_function = transferFun;
  
  paramsSSm$lambda_tau=0
  paramsSSm$lambda_k=lam
  paramsSSm$bootstrap=bootstrap
  paramsSSm$SSpenalty_fac=5
  paramsSSm$SScontrolPenalty_fac=10
  
  return(paramsSSm)
  
}



runSimulation <- function(opt_pars, nTimes, nObs, nCond, cnolist, pknmodel, 
                          paramsSSm, plotParams, condAnnot){
  outputs <- data.frame()
  for (run in 1:length(opt_pars)){
    optimized_parameters <- opt_pars[[run]]
    
    simulated_data_optimized=plotLBodeFitness(cnolist, pknmodel, 
                                              transfer_function=paramsSSm$transfer_function, 
                                              ode_parameters=optimized_parameters, 
                                              plotParams = plotParams) 
    for (oneTime in 1:nTimes){
      for (oneProtein in 1:nObs){
        values <- simulated_data_optimized[[oneTime]][,oneProtein]
        outputs <- rbind(outputs, data.frame(
          'Run'=rep(run, length(values)),
          'Value'=values,
          'Condition'=unique(condAnnot$Condition),
          'Time'=oneTime,
          'Protein'=cnolist[['namesSignals']][oneProtein]
        ))
      }
    }
    
  }
  
  outputs <- merge(outputs, condAnnot, by='Condition')
}


# calculate confidence interval
calculate_CI <- function(outputs, nTimes){
  ## Calculate confidence interval across multiple models for last time point ##
  temp_confidence_interval <- data.frame()
  for (single_cond in unique(outputs$Condition)){
    
    # sanity check if condition hasn't been removed 
    if (single_cond %in% unique(outputs$Condition)){
      temp_data <- outputs[outputs$Condition==single_cond & outputs$Protein=='CXCL9' & 
                             outputs$Time==nTimes,]
      temp_data <- temp_data[!is.na(temp_data$Value),] # remove NA
      
      # check whether there is an interval to be calculated in the first place 
      if (!min(temp_data$Value) == max(temp_data$Value)){
        result <- t.test(temp_data$Value)
        confidence_interval <- result$conf.int
        temp_confidence_interval <- rbind(temp_confidence_interval, data.frame('Cytokine'=unique(temp_data$Cytokine), 
                                                                               'Inhibitor'=unique(temp_data$Inhibitor), 
                                                                               'Protein'=unique(temp_data$Protein), 
                                                                               'LowerCI'=confidence_interval[1],
                                                                               'HigherCI'=confidence_interval[2], 
                                                                               'mean_activity'=mean(temp_data$Value),
                                                                               'Time'=nTimes))
      }else{
        temp_confidence_interval <- rbind(temp_confidence_interval, data.frame('Cytokine'=unique(temp_data$Cytokine), 
                                                                               'Inhibitor'=unique(temp_data$Inhibitor), 
                                                                               'Protein'=unique(temp_data$Protein), 
                                                                               'LowerCI'=temp_data$Value[1],
                                                                               'HigherCI'=temp_data$Value[1], 
                                                                               'mean_activity'=temp_data$Value[1],
                                                                               'Time'=nTimes))
      }
    }
    
  }
  temp_confidence_interval$IntervalCI <- temp_confidence_interval$HigherCI - 
    temp_confidence_interval$LowerCI
  return(temp_confidence_interval)
}


sample_new_conditions <- function(acquisition_function, 
                                  temp_confidence_interval, toAdd){
  # get conditions with the average largest CXCL9 output 
  meanActivity <- temp_confidence_interval %>% group_by(Cytokine, Inhibitor) %>%
    summarise(mean_activities = mean(mean_activity))
  meanActivity <- meanActivity[order(meanActivity$mean_activities, decreasing=T),]
  
  # get the conditions with the average largest CI interval 
  sumCI <- temp_confidence_interval %>% group_by(Cytokine, Inhibitor) %>% 
    summarise(sum_CI = sum(IntervalCI))
  sumCI <- sumCI[order(sumCI$sum_CI, decreasing=T),] # from small to large CI 
  
  # combine mean activity and CI
  greedy_uncertainty <- merge(meanActivity, sumCI, by=c('Cytokine', 'Inhibitor'))
  greedy_uncertainty$Fx <- greedy_uncertainty$mean_activities + greedy_uncertainty$sum_CI
  greedy_uncertainty <- greedy_uncertainty[order(greedy_uncertainty$Fx, decreasing=T),]
  
  if (acquisition_function == 'GU'){ # F(x) = mu(x) + sigma(x)
    largest <- greedy_uncertainty[1:toAdd,]
    return(list('full_list' = greedy_uncertainty, 'largest'=largest))
   
    
  }else if (acquisition_function == 'greedy'){ # F(x) = mu(x)
    largest <- meanActivity[1:toAdd,]
    return(list('full_list' = greedy_uncertainty, 'largest'=largest))
    
  }else if (acquisition_function == 'uncertainty'){ #(F(x) = sigma(x)
    largest <- sumCI[1:toAdd,]
    return(list('full_list' = greedy_uncertainty, 'largest'=largest))
    
  }else if (acquisition_function == 'random'){
    sampled <- sample(nrow(greedy_uncertainty), toAdd)
    largest <- greedy_uncertainty[sampled, ]
    return(list('full_list' = greedy_uncertainty, 'largest'=largest))
    
  }else{
    print('Please give a valid acquisition function (greedy, uncertainty, GU or random)!!')
    return('')
  }
}


get_training <- function(nRuns, nRounds, nCond_orig, folder, all_opt, nTimes,
                         nObserved, cnolist_training, 
                         pknmodel, paramsSSm, plotParams, cond_annot_training,
                         toAdd){
  outputs_training <- data.frame()
  start_temp <- 1
  end_temp <- start_temp + nRuns -1  
  temp_nCond <- nCond_orig
  for (single_rnd in 1:nRounds){
    data <-readMIDAS(MIDASfile=paste("outputFiles/", folder, "/MIDAS_training_round", 
                                     single_rnd, ".csv", sep=''))
    cnolist_training <-makeCNOlist(data, subfield=F) 
    pknmodel = preprocessing(data = cnolist_training, model = pknmodel,   
                             compression = F, expansion = F)
    
    # get simulations 
    print(paste(start_temp, end_temp))
    temp <- runSimulation(all_opt[start_temp:end_temp], nTimes, 
                          nObserved, temp_nCond, cnolist_training,
                          pknmodel, paramsSSm, plotParams, cond_annot_training[
                            cond_annot_training$round < single_rnd,])
    temp_nCond <- temp_nCond + toAdd 
    temp$round <- single_rnd
    
    # do this always except if it's the last round as we have an additional MIDAS file
    if (single_rnd < (nRounds-1)){
      start_temp <- start_temp + nRuns  
      end_temp <- end_temp + nRuns  
    }
    
    outputs_training <- rbind(outputs_training, temp)
  }
  return(outputs_training)
}

# replace all cytokine with correct term incl greek symbol
replace_with_greek <- function(old_values, new_values, column, data){
  # first check which old values (and corresponding new values) are within dataframe
  old_values <- old_values[old_values %in% data[[column]]]
  new_values <- new_values[old_values %in% data[[column]]]
  
  for (i in 1:length(old_values)){
    data[data[[column]] == old_values[i],][[column]] <- new_values[i]
  }
  return(data)
}


prep_for_accuracy <- function(temp, hit_threshold){
  pred = temp$simulation
  true = temp$experiment 
  
  pred[pred >= hit_threshold] = 1
  pred[pred < hit_threshold] = 0
  true[true >= hit_threshold] = 1
  true[true < hit_threshold] = 0 
  
  TP = 0 
  FP = 0 
  TN = 0 
  FN = 0 
  for (idx in 1:length(pred)){
    if (pred[idx] == 1 ){ 
      if (pred[idx] == true[idx]){ # TP
        TP = TP + 1 
      } else{ # FP
        FP = FP + 1 
      }
    } else{
      if (pred[idx] == true[idx]){ # TN
        TN = TN + 1 
      } else{ # FN
        FN = FN + 1 
      }
    }
  }
  return(data.frame('TP'=TP, 'FP'=FP, 'TN'=TN, 'FN'=FN))
}






