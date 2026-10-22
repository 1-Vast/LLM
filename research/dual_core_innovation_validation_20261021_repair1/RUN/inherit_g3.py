def choose(obs):
    drugs = obs['drugs']
    pred = obs['predictions']
    prior = obs['prior']
    nn = obs['nn']
    sim = obs['sim']
    qf = obs['queried_f']
    qm = obs['queried_m']
    budget = obs['budget_left']
    step = obs['step']
    costs = obs['costs']
    avail_m = obs['available_m']
    if budget < costs['m']:
        return {'kind': 'stop'}
    qf_set = set(qf.keys()) if isinstance(qf, dict) else set(qf)
    qm_set = set(qm.keys()) if isinstance(qm, dict) else set(qm)
    rem_f = [d for d in drugs if d not in qf_set]
    if not rem_f:
        if budget >= costs['m'] and avail_m:
            cand_m = [d for d in avail_m if d not in qm_set]
            if cand_m:
                drug = max(cand_m, key=lambda d: abs(pred[d] - 0.5))
                return {'kind': 'm', 'drug': drug}
        return {'kind': 'stop'}
    if step == 0 and avail_m:
        cand_m = [d for d in avail_m if d not in qm_set]
        if cand_m:
            drug = min(cand_m, key=lambda d: (abs(pred[d] - 0.5), d))
            return {'kind': 'm', 'drug': drug}
    if not qf_set:
        return {'kind': 'f', 'drug': max(rem_f, key=lambda d: (pred[d], d))}
    recent = []
    for d in qf_set:
        if isinstance(qf, dict):
            recent.append((d, qf[d]))
    if recent:
        recent.sort(key=lambda x: x[0])
        last_drug, last_label = recent[-1]
        if last_label == 0:
            if budget >= costs['m'] and avail_m and last_drug in avail_m and last_drug not in qm_set:
                return {'kind': 'm', 'drug': last_drug}
    def sim_to_q(d):
        s = 0.0
        for q in qf_set:
            if d in sim and q in sim[d]:
                v = sim[d][q]
            elif q in sim and d in sim[q]:
                v = sim[q][d]
            else:
                v = 0.0
            if v > s:
                s = v
        return s
    def score(d):
        p = pred[d]
        pr = prior.get(d, 0.5) if isinstance(prior, dict) else 0.5
        n = nn.get(d, 0.5) if isinstance(nn, dict) else 0.5
        unc = abs(p - 0.5)
        disagree = abs(p - pr) + abs(p - n)
        return p + 0.15 * disagree - 0.1 * sim_to_q(d) + 0.05 * unc
    best = max(rem_f, key=lambda d: (score(d), d))
    if budget >= costs['f']:
        return {'kind': 'f', 'drug': best}
    if budget >= costs['m'] and avail_m:
        cand_m = [d for d in avail_m if d not in qm_set]
        if cand_m:
            drug = max(cand_m, key=lambda d: abs(pred[d] - 0.5))
            return {'kind': 'm', 'drug': drug}
    return {'kind': 'stop'}
