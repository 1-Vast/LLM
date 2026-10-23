# Frozen decision-only compression diagnostic

Before execution: four equiprobable stipulated worlds (d,n) in {0,1}². Final drug a in {0,1} has loss 1[a != d]. Two legal noiseless probes reveal qN=n and qX=d XOR n. Each costs 1/8; budget is two probes. No biology is claimed and no observed biological outcomes enter this construction.

Enumerate exact Fraction posterior Bayes drug risk for no probe, each single probe and both probes; expected values are 1/2,1/2,1/2,0. Including probe costs yields 1/2,5/8,5/8,1/4. A greedy policy requiring strictly positive one-step net drug-risk improvement stops immediately. Ordinary two-step joint-law enumeration buys both and achieves objective1/4.

Then test a precisely restricted candidate: compress each world to d (the terminal optimal drug), preserve each probe's marginal likelihood P(q|d), and approximate joint probe outcomes by multiplying these likelihoods. For either d, both probe marginals are uniform, so the factorized pair cannot identify d and has risk1/2. This is not a proof that every decision representation or decision-focused acquisition fails: retaining the correct joint probe law recovers the ordinary planner. It tests whether the declared decision-only factorization discards nuisance information that enables a later decision-relevant observation.

Save protocol/code hashes before the single execution; retain exact results and errors. Do not tune this witness or interpret it as OPO reproduction, a criticism of its published theorem, cell-model performance, world-model advantage or RSI evidence.
