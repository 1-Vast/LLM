# Local verification path correction

Initial VERIFICATION.json retained:109checks, one failure. It resolved source/CROSS_SEAL.json's explicit phase-relative report path source/CROSS.md against the source directory, producing nonexistent source/source/CROSS.md. The actual source/CROSS.md bytes match the sealed digest4a3a781be675058b0199923df39d166f6bef4beb200cba8e35475b344404dcb5. No report, seal, experiment or score was modified to address the failure.

Initial verifier code copied to research/feedback_shift_mechanism_20261023/verify_phase_initial.py before correction. The current verifier adds an explicit phase-relative convention for the five named role subdirectories; other repository-relative/absolute/seal-directory bindings retain their meanings. Corrected results go to VERIFICATION_v2.json, not over the failed original. Only the corrected file may be reported as clean. This local path repair does not restore historical global provenance or improve biological evidence.
