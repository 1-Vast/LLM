import sys; sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import pandas as pd, agent_data as A
sc=pd.read_pickle('D:/MAESTRO/tmp/dev_scores.pkl')
w=sc[['cell','perts','M1']].rename(columns={'M1':'w'}).dropna()
o=A.build('dev',w,'m1'); print({k:[len(e['kwargs']['drugs']) for e in v] for k,v in o.items()})
w=A.w_from_npz('D:/MAESTRO/research/dual_core_innovation_validation_20261021/RUN/sel','sel','full',30)
o=A.build('sel',w,'m1'); print({k:[len(e['kwargs']['drugs']) for e in v] for k,v in o.items()})
