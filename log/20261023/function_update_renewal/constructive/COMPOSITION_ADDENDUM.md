# Operator composition: scope of equivalence

Written after independent report seal, in response to root's explicit algebra question. This is a specification refinement, not a peer-result review or an expanded candidate fit.

For f(a,b)=g^T T_a T_b s, freeze T_a,T_b,s: updating g is globally exact ordinary linear-head updating with fixed feature T_a T_b s. Freeze g,s,T_b: f is globally linear in vec(T_a), with feature vec(g(T_b s)^T) under consistent vectorization. These are exact finite identities, not Taylor approximations.

When both T_a and T_b change, the finite difference contains

    Delta f = g^T DeltaT_a T_b s + g^T T_a DeltaT_b s
              + g^T DeltaT_a DeltaT_b s.

The final term precludes claiming global fixed-feature *linear* equivalence from the first-order tangent features alone. Actual seeded composition_check.py gives actual-minus-first-order 4.802206999028414, equal to the cross term 4.802206999028415 to numerical precision. This is not a biological gain. An unrestricted direct predictor over pair identities can represent every finite table; a direct polynomial/shared-bilinear predictor can reproduce the composition when given the same factors. Representation equality alone does not establish equal sample complexity, optimization, cost or portability. Conversely, extra second-order terms alone do not establish a world-specific advantage.

The strongest retained potential difference is a **shared factorized intervention algebra** whose feedback corrections constrain multiple future combinations with fewer parameters than a free pair table. It would need an intervention-semantic restriction, identifiable state/readout measurements and transport to separate subsequent interventions/contexts. Generic low-rank bilinear interactions and representation sharing are already standard strong direct baselines (including NAIAD-style factor interactions); a proper candidate must specify what extra constraint beyond those buys statistical or decision efficiency.

Important biology: T_a T_b is ordered. Simultaneous Norman double-CRISPRa does not authenticate an intervention-order outcome. One may test a declared symmetric map (T_aT_b+T_bT_a)s/2 for unordered combinations, but must not infer genuine sequence dynamics, temporal memory or order dependence from those data. Both symmetric factorized direct models and an additive/residual model belong in the ordinary baseline menu.

The new data needed are paired state and function feedback under authenticated intervention/context identities, a measurement contract for simultaneous versus sequential actions, and an independent later task. Current function-only pair data do not identify orthogonal state changes. More nonlinear layers cannot manufacture those observations. Therefore no nonlinear operator is promoted merely because the simplest linear version fails; the algebra leaves this **conditional difference** open while stopping the instantiated linear candidate.
