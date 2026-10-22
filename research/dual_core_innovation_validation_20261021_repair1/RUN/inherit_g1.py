def choose(obs):
    if not obs['queried_m'] and obs['step'] == 0:
        drug = min(obs['available_m'], key=lambda d: (abs(obs['predictions'][d] - 0.5), d))
        return {'kind': 'm', 'drug': drug}
    remaining = [d for d in obs['drugs'] if d not in obs['queried_f']]
    if obs['budget_left'] < 1 or not remaining:
        return {'kind': 'stop'}
    return {'kind': 'f', 'drug': max(remaining, key=lambda d: (obs['predictions'][d], d))}
