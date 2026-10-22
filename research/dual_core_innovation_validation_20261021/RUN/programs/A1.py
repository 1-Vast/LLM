def run(env):
    drugs = list(env.drugs)
    order = sorted(drugs, key=lambda d: (-env.W[d], d))
    for d in order:
        if env.left() < 1.0:
            break
        env.query_f(d)
