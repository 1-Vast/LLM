%% process_output_data.m
%%% FEBRUARY 3, 2021

function process_output_data(exp_name)

disp(['I am processing the output data from: ' exp_name]);

load(['./Output_data/' exp_name '.mat'], 'removedCELLS', 'trackedCELLS', ...
    'dimEXP', 'PhaseMAT', 'smplngTM', 'cropRECT', 'inputLEVELS'); % Load experimental output

%% Retrieve the output data regarding fluorescence and radii
OBJS = [removedCELLS, trackedCELLS]; % Struct array of tracked objects

N = numel(OBJS); % Number of tracked objects

objsTRACES = nan(dimEXP,N); % Real-time single-cell traces

objsRAD = nan(dimEXP,N); % Real-time single-cell radii

for z = 1:N
    
    traceTP = OBJS(z).frame;
    
    objsTRACES(traceTP, z) = OBJS(z).MaxGreenFluo;
    
    objsRAD(traceTP, z) = (OBJS(z).MajorAxis)./2;

end

objsRAD(objsRAD>40) = NaN; % Set an upper limit for radius


%% Mean and std of fluorescence data
trMEAN = nan(dimEXP,1); % Array of average fluorescence data

trSTD = nan(dimEXP,1); % Array of std fluorescence data

FluoMAT = struct('data', {}); % Fluorescence data for generating heatmap

for r = 1:dimEXP
    
    tempTR = rmoutliers(objsTRACES(r,:), 'mean', 'ThresholdFactor', 10); % Remove outliers in fluorescence data
    
    trMEAN(r,1) = nanmean(tempTR);
    
    trSTD(r,1) = nanstd(tempTR);
    
    FluoMAT(r).data = tempTR(~isnan(tempTR));

end


%% fluo_lim defines the limits of the fluorescence representation
mean_fluo_lim = [10*floor(min(trMEAN)/10), 10*ceil(max(trMEAN)/10)];


%% Mean and std of radii
radMEAN = nanmean(objsRAD,2); % Array of average radii

radSTD = nanstd(objsRAD,0,2); % Array of std radii


%% Timestamps
vct_time = ((1:dimEXP).*smplngTM).'; % Array containing the timestamps


%% Budding index and Kuramoto order parameter
dim_n = length(PhaseMAT);

theta_c = .4 * 2 * pi; % Phase value at the G1 to S transition

Theta_ref = nan(1, dim_n); % Allocate an array for reference oscillator phases

BI = nan(1, dim_n); % Allocate an array for budding indices

R = nan(1, dim_n);  % Allocate an array for mean phase coherences

Psi = nan(1, dim_n);  % Allocate an array for mean phases

for p = 1:dim_n
    
    try
        
        tmp_ref = PhaseMAT(p).Theta_r;
        
    catch
        
        tmp_ref = [];
        
    end
    
    if ~isempty(tmp_ref)
        
        Theta_ref(p) = mod(tmp_ref, 2*pi);
        
    end
    
    tmp_Arr = PhaseMAT(p).stimaf;
    
    if isempty(tmp_Arr)
        
        continue
    
    end
    
    nmbr_Unb = sum(PhaseMAT(p).stimaf < theta_c);
    
    nmbr_Bud = sum(PhaseMAT(p).stimaf >= theta_c);
    
    BI(p) = nmbr_Bud / (nmbr_Bud + nmbr_Unb) * 100;
    
    tmp_Z = 1./numel(tmp_Arr).*sum(exp(1i*tmp_Arr));
    
    R(p) = abs(tmp_Z);
    
    Psi(p) = mod(angle(tmp_Z), 2*pi);

end


%% Single-cell traces
try
    
    load(['./Cell_traces/cell_traces_' exp_name '.mat']);

catch % Single-cell trace dataset not found
      % if you would performe the reverse segmentation, run this branch
    
    addpath('./Code_image_processing/'); % Add this subfolder to the path variable
    
    Cells_Reverse = reverse_segmentation(['./Raw_images/' exp_name '/'], ...
        cropRECT, dimEXP);
    
    Cells = [trackedCELLS, removedCELLS];
    
    SingleCellTraces = combine_cell_traces(Cells, Cells_Reverse, dimEXP);
    
    rmpath('./Code_image_processing/');
    
end


%% Save processed data
save(['./Processed_data/proc_data_' exp_name '.mat'], 'inputLEVELS', ...
    'trMEAN', 'trSTD', 'FluoMAT', 'vct_time', 'radMEAN', 'radSTD', ...
    'mean_fluo_lim', 'Theta_ref', 'BI', 'R', 'Psi', 'SingleCellTraces');

end