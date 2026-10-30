# R198-A3 动态路线：记录（metadata-only 资格 + 设计）

2026-10-27 ｜ 执行：cellstate-lit（task-26，revision 2 → completed） ｜ 工作目录：`D:\MAESTRO`。

## 0. 任务与纪律

- 任务：对本地 Mix-seq 做 **metadata-only 资格**，回答"哪些动态信息会改变具体药物决策"，写设计草案；**不训练、不跑时间预测、不读响应做统计、不改其它目录**。
- 只写：`research/2026-10-27-innovation-scouting/dynamic_route/` 与 `tmp/`。
- 禁止项执行情况：**未训练任何模型；未跑时间预测/任何 effect 统计；未读 h5ad 表达矩阵 `X` 的数值；未读任何响应/存活数值**。读到的只有：h5ad obs/var 元数据、census CSV、DepMap `sample_info.csv` 列连接、PRISM treatment-info/cell-line-info **元数据列**（药名/剂量/DepMap ID；logfold-change 响应文件未打开）、CADENCE 论文 HTML。

## 1. 实际执行

### 1.1 环境

- 解释器：`D:\anaconda\envs\maestro\python.exe`（anndata 0.12.19 / h5py 3.16.0 / pandas）。
- 输入 h5ad：`data/external/mixseq_scperturb/mcfarland_2020.h5ad`，1,459,410,830 B，SHA256 `94a7240047b9ce6822dc2aa1e7a66c1fd8b00be842e5a95fc72cbeb6f2834d2c`（脚本内计算）。
- 旧 census：`research/eight_directions_20261026/evidence_audit/mixseq_design_census.csv`，54,253 B，SHA256 `0ef7b1c7a907c0fdc456b3f0910363de874eb3131265d1d82b1ea5165256d625`，1,952 行，`cells` 合计 182,875 = h5ad `n_obs`。
- 旧轮基准：`research/2026-10-27-cross-domain-directions/mixseq_metadata_check.json`（285 键、per-drug 98/24/24/24/115、115 细胞系）与本轮 h5ad 复算逐项一致。

### 1.2 命令

```text
D:\anaconda\envs\maestro\python.exe research\2026-10-27-innovation-scouting\dynamic_route\a3_inspect.py
```

脚本行为：`anndata.read_h5ad(..., backed="r")`；只读 `obs` 列、`var` 列名、`X` 的 shape/encoding；统计列存在性、空值计数、设计列取值计数、实体键计数、QC 标志计数、身份连接；对 hashed 臂按 `hash_assignment` 的纯标签正则分类（不读表达）。输出 `a3_meta.json`。
另：`tmp/cadence_2605.23470v1.html`（arXiv 2605.23470v1 HTML，519,952 B）转 text 得到 `tmp/cadence_2605.23470v1.txt`（88,732 B），用于 CADENCE 条件逐字核对；**这是本轮唯一联网抓取（<20 MB）**，未下载数据集/模型。

### 1.3 验证（本轮实际跑过的检查）

```text
VERIFY common_keys 285 == prior 285                      True
VERIFY per_drug counts == prior                          True
VERIFY common_cell_lines 115 == prior 115                 True
VERIFY census common keys == 285                         True
VERIFY census cells sum == h5ad n_obs (182875)            True
VERIFY hashed clean+combo+unresolved == 20028             True
VERIFY no functional endpoint columns in obs/var          True (none found)
json.load(a3_meta.json)                                   OK
```

**没有**运行任何表达/响应统计；以上只是元数据计数与一致性断言。

## 2. 关键结果（详见 `qualification.md`）

1. **285 键复核通过**：h5ad 与旧 census 完全一致；`(perturbation, cell_line)` × 精确 `time∈{6,24}` = 285；BRD3379 98 / Bortezomib 24 / Idasanutlin 24 / Trametinib 24 / control 115；115 细胞系；两源共同键集合逐元素相同。
2. **每键细胞数**：6h min/median/max = 4/108/398；24h = 7/104/378；QC-normal ≥10 cells 的键 282/285（≥20 为 279，≥30 为 264）。**可支撑 pseudobulk 开发，但需设最小细胞门槛**。
3. **剂量/channel/批次**：每药仅单剂量（BRD3379 0.0、Bortezomib 2.5、Idasanutlin 2.5、Trametinib 0.1、control 0.0 µM；6h/24h 同键剂量集合无冲突）；**6h 的 channel 全缺失**，24h 仅部分有（common keys：222/285 两侧缺失，63/285 仅 24h 有）→ **时间与 channel/plate 混淆不能排除**；**无 batch/plate/run/donor 列**。
4. **新发现（相比旧轮 285 报告）**：`time="3, 6, 12, 24, 48"` 的 20,028 个 Trametinib 细胞，其 `hash_assignment` 可恢复 per-cell 处理/时间：**17,553 single-tag**（Tram 3/6/12/24/48h + DMSO 3/6/12/24/48h + Untreated_48hr），2,339 combo、136 unresolved；**24 个细胞系在全部 5 个时间点对 Tram 与 DMSO 均有细胞**（=focal24），中位 55 细胞/条件（normal-QC 中位 42）。**需清洗**：`perturbation` 字段把 DMSO 也写成 Trametinib、`dose_value` 全部写 0.1、`hash_tag` 与 `hash_assignment` 2,475 细胞不一致、无 run/batch 记录。
5. **24h-only 9 个药物臂**（AZD5591/Afatinib/Dabrafenib/Everolimus/Gemcitabine/JQ1/Navitoclax/Prexasertib/Taselisib；94–98 系/臂）：单快照，只能做静态层外部验证，不能做 6 vs 24 动态比较。
6. **功能结局**：h5ad 内 **无** viability/apoptosis/GR/IC50 列（obs/var 列名检索 0；obsm/layers/uns 空）。本地 PRISM 元数据有 Bortezomib/Trametinib/Idasanutlin（一级 2.5 µM 单剂；二级 16 剂量点），**无 BRD3379**；PRISM 细胞系覆盖 207/209（focal24 全在），但 PRISM 是不同 assay/时间/剂量，**不能当 6/24h 时间匹配功能终点**。
7. **前轮派生缓存** `data/external/kinetic_horizon_20261010/`：22 个文件（20 个 npz + 2 个 RESULTS.json；mixseq A/C/D control/treated、mixseq_state、prism_* 匹配缓存）**仅列目录**；未审计、未读值、不能当认证终点（另：本轮为判断"是否为响应缓存"，仅观察了 npz 的 keys/shapes/dtypes，未读取数组值）。
8. **CADENCE 条件**（`cadence_evidence.md`）：无结构时不可识别（Prop.1）；需要 DFA/COA/MRA + PR/FOA；**FOA 要求入组时间跨区间、在塌缩到单点时失败**；作者自述最根本漏洞是 COA 未观测混杂。本资产：2 个精确时间点（或单药 5 个固定点）、无个体链接、无批次记录 → **不能声称恢复真实路径**；流匹配仅作估计器。

## 3. 判定

- 资格：**`design_data_partial`**（部分可支撑）。
- 可支撑：群体层面 6h/24h 两快照开发、单药 Trametinib 5 时间点群体时间过程开发、24h-only 静态外部层、DepMap 身份连接。
- 不可支撑：**决策层**（无独立功能结局；批次/剂量未认证；时间与 channel 混淆）；**轨迹/路径**（无链接、无丰富入组时间）；**剂量/序贯/洗脱**（无数据）。
- 设计草案：`protocol_draft.md`（决策类型、动态量→决策→可证伪对比表、CADENCE 可识别性、L1 开发设计、L2 决策设计、功率/MDE 预注册要点、失败类别/停止条件、所需数据规格）。

## 4. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `dynamic_route/a3_inspect.py` | 29,844 | `09e334417fecd389842000ffd6a48a0b105de441680ec9e4789d469854c7faa0` |
| `dynamic_route/a3_meta.json` | 52,766 | `fcf56d459b3e78433b7efdb49ee29e0f9a65107b41b435e87664c4354c254000` |
| `dynamic_route/qualification.md` | 20,666 | `13272b01000102b1c3cd8612cdee8eb6f9eca50b2b3d862c1d3c7c364d0c65d5` |
| `dynamic_route/protocol_draft.md` | 21,521 | `9d7ae195224259a93defb57a7358752dbc7018b0562fb6dcdc2fb7cf09d4eedc` |
| `dynamic_route/cadence_evidence.md` | 6,388 | `0b6bdcc3cddadba68b4b2e51f2782fe046562c39c3d3f759739fc1128e169fd6` |
| `tmp/cadence_2605.23470v1.html` | 519,952 | `8b7b07163c4588dfe7fe1b9e941b8133146501fa42b851917fcbd7ae63366a3c` |
| `tmp/cadence_2605.23470v1.txt` | 88,732 | `fe5a576294422c85e91b6275ba565445d04fe78c6bb269a6bced906e0a5db87e` |

（`record.md`、`usage.json` 不自我哈希；`a3_meta.json` 的 hash 以本轮生成为准。）

## 5. 未执行 / 限制

- 未读表达矩阵 → 不能给出任何时间预测/可靠性/MDE 的实测值；`protocol_draft.md` 的 MDE 只是**预注册算法**，不是本资产的结果。
- 未重建 hash demultiplexing；hashed 臂的 per-cell 时间/处理是**原处理结果的再解释**（2,475 细胞字段不一致；combo/unresolved 排除）。
- 未认证独立培养/批次/剂量；6h 与 24h 的 channel 可用性不同 → 时间效应与 plate/channel 混杂未排除。
- PRISM 仅做元数据存在性检查；未读响应矩阵；PRISM 与 Mix-seq assay/时间/剂量不匹配。
- 未做文献综述（本任务是资格+设计）；CADENCE 引用为用户报告 P 级阅读 + 本轮 HTML 复核；target-identifiability SSRN（report.md:157）仅登记为近期先例压力（A 级，403 未读）。
- 未改 `PROTOCOL_A0`/`INDEX`/`SYNTHESIS`/其它研究目录/git；未晋升代码。

## 6. 下一执行者从哪里开始

1. 先读 `qualification.md` §6 判定表与 `protocol_draft.md` §5.5 失败类别。
2. **目前不要启动 L2/决策层**：先补 `protocol_draft.md` §6 的功能终点（同细胞×同药×同剂量×6/24/48h 的 viability/apoptosis + 时间匹配 vehicle + ≥2 独立培养）与批次/剂量元数据。
3. 若只做开发：按 `protocol_draft.md` §4 冻结 V1/V2 端点、留出切分与比较器，先算可靠性上限，再决定是否值得跑时间预测；**不得**把开发层的表达预测升级为"动态世界模型"或"药物决策"。
4. 若 Lead 决定不补数据：按 `qualification.md` §7 把动态路线登记为"决策层不可检验"，**不换名重启**，把资源优先给 R197 的 A0/B 主线。
