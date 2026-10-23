# Correction to sealed CROSS consistency coefficient

2026-10-23. Parent and constructive independently flagged a coefficient error in critic/CROSS.md. Preserve that sealed original; this addendum supersedes its claim that the proposed two penalties sum to 2*a^4 for the named A=0,B=1 case.

The actual constructive objective penalizes (AB-BA)^2+(AB-union)^2. For h0=0,yA=0,yB=1 and constant-step scalar SGD: AB=a, BA=a(1-a), union=a. Therefore its exact sum is a^4+0=a^4. The critic inadvertently counted BA-versus-union rather than the actual AB-versus-union term. If the labels are reversed, the sum is 2*a^4; averaging the two orders gives 3*a^4/2. These are distinct scopes and cannot be silently substituted.

The identity a=0 still makes every consistency penalty zero without learning. This remains a necessary anti-collapse/query-utility control, not proof that the joint query-supervised objective collapses. No biological result changes.

Constructive's actual reverse review also correctly notes that the critic diagnostic toy stipulates the two hypothesis operators and available diagnostic; neither was learned from source evidence. Its zero error reflects newly purchased distinguishing information and must not be reported as source-learned diagnostic discovery. Any later finite-budget test must include diagnostic/operator generation cost and freeze the permitted measurement pool without task-label leakage. Ordinary Bayesian discrimination still matches the entire stipulated toy.
