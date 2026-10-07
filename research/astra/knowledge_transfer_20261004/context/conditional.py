"""Transport response history using public biological context; no target response."""
from __future__ import annotations
import numpy as np
from scipy.spatial.distance import pdist


def context_weights(train, target, *, pca=False):
    train, target = np.asarray(train,float), np.asarray(target,float)
    if not np.isfinite(train).all() or not np.isfinite(target).all():
        raise ValueError('missing context requires explicit handling')
    mean, sd = train.mean(axis=0), train.std(axis=0)
    usable = sd > 1e-6
    if not usable.any():
        return np.ones(train.shape[0])
    z = (train[:,usable]-mean[usable])/sd[usable]
    t = (target[usable]-mean[usable])/sd[usable]
    if pca:
        _, _, vt = np.linalg.svd(z, full_matrices=False)
        r = min(5, train.shape[0]-1, vt.shape[0])
        z, t = z @ vt[:r].T, t @ vt[:r].T
    distances = pdist(z, metric='sqeuclidean')
    positive = distances[distances>1e-12]
    if not positive.size:
        return np.ones(train.shape[0])
    bandwidth = float(np.median(positive))
    d = ((z-t)**2).sum(axis=1)
    # Subtract min distance: weights share an arbitrary scale; this prevents
    # underflow and cancels exactly in weighted means and effective sample size.
    return np.exp(-(d-d.min())/bandwidth)


def weighted_quantities(history, role, target_pid, row_weights):
    pid = history.pid
    size = max(int(pid.max()),int(np.max(target_pid)))+1
    w = np.asarray(row_weights,float)
    if w.shape != pid.shape or not np.isfinite(w).all() or np.any(w<0):
        raise ValueError('invalid history weights')
    n = np.bincount(pid,weights=w,minlength=size)
    n2 = np.bincount(pid,weights=w*w,minlength=size)
    effective = np.divide(n*n,n2,out=np.zeros(size),where=n2>0)
    A = history.arrays[role]
    hs,hv = A['h_s'].astype(float),A['h_v'].astype(float)
    ys,yv = A['y_s'].astype(float),A['y_v'].astype(float)
    def shrunk(z):
        sums = np.bincount(pid,weights=w*z,minlength=size)
        m = np.divide(sums,n,out=np.zeros(size),where=n>0)
        return ((effective*m + 2*z.mean())/(effective+2))[target_pid]
    return {'p_s':shrunk(hs),'p_v':shrunk(hv),'p_sv':shrunk(hs*hv),
            'S_both':shrunk((ys+yv)/2),'L_v':shrunk(yv),'S':shrunk(ys),
            'effective_n':effective[target_pid]}


def score_from(q, arm):
    return {'C_mean':lambda:(q['p_s']+q['p_v'])/2,
            'C_prod':lambda:q['p_s']*q['p_v'],
            'S_both':lambda:q['S_both'], 'C_s':lambda:q['p_s'],
            'C_v':lambda:q['p_v'], 'L_v':lambda:q['L_v']}[arm]()
