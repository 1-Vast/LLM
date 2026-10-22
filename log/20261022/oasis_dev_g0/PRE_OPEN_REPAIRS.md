# Independent pre-opening review corrections

No response/count/CNN numeric export existed during these reviews.

1. Sceptical reviewer found pairs were first chosen after QC, allowing an outcome-dependent substitution of a third plate for a failed predesignated plate. The code now fixes first-two plate identities on the entire dev menu, then reports pair QC attrition without replacement. An invariant includes a failing early plate and a valid later plate.
2. Data reviewer found constant-response/no-variance data could produce NaN correlation or divide-by-zero, preventing an honest negative report. Such endpoints now produce null estimates and `NO_DYNAMIC_RANGE`/failure; nonfinite bootstrap draws are counted and an endpoint fails if <95% are finite. Original scientific margins remain unchanged.
3. Removed an initial trivial fold hash test duplicating the implementation; it added no protection. The first six-test output is retained. Current six tests address predicate export, physical duplicates, control-only normalisation, pre-QC plate selection, degenerate response reporting and failed observations.

Bootstrap intervals condition on these observed plates and controls; no independent culture/run uncertainty is claimed. High global repeat correlation can be driven by dose or broad injury range. It is only an entry gate, not information gain or decision utility. The 0.02 information margin is a computational screening margin; practical drug-discovery utility remains unqualified.
