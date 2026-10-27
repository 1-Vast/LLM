# R199-ON2.1 报告：O'Neil **complete-case** 开发性内部细胞留出协议（v2 + v2.1 补丁；设计 + 资格复核，**不运行**）

2026-10-27。角色：ON1/ON2 执行者（非挑战者；不参与效果设计）。依据：`challenge_ON2.md`（ON2 独立挑战：**revise，≤5 必改；当前不可冻结**）、Lead 采用指令（task-63）、R199-Q0（总体 `not_qualified`；O'Neil 唯一 `qualified_with_conditions`，仅开发性内部细胞留出）、R199 BRIEF、SYNTHESIS C178–C181。

- **规范文件（v2.2 更新）**：本文件为 **v2.1 规范报告**；协议 `PROTOCOL_ON2.md`（v2.1 + v2.2 errata 注记）、`REVISION_ON2_1.md`、`record_on2_1.md`（含冻结文本）、`usage_on2_1.json`、`ERRATA_ON2_1.md`（规范文件/supersession/基线勘误）。
- **v2.0 历史文件（不得作为冻结引用）**：`on2.py` / `on2.json` / `usage_on2.json`（未改、门级资格数字有效）；`report_on2.md` / `record_on2.md`（含 v1 描述统计 169.2/666、28/324/666、9,581–12,430）。
- **本文件取代 `report_on2.md`**（v2 报告 §2 有三处把 v1 描述统计当作 v2 重算结果，已按 challenge 修；v2 报告保留为历史记录）。
- **`on2.json` supersession**：其 `missingness_and_sensitivity.multiple_imputation_plan`（m=20/seed/Rubin）与 `verdict.verdict`（无 provisional）是 **v2.0 历史字段**；v2.1 以协议/本报告为准，**不得引用/执行旧 MI**（见 [ERRATA_ON2_1.md](ERRATA_ON2_1.md)）。
- 协议 v2.2 SHA `7B34DB79…0B2BA7`（v2.1 为 `8A3E065F…84CCFF`；见 §10）；数据 [on2.json](on2.json)（SHA `AD7E6D13…81F7C8`，**门级资格数字不变、未重跑**）。
- **本轮（ON2.2）只做文档/披露修补与只读重算；不运行效果/训练/更新器；viability1–4 只作空值掩码，响应数值未进入任何统计。**

## 0. 判定（一屏）

**`design_frozen_qualified_with_conditions` —— provisional pending independent challenge**（protocol frozen，post-observation；qualification verdict 仅 provisional，独立挑战通过后才可写 final）。complete-case 主分析下数据门 DG1–DG5 与设计门 DSG1–DSG4 全 PASS；**门级资格数字与 `on2.json` 一致，未改动**。

**冻结文本（approve_freeze 版，含规范文件/supersession/基线）见 `record_on2_1.md` §10；规范文件/errata 见 `ERRATA_ON2_1.md`。**

| 门 | v2 实测（complete-case） | 门槛 | 判定 |
|---|---|---|---|
| DG1 单元 Δ（batch1、目标 30 细胞） | **340,088** | ≥5,000 | PASS |
| DG1 贡献目标细胞 | **30/30** | ≥30 | PASS |
| DG1 `(cell,partner,role)` 上下文 | **2,149** | ≥200 | PASS |
| DG1 跨 ≥3 目标细胞 `(p,ρ,{a,a'})` 上下文 | **11,623** | ≥10 | PASS |
| DG2 完整成员上下文 | **44,070/45,474 = 96.91%** | ≥95% | PASS |
| DG3 **路径 A 披露门**（v2.1 语义；见 §6） | 披露完整（§1/§2） | 披露完整 | PASS |
| DG4 目标细胞 / 30 全贡献 | **30 / 30** | 30 / 30 | PASS |
| DG5 目标 ∩ Jaaks | **0/30**（9 重叠排除） | 0 | PASS |
| DSG1 5 折（各 6 细胞）单元/折 | **66,556–69,738**（[68,152, 66,743, 66,556, 69,738, 68,899]） | ≥1,000 | PASS |
| DSG1 上下文/折 | **427–432** | ≥5 | PASS |
| DSG2a 借用 σ_e 先验期望（σ=0.109, n_eff=6） | **0.02203838**（**仅期望，非资格证据**） | ≤δ_min=0.10 | PASS |
| DSG2b 执行期 σ_e 标定条款 | **已冻结**（固定重复索引分半；实测 MDE>δ_min→`design_invalid`） | 条款冻结 | PASS |
| DSG3/DSG4 端点/独立性边界 | 冻结 | — | PASS |

- **不写"资源足够"**：v1 仍是 `data_unavailable`；v2.1 只是"complete-case 人群下资格重算通过、且按 challenge 修完 5 条"的 **provisional** 结果，**须经同一挑战者只读复核**才可冻结；冻结 ≠ 资源足够/关系成立/Stage 1/效果。
- **v1 数字不得沿用**：v1 的 363,304 / 71,004–74,580 / 100% / 12,430 只在 §7 披露表出现。

## 1. 5 条必改的落实

| # | challenge_ON2 必改 | 落实 |
|---|---|---|
| ① | report/record 描述统计改为 v2 实测 | **已改**：per-context mean **158.3185**/max **630**（n=2,791）；per (cell,partner) min **21**/median **291**/max **630**（n=1,481）；每目标细胞单元 **9,047–11,623**/median **11,623**（n=30）——均来自 on2.json 且与 challenge 独立重算一致；v1 数字只留 §7 |
| ② | 对齐 v1.1 成员规则（二选一）并重算 + 补排除计数 | **已写死**："≥95% 的 16 行 **且** ≥12/16"；**45,948/46,104=99.66%**、**156 个 15/16=93.75% 失败上下文**、敏感性 Δ **360,452**；**排除 Δ 单元 = rule B−rule A：3,727/3,723/2,852（all/b1-all/b1-target；rule B 仅诊断基线）；排除成员上下文 156/154/118（all/b1-all/b1-target；"152" 不采用）**；**98.44%/99.81% 标注为 all-4 完整率**，all-available 覆盖率 **100%** |
| ③ | MI → 真随机或改称确定性单插补 | **改称"确定性行均值单插补敏感性"**；**删除 m=20/seed/Rubin**；协议/报告同步；本轮不运行 |
| ④ | σ_e 分半冻结 | **固定重复索引**（viability1–2 vs 3–4，禁按值排序）；写死 k=4→2+2、k=3→2+1、k=2→1+1、k=1 排除（78 行）计数、denom、执行 schema/顺序/stop |
| ⑤ | 门语义/冻结措辞 | **DG3→路径 A 披露门**（DG1/DG2/DSG 阈值不变；非阈值放宽）；report/verdict 标 **provisional pending challenge**；保留 v1 `data_unavailable`、AMENDMENT 不冻结、v1.1 仅敏感性、无"资源足够" |

## 2. complete-case 主分析人群与资格数字（未变，v2 实测）

- **cohort**：viability1–4 全非空 → **363,090/368,832 = 98.44%**；batch1 **357,876**（丢 684）、batch2 **5,214**（丢 18）、**batch3 0**（5,040 全失）。缺失 viability1–4 = **0/78/198/5,742**；共缺失模式：complete 363,090、`v2;v3;v4` 78、`v3;v4` 120、`v4` 5,544。complete-case 后 pair-cell：**702 个 15 行**、315 个 0 行（batch3）、22,035 个 16 行。
- **成员上下文定义（写死）**：`(batch, cell, partner, partner_role, member)` 的 **16 行**（4 partner doses × 4 member doses）；后文"排除 156/154/118 个成员上下文"均指**成员上下文数**，不是 member pair 数、不是成员数。
- **315 = 309 + 6（来源）**：原始数据 **315 个 pair-cell 跨两个 BatchID 各 16 行（32 行）**：**309 个 batch1+batch3、6 个 batch2+batch3**（来源：`on2.json` 的 batch pair-cells 22,410/327/315 + `cohort.pair_cell_rows_distribution_raw`；split 来自执行者只读重算 `tmp/_on2_2_check.py`，不在 on2.json 内，引用时注明）。**315 是 pair-cell 数，不是成员上下文数**；complete-case unique raw 分组 22,737=22,410+327（batch3 的 315 全部重叠）。
- **DG1**：**340,088** 单元 Δ / **2,149** 上下文 / **30/30** / 跨 ≥3 目标细胞 **11,623**。全 batch 442,996/2,927；batch1 全细胞 441,867/2,791；batch2 1,129/136。strict-row（同 partner-dose 行）：**1,429,518** 行级单元 / 8,596 上下文（batch1 目标）。
- **DG2**：**44,070/45,474 = 96.91%**。
- **5 折**（30 细胞 → 6/6/6/6/6）：单元 **[68,152, 66,743, 66,556, 69,738, 68,899]**、strict-row 279,479–293,376、上下文 **427–432**、`(partner,role)` 72；held-out 与训练不相交。
- **DG4/DG5**：目标 30、30/30 贡献；Jaaks 重叠 **0/30**（9 个排除：hct116, ht29, lovo, mdamb436, ocubm, rko, sw620, sw837, t47d）。

### 2.1 描述统计（**v2 实测；v1 值不得再用**）

| 量 | v2 实测（on2.json） |
|---|---|
| per-context 可替换对数（batch1 全细胞，n=2,791） | min **1**、median **153**、mean **158.3185**、max **630** |
| per (cell,partner) 合并角色对数（batch1 全细胞，n=1,481） | min **21**、median **291**、mean 298.3572、max **630** |
| 每目标细胞单元 Δ（n=30） | min **9,047**、median **11,623**、max **11,623**、mean 11,336.27 |
| 附：目标细胞子口径 per-context（n=2,149） | mean 158.2541、max 630 |
| 附：目标细胞子口径 per (cell,partner)（n=1,139） | min 28、median 291、max 630 |
| 跨细胞覆盖（`(p,ρ,{a,a'})`，batch1） | 11,623 个；33–39 细胞（目标口径 25–30，全部 ≥3） |

## 3. v1.1 all-available 敏感性（**仅敏感性**；规则 v2.1 对齐写死）

- **cohort**：原始行中 ≥1 非空技术重复 → **覆盖率 100%（368,832/368,832；viability1 无缺失）**；行可用重复数 k：**k=1 78、k=2 120、k=3 5,544、k=4 363,090**（k=0 为 0）。
- **成员可用（写死）**：该成员 16 行齐全 **且 ≥95% 的 16 行有 ≥2 非空重复（16 行下即 16/16）且 ≥12/16 行有 ≥2 非空重复**（冗余保留审计）。
- **成员上下文**：**45,948 / 46,104 = 99.66%** 满足行内 ≥95%。
- **失败上下文**：**156 个，行内比例全部 15/16 = 93.75%**——**明确 93.75% 不满足行内 ≥95%**（只由上下文级 95% 容许）；对应 **78 个 k=1 行 × 2 个角色方向**。
- **被排除成员/单元计数（v2.2 闭合基线）**：**排除 Δ 单元 = rule B（仅 ≥12/16，诊断基线、无排除）units − rule A units**：
  | scope | rule B（诊断基线，无排除） | rule A（敏感性） | 排除 Δ = B−A | 排除成员上下文 |
  |---|---:|---:|---:|---:|
  | all batches all cells | **473,906** | **470,179** | **3,727** | **156** |
  | batch1 all cells (b1-all) | **472,116** | **468,393** | **3,723** | **154** |
  | batch1 target cells | **363,304** | **360,452** | **2,852** | **118** |
  **rule B 只是诊断基线、不是资格规则/资格数**（其 b1-target 363,304 与 v1 数字相同、仅在 §7 披露）；**"152" 不采用**——只读重算 b1-all=154，152 无法复现；排除后上下文降到 <2 可用成员 = **0**（三 scope）。**成员上下文 = (batch,cell,partner,role,member) 的 16 行**。
- **敏感性 Δ 单元**：**470,179 / 468,393 / 360,452**（all / batch1 / batch1-target）——**仅敏感性，不作 v2 资格数**。
- **标签修正**：**98.44%（全表）与 99.81%（batch1-target：275,412/275,936）是 all-4 完整率，不是 all-available 覆盖率**；all-available 覆盖率 = 100%。

## 4. 缺失插补敏感性：**确定性行均值单插补（不是 MI）**

- v2.1 修正：原"MI、m=20、seed 20261120、Rubin 方差"计划不可执行（行均值插补是确定性的）→ **从 v2.1 协议/报告中删除**；**`on2.json` 保留该字段作为 v2.0 历史（superseded，不得引用/执行）**，见 [ERRATA_ON2_1.md](ERRATA_ON2_1.md)。
- 现冻结方案：**单次确定性插补**——缺失行值用其非空技术重复行均值补（≥1）；无随机抽样、无 m、无 Rubin；结构约束 batch/cell/partner/dose-row（不跨端点/跨研究）；执行期作为敏感性、与 complete-case 主结果并列；**本轮 metadata-only 不运行**。

## 5. σ_e / MDE 执行条款（v2.1 冻结）

- **借用先验（仅期望、非资格证据）**：`SE_unit=σ_e/√32`、`MDE80=2.801585·SE_unit/√n_eff`（n_eff=每折 6 held-out 细胞）；σ_e∈{0.041,0.058,0.109}；保守格 **0.02203838 ≤ δ_min=0.10**。来源锚点：0.041=A0/R4 σ_e=0.0408；0.058=A2 `q2.json` single-key σ=√0.003351；0.109=A2 `noise_variance_mean_per_observation`=0.011968 的平方根。
- **分半冻结（禁按值排序）**：固定重复列索引 `viability1..4`；每行在非空重复索引中按固定列序取前 `h1=⌈k/2⌉` vs 余 `h2=k−h1`：**k=4 → {v1,v2} vs {v3,v4}（2+2）；k=3 → 前两可用 vs 余 1（2+1）；k=2 → {第一个可用} vs {第二个可用}（1+1）；k=1（78 行）不参与标定并计数**。
- **估计量**：`σ̂_e² = Σ(Δ_h1−Δ_h2)² / Σdenom`，`denom = Σ_{两成员}Σ_{16 行}(1/h1+1/h2)/16²`（complete-case 每单元 = 1/8）；`SE_unit=σ̂_e/√32`、`MDE80=2.801585·SE_unit/√n_eff`。
- **执行顺序/schema/stop（冻结）**：先输出标定报告（cohort、units_used、rows_used、rows_excluded_k1、units_excluded、σ̂_e、SE_unit、MDE80、n_eff）→ 再判 MDE 门 → 最后才决定是否运行效果协议；**实测 MDE80>δ_min=0.10 → `design_invalid: precision_insufficient` 停**；脚本/输出 schema 须在效果协议前冻结。

## 6. DG3 门语义（v2.1：路径 A 披露门，非阈值放宽）

- **DG1/DG2/DSG 阈值不变**（仍是 v1/v2 的设计要求）。
- **DG3 变更**：由 v1 的"完整性门（viability1–4 非空计数=行数）"改为 **complete-case 路径 A 的披露门**——要求：路径 A 人群已声明为主分析；披露 §1 全部缺失项（覆盖率/缺失/batch/702 个 15 行/缺失模式）；**不假设 MCAR/MAR**；主分析只按空值掩码限制人群、不按响应选择；v1.1 敏感性闭合定义（§3）。**不设"完整性=行数"阈值**；v1 因该完整性门 `data_unavailable` 的记录保持。因此这是**人群/门语义变更，不是阈值放宽**，也不改变任何门级资格数字。

## 7. v1 vs v2（**仅披露；v1 数字不得沿用**）

| 项 | v1（完整网格存在性口径；`data_unavailable`） | v2.1（complete-case；provisional） |
|---|---|---|
| batch1-target 单元 Δ | 363,304 | **340,088** |
| batch1-target 上下文 | 2,149 | **2,149** |
| 每折单元 | 71,004–74,580 | **66,556–69,738** |
| 完整成员上下文 | 100% | **96.91%（44,070/45,474）** |
| 跨 ≥3 目标细胞上下文 | 12,430 | **11,623** |
| 判定 | `data_unavailable`（DG3） | **`design_frozen_qualified_with_conditions`（provisional）** |

## 8. 边界/措辞（写死）

- **v2.1 是 post-observation protocol revision，不是预注册**；v1 `data_unavailable` 记录保留；AMENDMENT_ON1-001 **不冻结**；v1.1 仅敏感性；**qualification verdict provisional pending independent challenge**。
- 仅 O'Neil **内部开发性**细胞留出；**不得**称独立确认/迁移/决策收益/机制/新算法；不比较更新器（另立效果协议+独立挑战）；不做 acquisition/Agent/反馈实验。
- 仅 **viability** 端点（mu/muMax、X/X0 派生，不作独立读数）；**不得与 Jaaks ΔEMAX 拼接/换算**；技术重复≠独立培养（3 BatchID 同 lab）；9 重叠细胞排除、目标 30；batch1 主分析、batch2 披露、batch3 全失披露。
- **不写"资源足够"**：只写"v1 的 DG3 完整性门是唯一阻塞；v2.1 complete-case 人群下资格门 PASS，但须独立挑战复核、且执行期须完成 σ_e 实测 MDE 认证后才可能进入效果协议"。
- 不声称新颖性；阴性/不足完整记录；不改 ON1/on2.json 门级数字。

## 9. 剩余缺口与解冻条件

1. **同一挑战者（endpoint-auditor）只读复核 v2.1**（5 条修复 + 重算数字）→ 通过后才可冻结 v2 资格判定（challenge §7）。
2. **执行期 σ_e 实测 + MDE 认证**（固定索引分半；MDE>δ_min → design_invalid 停）先于任何效果协议。
3. **确定性单插补敏感性**执行期运行（不是 MI）。
4. **缺失机制未知**（不假设 MCAR/MAR）；complete-case 覆盖 98.44%；batch3 全失、702 个 15 行 pair-cell 作为设计限制。
5. **无暴露时间/assay 方法列**：合法暴露仅部分可验证。
6. **单药参照未用**；技术重复≠独立培养；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**。

## 10. 产物与确定性

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_ON2.md`（v2.2；原 v2 `D990BD0A…`、v2.1 `8A3E065F…`） | `7B34DB796C9E1B7362722A553B155285E4E1E84686A7DE1A8B33CEF5120B2BA7` |
| `ERRATA_ON2_1.md` | `3C6138DF7BA1ACCDC7088FC78070F835D6DF61D0E7BBF77EF6B4DE0E0FE7870B` |
| `REVISION_ON2_1.md` | `65B8FFF98334594EAD69E3BB3DF96923E55A286B4C681E4FE1757FCCF4694D42`（未改） |
| `on2.py` / `on2.json` / `usage_on2.json` | 未改：`59ED8FFA…` / `AD7E6D13…` / `F23FECC2…`（v2.0 历史产物） |
| `report_on2_1.md` / `record_on2_1.md` | 本报告/本记录（SHA 由复核方重算） |

- **本轮只做文档/定义修订 + 只读 metadata 重算**：未重跑 `on2.py`、未改 `on2.json`/`on2.py`/ON1 产物；重算脚本在 `tmp/`（`_on2_1_recompute.py` 38.4 s、`_on2_1_recompute2.py` 47.9 s）；JSON 键排序/无时间戳的确定性要求沿用 on2 产物。
- 与 challenge 独立重算逐项一致（158.3185/630、21/291/630、9,047–11,623/11,623、45,948/46,104、156、360,452、98.44%/99.81%、k 分布、排除单元 3,727/3,723/2,852（rule B−rule A）与成员上下文 156/154/118）；门级数字 340,088/2,149/30/30/11,623/96.91%/66,556–69,738 未变。
