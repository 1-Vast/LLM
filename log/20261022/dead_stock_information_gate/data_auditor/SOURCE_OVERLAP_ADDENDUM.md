# Exact primary locator for cross-file reuse

This supplements the preserved independent DRAFT.md without rewriting it. Reused source: log/20261022/functional_dynamics_gate/skeptic/BESTDR_PRIMARY.body, SHA256 ea88af53978f52b086dbb98f3326e24c141982eed0c83ba5203210d974b5725c. The complete matching paragraph is already preserved verbatim in data_auditor/EVIDENCE.json under primary_exact_excerpts.

Unique locator: Results section, paragraph beginning “To investigate BESTDR’s ability to estimate a CR curve”. Its first sentence is:

> To investigate BESTDR’s ability to estimate a CR curve, we treated HCT116 p53-VKI cells with eight concentrations of cisplatin and tracked viable counts for 72 hours, including the data from the previous experiment at 0 and 12 μmol/L (Supplementary Fig. S1G).

The Materials and Methods HCT116 paragraph separately lists 12.50 μmol/L in its concentration series. The two wordings are retained. This primary statement is enough to reject an assumption that the two deposited file names represent independent experiments. It does not authenticate which exact rows were copied, whether all reported counts match, or the meaning of their opaque context labels; those array relationships were not opened in this audit.

Root's subsequent choice—DoseResponse.csv only, with Replicates.csv fully excluded from fitting, selection and verification—removes this cross-file reuse pathway for the proposed gate. The resulting inference remains dose-held-out readout prediction within the deposited dose-response source, rather than independent-run replication.
