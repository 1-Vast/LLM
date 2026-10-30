# PROTOCOL_ON2 —— O'Neil **complete-case** 开发性内部细胞留出协议（v2 + **v2.1 补丁**；**post-observation protocol revision**，2026-10-27；原始 v2 在任何 ON2 资格计数之前冻结，v2.1 为按 `challenge_ON2.md` 的 5 条必改补丁）

> **性质声明（写死）**：本协议是**看到 ON1 v1 结果之后**的新协议（v2），**不是预注册**。ON1 v1 记录保持：`PROTOCOL_ON1.md` v1 FROZEN、`on1.json` verdict=`data_unavailable`（DG3 字面门失败，failure category `replicates_missing`）；`AMENDMENT_ON1-001` **不冻结**（ON1-C1 判"事后门槛放宽"）；本 v2 走**路径 A = complete-case 分析人群**（不改数据质量门槛、不按响应选择行，只按空值掩码限制人群）。v2 必须经独立挑战后**才可解释/冻结**；本任务只做资格/设计，**不运行效果、不训练、不比较更新器**。
>
> 依据：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON1.md, on1.json, on1.py, AMENDMENT_ON1-001.md, challenge_ON1_amendment.md}`（ON1-C1：revise；推荐 complete-case）、R199-Q0（`qualification/{PROTOCOL_Q0.md, q0.json, report_q0.md}`：总体 `not_qualified`，O'Neil 唯一 `qualified_with_conditions`，仅开发性内部细胞留出）、R199 BRIEF、SYNTHESIS C178–C181。
>
> **输入与工作目录**：输入只读；只写 `research/2026-10-27-core-module-design/oneil_dev/`（v2 新文件）与 `tmp/`；不改 v1/AMENDMENT/challenge/其它目录/INDEX/SYNTHESIS/git。

> **v2.1 补丁（2026-10-27，按 `challenge_ON2.md` revise 的 5 条必改）**：原 v2 冻结文本 SHA256 `D990BD0A…DEFF51` 作为历史记录保留（本文件在原 v2 基础上直接修订；修订前文本见 `REVISION_ON2_1.md` 的 before/after 对照）；本补丁仅修改以下条款：§3 门语义（DG3→路径 A 披露门）、§3.3(1) v1.1 成员规则（对齐为"≥95% 的 16 行且 ≥12/16"并补排除计数）、§3.3(2) MI→确定性行均值单插补敏感性、§3.2 DSG2(b) σ_e 分半规则（固定重复索引、禁按值排序）、§4/§5 provisional 判定措辞。**门级资格数字不变**（DG1 340,088/2,149/30/30/11,623；DG2 96.91%；DSG1 66,556–69,738；见 `on2.json`）。v2.1 SHA256 见 `record_on2_1.md` / `REVISION_ON2_1.md`。**qualification verdict = provisional pending independent challenge。**

> **v2.2 errata（2026-10-27，按 `challenge_ON2_1.md` 3 条文档/披露必改）**：本协议补入 **规范文件/supersession 清单（§6）**、**v1.1 排除 Δ 的诊断基线（rule B − rule A）与成员上下文定义（§3.3(1)）**；`on2.json` 旧 MI/verdict 字段的历史属性见 `ERRATA_ON2_1.md`。**不重跑数据/效果、门级资格数字不变。**


## 0. 范围（写死）

- **仅 O'Neil 内部开发性细胞留出**；**仅 viability 端点**；**技术重复 ≠ 独立培养**（3 BatchID 同 lab、未认证独立培养）；**不得**称独立确认/迁移/决策收益/机制/新算法；**不比较更新器**（另立效果协议+独立挑战）；不做 acquisition/Agent/反馈实验。
- O'Neil 39 细胞中 **9 个与 Jaaks 重叠**（`hct116, ht29, lovo, mdamb436, ocubm, rko, sw620, sw837, t47d`）**排除**；目标 **30** 细胞；source/target 细胞不相交（Jaaks 仅作 lineage 重叠审计，不参与本任务）。
- **不得与 Jaaks `SYNERGY_DELTA_EMAX` 拼端点/换算**；`mu/muMax`、`X/X0` 是 viability 派生，不作独立功能读数。
- 主分析 **BatchID=1**（batch2/3 只在披露/敏感性中报告，不进入主设计；batch3 在 complete-case 下整体消失，须披露）。

## 1. 数据与主分析人群（冻结）

- 组合工作簿：`data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`（368,832 行；39 细胞；38 药；3 BatchID；每行 4×4 数字剂量网格；viability1–4 技术重复；SHA256 `A0E2E002…C14818`）。
- **complete-case 定义（主分析人群）**：**viability1–4 四列全部非空的行**（只看空值掩码；不读响应数值做效应/选择）。预期 **363,090** 行（覆盖率 363,090/368,832 = **98.44%**）；batch1 **357,876**、batch2 **5,214**、batch3 **0**（整体消失）。
- **元数据边界**：只读 `BatchID, cell_line, drugA_name, drugA Conc (µM), drugB_name, drugB Conc (µM)`；viability1–4 只做**非空/缺失掩码计数**（不做任何响应统计、不读数值做效应）。
- **缺失披露（必须报告）**：全局覆盖率与缺失数（viability1–4 = 0/78/198/5,742）；各 batch 的保留/丢失；complete-case 后每 pair-cell 行数分布与 **702 个 15 行 pair-cell** 计数；缺失按 batch / viability 列 / pair-cell / grid 行位（member-dose 位 × partner-dose 位）/ cell / partner 的分布；共缺失模式（同时缺哪几列）。

## 2. 冻结定义（与 ON1 一致处沿用，但所有资格数字必须按 complete-case 重算）

- **角色**：每行 drugA=A 角色、drugB=B 角色；无序药对只有一种 A/B 定向（复核）。
- **伙伴-角色上下文** `(batch, cell, partner, partner_role)`；**成员** = 同上下文、伙伴另一角色上的药。
- **成员网格**：每成员必须 4×4=16 行齐全（complete-case 下）才算完整；**单元 Δ** = `grid_mean(c,a,partner) − grid_mean(c,a',partner)`（16 行 × 4 重复均值；符号按归一名升序，前者减后者）；等价于 4 个 partner-dose 行 Δ 的均值。
- **可替换单元**：同 `(batch,cell,partner,role)` 下两个成员均完整的无序成员对。
- **跨细胞覆盖**：固定 `(partner,role,{a,a'})`，在多少个不同目标细胞可算 Δ（complete-case、batch1）。
- **目标细胞**：39−9=30（列表冻结于 `on2.json`）；**5 折设计**：目标细胞按归一名升序 `index%5` → 5 折 × 6 细胞；held-out 与训练细胞不相交。
- **批次**：主分析 batch1；batch2 只作披露；batch3 complete-case 下为 0（披露）。

## 3. 冻结门（v2 + v2.1 补丁；**DG1/DG2/DSG 阈值不变**；**DG3 由 v1 完整性门改为 complete-case 路径 A 的披露门——人群/门语义变更，不是阈值放宽**）

### 3.1 数据门（任一 FAIL → `data_unavailable`，停）

- **DG1 交叉规模（complete-case、batch1、目标 30 细胞）**：可计算单元 Δ **≥5,000**；贡献 ≥1 单元的目标细胞 **≥30**（30/30）；`(cell,partner,role)` 成员上下文（成员≥2）**≥200**；跨细胞覆盖 ≥3 个目标细胞的 `(partner,role,{a,a'})` 上下文 **≥10**。
- **DG2 完整成员网格**：complete-case 下完整成员上下文（16 行齐全）**≥95%**（分母 = complete-case 中出现的成员上下文数；同时报绝对数）。v1 的 100%/363,304 等数字**不得**沿用。
- **DG3（v2.1 路径 A 披露门；门语义变更，不是阈值放宽）**：complete-case 必须作为**主分析人群**并披露 §1 全部缺失项（覆盖率 98.44%；缺失 0/78/198/5,742；batch1 357,876 / batch2 5,214 / batch3 0；complete-case 后 pair-cell 行数 22,035×16 / **702×15** / 315×0；缺失 grid 位与 by cell/partner 分布）；**不得假设 MCAR/MAR**；主分析只按行级空值掩码限制人群、**不按响应/缺失与响应关系选择**；v1.1 all-available 敏感性须闭合定义与报告（§3.3）。该门以"路径 A 人群已声明 + 披露完整 + 不假设机制 + 无响应选择"为通过条件；**不设"完整性=行数"阈值**（那是 v1 完整性门，v1 因此 `data_unavailable`），因此是**门语义/人群变更，不是阈值放宽**。
- **DG4 目标细胞**：complete-case 下目标 30/30 有 ≥1 合法单元；重叠 9 细胞排除；**复算**。
- **DG5 边界/lineage**：目标 30 细胞 ∩ Jaaks = 0；端点仅 viability；不与 ΔEMAX 拼接；技术重复≠独立培养如实披露。

### 3.2 设计门（任一 FAIL → `design_invalid`，停）

- **DSG1 留出设计**：5 折 × 6 细胞；held-out 与训练不相交；每折 complete-case 单元 Δ **≥1,000**、`(partner,role)` 上下文 **≥5**；报每折数字（v2 必须重算，不沿用 71,004–74,580）。
- **DSG2 精度（σ_e/MDE）**：
  - **(a) 先验期望（报告，不作资格证据）**：`SE_unit=σ_e/√32`、`MDE80=2.801585·SE_unit/√n_eff`（n_eff=每折 6 held-out 细胞，保守）；σ_e ∈ {0.041,0.058,0.109}（借用 A0/A2；**非 O'Neil 实测**）。要求先验期望（σ_e=0.109, n_eff=6）≤ δ_min_provisional=0.10，否则 `design_invalid: precision_insufficient`。
  - **(b) 执行前实测条款（冻结，写死）**：**不把借用 σ_e 的先验当资格证据**。执行效果协议前必须先做 **O'Neil σ_e 标定**（只作噪声标定，不是效应），规则：
    1. cohort：**complete-case 行**（主）与 **all-available 且该行 ≥2 个非空重复**（敏感性）；**k=1 的行（全表 78 行）不参与标定并计数**；
    2. **固定重复索引分半（禁止按观测值排序）**：重复列固定为 `viability1, viability2, viability3, viability4`；每行只在**非空重复列索引**中按该固定列序取前 `h1 = ⌈k/2⌉` 个 vs 余 `h2 = k − h1` 个（k=4 → {v1,v2} vs {v3,v4}，h1=h2=2；k=3 → 前两个可用索引 vs 余下 1 个，2+1；k=2 → {第一个可用} vs {第二个可用}，1+1）。**不得按响应值排序/分半**；分半只依赖空值掩码与固定列序；
    3. 计算行半均值、成员曲线半均值（16 行半均值之均值）、Δ 半值（两成员半均值差）；
    4. `σ̂_e² = Σ_units (Δ_h1 − Δ_h2)² / Σ_units denom`，`denom = Σ_{两成员}Σ_{16 行} (1/h1 + 1/h2) / 16²`（h1/h2 为该行两半实际可用重复数；complete-case 每单元 = 2·16·(1/2+1/2)/256 = 1/8）；σ̂_e 是 well 级标准差；
    5. `SE_unit = σ̂_e/√32`、`MDE80 = 2.801585·SE_unit/√n_eff`（n_eff = 每折 6 held-out 细胞，保守）；**实测 MDE80 > δ_min_provisional=0.10 → `design_invalid: precision_insufficient` 停**；
    6. **执行期顺序（冻结）**：先输出 σ_e 标定报告（schema 至少含 cohort、units_used、rows_used、rows_excluded_k1、units_excluded、σ̂_e、SE_unit、MDE80、n_eff），再判 MDE 门，最后才允许决定是否运行效果协议；执行脚本/输出 schema 须在效果协议前冻结；
    7. σ_e 借用先验来源锚点：0.041 = A0/R4 σ_e=0.0408；0.058 = A2 `q2.json` single-key σ=√0.003351；0.109 = A2 `noise_variance_mean_per_observation`=0.011968 的平方根；**仅期望、不作资格证据**。
  - **(c) 资格判定**：v2 资格只判"条款已冻结 + 先验期望通过"；**实测 MDE 的认证在执行协议中进行**，未认证前不得运行效果/更新器比较。
- **DSG3 端点不可变**：点位/聚合/符号/人群/剂量规则=§2 冻结；不得换端点/换聚合/换剂量档/外推；不得与 Jaaks 端点拼接。
- **DSG4 独立性边界**：目标细胞与 Jaaks 不重叠；仅内部开发性；不得称独立确认/迁移/决策收益/机制；未来效果协议须另立并独立挑战。

### 3.3 缺失机制与敏感性（冻结；不进 v2 主判定）

- **机制假设**：metadata-only **不能假设 MCAR/MAR**，也不得假设 MNAR；**主分析 = complete-case**（仅空值掩码选择人群，不按响应选择）。执行期须报告缺失模式与敏感性。
- **灵敏度分析（预注册，仅敏感性、不改主判定）**：
  1. **all-available（v1.1 规则；v2.1 对齐写死）**：cohort = 原始行中 ≥1 个非空技术重复的行（**覆盖率 100%（368,832/368,832；viability1 无缺失）**）；行值 = 非空重复均值（≥1）；**成员可用 = 该成员 16 行齐全 且 ≥95% 的 16 行有 ≥2 非空重复 且 ≥12/16 行有 ≥2 非空重复**（16 行下 ≥95% 即 16/16 行；≥12/16 作为冗余保留以便审计）；成员曲线 = 有 ≥2 重复的行上的均值；Δ 单元 = 两成员可在同上下文使用。必须闭合报告：
     - **all-4 完整率（不是 all-available 覆盖率）双分母**：全表 363,090/368,832 = **98.44%**；batch1-target 分析人群 275,412/275,936 = **99.81%**；
     - all-available cohort 覆盖率 = **100%**（368,832/368,832）；行可用重复数分布：**k=1 78 行、k=2 120、k=3 5,544、k=4 363,090**（k=0 为 0）；
     - 成员上下文层级"行内条件"的单位 = 每个成员上下文 16 行（分母 16）；**上下文级 95%** 分子/分母 = 满足"该上下文 ≥95% 的 16 行有 ≥2 非空重复"的成员上下文数 / 完整成员上下文数 = **45,948 / 46,104 = 99.66%**；
     - **失败上下文计数**：不满足行内 ≥95% 的成员上下文 **156 个**，行内比例均为 **15/16 = 93.75%**；**明确 93.75% 不满足行内 ≥95% 条件**（只由上下文级 95% 容许）；对应 **78 个 k=1 行 × 2 个角色方向 = 156 个成员上下文**；
      - **被排除成员/单元计数（v2.2 闭合基线）**：**排除 Δ 单元 = rule B（仅 ≥12/16，诊断基线、无排除）units − rule A units**：all **473,906−470,179=3,727**、b1-all **472,116−468,393=3,723**、b1-target **363,304−360,452=2,852**；**rule B 只是诊断基线、不是资格规则/资格数**（其 b1-target 363,304 与 v1 数字相同、仅披露）。排除成员上下文 = **156（all）/ 154（b1-all）/ 118（b1-target）**（batch2 为 2；**"152" 不采用**——只读重算 b1-all=154，152 无法复现）。**成员上下文定义 = `(batch,cell,partner,role,member)` 的 16 行**（4 partner doses × 4 member doses；156/154/118 是成员上下文数，不是成员对/成员数）。排除后上下文降到 <2 可用成员 = **0**（三 scope 均 0）；敏感性 Δ 单元 = **470,179 / 468,393 / 360,452**（all / b1-all / b1-target，仅敏感性、不作主判定）。
  2. **确定性行均值单插补敏感性（不是多重插补；v2.1 修正）**：预注册方案（执行期才运行；ON2.1 metadata-only 不读响应数值）：**单次确定性插补**——每个缺失行值用其非空技术重复的行均值补（≥1）；无随机抽样、**无 m、无独立 seed、无 Rubin within/between 方差**；结构约束为 batch/cell/partner/dose-row（不跨端点、不跨研究）；报告 Δ 单元集合与均值 Δ 的敏感性；执行期须与 complete-case 主结果并列。**删除原"MI/m=20/seed 20261120"声明**（该计划不可执行，challenge_ON2 已判）。
- **技术重复**：只作精度/标定，**不作独立 n**；n_eff = held-out 细胞数（保守）；不得把 64 well 当 64 独立样本。

## 4. 判定（冻结）

- 数据门全过 + 设计门全过 → **`design_frozen_qualified_with_conditions`（provisional pending independent challenge）**：protocol frozen（post-observation）；**qualification verdict 仅 provisional**，独立挑战通过后才可写 final；不运行效果；条件=§5 清单；**不写"资源足够"**。
- 任一数据门 FAIL → **`data_unavailable`**；任一设计门 FAIL → **`design_invalid`**。不降门槛、不换端点/切分/剂量档、不用 v1.1 敏感性替代主判定。

## 5. 条件与边界（随判定一起读）

1. 本协议是 **post-observation revision（v2/v2.1）**，不是预注册；v1 的 `data_unavailable` 记录保留；**本判定为 provisional pending independent challenge**。
2. complete-case 主分析覆盖 98.44%；缺失 78/198/5,742；batch3 全部丢失；702 个 pair-cell 只剩 15 行；缺失机制未知（不假设 MCAR/MAR）；需执行期**确定性行均值单插补**敏感性（不是 MI）。
3. 仅 O'Neil 内部开发性；不得称独立确认/迁移/决策收益/机制/新算法；技术重复≠独立培养；3 BatchID 同 lab。
4. 仅 viability 端点（mu/muMax、X/X0 为派生，不作独立功能读数）；不得与 Jaaks ΔEMAX 拼接。
5. σ_e/MDE：借用先验只作期望；**实测标定（固定重复索引分半、禁按值排序）与 MDE 认证在执行协议中进行**，MDE>δ_min → design_invalid 停。
6. δ_min_provisional=0.10 是临时先验（沿 Q0），不是决策效用阈值。
7. 未运行效果/训练/更新器比较；阴性/不足同样完整记录；不声称新颖性。

## 6. 确定性/交付

- **交付与规范文件（v2.2 更新）**：
  - **v2.1 规范（冻结后引用）**：本协议 `PROTOCOL_ON2.md`（v2.1 + v2.2 errata 注记）、`REVISION_ON2_1.md`、**`report_on2_1.md`（规范报告）**、**`record_on2_1.md`（记录 + 冻结文本）**、`usage_on2_1.json`、**`ERRATA_ON2_1.md`（规范文件/supersession/基线勘误）**。
  - **v2.0 历史（不得作为冻结引用）**：`on2.py` / `on2.json` / `usage_on2.json`（未改，门级数字有效）；`report_on2.md` / `record_on2.md`（含 v1 描述统计）；`AMENDMENT_ON1-001.md`（不冻结记录）。
  - **`on2.json` supersession**：其 `missingness_and_sensitivity.multiple_imputation_plan`（m=20/seed/Rubin）与 `verdict.verdict`（无 provisional）是 **v2.0 历史字段**；v2.1 以本协议/`report_on2_1.md` 为准，**不得引用/执行旧 MI**（见 `ERRATA_ON2_1.md`）。
- `on2.py`：metadata-only；JSON 键排序、无时间戳、`allow_nan=False`；输入/脚本 SHA256 写入；两跑 `on2.json` 逐字节一致；单命令 ≤45 min；只写本目录与 `tmp/`。
