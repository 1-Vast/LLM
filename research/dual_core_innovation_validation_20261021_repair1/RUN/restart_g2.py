def choose(obs):
    drugs = list(obs['drugs'])
    pred = obs['predictions']
    prior = obs['prior']
    nn = obs['nn']
    sim = obs['sim']
    qf = set(obs['queried_f'])
    qm = set(obs['queried_m'])
    avail_m = set(obs['available_m'])
    budget = obs['budget_left']
    costs = obs['costs']
    step = obs['step']
    def score_f(d):
        p = pred[d]
        disagreement = abs(p - prior[d]) + abs(p - nn[d])
        return p + 0.08 * (1.0 - p) * disagreement
    def score_m(d):
        p = pred[d]
        return p + 0.04 * (1.0 - p) * abs(p - prior[d])
    best_f = None
    best_f_val = -1.0
    for d in drugs:
        if d in qf:
            continue
        if budget < costs['f']:
            continue
        v = score_f(d)
        if v > best_f_val:
            best_f_val = v
            best_f = d
    best_m = None
    best_m_val = -1.0
    if budget >= costs['m']:
        for d in drugs:
            if d in qm or d not in avail_m:
                continue
            v = score_m(d)
            if v > best_m_val:
                best_m_val = v
                best_m = d
    if best_f is None and best_m is None:
        return {'kind': 'stop'}
    if best_f is None:
        return {'kind': 'm', 'drug': best_m}
    if best_m is None:
        return {'kind': 'f', 'drug': best_f}
    f_val = best_f_val
    m_val = best_m_val
    remaining_after_f = budget - costs['f']
    remaining_after_m = budget - costs['m']
    f_can_continue = remaining_after_f >= costs['f'] or remaining_after_f >= costs['m']
    m_can_continue = remaining_after_m >= costs['f'] or remaining_after_m >= costs['m']
    if f_can_continue and not m_can_continue:
        return {'kind': 'f', 'drug': best_f}
    if m_can_continue and not f_can_continue:
        return {'kind': 'm', 'drug': best_m}
    if f_val >= m_val + 0.06:
        return {'kind': 'f', 'drug': best_f}
    if m_val >= f_val + 0.06:
        return {'kind': 'm', 'drug': best_m}
    if best_f_val >= 0.75:
        return {'kind': 'f', 'drug': best_f}
    if step <= 1 and budget >= 2:
        return {'kind': 'm', 'drug': best_m}
    return {'kind': 'f', 'drug': best_f}
