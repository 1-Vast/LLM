# Independent prepared-data audit attempts

The first attempt stopped at import with `ModuleNotFoundError: No module named 'lxml'`. This occurred before audit main, before any newly opened protein values, and before writing the audit result. The independent parser dependency is installed into the maestro Python environment; installation output is retained in `AUDIT_DEPENDENCY_INSTALL.log`. This dependency repair does not alter baseline preparation, transform order or evaluation code. The audit has not imported prepare_baseline.py or evaluate_baseline.py and will not run a classifier.
