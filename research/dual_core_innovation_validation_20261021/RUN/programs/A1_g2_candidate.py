def run(env):
    drugs = list(env.drugs)
    def score(d):
        return 0.5 * env.W[d] + 0.3 * env.nn[d] + 0.2 * env.prior[d]
    order = sorted(drugs, key=lambda d: (-score(d), d))
    for d in order:
        if env.left() < 1.0:
            break
        env.query_f(d)
