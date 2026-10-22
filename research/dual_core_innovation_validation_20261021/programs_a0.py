A0 = '''
def run(env):
    kappa = 0.5
    drugs = list(env.drugs)
    adj = {d: 0.0 for d in drugs}
    done = {}
    while env.left() >= 1.0 and len(done) < len(drugs):
        best = None
        bs = -1e9
        for d in drugs:
            if d in done:
                continue
            s = env.W[d] + adj[d]
            if s > bs:
                bs = s
                best = d
        y = env.query_f(best)
        done[best] = y
        resid = y - env.W[best]
        for d in drugs:
            if d not in done:
                w = env.sim(d, best)
                if w > 0:
                    adj[d] = adj[d] + kappa * w * w * resid
'''
