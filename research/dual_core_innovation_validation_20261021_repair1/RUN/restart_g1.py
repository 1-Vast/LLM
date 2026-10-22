def choose(obs):
    budget = obs['budget_left']
    preds = obs['predictions']
    drugs = list(obs['drugs'])
    qf = set(obs['queried_f'])
    qm = set(obs['queried_m'])
    avail_m = set(obs.get('available_m', []))
    costs = obs['costs']
    cf = costs.get('f', 1.0)
    cm = costs.get('m', 0.5)
    if budget < min(cf, cm):
        return {'kind': 'stop'}
    cand_f = [d for d in drugs if d not in qf]
    cand_m = [d for d in drugs if d not in qm and d in avail_m]
    def score_f(d):
        p = preds.get(d, 0.0)
        return p
    def score_m(d):
        p = preds.get(d, 0.0)
        return p
    best_f = None
    if cand_f and budget >= cf:
        best_f = max(cand_f, key=lambda d: (score_f(d), -cf))
    best_m = None
    if cand_m and budget >= cm:
        best_m = max(cand_m, key=lambda d: (score_m(d), -cm))
    if best_f is None and best_m is None:
        return {'kind': 'stop'}
    if best_f is None:
        return {'kind': 'm', 'drug': best_m}
    if best_m is None:
        return {'kind': 'f', 'drug': best_f}
    pf = score_f(best_f)
    pm = score_m(best_m)
    step = obs.get('step', 0)
    prior = obs.get('prior', {})
    nn = obs.get('nn', {})
    base_f = prior.get(best_f, pf)
    base_m = prior.get(best_m, pm)
    lift_f = pf - base_f
    lift_m = pm - base_m
    n_f = len(qf)
    n_m = len(qm)
    hit_rate_hint = 0.0
    if n_f > 0:
        hit_rate_hint = 0.5
    explore_bias = 0.0
    if n_f == 0:
        explore_bias = 0.15
    elif n_f < 2:
        explore_bias = 0.05
    f_value = pf + lift_f * 0.5 + explore_bias
    m_value = pm * 0.9 + lift_m * 0.3
    if n_m == 0 and n_f > 0:
        m_value += 0.05
    if budget < cf + cm:
        if pf >= pm - 0.05:
            return {'kind': 'f', 'drug': best_f} if budget >= cf else {'kind': 'm', 'drug': best_m}
        else:
            return {'kind': 'm', 'drug': best_m} if budget >= cm else {'kind': 'f', 'drug': best_f}
    if f_value >= m_value:
        return {'kind': 'f', 'drug': best_f}
    return {'kind': 'm', 'drug': best_m}
