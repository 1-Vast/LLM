# Independent AML lineage join static audit

Read the three requested source files and pinned nontruncated tree at3d5ef9070a259fb902feccbc5948f10e6a9d44ae. All3source SHA256, Git blob SHA1 and byte sizes independently match receipts/tree (AML_JOIN_SOURCE_CHECK.json). No author code imported/executed, raw.statsrecord read, network, expression/response arrays or fit. Existing sealed reports are unchanged. Line numbers below are one-based within the saved `.body` source files, corresponding to the pinned Python files.

## What the parser actually assumes

`AML_lineage_utilities.py:40–53` defines extractReadInfo. It splits **readName on `_` into exactly seven columns** named seq_info,R1,readCount,totalReads,x2,x3,x4. Under default method10X it extracts cellBC=R1[0:16] and UMI=R1[16:28], reconstructs readName and casts readCount toint. It does not simply trust or parse a separate public.stats`umi`column. A public readName must therefore preserve the expected28base barcode+UMI encoding and7field grammar. That contract is currently **unverified from these source files alone**, because no raw stats records were read. A column named umi does not prove equivalence to this extracted UMI or to the GEX barcode.

`getBC`,utilities33–38, finds an N-pattern's positions in mergedReadRef and takes the same substring of mergedRead, otherwise emits dashes. Lineage preprocessing36–43 applies this to a14N founderTag, filters keep==PASS and merges external whitelist on cellBC=FB_bc. Its48explicitly selects **both GEX_bc and FB_bc**. This demonstrates the required feature-barcode→gene-expression-barcode join, but the script does not instantiate the whitelist or certify its public presence, sample scope, uniqueness or barcode-suffix convention. It cannot be replaced by an assumed identity mapping. The clustering code later expects lin_cellID and exp, which are also not constructed from the public sample manifest in these snippets.

Founder/allele processing then uses eight target columns, Cassiopeia UMI/read filters, Starcode founder-tag correction and optional founder whitelist (preprocessing49–92). Postprocessing resolves each cell toward a single founder using read/UMI proportions (104–128). These are meaningful components of a recovery pipeline. Their existence does not certify final public GEX→founder/clone annotations or a unique baseline-control-treated join.

Clone-tag extraction at139–170reads a separate statsfile, uses a38N template, applies whitelist/pattern filters, Starcode correction and aggregation by cellBC,exp,CasTag. Matching founder and clone tags requires **same physical sample/cell identity**, not merely identical16base strings. TenX cell barcodes can recur across libraries. Utilities grouping by cellBC (e.g.226–227) and clustering merges on cellBC do not themselves add sample namespaces; any upstream prefix/exp mapping must be authenticated before combining libraries.

## Why these snippets are not a ready executable contract

The pinned scripts include unresolved variables and inconsistent names typical of exported analysis fragments. Concrete examples:

- preprocessing48uses target_cols before local definition at49; external barcode_path,whitelist,path_to_founder_whitelist,exp and other paths are not instantiated.
- preprocessing151defines pattern,153uses rs29_pattern;157expects exp absent from the explicitly selected145columns;158references c1498_raw_cmb rather than the current local frame.
- tag clustering57defines intBC_to_founders but60uses intBC_to_Founders. Its60and137call do_clusters with tag/algorithm keywords, whereas the requested utilities226signature is only do_clusters(data,res=.8), and227hardcodes grouping the CasTag column.
- clustering105expects lin_cellID/exp before source code shown establishes their mapping. Later founder/cluster column naming changes are not fully connected by a declared sample-specific workflow.

I did not execute these to manufacture a runtime failure. The static inconsistencies are sufficient to say **the exact standalone concatenation is not an authenticated end-to-end recipe**; a compatible original notebook/session or explicit reconstruction is required. They are not proof the paper's analysis was invalid, that no matching utility version exists, or that recovery from public data is impossible. Do not silently fix them and claim a faithful author-pipeline reproduction.

## Founder/clone clustering and look-ahead

TagClustering36–60accepts a combined allele table, derives tag-frequency/read thresholds from all its cells and forms founder clusters. Utilities193–204builds a graph connecting cells by nonzero Jaccard overlap of tag sets;207runs Louvain and226–237clusters the provided frame without a baseline-only partition. TagClustering141–163prunes clone tags using cluster frequencies. At178–203, founder and clone labels are assigned by descending **observed population size ranks**, producing names such asH1andH1.1.

These functions do not force baseline-only construction or prevent treated/untreated endpoint cells from changing baseline cluster membership, retained tags, cluster support thresholds and size-ranked identities. If their input includes all pre/post samples, a “pretreatment” feature derived from those assignments, ranks, tree topology, modules, clone-size counts or retained-cell mask can contain future information. Even barcode-only clustering can become outcome-conditioned through survivor abundance and detection. A labelH1is not a natural fixed entity across independently ranked experiments.

This is a **conditional risk**, not evidence that these snippets necessarily concatenated every timepoint or that the authors used endpoint-derived features prospectively. The snippets leave the actual input population and sample manifest unresolved. Endpoint-assisted lineage reconstruction can be legitimate for constructing retrospective fate labels and conservative grouping; using it as a baseline predictor is a distinct claim. If future samples are used only to ascertain outcomes, isolate that label-construction pipeline and never feed future-derived ranks/counts/modules into baseline features or source selection. Freeze the entity definition and group shared founders/related descendants before evaluating heldout tasks.

Utilities56–94also offers make_vanilla_tree, building a character matrix and Cassiopeia tree from the supplied allele table, optionally merging metadata. No chronological restriction is imposed in that function. A downstream tree can reflect all supplied terminal cells; it is not automatically a lawfully observed pretreatment world state. I did not read or run a separate full tree-analysis pipeline in this audit.

## HL60 versus C1498 cannot be inferred by filename reuse

TagClustering's header5explicitly identifies founder clustering for **HL60**, and outputs at92,127,136,163use241211_hl60s filenames. In contrast preprocessing158contains a c1498_raw_cmb reference. The lineage and clone-tag routines are generic partly shared fragments, not a sample manifest assigning public.stats/GEXlibraries to HL60orC1498. A humanAMLorpreAraCfilename does not on its own instantiate which engineered cell line, replicate flask, founder pool, treatment arm and duration it represents.

Do not connect murine C1498 founder-specific growth assays to humanHL60baseline expression solely because both have these tags. Treat the systems and each pool/flask as distinct namespaces until the exact author manifest/known founder whitelist and matched culture design are authenticated. Independent clones within one founder pool are not automatically independent treatment histories. Prior reports' differing HL60treated/control durations must not be silently equated as matched-time outcomes; this code audit does not resolve those metadata.

## Feasible conditions and smallest next step

The code establishes a **plausible recovery path**: stats read identifiers→feature barcode/UMI→founder/clone tags→error-corrected assignments→external GEXbarcode mapping→sample-namespaced GEXjoin. It does not close that path. Current status is **NO_NUMERICAL_GO / CONDITIONAL_SOURCE_JOIN_FEASIBILITY**, not a global data impossibility.

The minimum next action is a bounded **identity-only contract audit**, after root explicitly defines/authorizes it: obtain/locate the exact sample manifest and FB_bc→GEX_bc whitelist (or authenticated conversion rule), verify parser grammar on a tiny predetermined number of permitted nonexpression stats identifiers, and verify how matching GEX barcode files encode library/sample suffixes. Report collisions/cardinality and schema only, no clone abundances/fates, expression or treatment outcomes. Raw barcode/tag identities may themselves be sensitive to lineage grouping and should be recorded as exposure, not called untouched.

Then choose one system and explicit baseline/control/treated libraries; establish founder-level matching and culture duration, freeze code/environment/Starcode/Cassiopeia versions, and state whether labels use endpoint-assisted clustering. Prefer an authenticated final sample-namespaced annotation table or externally defined founder/tag whitelist. If no such mapping or valid conversion can be authenticated within that bounded audit, stop this specific source join rather than repeatedly retrieving unrelated expression matrices. If authenticated, source-only/baseline-only feature construction and outcome-only endpoint linkage still require separate tests before functional modeling.

No source-specific incremental control, new updater, world model, inherited research rule or RSI benefit follows from this static recovery outline. It is a concrete evidence gap with a finite next check, not permission to fit generic treatment-interaction models as a novel mechanism.
