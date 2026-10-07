"""One correlated ranking-boundary heuristic and reference-only error diagnostic."""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr

RIDGE = 1000.


def validate_inputs(mean,covariance,obsvar):
    n=len(mean)
    if (covariance.shape!=(n,n) or obsvar.shape!=(n,) or n<6
            or not np.all(np.isfinite(mean)) or not np.all(np.isfinite(covariance))
            or not np.all(np.isfinite(obsvar)) or np.any(obsvar<0)
            or np.any(np.diag(covariance)<0) or not np.allclose(covariance,covariance.T,atol=1e-12)):
        raise ValueError("Invalid finite/symmetric/nonnegative acquisition inputs")
    tolerance=1e-10*max(float(np.max(np.diag(covariance))),1e-12)
    if np.linalg.eigvalsh(covariance).min() < -tolerance:
        raise ValueError("Invalid nonPSD acquisition covariance")


def boundary_scores(mean, covariance, obsvar, available, top=5):
    """Expected positive gap crossing, maximized over incumbent/challenger pairs."""
    order = np.lexsort((np.arange(len(mean)), -mean))
    inside, outside = order[:top], order[top:]
    gap = np.maximum(mean[inside, None] - mean[outside][None], 0.)
    scores, details = {}, {}
    for i in available:
        leverage = (covariance[inside, i, None] - covariance[outside, i][None])
        leverage /= np.sqrt(max(covariance[i, i]+obsvar[i], 1e-12))
        sd = np.abs(leverage)
        z = np.divide(gap, sd, out=np.full_like(sd, np.inf), where=sd > 0)
        gain = np.maximum(sd*np.exp(-.5*z*z)/np.sqrt(2*np.pi)-gap*ndtr(-z), 0.)
        j, k = np.unravel_index(np.argmax(gain), gain.shape)
        scores[int(i)] = float(gain[j,k])
        incumbent, challenger = int(inside[j]), int(outside[k])
        details[int(i)] = dict(incumbent=incumbent, challenger=challenger,
            mean_gap=float(gap[j,k]), observation_gap_sd=float(sd[j,k]),
            signed_observation_leverage=float(leverage[j,k]),
            model_implied_pair_variance=float(max(covariance[incumbent,incumbent]+
                covariance[challenger,challenger]-2*covariance[incumbent,challenger],0.)))
    return scores, details


def nearest_basal_distance(target, reference):
    centre = reference.mean(0)
    x, others = target-centre, reference-centre
    cosine = (others @ x)/(np.linalg.norm(others,axis=1)*np.linalg.norm(x)+1e-12)
    return float(np.clip(1-cosine.max(),0,2))


def features(disagreement, basal_distance, dose, plate_design, availability, state_availability, variance):
    n = len(dose)
    return np.column_stack((np.log(np.abs(disagreement)+1e-12), np.full(n,basal_distance),
        np.log10(dose), plate_design, availability, state_availability,
        np.log(np.maximum(variance,1e-12)), availability < 1., state_availability < 1.))


def design_only(x):
    x=x.copy()
    x[:,[0,1,x.shape[1]-3]]=0.
    return x


def mean_for_reference(values, availability, keep, weights=None):
    active = availability & keep[:,None]
    w=active.astype(float) if weights is None else weights*active
    if np.any(w.sum(0)<=0):
        raise ValueError("Every candidate needs retained training support")
    w/=w.sum(0)
    return (w*values).sum(0), active.mean(0)


def reference_row(arrays, held, excluded=(), permuted=False):
    """Both the row context and any outer-fold context are excluded from references."""
    keep=np.ones(len(arrays['basal']),bool)
    keep[list(excluded)]=False
    keep[held]=False
    obs=arrays['train_B'];available=arrays['availability_B']
    m0,coverage=mean_for_reference(obs,available,keep,arrays['precision_B'])
    states=arrays['state_B_permuted'] if permuted else arrays['state_B']
    state_available=arrays['state_available_B_permuted'] if permuted else arrays['state_available_B']
    state_mean,state_coverage=mean_for_reference(states,state_available,keep)
    dev=np.where(state_available[held],states[held]-state_mean,0.)
    masked=np.where(available & keep[:,None],obs,np.nan)
    variance=np.nanvar(masked,axis=0,ddof=1)
    x=features(.5*dev,nearest_basal_distance(arrays['basal'][held],arrays['basal'][keep]),
        arrays['dose'],arrays['plate_design'],coverage/(keep.sum()/len(keep)),
        state_coverage/(keep.sum()/len(keep)),variance)
    return x, (m0+.5*dev-obs[held])**2, arrays['availability_A'][held]&available[held]&state_available[held], m0


def dataset(arrays, included, permuted=False):
    excluded=np.flatnonzero(~included)
    xs,errors,groups=[],[],[]
    for held in np.flatnonzero(included):
        x,error,eligible,_=reference_row(arrays,int(held),excluded,permuted)
        xs.append(x[eligible]);errors.append(error[eligible]);groups.extend([int(held)]*int(eligible.sum()))
    return np.concatenate(xs),np.concatenate(errors),np.array(groups)


def fit(x, errors, design=False):
    if design:x=design_only(x)
    positive=errors[errors>0]
    floor=max(float(np.median(positive))*.01,1e-12)
    target=np.log(errors+floor)
    centre=x.mean(0);scale=x.std(0);scale=np.where(scale>1e-12,scale,1.)
    z=(x-centre)/scale
    intercept=float(target.mean())
    coef=np.linalg.solve(z.T@z+RIDGE*np.eye(z.shape[1]),z.T@(target-intercept))
    predicted=z@coef+intercept
    return dict(centre=centre,scale=scale,coef=coef,intercept=intercept,
                predicted_centre=float(predicted.mean()),floor=floor,design=design)


def predict(model,x):
    if model['design']:x=design_only(x)
    return (x-model['centre'])/model['scale']@model['coef']+model['intercept']


def variance_ratio(model,x):
    logratio=.5*(predict(model,x)-model['predicted_centre'])
    return np.exp(np.clip(logratio,np.log(.5),np.log(2.)))


def scale_covariance(covariance,ratio):
    d=np.sqrt(ratio)
    return covariance*d[:,None]*d[None]


def nested_diagnostic(arrays,permuted=False):
    """Outer held context never enters any inner error/feature/floor/fit."""
    predicted,true,constant=[],[],[]
    n=len(arrays['basal'])
    for held in range(n):
        included=np.ones(n,bool);included[held]=False
        x,errors,_=dataset(arrays,included,permuted)
        model=fit(x,errors)
        heldx,helderror,eligible,_=reference_row(arrays,held,permuted=permuted)
        y=np.log(helderror[eligible]+model['floor'])
        predicted.extend(predict(model,heldx[eligible]));true.extend(y)
        constant.extend([model['intercept']]*len(y))
    return np.array(predicted),np.array(true),np.array(constant)
