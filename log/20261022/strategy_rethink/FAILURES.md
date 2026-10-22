# Failures and corrections

2026-10-22 first `inspect_schema.py` execution exited 1 before any output file or outcome cast: this NumPy build does not expose private `_read_array_header`. Replaced it with public version-specific `read_array_header_1_0`/`read_array_header_2_0`. No biological result existed or was changed.
