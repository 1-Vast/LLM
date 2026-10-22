# Retained synthetic-run failure

The first test command exited before execution with `SyntaxError: unmatched ')'` at the synthetic fixture's enumerate loop. No source workbook or source numerical value was opened by that failed command. Corrected the parenthesis and removed an unused import from the new worker; added an unexpected-lineage product test. This correction occurred before freeze and before the source census. The failed command and reason are retained here; the subsequent structured test result records the corrected test run.
