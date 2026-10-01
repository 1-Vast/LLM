%% main_script.m
%%% FEBRUARY 7, 2021

clear all

close all

%% List of microfluidics experiments of the cycling strain
exp_list = {'SFIG7_abcde_-MET', 'SFIG7_fghij_+MET', ...
    'FIG4_fghij_RefOsc_I', 'SFIG8_abcde_RefOsc_II', ...
    'SFIG8_fghij_RefOsc_III', 'SFIG7_klmno_OpenLoop80', ...
    'FIG4_pqrst_RefOscG', 'FIG4_klmno_OpenLoopG'};


%%
for q = exp_list
    
    exp_name = q{1};
    
    disp(['I am generating the figure: ' exp_name]);
    
    %% Try to loading the processed data
    try
        
        load(['./Processed_data/proc_data_' exp_name '.mat']);
        
    catch % Otherwise, process the output data
        
        process_output_data(exp_name);
        
        load(['./Processed_data/proc_data_' exp_name '.mat']);
        
    end
    
    
    %%
    dim_bin = 4; % Number of bins in the third panel
    
    cmap = parula(4); % Colormap
    
    ideal_bi_pc = 60; % Percentage value of the budding index in -Met
    
    
    %% 
    F = figure('Position', [1 1 720 720], 'DefaultAxesFontSize', 20, ...
        'DefaultAxesLineWidth', 2.5, 'Renderer', 'Painters');
    
    
    %% First panel containing the total cells measured in each frame
    % during the time-lapse
    subplot(8,1,1:2);
    
    dim_n = length(FluoMAT);
    
    tmp_Var = nan(1,dim_n);
    
    for p = 1:dim_n
        
        tmp_Var(p)= length(FluoMAT(p).data);
        
    end
    
    dim_m = max(tmp_Var);
    
    
    matr_fluo = nan(dim_m, dim_n);
    
    for p = 1:dim_n
        
        tmp_Arr = FluoMAT(p).data;
        
        tmp_Dim = length(tmp_Arr); 
        
        if ~isempty(tmp_Arr)
            
            matr_fluo(1:tmp_Dim,p) = tmp_Arr.';
        
        end
        
    end
    
    y_bins = [-Inf, quantile(reshape(matr_fluo, [1,numel(matr_fluo)]), ...
        [.25,.5,.75]), +Inf];
    
    y_lim = y_bins([2,4]);
    
    
    colour_mtrx = matr_fluo;
    
    colour_mtrx(colour_mtrx < y_bins(2)) = .5;
    
    colour_mtrx(colour_mtrx >= y_bins(2) & colour_mtrx < y_bins(3)) = 1.5;
    
    colour_mtrx(colour_mtrx >= y_bins(3) & colour_mtrx < y_bins(4)) = 2.5;
    
    colour_mtrx(colour_mtrx >= y_bins(4)) = 3.5;
    
    
    % imALPHA denotes the points in the matrix matr_fluo that are valid
    imALPHA = ones(dim_m, dim_n);

    imALPHA(isnan(colour_mtrx)) = 0;
    
    
    % This is the code used to draw the first panel
    imagesc(colour_mtrx, 'AlphaData', imALPHA);

    caxis([0,4]);

    CB = colorbar;
    
    colormap(gca, cmap);
    
    CB.Location = 'Eastoutside';
    
    CB.LineWidth = 2.5;
    
    CB.Ticks = linspace(0,4,dim_bin+1);
    
    CB.TickLabels = {'',y_bins(2:end-1),''};
    
    CB.Label.String = 'Fluorescence (a.u.)';
    
    ylabel('Cell (#)')
    
    set(gca, 'XLim', [0,dim_n], 'XTick', 0:50:dim_n, 'XTickLabel', {}, ...
        'YLim', [0,+Inf], 'YDir', 'Normal');
    
    
    %% Second panel containing the average fluorescence signal
    subplot(8,1,3:4)
    
    plot(vct_time, trMEAN, 'LineWidth', 2.5, 'Color', [.4 .76 .65]);
    
    set(gca, 'XLim', [0,vct_time(end)], 'YLim', mean_fluo_lim, 'XTick', ...
        0:100:1000, 'XTickLabel', {});
    
    ylabel('Mean fluo (a.u.)');
    
    CB = colorbar;
    
    CB.Visible = 'Off';
    
    
    %% Third panel containing the total cells measured in each frame
    % during the time-lapse
    subplot(8,1,5:6);
    
    [dim_m, dim_n] = size(SingleCellTraces);
    
    colour_mtrx = SingleCellTraces;
    
    colour_mtrx(colour_mtrx < y_bins(2)) = .5;
    
    colour_mtrx(colour_mtrx >= y_bins(2) & colour_mtrx < y_bins(3)) = 1.5;
    
    colour_mtrx(colour_mtrx >= y_bins(3) & colour_mtrx < y_bins(4)) = 2.5;
    
    colour_mtrx(colour_mtrx >= y_bins(4)) = 3.5;
    
    
    % imALPHA denotes the points in the matrix matr_fluo that are valid
    imALPHA = ones(dim_m, dim_n);

    imALPHA(isnan(colour_mtrx)) = 0;
    
    
    % This is the code used to draw the first panel
    imagesc(colour_mtrx, 'AlphaData', imALPHA);

    caxis([0,4]);

    CB = colorbar;
    
    colormap(gca, cmap);
    
    CB.Location = 'Eastoutside';
    
    CB.LineWidth = 2.5;
    
    CB.Ticks = linspace(0,4,dim_bin+1);
    
    CB.TickLabels = {'',y_bins(2:end-1),''};
    
    CB.Label.String = 'Fluorescence (a.u.)';
    
    ylabel('Cell trace (#)')
    
    set(gca, 'XLim', [0,dim_n], 'XTick', 0:50:dim_n, 'XTickLabel', {}, 'YLim', [0,+Inf], 'YDir', 'Normal');
    
    
    %% Fourth panel containing the budding index
    subplot(8,1,7)
    
    hold on;
    
    line([0 vct_time(end)], ideal_bi_pc.*ones(1,2), 'LineWidth', 2.5, ...
    'Color', [1 .45 .45]);
    
    plot(vct_time, BI, 'LineWidth', 2.5, 'Color', [.55 .63 .80]);
    
    
    set(gca, 'XLim', [0,vct_time(end)], 'YLim', [0,100], 'XTick', ...
        0:100:1000, 'XTickLabel', {}, 'YTick', 0:50:100, 'YTickLabel', ...
        {'0%','50%','100%'});
    
    ylabel('B.I. (%)');
    
    CB = colorbar;
    
    CB.Visible = 'Off';
    
    
    %% Fifth panel containing the input
    subplot(8,1,8);
    
    input_Arr = [zeros(1,dim_n); inputLEVELS];

    % This is the code used to draw the first panel
    imagesc(input_Arr, 'AlphaData', input_Arr);
    
    colormap(gca,[.99 .55 .38]);
    
    CB = colorbar;
    
    CB.Visible = 'Off';
    
    set(gca, 'XLim', [0,dim_n], 'YLim', [1.25,2.5], 'XTick', 0:50:450, ...
        'XTickLabel', 0:100:1000, 'YTick', [1.5,2.5], 'YTickLabel', ...
        {'-MET','+MET'});
    
    xlabel('Time (min)');
    
    ylabel('Input');

    
    %% Print the figure
    print(F, ['./Figures/' exp_name], '-dpng')
    
end