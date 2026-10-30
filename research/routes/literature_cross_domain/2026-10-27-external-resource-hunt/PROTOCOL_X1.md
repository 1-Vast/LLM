# R202-Q1 协议：外部独立组合/功能资源定向征询与资格（metadata-only）

**版本 v1，FROZEN（在任何外部资格判定前冻结）** ｜ 2026-10-28 ｜ 执行：drugcomb-auditor（task-126）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-27-external-resource-hunt/`（`PROTOCOL_X1.md`、`hunt_x1.py`、`hunt_x1.json`、`report_x1.md`、`record_x1.md`、`usage_x1.json`、`receipts/`）与 `tmp/`；不改其它目录/INDEX/git。
**纪律**：metadata-only；先资格后设计；**不运行效果/不拟合预测/不读响应做效应**；不称新颖性/迁移/决策收益/机制；阴性写"未发现/不可得"不写"不存在"；不得把同一 96 细胞换聚合当新数据；不得把已聚合挑战分数当原始重复。

## 0. 背景与目标

R201 收束后瓶颈=**缺少独立测量/独立培养/重复结构/功能端点的组合资源**（A 线零模型/σ 无法从 O'Neil 4×4 技术重复独立校准；B 线 T3 需真实报价/湿预算；方向 3/4/5 需真实顺序程序与功能数据）。本轮只做**外部资源定向征询 + 资格**：是否存在本地未收录的公开资源，能提供独立测量/独立培养/重复/功能端点/合法暴露，从而重开 A/B/D3/4/5 的最小实验。

## 1. 候选（逐一核，不预设结论）

1. **AstraZeneca-Sanger DREAM 2015**（组合预测挑战；synergy/viability、多细胞系；核重复/独立培养/剂量/端点/与 Jaaks 实体重叠/是否已聚合）。已知可能与 DrugComb `ASTRAZENECA` study 同源，须核 lineage。
2. **NCI-ALMANAC**（NCI-60 组合；核重复/独立培养、端点、剂量、与 Jaaks 重叠；本地旧空目录 `data/external/nci_almanac_2017` 需说明）。
3. **Novartis 公开组合 / 其他 2024–2026 公开组合资源**（GDSC2 扩展、Community、PharmacoDB 汇总、DepMap 组合子集等；核原始性）。
4. **功能独立性资源**：同一细胞/干预的独立功能读数（apoptosis/caspase/靶点参与/再生长）公开集；无则明确记录。
5. **其他 2024–2026 组合/顺序程序时间序列公开数据**（Mix-seq 之外；核顺序/功能/重复/暴露）。

**已审/不重复**（BRIEF）：DrugComb v1.4/v1.5、PRISM/BeatAML/Mix-seq、O'Neil、Jaaks O/V、GCP2020、ALMANAC 空目录（本次重新核）、VIS2024/Nyman2020/Hill2017/JUMP-CP/BATCHIE/GDSC2 等。

## 2. 定义（冻结）

- 一次测量 `y(c,a,b)`：细胞 c 中药物 a、b 在合法暴露 E=(数字剂量设计 D、暴露时间 T、端点 M) 下的功能响应。
- 合法暴露：同细胞/同伙伴身份、伙伴浓度档匹配、每成员完整剂量曲线（或预注册可比较方案）、暴露时间/端点/批次可核对；不得事后挑剂量档。
- **独立测量/独立培养**：不同日/不同 plate/不同 passage/不同培养瓶；**技术重复（同板同孔批的 replica）不算**。
- **正交功能读数**：与 viability/synergy 不同的功能测量（apoptosis/caspase、靶点参与/占位、再生长/恢复、live imaging 等）；仅有 viability 派生协同分数 = 非正交，只能 conditional。
- **已聚合挑战分数**：比赛提交/评分表、预聚合 synergy/viability 汇总不能当原始重复；必须有其底层 wells/keys 或明确单次测量的原始表。
- **非重聚合 lineage**：候选不得由 Jaaks/DrugComb/PRISM/BATCHIE/O'Neil 等已审资源的同一批原始 wells 重排/重聚合而来；须有独立 study/screen/lineage（报告来源链）。

## 3. 资格门槛（冻结）

| 门 | 门槛 | 判定 |
|---|---|---|
| **G1 实体/匹配规模** | 与 Jaaks：共享 **≥10 细胞**、**≥10 有向药对**、**≥500 匹配键**（A0 匹配口径：细胞×有向对×剂量设计可匹配；无法匹配时报告上界并判未认证） | 全满足 pass；部分满足 conditional；否则 fail |
| **G2 板孔不相交** | 原始板/well 标识与 Jaaks Original/Validation **不相交**；或提供可验证的独立 screen/plate 来源链 | pass / conditional（无板 ID 但有来源链）/ fail（同源/无法核） |
| **G3 合法暴露** | 数字剂量列存在且可解析、伙伴浓度档匹配、暴露时间/检测方法记录 | pass / conditional（缺暴露时间或成员剂量曲线仅部分）/ fail |
| **G4 独立测量/培养** | 每键 ≥2 次**独立**测量（不同日/plate/passage/flask）或独立培养；报告重复类型 | pass / conditional（只有技术重复但明确）/ fail |
| **G5 正交功能读数** | ≥1 个与 viability 不同的功能读数（若主张功能） | pass / conditional（只有 viability/协同，限定任务）/ fail |
| **G6 冻结聚合/Δ** | 预注册剂量平均/聚合规则与 Δ 定义；不得用挑战已聚合分数当原始重复；端点为功能 viability 或可换算的 Δ | pass / conditional / fail |
| **G7 非重聚合 lineage** | 独立 study/screen；不与已审资源共享原始 wells/keys；报告实体重叠 | pass / conditional / fail |

**判定规则（冻结）**
- `qualified`：G1–G7 全 pass。
- `qualified_with_conditions`：G1 pass、G2–G7 均 ∈ {pass, conditional} 且至少一项 conditional，无 fail；列出全部条件与可执行范围（如"仅 viability 排序"、"仅开发性"）。
- `not_qualified`：任一 gate fail；写原因码 + 所需测量规格；**不达标不得进入效果**。
- **原因码**：`access_restricted`（登录/许可/地区）、`data_unavailable`（链接失效/文件不可得）、`no_combination_data`、`no_numeric_dose_or_exposure`、`no_independent_replicate_or_culture`、`wells_not_disjoint_or_unknown`、`jaaks_overlap_insufficient`、`reaggregated_lineage`、`no_orthogonal_functional_readout`、`aggregation_not_frozen`、`no_sequential_data`、`endpoint_not_viability_or_functional`、`license_unclear`。
- **总体**：若存在任一 `qualified` → 建议独立挑战该资源资格；若只有 `qualified_with_conditions` → 建议独立挑战"条件下可执行范围"；若全部 `not_qualified` → **建议停止外部征询**（不再逐库追索），记录缺口与所需新测量；不把"未发现/不可得"写成"不存在"。

## 4. 下载/API/记录规则（冻结）

- 单文件 ≤ **500 MB**；超限不下载，只记录 HEAD/Content-Length/许可/部分范围（Range ≤1 MB）与原因。
- 每个实际下载/抓取：记录 **URL、HTTP 状态、Content-Length/bytes、SHA256、日期、许可/登录要求**；回执写 `receipts/*.json`。
- 可下载格式优先：README/metadata/数据字典/小表；大矩阵只取表头/空值计数；**不读响应值做效应**（响应列仅存在性/空值计数）。
- 登录/许可限制：记录 `access_restricted` + 原因 + 可公开访问的替代元数据；**不绕过**登录/付费/许可。
- 网络失败/超时：如实记 `data_unavailable`（含错误文本），不重试到无限；不伪造下载。

## 5. 检索与边界

- 检索日期 2026-10-28；限定 2024–2026（新资源）+ 上述经典资源官方页；查询记录写 `receipts/search_log.json`（query/URL/status）。
- 本审计不做系统综述；**"未发现/不可得"只作本次有界检索结果**，不是"不存在"。
- 不重开已审资源；不把 DrugComb/A3 的 41/4,179 当 Q1 证据；不把同一 96 细胞换聚合；不称新颖性/迁移/决策收益/机制。

## 6. 输出与确定性

- `hunt_x1.json`：每候选的 gate 状态、关键数字（实体重叠/重复/剂量/端点/独立性）、下载/许可记录、判定+原因码、总体建议；JSON 键排序、无时间戳、输入/脚本/协议 SHA。
- 报告 `report_x1.md`、记录 `record_x1.md`、运行账 `usage_x1.json`。
- `hunt_x1.py` 只做结构/元数据/空值统计与实体归一/重叠计数；**不读响应做效应、不训练/不拟合**；单命令 ≤15 min。
