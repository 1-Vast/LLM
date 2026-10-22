# Retained failures

2026-10-22: first source_check.py invocation exited1 before any HTTP request because Maestro Python has no bs4 module. Replaced the HTML extraction with the Python standard-library HTMLParser; no package install or environment mutation. The initial source code was unsealed and no result had been produced.
