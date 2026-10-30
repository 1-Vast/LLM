# CDI 数据契约审计

日期：2026-10-30（Asia/Shanghai）  
范围：仅审计当前工作区可访问的公开/本地资产和轻量元数据；不读 sealed/confirmation 响应，不改 `src/` 或 `tools/`。本审计把 CDI 定义为四层：

1. 分子相对结合/亲和力差异；
2. drug × cell 的功能响应（本报告以 viability/药敏为功能端点）；
3. target/subtype 与 cell 的遗传/背景上下文；
4. Agent 用上述信息选择下一项 drug × cell（必要时带剂量）测量。

“跨 assay 的预测关联”不要求 affinity 与 viability 在同一培养物、同一剂量或同一时间采集；但它只能支持预测/排序。要把关联解释成细胞内 target engagement 或 mediation，仍需同条件 engagement 或受控遗传干预。

## 判定摘要

| CDI 层 | 当前可行性 | 结论 |
|---|---|---|
| 分子相对亲和力差异 | **可行（受限）** | Klaeger 2017/ChEMBL 有可追溯的 lysate kinobead apparent Kd；可构造同 assay/target 内的相对排序，但大量值是右删失 `>`，不能当精确 Kd，也不是活细胞结合。 |
| drug × cell 功能响应 | **可行** | PRISM 19Q4 有 drug-batch × cell-line pooled viability、剂量和 plate/well；GDSC Jaaks 有单药/组合 viability 与剂量；BeatAML2 有患者样本单药药敏。三者端点和背景单位不同，不能直接合并成一个标签。 |
| target/genetic context | **可行（注释/背景层）** | PRISM 的 MoA/target 是药物注释；DepMap 19Q4 提供细胞身份、lineage/subtype、表达/突变；GDSC 提供 target/pathway 注释。它们可作条件特征，不能替代药物 engagement。 |
| Agent 选测 | **可做回溯式 masked 设计** | 已有完整公开矩阵可模拟逐轮揭示和选测；尚无公开的前瞻动作成本、真实购买/培养记录或独立 prospective Agent 结果。 |
| affinity→cell response 的因果 mediation | **当前不可识别** | 需要 cellular engagement、target subtype/isoform 解析和受控遗传对照；现有跨库 join 只能检验预测关联。 |

## 逐项资源审计

### 1. Klaeger 2017 / ChEMBL CHEMBL3991601

本地文件：`data/external/klaeger2017_chembl/klaeger2017_CHEMBL3991601_kd.csv`、`MANIFEST.json`、`molecules.json`。Manifest 记录来源为 ChEMBL REST、Klaeger et al. 2017（Science，CHEMBL3991601），并给出 CC BY-SA 3.0、检索日期 2026-10-19 与文件 hash。

- 规模/身份：70,505 activities，243 个 ChEMBL molecule，325 个 assay；CSV 的分子键为 `molecule_chembl_id`，同时有 `molecule_pref_name`。
- 亲和力：全部 `standard_type=Kd`、`standard_units=nM`；65,576 条是 `standard_relation=>`，4,929 条为 `=`。因此适合 censored relative-affinity/ranking 特征，不适合把每条记录当作可比较的精确数值。
- 靶点：`target_chembl_id`、`target_pref_name`、`target_organism`、`assay_chembl_id` 均存在；目标名称计数为 320（含 1,103 行 `Unchecked` organism/记录语义需谨慎）。同一 molecule 可对应多个 kinase/非 kinase target，不能只按药名挑一个“主靶点”。
- 缺失条件：没有 cell background、细胞内剂量、exposure time、vehicle、细胞培养 preparation 或 biological replicate。它是裂解液/kinobead binding 层，不能直接叫 cellular engagement。
- 允许用途：按 `molecule_chembl_id × target_chembl_id × assay` 聚合，保留 `=`/`>` censor 状态，作为分子层相对结合特征。要连 PRISM，必须用 ChEMBL/标准化结构（优先 InChIKey；PRISM 只有 Broad batch、name、SMILES）完成可复核映射，不能用模糊药名 join。

### 2. Broad PRISM Repurposing 19Q4

本地目录：`data/external/prism_19q4/raw/`；依据 `primary-screen-readme.txt` 与 `secondary-screen-readme.txt` 的原始说明和表头。

- primary：4,518 compounds × 578/562 cell lines；secondary：1,448 compounds × 489 cell lines。secondary 是 8-step、4-fold dilution、起始 10 µM。
- drug identity/target：`broad_id`（药物批次）、`name`、`smiles`、`moa`、`target`、`phase`；dose 的单位在 README 中为 µM。target/MoA 是 Broad Repurposing Hub 注释，不是实验测得的 engagement。
- cell identity/context：`depmap_id`、`ccle_name`、组织字段和 STR 质控字段；pooling 表有 `analyte_id`、`detection_pool`、`pool_id`。
- dose/plate/repeat：replicate treatment 表有 `dose`、`screen_id`、`detection_plate`、`compound_plate`、`well`；这是可审计的处理槽位和技术重复索引。README 明确 MTS010 是 147 个既有 oncology compounds 的 **technical redo**，不能自动升格为独立 biological replicate。
- endpoint/vehicle/time：`primary/secondary_*_logfold_change` 是相对 DMSO 的 log-fold viability，经过 ComBat；secondary 还提供 dose-response curve parameters（AUC/EC50/IC50 等）。README 没有 exposure-time 字段；因此不能把曲线 AUC 当成某个固定时间和单点剂量的 readout。vehicle 只由相对 DMSO 处理语义支持，桥接表仍需保留该限制。
- 允许用途：以 `broad_id`/标准化结构 × `depmap_id` × dose/screen 为功能标签，和 Klaeger 的分子层特征、DepMap 背景做预测；评估时必须按药物或 scaffold、细胞背景/lineage 分组，避免 replicate/plate 泄漏。

### 3. DepMap 19Q4

本地目录：`data/external/depmap_19q4/`。

- `sample_info.csv` 字段包括 `DepMap_ID`、`CCLE_Name`、`COSMIC_ID`、`lineage`、`lineage_subtype`、`lineage_sub_subtype`、`lineage_molecular_subtype`、`culture_type`、`culture_medium`、RRID、疾病和来源等。
- `CCLE_expression.csv` 与 `CCLE_mutations.csv` 提供 baseline 分子背景；这些是未处理背景，不能解释为药物处理后的功能或 target engagement。
- 没有本目录内的 drug、dose、time、vehicle、功能终点；因此它只能作 PRISM/GDSC 的背景与遗传上下文。PRISM 的 `depmap_id` 可作精确细胞键，但这只证明身份对齐，不证明两库培养/时间/批次相同。

### 4. GDSC Jaaks 2022 anchored combinations

本地目录：`data/external/gdsc_combinations/jaaks2022_figshare/`，包含 original/validation fitted CSV、原始 wells zip 与 `Glossary.xlsx`。

- fitted 表有 46 列，关键字段为 `CELL_LINE_NAME`、`SIDM`、`COSMIC_ID`、`ANCHOR_NAME/TARGET/PATHWAY/CONC`、`LIBRARY_NAME/TARGET/PATHWAY/CONC`、单药 viability 与 synergy EMAX/AUC/XMID 等。
- raw zip 表头另含 `BARCODE`、`SCAN_ID`、`DATE_CREATED`、`SCAN_DATE`、`ASSAY`、`DURATION`、`POSITION`、`DRUG_NAME`、`CONC`、`INTENSITY`，说明剂量与实验时间字段在原始层可追溯；fitted 派生表不应被误读成原始重复。
- 该资源适合组合/药敏响应开发和剂量条件化；anchor/library target/pathway 是注释，不是 engagement。不同 screen 的日期/stock/重复关系需按 raw barcode 和 glossary 另行确认；不能把 original 与 validation 自动称为独立生物实验。

### 5. BeatAML 2.0（补充功能—遗传背景）

本地目录：`data/external/beataml2_20261017/`。

- `beataml_probit_curve_fits_v4_dbgap.txt` 有 63,395 条 single-agent curve-fit 行，569 个患者样本、166 个 inhibitor；键为 `dbgap_subject_id`、RNA/DNA sample、`inhibitor`，含 concentration range、curve status 与 AUC/IC 等派生字段。
- raw inhibitor 表头保留 `plate_num`、`replicate`、`well_concentration`、`normalized_viability`、`time_of_read`、`passed_qc`，所以可做患者背景的剂量/时间/重复审计；它不是 PRISM 的 cell-line 单位。
- `beataml_waves1to4_norm_exp_dbgap.txt` 是 RNA 背景矩阵，WES 表有样本、变异和 gene/symbol 字段。药物 target/subtype 并非该 release 的实验测量，需外部标准化注释后才可作为特征。
- 允许用途：独立外部功能评估或患者背景泛化；不得把患者样本与 PRISM cell line 名称直接 join 成同一实验单位。

### 6. LINCS L1000（proxy，不是功能标签）

本地目录：`data/external/lincs_l1000_gse92742/`（GSE92742 phase 1）与 `data/external/lincs_l1000_phase2/`（GSE70138）。

- sig metadata 有 `pert_id`、`pert_iname`、`pert_type`、`cell_id`、dose、dose unit、time、time unit、`distil_id`；vehicle 行显式为 `ctl_vehicle`/DMSO。pert metadata 提供 canonical SMILES/PubChem（部分遗传扰动记录为 `-666`）。cell metadata 有 cell type、site、subtype 和 provider 信息。
- GCTX 是 Level 5 COMPZ L1000 transcriptomic signature（phase 1 473,647 × 12,328；phase 2 118,050 × 12,328 的 schema）。它没有 PRISM/GDSC viability，也没有同条件独立功能终点。
- 允许用途：做药物×细胞×dose×time 的分子状态 proxy 或 Agent 选测先验；禁止把转录响应补写为 viability，禁止与 PRISM 以药名/细胞名 join 后声称同一条件功能配对。

### 7. MIX-seq / scPerturb（状态 proxy）

`data/external/mixseq_scperturb/mcfarland_2020.h5ad` 的 `obs` schema 含 `DepMap_ID`、`perturbation`、`dose_value`/`dose_unit`、`time`、`hash_tag`、`channel`、`chembl-ID`、QC 和单细胞状态字段；X 为稀疏表达矩阵。没有 viability、再生长或独立功能端点，故只作状态 proxy，不作 CDI 功能标签。

## 资源缺口与名义交集限制

- 当前未发现可读的 BindingDB、KIBA、Davis 或 PBCNet2.0 release；`data/raw/kinobeads`、`kinobeads1000`、`kinome_gxe`、`prism`、`depmap`、`combination_sources` 等目录为空，不能当作数据存在的证据。`data/external/gdsc2_fitted` 也为空。
- 三方名义交集最多可定义为：标准化 drug identity（ChEMBL↔Broad↔GDSC）× PRISM/DepMap exact `depmap_id` × Kd target annotation。它不等于三方同一实验。必须保留每个来源自己的 assay、dose、time、vehicle、plate/preparation、replicate 和 endpoint；缺失字段不能从另一库补写。
- Kd target 与 PRISM/GDSC target 注释的名称相同，也不能证明同一 isoform、细胞内占有率或下游因果。若要声称 mediation，至少需要同一细胞背景的 cellular engagement 或可识别的 genetic perturbation/rescue；当前公开资产没有这样的配对。

## 最小可行 CDI holdout 设计

这是可在当前公开矩阵上执行的回溯式 Agent 选测，不是 prospective wet-lab 证明：

1. **先冻结身份。** 用标准化结构/InChIKey 建立 ChEMBL molecule ↔ PRISM `broad_id` ↔ GDSC drug 的白名单；保留盐型/批次歧义为未映射。DepMap 只用 exact `depmap_id` 对齐。
2. **分组留出。** 外层按 drug scaffold（或严格 drug group）和 cell lineage 分组，至少 3 个互不重叠的 drug 组 × 3 个 lineage 组；每组保留多个完整 drug×cell block，禁止随机拆同一药物或同一细胞的剂量行。这个规模只能作为 pilot，不能宣称普适收益。
3. **可见输入。** Agent 只读训练块中的 affinity summary（含 censor flag）、结构、target/MoA 注释、DepMap baseline context 和已揭示的功能响应；剂量/时间等字段缺失必须作为 mask，而非填成默认值。
4. **动作与对照。** 每轮从未揭示的 drug×cell（可选固定 dose）候选中选 1 个或固定 batch；与随机、结构相似度、uncertainty 和 oracle 上限比较。记录动作数、实际可用候选数、是否跨 scaffold/lineage，以及每一轮的预测误差/排序质量。
5. **评估。** 在整块冻结的 PRISM viability 上报告 held-out drug、held-out cell lineage 和双冷启动三种结果；BeatAML 只作独立患者背景外评估，不与 PRISM 标签混合训练。用 cluster/bootstrap 以 drug 或 cell 为统计单位，不能把 dose 行数当独立样本。
6. **因果边界。** 若 Agent 只提高 viability 预测或下一测量排序，结论限于 predictive selection。没有 cellular engagement/genetic intervention 时，不报告“亲和力导致响应”或“靶点介导”的机制结论。

## 最终裁定

- **可行：** 以 Klaeger Kd 的 censored relative-affinity 特征 + PRISM/GDSC drug×cell viability + DepMap genetic/background context，进行严格身份映射后的跨 assay 预测和回溯式 Agent 选测。
- **条件可行：** 将 BeatAML 作为患者背景的外部功能评估；必须保持 patient sample 与 cell-line 任务分开。
- **当前不可行：** 从现有跨库数据直接证明 cellular target engagement、affinity→viability 的因果 mediation、实际少测省钱或 prospective Agent 优势。
- **重开数据门：** 取得结构级 drug mapping、PRISM exposure-time/vehicle 与独立 biological replicate 说明；补充 cellular engagement 或受控遗传扰动后，才可升级 mediation/机制主张。功能主张若限定为 viability，不额外要求第三种功能读出，但必须保留 endpoint/条件差异和独立性边界。

