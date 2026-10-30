# 开放元数据配对资格审计

2026-10-28；使用 `D:\anaconda\envs\maestro\python.exe` 实际运行 `audit_metadata.py`。只读开放元数据、pilot manifest/schema和旧报告；未读取 gctx、h5ad矩阵、PRISM效应矩阵、response_arrays、sealed或confirmation；无网络、无训练。当前模型/effort未知。

结论：本地可重建 **LINCS RNA—PRISM名义药物/细胞/剂量候选交集**，尤其 secondary；尚不能据此检验“相同实测近端作用下，程序跨化学实现充分”。缺失的是实测作用锚、暴露/时程可比性和独立培养配对。元数据交集不代表对应效果值存在或通过QC，不能视为已完成生物实验或效果独立确认。

## 1. 本次重算结果

连接规则：LINCS `pert_type=trt_cp`；`pert_id`与PRISM `broad_id`截取 `BRD-[AK]八位数字` core；LINCS `cell_id`与CCLE名称下划线前缀去非字母数字并大写；PRISM细胞要求 `passed_str_profiling=true`。剂量由LINCS `pert_idose`解析，µM/μM/um统一为uM，nM除1000；PRISM README明确dose为uM。剂量按数值严格相等，不设容差。secondary还按 `pooling-info` 的 `screen_id × cell`约束。

BRD core忽略制剂/批次；细胞名连接不等于同一培养、同一传代或同一实验批。输入所有实际读取文件的字节数、SHA256、表行数与列名均保存在 `metadata_counts.json.inputs`。

| RNA来源 → PRISM | core药物交集 | 名义同药/同细胞/RNA时间/剂量键（尚未要求PRISM剂量相同） | 再要求相同uM与screen后键数 | 匹配药物/细胞数 |
|---|---:|---:|---:|---:|
| GSE92742 → primary | 1,845 | 24,068 | 0 | 0 / 0 |
| GSE70138 → primary | 1,537 | 48,557 | 1 | 1 / 1 |
| GSE92742 → secondary | 633 | 11,038 | 6,303 | 566 / 30 |
| GSE70138 → secondary | 602 | 20,335 | 3,790 | 575 / 7 |

最后列的键是 `core × normalized_cell × dose_um × RNA_time × PRISMscreen`，不是独立样本数；多个screen及RNA时间可能重复同药物/细胞。两期数字不相加作为独立观察数。primary唯一严格剂量候选是 GSE70138 `BRD-K25412176 × A375 × 2.5 uM × RNA 6 h × HTS`。零交集限于上述明确的严格连接规则，不能宣称所有可比剂量数据不存在。

GSE92742共473,647条signature，其中compound 205,034条、20,413个pert_id；RNA时间为24 h 109,721、6 h 95,254、48 h 58、144 h 1。GSE70138共118,050条signature，其中compound 107,404条、1,796个pert_id；RNA时间为24 h 101,360、3 h 4,950、6 h 1,094。

PRISM primary有4,686条collapsed treatment、4,508个core药物，588行细胞元数据、578行STR通过；secondary有13,008条collapsed treatment、1,442个core药物，588行细胞元数据、568行STR通过。

## 2. 字段能回答什么

| 维度 | 实际字段与限制 |
|---|---|
| LINCS RNA | GSE92742有`pert_dose/pert_dose_unit/pert_time/pert_time_unit/pert_idose/pert_itime/distil_id`；Phase2有`pert_idose/pert_itime/distil_id`，没有独立的数值剂量/时间列。本次统一从文本字段解析。|
| PRISM功能 | collapsed treatment有`broad_id/dose/screen_id/moa/target`；secondary另有`compound_plate`。这些表不含功能数值；未读取功能矩阵。|
| 功能端点时间 | secondary replicate treatment的`detection_plate`中4,663行显式含`120H`，44,304行不能从该字段恢复时间；不得把120 h推广为所有screen。primary当前表无显式端点时间。本次未恢复额外方法来源。|
| 作用测量 | `moa/target`是注释；现读表无target occupancy、活细胞engagement、磷酸化等实测近端作用列。RNA是扰动后状态，不能自动升级为已测target engagement。|
| 时间配对 | 6/24 h RNA与检测板120H功能端点属于不同读出时间，不能以相同药物/剂量称“相同时程”。尚缺给药、洗脱、持续暴露、重复给药及实际浓度轨迹。|
| 重复单位 | LINCS `distil_id`列出原profile；PRISM `detection_plate/well/screen/pool`表明技术结构。当前字段不能核定独立culture。README说collapsed结果合并screen内重复，不得把其行数、多个screen或hash/well当独立生物重复。|

GSE92742→secondary严格候选的RNA时间：6 h 4,188键、24 h 2,115键；GSE70138→secondary：24 h 3,589键、3 h 173键、6 h 28键。这些都是RNA时间，不是功能端点时间。

## 3. sci-Plex当前可用性

v1/v2 manifest引用 `data/external/sciplex_family/SrivatsanTrapnell2020_sciplex2.h5ad`（历史145,178,504 bytes）与 `...sciplex4.h5ad`（历史253,335,945 bytes）。本轮对这两个实际路径 `is_file()` 均为false；当前family目录文件列表也为空。manifest的历史hash/计数不能证明原h5ad仍在本地。本轮未读任何h5ad矩阵。

v2 provenance实际238行：sciPlex2 32、sciPlex4 206；A549 135、MCF7 103；classification为combination 96、agent1_only 80、agent2_only 28、single_agent 28、vehicle 4、vehicle_vehicle 2。全部238行`dose_unit`均为unverified_token，`biological_replicate_id`均为unavailable；无RNA time字段。well_summaries是816行技术well摘要，不是独立培养证据。

干预token包含BMS、Dex、Nutlin、SAHA、Pracinostat、Abexinostat及ACLY/ACSS2/PDH inhibitor等。按大小写折叠后的**确切名称**与本次LINCS/PRISM名称均无交集；这不代表化合物不重叠，因为别名尚未通过化学标识核定。不得猜测BMS/Nutlin等具体实现或用SAHA药名别称自动接成合格三方配对。当前pilot不含可直接连接的BRD/InChI字段，剂量单位与RNA时间也未确认。

## 4. 旧research是否已有跨药充分性实证

本轮有界检索了旧research的同靶点/跨化学关键词，并实读以下最相关报告；没有读取旧效应矩阵。

- `research/eight_directions_20261026/report.md`第11–17行及第23–39行：真实primary、2.5 uM、16个名义单靶点家族、96药、485个STR通过背景；每家族留出1药，统计家族内功能分歧并比较refit/交互模型。它是同靶点注释下的功能异质性及有限预测比较；报告明确不同SMILES不等于不同骨架、名义靶点不等于参与，且缺正交因果参照。不是在相同实测作用/暴露下的跨化学充分性实证。
- `research/2026-10-27-agent-cell-identifiability-r106/report.md`：通路/靶点注释加入身份预测器后的top-k差异；靶点字符串还混合基因与复合物。不是作用变量充分性检验。
- `research/2026-10-27-agent-cell-identifiability-r107/report.md`：5个随机流中的注释增量稳健性；随机流不等于独立培养或独立screen，不建立机制/跨药作用充分性。
- `research/2026-10-27-innovation-scouting/logic_constraints/spec_v3.md`：C1′仅QA，即使正显著也禁止解释为同靶点等功能；属于协议限制，不是已经完成的充分性实验。

结论严格限定为：**在本次检索与实读的相关旧资料中，未找到满足“同背景、可比暴露、实测近端作用、跨化学实现、独立功能单位”的已完成充分性实证。** 不能把注释top-k提升、家族内分歧或缺少原h5ad写成对机制的独立证伪。

## 5. 可检验范围与停止点

当前字段可支持确定药物/背景/名义剂量交集、计划早期RNA与后期药敏的跨数据预测可行性；实际执行前仍须单独核定效果缺失、完整化学身份、时程与培养来源。它不能在本轮支撑CL1实测作用中介的跨药充分性主张，故本审计不生成效果实验、不补造近端标签、不报告科学效果独立确认。

重放命令：`D:\anaconda\envs\maestro\python.exe D:\MAESTRO\research\2026-10-28-agent-a-program-evidence\audit_metadata.py`。结果JSON内保存输入hash、字段schema、计数、连接示例和明确假设。
