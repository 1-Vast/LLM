# Explicit metadata whitelist, before row parsing

Header-only retrieval succeeded: PC9 metadata has nGene,nUMI,orig.ident,percent.mito,sample_id,time_point,sample_name,sample_type,full_cell_barcode,lineage_barcode,clone_size. Pooled metadata has cell,orig.ident,nCount_RNA,nFeature_RNA,sample_id,sample_type,sample_pool,percent.mt,cell_line,droplet.type,best.LLK,experiment. Two compressed full metadata assets were contacted (1,759,405 and1,183,808 bytes), zero data rows parsed before this protocol. Author LFS pointers were authenticated, not fetched:581,991,189 and1,007,291,633 bytes; author README gives Seurat dimensions. Count/expression matrices remain unopened.

The next parser may access exactly these field values:

- PC9: orig.ident,sample_id,time_point,sample_name,sample_type. It may validate schema/row width and total row count. full_cell_barcode and lineage_barcode remain unparsed in this design step.
- Pooled: orig.ident,sample_id,sample_type,sample_pool,cell_line,droplet.type,experiment. The cell identifier may be skipped, not summarized.

All other cell values, in particular clone_size, nGene/nUMI, nCount_RNA/nFeature_RNA, percentages and likelihoods, are skipped without numeric conversion or statistics. Report distinct design tuples and their captured-row counts. These counts describe a released, sorted scRNA sampling design and are not viability, expansion or true population proportions. Any explicit majority fate or future-derived category in an allowed label is exposed as a design string only and must be prohibited as model input later.

Purpose: authenticate early timepoints, physical/library and replicate labels, raw sort gates, pooled model mapping and whether independent tasks/action units actually exist. No prediction, performance optimization or biological hypothesis test runs here. A subsequent lineage-join or outcome analysis requires a separate frozen specification; no threshold is selected from biological response values.
