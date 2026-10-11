# Independent read-only review

Reviewed on 2026-10-11: `src/maestro/campaign_budget.py`, the incremental changes in
`tools/evaluation/decision_report.py`, the research `DESIGN.md`, and the matching budget
and report tests. This review changed none of those files and did not rerun their tests.

No blocking correctness issue was found in the reviewed changes. The hard cap uses
named resource units; terminal net utility uses separate declared utility prices.
Additional resource and utility costs are not implicitly converted or counted twice.
Both paired arms must pass the same cap for every campaign. The optional cap and
zero-default additional costs preserve the prior arithmetic for old inputs.

The report enforces feasibility retrospectively. A purchase executor must call
`require_feasible` on cumulative proposed expenditure before issuing the purchase;
adding this reporting contract alone does not wire it into every production executor.
The design accurately describes the new exposed-data experiment as development, its
coverage calculation as a diagnostic, and LLM improvement as an untested contrast.

For the separate source audit, `audit_assets.py` was executed successfully: all 17
retained successful source responses matched their recorded SHA-256, downloaded table
counts were reconstructed, and strict structural input matching produced five
BBBC021/PRISM matches. File counting of large existing assets is an availability audit,
not a complete hash verification of those large datasets.
