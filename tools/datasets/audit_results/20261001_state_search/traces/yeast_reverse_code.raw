%% reverse_segmentation.m
%%% OCTOBER 15, 2020 

function Cells_Reverse = reverse_segmentation(Im_Path, cropRECT, dimITR)

bfsub = 'c1.tif';
greensub = 'c2.tif';
redsub = 'c3.tif';

idN = 1;

for ITR = dimITR:-1:1
    disp(['ITR:' num2str(ITR) '/' num2str(dimITR)])
    
    bf=strcat(Im_Path,'t',num2str(ITR,'%.6d'),bfsub);
    green=strcat(Im_Path,'t',num2str(ITR,'%.6d'),greensub);
    red=strcat(Im_Path,'t',num2str(ITR,'%.6d'),redsub);
    
    Bf_Img = imread(bf);
    Green_Img = imread(green);
    Red_Img = imread(red);
    
    if ITR == dimITR
        [trackedCELLS, removedCELLS, idN] = trackingYeastCycling_Rev(...
            Bf_Img, Green_Img, Red_Img, ITR, cropRECT, idN, dimITR);
    else
        [trackedCELLS, removedCELLS, idN] = trackingYeastCycling_Rev(...
            Bf_Img, Green_Img, Red_Img, ITR, cropRECT, idN, dimITR, ...
            trackedCELLS, removedCELLS);
    end
    
end

Cells_Reverse = [trackedCELLS,removedCELLS];
    
end