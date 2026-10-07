"""Training/development-only technical precision requirements; not power claims."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
table=pd.read_csv(HERE/'observations/bias_corrected_observations.csv')
table=table[(table.role=='full') & table.split.isin(['train','development'])]
variance=(table.treated_mean_gene_variance+table.control_mean_gene_variance).to_numpy()
rows=[]
for squared_signal in [.0005,.001,.005]:
    needed=np.ceil(variance/(.25*squared_signal))
    rows.append({'assumed_true_mean_squared_shift':squared_signal,
        'corresponding_RMS':float(np.sqrt(squared_signal)),
        'noise_budget_fraction_of_signal':.25,
        'equal_treated_and_control_cells_median_required':int(np.median(needed)),
        'equal_cells_90th_percentile_required':int(np.ceil(np.quantile(needed,.9)))})
result={'scope':'precision planning scenarios using90train/development conditions; NOT observed effects or biological sample-size/power estimates',
    'formula':'n >= (mean_gene_varianceT + mean_gene_varianceC)/(0.25*assumed_true_squared_shift), equal n per treated/control pool',
    'assumptions':['iid cells within source pool','source variance transferable','no culture random effect',
        'source survivor/QC selection not corrected'],
    'important':'More cells do not replace independent cultures. A prospective precision/power design needs between-culture variance, currently unavailable.',
    'scenarios':rows,'API_calls':0,'downloaded_bytes':0}
(HERE/'MEASUREMENT_DESIGN.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(rows))
