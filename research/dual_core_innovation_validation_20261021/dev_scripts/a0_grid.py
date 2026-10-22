import sys; sys.path.insert(0,'D:/MAESTRO/research/dual_core_innovation_validation_20261021')
import numpy as np, agent_data as A, ptv_env as ENV, programs_a0 as P0
for stage in ('dev','sel'):
    E=A.load(stage,'m1')
    for w in ('W0','W1','B1'):
        row=[]
        for kappa in (0.0,0.25,0.5,1.0,2.0):
            src=P0.A0.replace('kappa = 0.5',f'kappa = {kappa}')
            ys=[ENV.run_program(src,e['kwargs'])['yield'] for e in E[w]]
            row.append((kappa,round(float(np.mean(ys)),2)))
        pos=[sum(e['kwargs']['labels'].values()) for e in E[w]]
        print(stage,w,row,'n_pos',pos,'prev',round(float(np.mean([np.mean(list(e['kwargs']['labels'].values())) for e in E[w]])),2))
