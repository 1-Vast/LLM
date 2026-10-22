# Frozen array-local MAS5 protocol

Scope: exact RNA_IDENTITY_MANIFEST 172 arrays, 24 source Middle/High/Control and seven development Middle/Control at 2h. No Low, development High, or later RNA. Compound archive acquisition contacts excluded compressed bytes; extraction decodes only exact selected basenames.

R4.5.2, affy1.88.0, affyio1.80.0, preprocessCore1.72.0. One CEL per process, ReadAffy then mas5(normalize=TRUE,sc=500), then log2(pmax(signal,1)). All 54,675 manufacturer probesets, sorted radix IDs. No joint normalization, fitted reference, filtering, PCA or outcome-dependent annotation. Detection alpha1=.04,alpha2=.06,tau=.015 is QC only. State = arithmetic mean of two treated log vectors minus mean of their two matched 2h control log vectors. No averaging raw signal before log. No absolute RNA/cell interpretation.

Manufacturer CDF2.18.0: original official tar.gz and exact embedded data/hgu133plus2cdf.rda pinned by SHA256. Its data load yields 54,675 original probe definitions. Original package fails at R lazy loading even with no byte compilation/nonstaged installation; all logs retained. Use the unchanged embedded CDF environment through affy's native environment lookup (getCdfInfo / cdfFromEnvironment), with automatic package/network fallback disabled. No CDF definition is edited. This changes package loading only; MAS5 and probe definitions are unchanged. CDF namespace installation is not claimed successful. Annotation route decision made before any real CEL parsing.

Wrong platform, missing/duplicate probe IDs, nonfinite signal, acquisition/hash mismatch: technical abort with logs retained, no replacement or biological interpretation. No QC sample/probe exclusions. Negative/under-one signal uses the fixed floor above. All QC summaries retained.

First benchmark: the lexicographically first frozen source barcode in the authenticated WY-14643 archive. Only that source array may run initially. Continue others only if return code0, finite54675 outputs, elapsed<1800seconds and sampled peak RSS<4GiB. These are resource/technical gates, not biological selection. A failure cannot justify switching normalization or choosing another array without a recorded amendment.

Four-gene comparison uses independently frozen exact GPL570 EGR1/ATF3/GDF15/FGF21 mapping, arithmetic mean of all matched single-symbol probe log differences. No best-probe selection. These genes are ordinary prior-art baseline features.

Modeling contract is frozen separately before this protocol authorizes CEL conversion. RNA observation utility is separate from structure, agent and RSI claims. Later14 remains unopened.

## QC accessor technical revision2

First source run completed MAS5 and detection computation but failed before output because se.exprs has no ExpressionSet method. Verified actual affy mas5calls.AffyBatch source constructs ExpressionSet with assayData element se.exprs. Replace only se.exprs(calls) by assayDataElement(calls,"se.exprs"). Keep all numeric transformation/thresholds. Preserve attempt1 code, logs and receipt. Revision2 outputs use mas5_v2; same source barcode, no substitution. Retest source before any remaining array.
