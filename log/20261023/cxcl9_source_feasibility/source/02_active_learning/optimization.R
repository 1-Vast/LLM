# Set path --------------------------------------------------------------------
path <- dirname(rstudioapi::getActiveDocumentContext()$path)
setwd(path)

# Load libraries --------------------------------------------------------------
library(CellNOptR)
library(MEIGOR)
library(openxlsx)
library(dplyr)

source('utils.R')

# Set optimization parameters ------------------------------------------------
experiment_folder <- 'AsPC1/AsPC1_original'
intermediate_plots <- F

# optimization parameters 
start = 1 # which run to start 
nRuns = 10 # total number of model optimizations per round 

startRounds = 1 # which round to start 
nRounds = 5 # total number of rounds 

toAdd = 10 # number of conditions to add each round 

maxTime = 4000 
maxSteps = 1e5 
bootstrap = F
lam_lst = c(1e-10)

# if final obj function is not below this threshold, the model will be discarded
# and optimization will be attempted again 
all_obj_threshold = c(0.5, 0.5, 0.5, 1, 1) 
max_attempts = 5 # continue if after max_attempts model still didn't converge properly 

acquisition_function  = 'greedy'
set.seed(139421)

# get PKN
pknmodel<-readSIF(paste("../data/model_inputs_active_learning/", experiment_folder, "/CXCL9_Thesis_Network_V3B.sif", sep=''))

# get synthetic values 
synthetic_values <- read.csv('../data/model_inputs_active_learning/synthetic_data/CXCL9_values_AsPC1.csv')

# for plotting of optimized data
plotParams=list(margin=0.001, width=20, height=15, cmap_scale=1, cex=1, ymin=0,
                'maxrow'=100)

# initialize parameters from previous (simpler model) optimization
load('../data/model_inputs/initial_parameters.RData')
initial_parameters = optimized_parameters

# check if data is loaded from previous runs
no_data_loaded <- !exists('cond_annot_training') 

# create two dataframes to keep track of which annotations are from training and test 
if (no_data_loaded){
  total_iter <- 1 
  cond_annot_training <- read.csv(paste('../data/model_inputs_active_learning/', 
                                  experiment_folder, '/Conditions_Annotations_training.csv', sep=''))
  cond_annot_training <- cond_annot_training[,c('Condition', 'Cytokine', 'Inhibitor')]
  cond_annot_training$round <- 0
  cond_annot_test <- read.csv(paste('../data/model_inputs_active_learning/', 
                                    experiment_folder, '/Conditions_Annotations_test.csv', sep=''))
  cond_annot_test <- cond_annot_test[,c('Condition', 'Cytokine', 'Inhibitor')]
}
  
# get a CSV file that helps with updated MIDAS files when adding / removing conditions 
MIDAS_test_inputs <- read.csv(paste('../data/model_inputs_active_learning/', experiment_folder, '/MIDAS_test_inputs.csv', sep=''),
                              check.names=F)
  

# don't do following if previous part of data is loaded 
if (no_data_loaded){
  all_opt = list() # to save all optimized model parameters
  all_outputs <- list() # to save all model ouputs per round 
  all_ranked_lst <- list() # to save all F(x) values of test conditions per round 
  all_best_obj <- data.frame() # to save all best obj function values per model
  all_pred_vs_synthetic <- data.frame() # to save all (intermediate) predictions and in-silico value
}

for (lam in lam_lst){
  for (round in startRounds:nRounds){
    obj_threshold <- all_obj_threshold[round]
    
    # check if there are still conditions left to add
    if (nrow(cond_annot_test) > 0){
      
      ## PREP MODEL TRAINING --------
      # adjust toAdd depending on how many conditions are left 
      toAdd <- min(toAdd, nrow(cond_annot_test))
      print(paste('------ PREP ------ toAdd:', toAdd))
      
      # load training data 
      data <-readMIDAS(MIDASfile=paste("../data/model_inputs_active_learning/", experiment_folder, '/MIDAS_training_round', 
                                       round, ".csv", sep=''), verbose=F)
      cnolist <-makeCNOlist(data, subfield=F, verbose=F) 
      
      # get some details about the input data 
      if (no_data_loaded){
        nInputs <- length(cnolist$namesCues) # number of stimuli / inhibitors
        nCond_train_orig <- nrow(cnolist$valueCues) # (original) number of training conditions
        nCond_train <- nCond_train_orig # (current) number of training conditions
        nCond_test_orig <- nrow(MIDAS_test_inputs) # (original) number of test conditions
        nCond_test <- nCond_test_orig # (current) number of test conditions 
        
        nTimes <- length(cnolist$timeSignals)
        nObserved <- length(cnolist$namesSignals)
        actual_times <- cnolist$timeSignals
      }
      
      ## MODEL TRAINING --------
      for (run in start:nRuns){
        print(paste('------ TRAINING ------ Round =', round, 'and run =', run, 
                    'with acquisition function =', acquisition_function)) 
        
        # get optimization parameters 
        paramsSSm = init_pars_ssm(lam, maxTime, maxSteps, bootstrap)
        
        if (bootstrap){
          print(paste('------ TRAINING ------ BOOT SEED:', paramsSSm$boot_seed))
        }else{
          print('------ TRAINING ------ No bootstrapping')
        }
       
        
        # 1) preprocessing & initialization ---------
        pknmodel = preprocessing(data = cnolist, model = pknmodel, compression = F, expansion = F,
                                 verbose = F)
        
        # if applicable, get model from previous round and continue training 
        if (round > 1){
          initial_parameters <- all_opt[[run + nRuns*(round-2)]]  
          print(paste('------ TRAINING ------ Continue training with model', run + nRuns*(round-2)))
        }
        
        # create some plot of PKN and simulation with initial parameters if needed
        if (intermediate_plots){
          plotModel(pknmodel, cnolist)
          plotLBodeFitness(cnolist = cnolist, model = pknmodel, 
                           transfer_function=paramsSSm$transfer_function,
                           ode_parameters=initial_parameters)
        }
        
        # 2) optimization 
        start.time <- Sys.time() # start timer 
        optimize <- T # continue until model converged properly 
        attempt = 1 
        
        for (i in 1:max_attempts){
          if (optimize){
            optimized_parameters=parEstimationLBode(cnolist, pknmodel, method="essm", 
                                                    ode_parameters=initial_parameters, 
                                                    paramsSSm=paramsSSm)
            simulated_data_optimized=getLBodeModelSim(cnolist, pknmodel,
                                                      transfer_function=paramsSSm$transfer_function,
                                                      ode_parameters=optimized_parameters)
            
            if (optimized_parameters$ssm_results$fbest <= obj_threshold){
              optimize = F
            }else if (attempt == max_attempts){
              optimize = F 
              print("------ TRAINING ------ Reached max amount of attempts but model didn't converge")
            }else{
              attempt = attempt + 1 
              print(paste("------ TRAINING ------ Model didn't converge, starting attempt", attempt, 
                          'of round =', round, 'and run =', run))
            }
          }
        }
        
        if (intermediate_plots){
          plotLBodeFitness(cnolist, pknmodel, transfer_function=paramsSSm$transfer_function, 
                           ode_parameters=optimized_parameters, plotParams = plotParams)  
        }
        
        end.time <- Sys.time() # end timer 
        time.taken <- round(end.time - start.time,2)
        print(paste('------ TRAINING ------ Run time =', time.taken))
        
        # 3) save results for this specific run 
        save(simulated_data_optimized, optimized_parameters, lam, paramsSSm,
             file = paste("../output/active_learning/", experiment_folder, "/Lam", lam, "_Round", round,
                          "_Run", run, "_Results_Training.RData", sep=""))
        
        # 4) update variables with new training results  
        all_opt[[total_iter]] <- optimized_parameters # save optimized parameters 
        # save best objective function value 
        all_best_obj <- rbind(all_best_obj, 
                              data.frame('round'=round, 
                                         'run'=run,
                                         'best_obj_value'=optimized_parameters$ssm_results$fbest))
        
        total_iter = total_iter + 1 
        
        
      }
      
      ## SELECTION OF NEW TRAINING CONDITIONS --------
      # get test data
      data_test <-readMIDAS(MIDASfile=paste("../data/model_inputs_active_learning/", experiment_folder, "/MIDAS_test_round", 
                                            round, ".csv", sep=''))
      cnolist_test <-makeCNOlist(data_test, subfield=F) 
      
      # get indices to retrieve only models from this round 
      start_temp <- (round * nRuns) - (nRuns - 1)
      end_temp <- length(all_opt)
      print(paste('------ SELECT NEW TRAIN CONDITIONS ------ Check model indices:', start_temp, 'to', end_temp))
      
      # get model simulations from which new training conditions can be selected
      outputs <- runSimulation(all_opt[start_temp:end_temp], nTimes, nObserved, nCond_test, 
                               cnolist_test, pknmodel, paramsSSm, plotParams, cond_annot_test)
      all_outputs[[round]] <- outputs 
      
      # calculate confidence interval 
      temp_confidence_interval <- calculate_CI(outputs, nTimes)
      
      # sample new training conditions 
      temp_lst <- sample_new_conditions(acquisition_function, temp_confidence_interval, toAdd)
      all_ranked_lst[[round]] <- temp_lst[['full_list']]
      largest <- temp_lst[['largest']]
      
      
      ## UPDATING TRAIN AND TEST SETS ----------
      # get MIDAS file which can eb adjusted 
      MIDAS_training <- read.csv(paste('../data/model_inputs_active_learning/', experiment_folder, '/MIDAS_training_round', 
                                       round, '.csv', sep=''), check.names=F)
      MIDAS_test <- read.csv(paste('../data/model_inputs_active_learning/', experiment_folder, '/MIDAS_test_round', 
                                   round, '.csv', sep=''), check.names=F)
      
      # process each new training condition 
      for (one_idx in 1:toAdd){
        # get inputs corresponding with this condition 
        newCyt <- largest[one_idx,]$Cytokine
        newInh <- largest[one_idx,]$Inhibitor
        
        # 1) adjust annotations of conditions 
        # add to training
        cond_annot_training[nCond_train + one_idx,] <- c(nCond_train+one_idx, newCyt, newInh, round)
        
        # remove from test 
        orig_cond_idx <- cond_annot_test[(cond_annot_test$Cytokine==newCyt & 
                                            cond_annot_test$Inhibitor==newInh),]$Condition
        cond_annot_test <- cond_annot_test[!(cond_annot_test$Cytokine==newCyt & 
                                               cond_annot_test$Inhibitor==newInh),]
        
        # 2) adjust MIDAS training 
        # 2a) add initial time point
        values <- MIDAS_test_inputs[MIDAS_test_inputs$Condition==orig_cond_idx,][,2:ncol(MIDAS_test_inputs)]
        MIDAS_training[nrow(MIDAS_training)+1,] <- unlist(c(1, values, 0, rep(0.5, nObserved-1), 0),
                                                          use.names=F)
        # 2b) add intermediate time points
        for (oneTime in 2:(nTimes-1)){
          oneTime <- actual_times[oneTime]
          one_row <- c(1, values, oneTime, rep(NA, nObserved))
          MIDAS_training[nrow(MIDAS_training)+1,] <- unlist(one_row, use.names=F)
        }
        
        # 2c) add final time point 
        # predict CXCL9 output 
        pred_mean <- temp_confidence_interval[temp_confidence_interval$Cytokine==newCyt & 
                                                temp_confidence_interval$Inhibitor==newInh & 
                                                temp_confidence_interval$Time==nTimes,]$mean_activity
        
        # use either experimental value or, if not available, activity from synthetic data set 
        synthetic_mean <- synthetic_values[synthetic_values$Cytokine==newCyt &
                                             synthetic_values$Inhibitor==newInh,]$CXCL9_value
        
        # save predicted mean CXCL9 activity vs in-silico CXCL9 activity of condition to-be added
        all_pred_vs_synthetic <- rbind(all_pred_vs_synthetic, 
                                       data.frame('Cytokine'=newCyt,
                                                  'Inhibitor'=newInh,
                                                  'round'=round,
                                                  'CXCL9_activity'=pred_mean,
                                                  'data_set'='predicted'))
        all_pred_vs_synthetic <- rbind(all_pred_vs_synthetic, 
                                       data.frame('Cytokine'=newCyt,
                                                  'Inhibitor'=newInh,
                                                  'round'=round,
                                                  'CXCL9_activity'=synthetic_mean,
                                                  'data_set'='synthetic data'))
        
        # add final time point 
        MIDAS_training[nrow(MIDAS_training)+1,] <- unlist(c(1, values, actual_times[nTimes], 
                                                            rep(NA, nObserved-1), synthetic_mean),
                                                          use.names=F)
        
        # 3) adjust MIDAS test 
        # remove rows of added condition 
        rows_to_add <- c()
        for (singleRow in 1:nrow(MIDAS_test)){
          if (!sum(MIDAS_test[singleRow, colnames(values)] == values)==nInputs){
            rows_to_add <- c(rows_to_add, singleRow)
          }
        }
        MIDAS_test <- MIDAS_test[rows_to_add,]
        
      }
      
      # save new MIDAS files 
      write.csv(MIDAS_training, file=paste('../data/model_inputs_active_learning/', 
                                           experiment_folder, '/MIDAS_training_round', 
                                           round+1, '.csv', sep=''), row.names=F)
      write.csv(MIDAS_test, file=paste('../data/model_inputs_active_learning/', 
                                       experiment_folder, '/MIDAS_test_round', 
                                       round+1, '.csv', sep=''), row.names=F)
      write.csv(MIDAS_training, file=paste('../output/active_learnings/', 
                                           experiment_folder, '/MIDAS_training_round', 
                                           round+1, '.csv', sep=''), row.names=F)
      write.csv(MIDAS_test, file=paste('../output/active_learning/', 
                                       experiment_folder, '/MIDAS_test_round', 
                                       round+1, '.csv', sep=''), row.names=F)
      
      # update total number of conditions 
      nCond_train <- nCond_train + toAdd 
      nCond_test <- nCond_test - toAdd 
      
      # save results after each round 
      filename <- paste("../output/active_learning/", experiment_folder, "/00Lam", lam, "_Round=", round,
                        "_Results.RData", sep="")
      save(nCond_train_orig, nCond_train, nCond_test_orig, nCond_test, 
           nInputs, nTimes, nObserved, total_iter, actual_times, 
           cond_annot_training, cond_annot_test, 
           all_opt, all_outputs, all_ranked_lst, all_best_obj, all_pred_vs_synthetic, 
           toAdd, paramsSSm, plotParams, 
           file = filename)
      
    } else{
      print('------ EARLY STOPPING ------ No conditions left to add!!')
    }
  }
}

    


