# Stage 3: initial-screen raw schema, prior to functional analysis

The source-only stages are complete: repository metadata, pinned tree, eight explicitly allowlisted source/metadata files. Commit b654a45faf5a80cdb1b514188cc90af8c9565b85. Initial raw CSV names and passage metadata establish a potential lawful alternative to whole-screen min/max normalization. They do not establish a new mechanism.

Download exactly E3CA/E3CB/E3DA/E3DB from data/cxcl9_assay/. Leave all AL1/AL2 files, prepared MIDAS labels, optimization outputs and synthetic labels unfetched. The schema script may expose headers, categorical identities, missing-value counts and condition/sample group sizes; it must not print fluorescence values or aggregate function statistics. Raw bytes are saved for reproducibility, but root and peer reviewers read only schema until the prediction protocol is frozen.

The aim of a later scoped development experiment is to test whether ordinary direct models leave reproducible intervention-by-stimulus error. No claim that binary activity clamping is wrong follows solely from such a comparison. No model, novelty, WM necessity, agent, inheritance or RSI advantage is predeclared.

Design feasibility requires authenticated intervention labels, matched per-sample blank and positive no-inhibitor controls, and clarity on passage/sample independence. If these are absent, revise the endpoint or stop before predictions. Schema parsing failure is recorded and repaired before outcome access. Source code is evidence of implementation, not proof all repository data follow that implementation.
