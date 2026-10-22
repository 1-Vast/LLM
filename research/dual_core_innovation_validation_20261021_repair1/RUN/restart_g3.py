def choose(obs):
    budget = obs['budget_left']
    drugs = obs['drugs']
    preds = obs['predictions']
    prior = obs.get('prior', {})
    sim = obs.get('sim', {})
    qf = set(obs.get('queried_f', []))
    qm = set(obs.get('queried_m', []))
    avail_m = obs.get('available_m', True)
    costs = obs.get('costs', {'f': 1, 'm': 0.5})
    cf = costs.get('f', 1)
    cm = costs.get('m', 0.5)
    if budget < cf:
        return {'kind': 'stop'}
    # score each drug by expected value of a functional query
    def score(d):
        p = preds.get(d, 0.5)
        pr = prior.get(d, 0.5)
        # uncertainty bonus: disagreement between model and prior
        unc = abs(p - pr)
        # neighbor support: similarity-weighted mean prediction of already-queried positives
        neigh = 0.0
        wsum = 0.0
        sd = sim.get(d, {})
        if isinstance(sd, dict):
            for o, s in sd.items():
                if o in qf:
                    neigh += s * (1.0 if o in qf and preds.get(o, 0.0) > 0.5 else 0.0)
                    wsum += s
        bonus = 0.0
        if wsum > 0:
            bonus = 0.15 * (neigh / wsum)
        # penalize drugs already queried functionally
        pen = 0.0
        if d in qf:
            pen = 10.0
        return p + 0.5 * unc + bonus - pen
    candidates = [d for d in drugs if d not in qf]
    if not candidates:
        return {'kind': 'stop'}
    # if a molecular query is affordable and there is an unqueried-molecular drug
    # with high prediction, consider it when it could improve the model cheaply
    best_f = max(candidates, key=lambda d: (score(d), d))
    best_f_score = score(best_f)
    if avail_m and budget >= cm and cm < cf:
        m_cands = [d for d in drugs if d not in qm]
        if m_cands:
            # prefer molecular query for a drug whose prediction is uncertain and
            # which we might then functionally query
            def m_score(d):
                p = preds.get(d, 0.5)
                pr = prior.get(d, 0.5)
                return abs(p - pr) + 0.2 * p
            best_m = max(m_cands, key=lambda d: (m_score(d), d))
            # only spend on molecular if it leaves enough budget for at least one functional query
            if budget - cm >= cf and m_score(best_m) > 0.45 and best_m not in qf:
                # avoid molecular if we already have a very confident functional candidate
                if best_f_score < 0.9:
                    return {'kind': 'm', 'drug': best_m}
    # require a minimum expected value to spend a functional query
    if best_f_score < 0.35 and budget < 2:
        return {'kind': 'stop'}
    return {'kind': 'f', 'drug': best_f}
