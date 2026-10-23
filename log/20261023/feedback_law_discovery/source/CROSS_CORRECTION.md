# Correction of the consistency-penalty coefficient

After source sealed CROSS.md, critic reported a correction that source accepts. Source's claimed hand-check of the summed penalty was incorrect: the arithmetic AB=a, BA=a(1−a), union=a is correct, but constructive's actual objective uses **(AB−BA)^2 + (AB−union)^2**, not a symmetric sum of both order-to-union distances.

For yA=0, yB=1 this actual penalty is **a^4**, not 2*a^4, since AB−union=0. For the reversed yA=1, yB=0 labeling it is 2*a^4; averaging both assignments gives 1.5*a^4. The zero-penalty identity solution a=0 and the scoped conclusion that invariance alone does not establish useful updating remain valid. Query supervision can still prevent this collapse in principle. The correction does not establish failure of the joint learned objective.

The previously sealed CROSS.md is preserved. This separate addendum supersedes only its numerical penalty coefficient and records the source verification mistake transparently.
