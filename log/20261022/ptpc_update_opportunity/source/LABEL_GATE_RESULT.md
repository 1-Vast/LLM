# HCT116-only PTPC label qualification

Decision: recognized author-annotation encoding and usable development condition groups. This is a source/type/grouping gate, not a model experiment, efficacy assay authentication or positive innovation result.

The protocol and source_gate.py were hashed before values were accessed. PROTOCOL_SEAL SHA256: `16e6d87dd19f4faf1056876ad9a459a9e8fd4ba4e95a3b395e93a776cab1c102`. Exactly one local S8 workbook access followed. The prior identity-stage seal SHA256 is `d24e4f921d09422a8b958997b4c1c45553e7befee191e89bb5c1e651d923a799`; all 23 listed files rehashed unchanged. Archive SHA256: `efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133`. Member `TableS8_PTPC_info_0703.xlsx` SHA256: `540ec451edeca2bbbd08e53254cb9c09ba67b6f98727ff9c31e373a192290fdc`. No source archive or earlier sealed artifact was changed.

## Actual HCT116 tokens and grouping

HCT116 has 1,289 metadata rows. Actual Efficacy values are shared-string `N` (1,195 rows), shared-string `Y` (69 rows), or an absent cell (25 rows). All missing cells are explicit controls; all 1,264 noncontrol rows have recognized Y/N labels. No other token or storage type occurred. The predeclared annotation encoding is N=0, Y=1. This does not establish a viability horizon, threshold, dose or clinical meaning.

Grouping all 6/24h and Rep rows by `(Cell_line, Pert_ID)` yields 603 conditions including one all-missing control condition and 602 complete-label noncontrol conditions: 568 N and 34 Y. There are no conflicting known-class groups, mixed-missing groups or unknown groups. Thus the 69 Y rows represent 34 condition annotations; they are not 69 independent functional measurements. The class imbalance is material for any later metric and split definition.

Time coverage among noncontrols: {('24', '6'): 600, ('6',): 1, ('24',): 1}. Requiring both molecular times would retain 600 conditions (566 N, 34 Y). This coverage result is descriptive; no favorable subset is selected here. Keep the distinction between an all-condition annotation task and a paired-time state task in the next protocol.

| Kind | Actual hours | Rep | Rows | N | Y | Missing |
|---|---:|---|---:|---:|---:|---:|
| drug | 24 | (blank) | 601 | 567 | 34 | 0 |
| drug | 24 | biorep | 16 | 16 | 0 | 0 |
| drug | 24 | techrep | 26 | 25 | 1 | 0 |
| drug | 6 | (blank) | 601 | 567 | 34 | 0 |
| drug | 6 | techrep | 20 | 20 | 0 | 0 |
| control | 24 | (blank) | 1 | 0 | 0 | 1 |
| control | 24 | biorep | 11 | 0 | 0 | 11 |
| control | 24 | techrep | 1 | 0 | 0 | 1 |
| control | 6 | (blank) | 1 | 0 | 0 | 1 |
| control | 6 | biorep | 11 | 0 | 0 | 11 |

## Deduplication and later partition constraints

There are 1,242 distinct Sample_IDs and 47 technical-repeat rows; each of the 47 duplicated IDs occurs twice. Removing technical-repeat rows leaves 1,242 records, but these remain measurements across time and biological repeats, not independent outcome tasks. The result JSON separately lists the duplicated IDs and workbook row identities. One duplicated ID is a biorep+techrep pair; the others are blank-Rep+techrep. No many-to-many Sample_ID merge is permitted.

Use `(Cell_line, Pert_ID)` as the minimum indivisible later partition group and bind every 6/24h, plate and Rep row to it. If a subsequent chemical-identity audit finds multiple Pert_IDs for the same compound, merge those partition groups too. Treat technical repeats as replicate measurements of one sample; retain authenticated workbook row mapping before any aggregation. Biological repeats and two molecular times must not purchase additional functional labels or independent active-learning/RSI tasks. The measured function's actual replicate/assay independence is unknown.

Exclude explicit controls from supervised annotation training. For this HCT116 gate, all 602 noncontrol groups satisfy the prespecified complete/consistent-label rule; no unknown or inconsistent group needs removal. This does not authorize downstream split design based on test outcomes. Any later paired-time restriction or replicate aggregation must be frozen before state values are opened. With only 34 positive condition groups, use grouped splits and metrics that expose minority-class performance; a majority-label accuracy alone would be uninformative.

## Retained blindness and scientific limits

Cell_line was resolved before Efficacy. All 928 non-HCT116 rows were directly skipped before resolving their Efficacy cells: A375 216; NCI-H1975 249; NCI-H2170 255; Panc1005 208. Shared-string nodes were an in-memory lookup table only; no non-HCT116 label values were resolved or displayed. No protein worksheet or abundance was opened. HCT116 is development only; A375 remains selection-unopened; the other three backgrounds remain final-unopened.

The released target is author Efficacy. Its apparent Y/N format does not authenticate the PTNC assay contract for PTPC. Actual molecular/control times remain 6/24h while the Legend says controls were assigned 0h; do not recode them or claim a measured pretreatment baseline. No same-culture trajectory, early decision timing, prospective label-acquisition sequence, drug utility or RSI gain has been demonstrated. No API call, fit or search occurred. Stop at this gate; a separate frozen numerical protocol is required for further work.
