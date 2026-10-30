# PROTOCOL_ON1 —— O'Neil 开发性内部细胞留出协议草案（v1 **FROZEN**，2026-10-27，任何 ON1 资格计数之前）

> 依据：`research/2026-10-27-core-module-design/qualification/{PROTOCOL_Q0.md, q0.json, report_q0.md}`（R199-Q0：总体 `not_qualified`，**O'Neil = 唯一 `qualified_with_conditions`，仅开发性内部细胞留出**）、`research/2026-10-27-innovation-round-r199/BRIEF.md`、`research/2026-10-27-core-module-design/report.md`、`SYNTHESIS.md` C178–C181（含 C181：A1 Stage-0 `data_unavailable`，批准窗口用尽，唯一窄口径=ONeil 开发性）。
>
> **本文件在任何 ON1 资格计数/门控判定之前冻结；冻结后不改。** 本任务**只做设计 + 资格复核，不运行效果、不训练、不比较更新器**；不写机制/迁移/决策收益/新颖性；不声称独立确认。
>
> 角色：独立设计/资格复核 runner（非提案者；不参与效果设计）。

## 0. 范围（写死）

- **唯一对象**：R199-Q0 允许的窄口径——**O'Neil 资源内部的开发性细胞留出协议**。只用 O'Neil 内部细胞切分，**不是**跨资源/跨 screen 确认，**不是** BRIEF 要求的公平 source→target 更新器比较；不得称独立确认/迁移/决策收益/机制。
- **端点**：仅 **viability（组合响应原始 viability1–4 的均值）**；`mu/muMax`、`X/X0` 是 viability 派生，**不得**当独立功能读数；**不得**与 Jaaks `SYNERGY_DELTA_EMAX` 拼成同一端点/换算；不跨端点、不插值、不外推剂量。
- **细胞**：O'Neil 39 细胞中 **9 个与 Jaaks 重叠**（C178 后复核）必须从目标集**排除**（单列审计报告），开发目标细胞 = **30**；source/target 细胞不相交（此处 source=Jaaks 仅作 lineage 重叠审计，不参与本开发任务）。
- **重复**：O'Neil 每行 4 个 viability 技术重复（viability1–4）；3 个 BatchID 同 lab，**技术重复 ≠ 独立培养**，如实披露；无暴露时间/assay 方法列。
- **不做**：不比较更新器（那是下一阶段，须另立协议+独立挑战）、不训练/不拟合/不估效果、不读 viability 数值做效应统计、不重开 R196/R197 旧判定、不写机制/迁移/决策收益/新颖性、不换端点/切分凑资格。

## 1. 输入与元数据边界

- 主输入：`data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`（OOXML despite .xls；sheet `combination response`；368,832 行；列：BatchID, cell_line, drugA_name, drugA Conc (µM), drugB_name, drugB Conc (µM), combination_name, viability1–4, mu/muMax, X/X0；SHA256 `A0E2E002…C14818`）。
- 元数据只读列：`BatchID, cell_line, drugA_name, drugA Conc (µM), drugB_name, drugB Conc (µM)`；viability 列只做**存在性/非空计数**（不读数值做任何统计/效应）。
- 单药工作簿（只登记元数据，不读数值、本任务不用）：`…_supp_0_w2lh45.xlsx`（sheet 单药；16,752 行；39 细胞；38 药；`Drug_concentration (µM)`；viability1–6）。若未来协议要用单药参照作对照，必须另立预注册 + 该表的独立资格（同 lab/技术重复 ≠ 独立培养）。
- Jaaks Original fitted（`1188968C…`）只用于细胞名重叠审计（读 `CELL_LINE_NAME` 列）。
- 输入 SHA256、脚本 SHA256 写入 `on1.json`；JSON 键排序、无时间戳；确定性（同代码两跑 `on1.json` 逐字节相同）。

## 2. 冻结定义

- **行** `r=(BatchID, cell c, drugA a, doseA, drugB b, doseB)` + 4 个技术重复。
- **角色**：每行的 `drugA` 为 A-角色、`drugB` 为 B-角色；每个无序药对在数据中只有一种 A/B 角色定向（本审计复核）。
- **伙伴上下文** `ctx=(batch, c, partner p, partner_role ρ∈{A,B})`：满足在该 batch/cell 下 p 以角色 ρ 出现。**成员** = 与 p 共测的、在 p 的另一角色上的药。
- **合法暴露（本资源内）**：同一 `ctx` 内，伙伴的剂量集合一致、成员完整 4 剂量曲线（4×4 数字剂量网格；本审计复核完整率）、无暴露时间/assay 列（作为**已知条件**记录，不判 fail；限制写死）。
- **成员曲线均值** `m(c,a,p;ρ) = mean over 4 partner doses of [mean over 4 member doses of y(c,a,p)]`（= 完整 4×4 网格均值；**完整曲线平均规则**，不得看结果挑剂量档）。
- **替换关系单元 Δ**：固定 `(batch=1, c, p, ρ, {a,a'})`，`Δ = m(c,a,p;ρ) − m(c,a',p;ρ)`（符号按归一名升序：`a`=排序前者）。等价地：逐 partner-dose 行计算 `Δ_row = mean_a − mean_a'` 后对 4 行取均值（完整网格下两式相同）。
- **行级 Δ**：`(batch, c, p, ρ, partner_dose d, {a,a'})` 的同一行内 Δ（比单元 Δ 更细，只作严格性报告）。
- **三向交叉单元** = 可计算的单元 Δ 数（每单元要求两个成员各自完整 4×4 网格）。
- **可替换成员对/上下文**：`(c,p,ρ)` 下成员数 ≥2 的无序成员对数。
- **跨细胞覆盖**：固定 `(p, ρ, {a,a'})`，在多少个不同细胞 `c` 上可算单元 Δ（batch=1）。
- **开发目标细胞**：39 − 与 Jaaks 重叠的 9 = **30**（归一名精确匹配；逐一列出）。
- **批次处理（冻结）**：**主分析只用 BatchID=1**（358,560 行；39 细胞；22,410 pair-cells；其余 batch2=5,232 行/9 细胞、batch3=5,040 行/15 细胞；pair-cell 的跨 batch 集合 {(1,):22,101, (2,):321, (1,3):309, (2,3):6}）。Batch 2/3 **不进入主设计**；batch1∩batch3 的 309 个 pair-cell 只是同 lab 技术/批次重复，可作**技术一致性敏感性**（未来），**不是独立培养**。

## 3. 资格门（冻结；先于任何设计判定）

### 3.1 数据门（任一 FAIL → `data_unavailable`，停）

- **DG1 交叉规模**（batch=1、目标 30 细胞、单元 Δ）：可计算单元 Δ **≥ 5,000**；贡献 ≥1 单元的**目标细胞 ≥ 30**（30/30）；`(cell,p,ρ)` 成员上下文（成员≥2）**≥ 200**；跨细胞覆盖 ≥3 个目标细胞的 `(p,ρ,{a,a'})` 上下文 **≥ 10**。
- **DG2 合法暴露**：数值剂量列存在且可解析；每个成员上下文完整 4×4 网格比例 **≥ 95%**；同一 `(batch,cell,partner)` 的伙伴剂量集在角色内 **100% 唯一匹配**；暴露时间/assay 方法列存在性如实记录（缺失=已知条件，不单独 fail，但不得写"暴露已验证"）。
- **DG3 重复存在性**：viability1–4 四列存在且非空计数=行数（仅存在性/空值检查）；`mu/muMax`、`X/X0` 存在性记录（派生端点，不作独立功能读数）。
- **DG4 目标细胞**：非重叠目标细胞 = 30；30/30 在 batch1 有 ≥1 个合法单元；重叠 9 细胞单列报告、**不进入**训练/测试/任何结论。
- **DG5 lineage/端点边界**：目标 30 细胞与 Jaaks 125 细胞交集 = **0**；端点仅 viability（不得与 ΔEMAX 混用）；技术重复≠独立培养如实披露。

### 3.2 设计门（任一 FAIL → `design_invalid`，停）

- **DSG1 留出设计**：30 目标细胞按归一名升序 `index % 5` → **5 折、每折 6 细胞**；held-out 细胞与训练细胞**不相交**；每折 ≥ **1,000** 单元 Δ 且 ≥ **5** 个 `(partner,role)` 上下文。
- **DSG2 MDE 先验**：`SE_unit = σ_e · sqrt(1/(4·4·4) + 1/(4·4·4)) = σ_e/√32`（每成员 = 4 partner doses × 4 member doses × 4 技术重复 = 64 个 well 读数取均值；Δ 为两成员均值之差）；`MDE80 = 2.801585 · SE_unit / sqrt(n_eff)`；`n_eff` = 每折 held-out 细胞数（=6，保守聚类口径；另报 12/24/30）；σ_e ∈ {0.041, 0.058, 0.109}（借用既有 A0/A2 估计，**非本轮 O'Neil 实测**）。要求 **保守格（σ_e=0.109, n_eff=6）MDE80 ≤ δ_min_provisional=0.10**，否则 `design_invalid: precision_insufficient`。**限制**：σ_e 借用与 well 级独立假设未经 O'Neil 实测认证；执行前须用 O'Neil viability1–4 分半标定（噪声标定≠效应）替换并重算，不达标即停。
- **DSG3 端点不可变**：端点/聚合/符号规则=§2 冻结；不得换端点/换聚合/换剂量档/外推；不得与 Jaaks ΔEMAX 拼端点。
- **DSG4 独立性边界**：目标细胞与 Jaaks 不重叠；仅内部开发性；不得用该设计宣称独立确认/迁移/决策收益/机制；未来效果协议须另立并独立挑战。

### 3.3 ON1 判定（冻结）

- 数据门全过 + 设计门全过 → **`design_frozen_qualified_with_conditions`**（建议冻结本开发性协议草案；**不运行**；条件=§4 限制清单）。
- 任一数据门 FAIL → **`data_unavailable`**；任一设计门 FAIL → **`design_invalid`**。不降门槛、不换端点、不换切分、不挑剂量档。

## 4. 开发性设计骨架（冻结；未来效果协议须原样继承，改则需新协议+挑战）

- **留出**：30 目标细胞 → 5 折 × 6 细胞（归一名升序 `index%5`）；冻结清单写入 `on1.json`；held-out 不参与训练/调参/标准化/特征选择。
- **评估单元**：held-out 细胞上的单元 Δ（batch=1；角色分层；符号按§2）。
- **对照（未来协议候选，冻结定义；本轮不评估）**：① cell-blind：`(p,ρ)` 全局均值 Δ；② 成员对常数（identity-only/transductive 基线；只能作基线，不得当证据）；③ 单药参照对照：**仅当**单药工作簿另立资格后可用（本协议不读其数值）；④ 打乱成员标签零分布（按细胞聚类）；⑤ 跨细胞均值（训练细胞均值）。
- **失败类别**：`data_unavailable` / `design_invalid` / `evaluation_cannot_distinguish`（未来效果 MDE80 > δ_min 或 CI 不能区分）/ `no_increment`（未来效果比较无增量）。
- **δ_min**：`δ_min_provisional = 0.10`（沿 R199-Q0 临时值，Δ viability 尺度；**不是**决策效用阈值；第 2 步前必须由 A5 决策成本冻结替换，不得沿用宣称收益）。
- **停止条件**：数据/设计门不过即停；未来效果若 MDE80>δ_min 判 `evaluation_cannot_distinguish`；无增量判 `no_increment`；不得换指标/换切分/换端点复活；不得与 Jaaks 端点和数据拼接。
- **描述边界**：仅"该资源/该端点内的描述性开发结果"；不得称独立确认/迁移/决策收益/机制/新算法；阴性完整记录。

## 5. 交付与确定性

- 交付（新建 `research/2026-10-27-core-module-design/oneil_dev/`）：本协议、`on1.py`（仅资格/数据准备，不拟合）、`on1.json`、`report_on1.md`、`record_on1.md`、`usage_on1.json`。
- `on1.py`：逐个数字从原始文件重算（不使用任何侦察结果）；metadata-only；JSON 键排序、无时间戳、`allow_nan=False`；输入/脚本 SHA256 写入 `on1.json`；两跑逐字节一致；单命令 ≤15 min。
- 只写本目录与 `tmp/`；不改 Q0 产物/其它目录/INDEX/SYNTHESIS/git。

## 6. 明确不做 / 边界

- 不运行效果、不训练、不比较更新器、不选药、不做 acquisition/Agent/反馈实验。
- 不写"规律成立/迁移/决策收益/机制/新颖性"；不把 viability 派生当独立功能终点；不把技术重复当独立培养；不把 O'Neil 当 Jaaks 的 endpoint-compatible target。
- 不改 R199-Q0 的判定（总体 `not_qualified`、O'Neil `qualified_with_conditions`）；本协议只落实其"ONeil 开发性窄任务"的**设计+资格**，执行另立。
