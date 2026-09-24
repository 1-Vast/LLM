# Table Filter

Applies one explicit condition to a named CSV or TSV column and returns the match count plus a
bounded row sample. Supported operators are `equals`, `contains`, `greater_than`, and `less_than`.
It never evaluates code expressions or constructs shell commands.

Entry point: `tool.py`, function `run(parameters)`. Required parameters: `column`, `operator`, and
`value`. Optional `max_rows` is limited to 1 through 100.
