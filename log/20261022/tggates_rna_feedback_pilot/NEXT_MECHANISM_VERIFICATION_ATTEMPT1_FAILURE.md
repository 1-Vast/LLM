# Retained review-receipt verification failure

2026-10-22. First finalize_next_mechanism_review.py execution exited1 at the assertion comparing raw EXACT_REQUEST.txt bytes with receipt request_sha256. No terminal receipt was written and no API call or biological experiment was repeated.

The maintained call_review.py hashes the in-memory prompt's UTF-8 text before Path.write_text writes EXACT_REQUEST.txt. On Windows that text write serializes line endings as CRLF, so a raw-file hash is not necessarily the logical request hash. Preserve every original request and receipt. The verifier repair compares the universal-newline-decoded request text to the receipt's logical request hash, and separately records the serialized file's raw hash. Successful execution must establish that relation for every call; it cannot establish an authenticated server-side request capture or hidden transport-attempt count.

This is a local serialization-verifier failure, not a failed scientific hypothesis or a provider/review failure. The original assertion and traceback remain in the tool transcript; this record retains the failure in log/ as required.
