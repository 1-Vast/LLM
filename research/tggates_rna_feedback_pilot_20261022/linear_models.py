"""Small-sample dual estimators; fit transformations only on supplied rows."""
import numpy as np
COUNTERS={'transform_fits':0,'coefficient_fits':0,'linear_solves':0,'svd_calls':0}


class Blocks:
    def fit(self, blocks):
        COUNTERS['transform_fits']+=1
        self.means = [np.mean(x, axis=0) for x in blocks]
        self.scales = [float(np.sqrt(np.mean(np.sum((x-m)**2, axis=1)))) or 1.
                       for x,m in zip(blocks,self.means)]
        return self

    def transform(self, blocks, weights=None):
        assert len(blocks) == len(self.means)
        weights = [1.]*len(blocks) if weights is None else weights
        return np.concatenate([(x-m)/s*w for x,m,s,w in
            zip(blocks,self.means,self.scales,weights)],axis=1)/np.sqrt(len(blocks))


class Ridge:
    def fit(self, blocks, y, penalty, weights=None):
        self.transformer=Blocks().fit(blocks)
        return self.fit_transformed(self.transformer.transform(blocks), y, penalty, weights)

    def fit_transformed(self, x, y, penalty, weights=None):
        COUNTERS['coefficient_fits']+=1;COUNTERS['linear_solves']+=1
        n=len(x); assert penalty > 0
        w=np.ones(n) if weights is None else np.asarray(weights,dtype=float)
        assert np.all(w>0)
        self.xmean=np.average(x,axis=0,weights=w)
        self.ymean=np.average(y,axis=0,weights=w)
        # weights are literal observation multiplicities; penalty is n*lambda
        self.x=(x-self.xmean)*np.sqrt(w[:,None])
        self.dual=np.linalg.solve(self.x@self.x.T+n*penalty*np.eye(n),
                                 (y-self.ymean)*np.sqrt(w[:,None]))
        return self

    def predict_transformed(self, x):
        return self.ymean+((x-self.xmean)@self.x.T)@self.dual

    def predict(self, blocks):
        return self.predict_transformed(self.transformer.transform(blocks))


class ReducedRidge:
    def fit(self, blocks, y, penalty, rank, weights):
        COUNTERS['coefficient_fits']+=1;COUNTERS['svd_calls']+=1
        self.transformer=Blocks().fit(blocks)
        self.weights=weights
        x=self.transformer.transform(blocks,weights)
        self.xmean=x.mean(0); self.ymean=y.mean(0)
        u,s,vt=np.linalg.svd(x-self.xmean,full_matrices=False)
        tol=(s[0] if len(s) else 0)*max(x.shape)*np.finfo(float).eps
        keep=s>tol; u,s,vt=u[:,keep],s[keep],vt[keep]
        n=len(x)
        uy=u.T@(y-self.ymean)
        z=(s/np.sqrt(s*s+n*penalty))[:,None]*uy
        if not len(s):
            self.left=np.zeros((x.shape[1],0)); self.right=np.zeros((0,y.shape[1]))
        else:
            COUNTERS['svd_calls']+=1
            _,_,q=np.linalg.svd(z,full_matrices=False)
            q=q[:min(rank,len(s),y.shape[1])].T
            self.left=vt.T@((s/(s*s+n*penalty))[:,None]*(uy@q))
            self.right=q.T
        return self

    def predict(self,blocks):
        x=self.transformer.transform(blocks,self.weights)
        return self.ymean+((x-self.xmean)@self.left)@self.right


class RBF:
    def fit(self,blocks,y,penalty,factor):
        COUNTERS['coefficient_fits']+=1;COUNTERS['linear_solves']+=1
        self.transformer=Blocks().fit(blocks)
        self.x=self.transformer.transform(blocks)
        d=self.dist(self.x,self.x); positive=d[d>0]
        self.bandwidth=factor*np.median(positive) if len(positive) else 1.
        self.ymean=y.mean(0)
        k=np.exp(-d/self.bandwidth)
        # Intercept via centered kernel, consistent for new rows.
        self.kmean=k.mean(0); self.kgrand=k.mean()
        kc=k-self.kmean[None,:]-self.kmean[:,None]+self.kgrand
        self.dual=np.linalg.solve(kc+len(k)*penalty*np.eye(len(k)),y-self.ymean)
        return self

    @staticmethod
    def dist(x,y):
        return np.maximum(np.sum(x*x,1)[:,None]+np.sum(y*y,1)[None,:]-2*x@y.T,0)

    def predict(self,blocks):
        x=self.transformer.transform(blocks)
        k=np.exp(-self.dist(x,self.x)/self.bandwidth)
        kc=k-k.mean(1)[:,None]-self.kmean[None,:]+self.kgrand
        return self.ymean+kc@self.dual
