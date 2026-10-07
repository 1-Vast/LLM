"""Candidate-specific state interaction; small CPU ridge with explicit training scope."""
import numpy as np
from scipy.linalg import solve


def pair_features(kernel, rank=16):
    val,vec = np.linalg.eigh(kernel)
    idx = np.argsort(val)[::-1][:min(rank,len(val))]
    features = vec[:,idx]*np.sqrt(np.maximum(val[idx],0))
    return features/np.maximum(np.linalg.norm(features,axis=1,keepdims=True),1e-12)


def state_features(pathway_history,pathway_target,tf_history,tf_target):
    def standardise(h,t):
        mu,sd = h.mean(axis=0),h.std(axis=0)
        keep = sd>1e-6
        return (h[:,keep]-mu[keep])/sd[keep],(t[keep]-mu[keep])/sd[keep]
    ph,pt = standardise(np.asarray(pathway_history),np.asarray(pathway_target))
    th,tt = standardise(np.asarray(tf_history),np.asarray(tf_target))
    if th.shape[1]:
        _,_,vt = np.linalg.svd(th,full_matrices=False)
        rank = min(5,len(th)-1,vt.shape[0])
        th,tt = th@vt[:rank].T,tt@vt[:rank].T
        sd = th.std(axis=0)
        keep = sd>1e-6
        th,tt = th[:,keep]/sd[keep],tt[keep]/sd[keep]
    ph,pt = ph/np.sqrt(max(1,ph.shape[1])),pt/np.sqrt(max(1,ph.shape[1]))
    th,tt = th/np.sqrt(max(1,th.shape[1])),tt/np.sqrt(max(1,th.shape[1]))
    return np.concatenate([ph,th],axis=1)/np.sqrt(2),np.concatenate([pt,tt])/np.sqrt(2)


def centre_by_line(x,y,line_index):
    x,y = np.array(x,float,copy=True),np.array(y,float,copy=True)
    for li in np.unique(line_index):
        mask = line_index==li
        x[mask] -= x[mask].mean(axis=0)
        y[mask] -= y[mask].mean(axis=0)
    return x,y


def residual_prediction(pair_phi,row_pid,row_line_states,residuals,line_index,target_pid,target_state,ridge=10.):
    x = (pair_phi[row_pid,:,None]*row_line_states[:,None,:]).reshape(len(row_pid),-1)
    xt = (pair_phi[target_pid,:,None]*target_state[None,None,:]).reshape(len(target_pid),-1)
    x,y = centre_by_line(x,residuals,line_index)
    xt -= xt.mean(axis=0)
    if not x.shape[1]:
        return np.zeros((len(target_pid),residuals.shape[1]))
    coef = solve(x.T@x+ridge*np.eye(x.shape[1]),x.T@y,assume_a='pos')
    return xt@coef
