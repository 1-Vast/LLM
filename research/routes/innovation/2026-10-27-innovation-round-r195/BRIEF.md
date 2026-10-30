# R195 BRIEF（2026-10-27，Lead 起草；下一轮执行）

## 0. 入口状态

- R192：DrugComb 外部复现 `not_replicated`（功效未校准，未解冻；C167）。
- R193-A1：Q 跨 screen 可复验性 `inconclusive`——有效样本量被 **96 个共享细胞**限制（n_eff≈189；MDE80_obs=0.2042 > δ_min_obs=0.0893；C171），不是阴性。
- R194-A2：Q 条件级结构"可估但份额可忽略"——**σ²_cond=1.43%**（p=0.001、条件级可靠性 0.868/435 cp 平均），**condition×cell 交互 48.5%**、**barcode 噪声 46.1%**、cell-pair 3.94%（C172）。
- 分支（R194/BRIEF 冻结）：present 但可忽略 → 反馈/迁移/Agent 不以条件级共享规律为前提；**下一轮只做"更大独立资源 + 更好噪声标定"的条件级跨 screen 资格审计**；B/C/acquisition 不启动。

## 1. R195 唯一任务：条件级跨 screen 资源资格审计（A3）

**问题**：是否存在一个**独立于 Jaaks 资源**、具有**≥2 个独立测量组（不同 screen/study/lab，不是同日 barcode 分半）**、**≥200 个共享细胞系**、且**同一细胞上可匹配同一/等价条件（药对+剂量设计+端点）**的资源，使"条件级 Q 跨 screen 复验"可被检验？

- 这是**资源资格审计**：不读响应值做效应统计、不估 Q、不训练模型；只做结构/身份/单位/匹配可行性 + 存在性检查。
- 若不存在合格资源 → 记录 **`condition_level_cross_screen_untestable`** 边界：分析 A 收口（条件级共享规律 1.43%、跨 screen 复验不可及），并给出所需资源规格（下一资源资格门槛）；这是有效负结果。
- 若存在 → 输出候选资源与所需 A4 预注册要点（匹配定义、独立组、噪声标定、MDE 先验），下一轮再冻结效果协议。

## 2. 候选资源（本地优先；允许下载但先列预算）

按顺序核查（metadata-only；先查本机，再决定是否下载）：
1. **DrugComb v1.5 full summary**（Zenodo 15235991，1.42 GB；本机只有 60×1MB 字节分块样本）：`study_name` 37 个 study、2,320 细胞、8,396 药、synergy_bliss 等。核查：同一 `cell_line_name` 与同一药对（或等价条件）是否跨 **≥2 个 study** 出现；跨 study 匹配的 (cell, condition) 数量；各 study 的细胞覆盖；若可行则给出 download 预算（≤1.5 GB，SHA 回执）。
2. **DrugComb v1.4**（本地全量）：同一 cell×pair 有多 block（1.23 blocks/unit、最多 10）；按 block_id 窗口/study 代理分组（不是独立 screen）——报告其作为"重复测量组"的可用性与局限。
3. **本机其它成对资源**：`data/external/gdsc2_fitted`、`prism_19q4`（primary/secondary 是否均为组合端点）、`beataml2_20261017`、`batchie_zenodo_13871987`（round/duplicate 组）、`nci_almanac_2017`、`data/raw/oneil2026_qualification`。逐个核查：是否存在 ≥2 独立测量组、≥200 共享细胞、组合端点、剂量/条件元数据。
4. **外部候选（仅在小体量或已有回执时）**：不主动大下载；先报告缺口与所需规格。

## 3. 冻结门槛（A3）

- G1 独立测量组：≥2，且不是同日/同板 barcode 分半（需 study/screen/lab/日期等可辨认分组；若只能同日分半 → 不合格）。
- G2 共享实体：≥200 个共享细胞系（严格名归一 + 碰撞报告；禁止同义词推断）。
- G3 条件匹配：同一 cell 上同一（或可证明等价）条件（药对+剂量设计+端点）在 ≥2 组均被测；匹配四元组/条件数量 ≥ 预注册门槛（建议 ≥10,000 配对单元；A4 MDE 反推后可辩护修订，先写死）。
- G4 噪声标定：≥5% 观测有组内重复（barcode/技术重复/同 study 重复），可估测量噪声；否则记录"噪声标定不足"。
- G5 端点：组合协同类端点存在（Bliss/ZIP/ΔEMAX 等），非饱和/QC 元数据可查；不读数值，只查列存在与语义/论文定义。
- G6 外部性/泄漏：与 Jaaks 资源实体/条件重叠需报告（本分析不训练模型，但"独立资源"表述需限定）。
- 判定：`resource_qualified` / `not_qualified`（逐条失败原因 + 解冻条件/所需规格）。任何一条不过 → not_qualified（可以 qualified_with_conditions 只用于"数据可得但需下载/清洗"的情形，条件必须列清）。

## 4. 代理、预算与纪律

- 1 名独立资源审计员（metadata-only）；1 名独立挑战者审 A3 协议/结论（必做）。
- 下载上限 1.5 GB，单文件先记录 URL/大小/SHA；单命令 ≤15 min；不读响应数值（只做列存在性/缺失空串检查）。
- 交付：`research/2026-10-27-conditional-shift/` 下新增 `PROTOCOL_A3.md`、`a3.py`、`a3.json`、`a3_overlap/`（如需）、`report_a3.md`、`record_a3.md`、`usage_a3.json`；轮次记录与登记。
- 纪律：资格审计≠Q 复验；不换聚合/不把同一 96 细胞当更大资源；阴性同样记录；不晋升代码。

## 5. 明确不做

不把 A3 通过写成条件级结构存在/可迁移；不启动 B/C/acquisition/RSI；不做机制/临床主张；不下载数据集做效应建模（只做资格）。
