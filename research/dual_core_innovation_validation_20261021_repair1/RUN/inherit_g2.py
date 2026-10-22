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
    # Use molecular query to calibrate the model when predictions are uncertain
    # and a molecular query is affordable. Choose the drug with prediction closest
    # to 0.5 among available molecular candidates, but only if no functional
    # query has been made yet or if the model's uncertainty is high.
    if step == 0 and avail_m:
        cand = [d for d in avail_m if d not in qm]
        if cand:
            drug = min(cand, key=lambda d: (abs(pred[d] - 0.5), d))
            return {'kind': 'm', 'drug': drug}
    # After feedback, decide whether to trust the model or override it.
    # Compute a trust score based on how much predictions have shifted
    # and how consistent they are with the prior and nn baseline.
    # If the model has been updated (step > 0), we may want to explore
    # drugs with high uncertainty or disagreement between model and baselines.
    # We prioritize functional queries on drugs with high predicted probability
    # but also consider disagreement with prior/nn to avoid overfitting.
    # First, gather remaining functional candidates (not yet queried functionally).
    rem_f = [d for d in drugs if d not in qf]
    if budget < costs['f'] or not rem_f:
        # If no functional budget, try molecular if affordable and useful
        if budget >= costs['m'] and avail_m:
            cand_m = [d for d in avail_m if d not in qm]
            if cand_m:
                # Choose molecular query on drug with highest prediction uncertainty
                drug = max(cand_m, key=lambda d: abs(pred[d] - 0.5))
                return {'kind': 'm', 'drug': drug}
        return {'kind': 'stop'}
    # After step 0, we have some feedback. Decide whether to trust model or override.
    # Compute a simple trust metric: if the model's predictions are close to prior
    # and nn, we trust it less (since it hasn't learned much). If predictions
    # deviate significantly, we trust the model more.
    # For each candidate, compute a score that balances predicted probability
    # with disagreement from prior/nn (to encourage exploration) and similarity
    # to already queried drugs (to avoid redundancy).
    # We'll use a weighted score:
    #   score = pred[d] + alpha * |pred[d] - prior[d]| + beta * |pred[d] - nn[d]|
    #   - gamma * max_sim_to_queried(d)
    # where alpha, beta, gamma are small constants.
    alpha = 0.1
    beta = 0.1
    gamma = 0.05
    queried_set = set(qf.keys()) if isinstance(qf, dict) else set(qf)
    # Actually qf is a dict mapping drug to label? The spec says queried_f is drug to observed binary label.
    # So qf is a dict. Similarly qm.
    # We'll handle both dict and list for safety.
    if isinstance(qf, dict):
        queried_f_set = set(qf.keys())
    else:
        queried_f_set = set(qf)
    def max_sim_to_queried(d):
        if not queried_f_set:
            return 0.0
        # sim is nested drug fingerprint similarities: sim[d1][d2]?
        # We'll assume sim is a dict of dicts or a function? The spec says sim is nested drug fingerprint similarities.
        # We'll try to access sim[d][q] if available, else 0.
        s = 0.0
        for q in queried_f_set:
            if d in sim and q in sim[d]:
                val = sim[d][q]
            elif q in sim and d in sim[q]:
                val = sim[q][d]
            else:
                val = 0.0
            if val > s:
                s = val
        return s
    def score(d):
        p = pred[d]
        pr = prior.get(d, 0.5) if isinstance(prior, dict) else 0.5
        n = nn.get(d, 0.5) if isinstance(nn, dict) else 0.5
        disagree = abs(p - pr) + abs(p - n)
        sim_pen = max_sim_to_queried(d)
        return p + alpha * disagree - gamma * sim_pen
    # Choose the drug with highest score among remaining functional candidates.
    best = max(rem_f, key=lambda d: (score(d), d))
    return {'kind': 'f', 'drug': best}
