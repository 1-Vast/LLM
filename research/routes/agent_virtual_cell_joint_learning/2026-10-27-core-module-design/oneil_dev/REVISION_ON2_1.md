# REVISION_ON2_1 —— 按 `challenge_ON2.md` 的 5 条必改对 ON2 协议/报告的修订记录（v2.1）

2026-10-27。角色：ON1/ON2 执行者（非挑战者）。依据：`challenge_ON2.md`（ON2 独立挑战，总判决 **revise，≤5 必改；当前不可冻结**）、Lead 采用指令（task-63）。**本轮不运行效果/训练/更新器比较；不读响应数值做统计；不改门级资格数字。**

## 0. 结论

- **5 条必改已全部落实**：报告/记录描述统计改用 v2 实测；v1.1 成员规则二选一写死（选"≥95% 的 16 行 **且** ≥12/16"，并补排除计数、区分 all-4 完整率 vs all-available 覆盖率）；MI 改为"确定性行均值单插补敏感性"（删除 m=20/seed/Rubin）；σ_e 分半冻结为固定重复索引（禁按值排序，写死 k=2/3/4 的 h1/h2、k=1 排除、denom、执行 schema/stop）；DG3 改为路径 A 披露门（门语义变更，非阈值放宽），report/verdict 标 **provisional pending challenge**。
- **门级资格数字不变**（与 `on2.json` 及 challenge 独立重算一致）：complete-case 363,090/98.44%；DG1 340,088 / 2,149 / 30-30 / 11,623；DG2 44,070/45,474=96.91%；DSG1 66,556–69,738（427–432）；strict-row 1,429,518/8,596；σ_e 先验保守格 0.02203838。**未重跑 on2.py，on2.json/on2.py 未改。**
- **判定状态**：`design_frozen_qualified_with_conditions` **（provisional pending independent challenge）**；protocol frozen（post-observation）；挑战通过后才可写 final；仍不运行效果/更新器比较。

## 1. SHA 对照（原 v2 → v2.1）

| 文件 | 原 SHA256 | 现 SHA256 | 说明 |
|---|---|---|---|
| `PROTOCOL_ON2.md` | `D990BD0ABD73E4C2CF59ADA6962509DEB3C91AB7B549F259D34164394CDEFF51`（v2 FROZEN） | `8A3E065FFE80863DD1B723D03E9DB49F5464C053519F024A4066B7369584CCFF`（v2.1） | 仅按本文件 §2 的 5 条修订；原 v2 文本作为历史记录保留（before/after 见 §2） |
| `on2.py` | `59ED8FFAAD9D0874E85AB52DF46B1E5BDA74B8C950FDC5963C79B7B5A93B745B` | 不变 | 未改 |
| `on2.json` | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` | 不变 | 未改；门级数字保持 |
| `report_on2.md` / `record_on2.md` | — | 不变 | 保持 v2 历史；**由 `report_on2_1.md`/`record_on2_1.md` 取代**（v2 报告中 3 处描述统计为 v1 数字，见 §2.1） |
| `usage_on2.json` | `F23FECC27C8494E70E03A75B9B8666CB0D24B24535C6145309BE615BAF3D37BF` | 不变 | 未改 |
| ON1 全部产物 | — | 不变 | 未改；v1 `data_unavailable`、AMENDMENT 不冻结记录保留 |

## 2. 5 条必改的落实（before → after）

### 2.1 ① report/record 的 v1 数字复用（FAIL → 已修）

- **问题（challenge §5.1）**：`report_on2.md:48/50`、`record_on2.md:38` 用了 on1.json 的 v1 描述统计（mean 169.2/max 666；min 28/median 324/max 666；9,581–12,430/median 12,430），违反"v1 数字不得沿用"。
- **修复**：`report_on2_1.md` 全部改用 **v2 实测（on2.json，已与 challenge 独立重算一致）**：
  - per-context（batch1 全细胞，n=**2,791**）：min **1**、median **153**、mean **158.3185**、max **630**；
  - per (cell,partner) 合并角色（batch1 全细胞，n=**1,481**）：min **21**、median **291**、mean **298.3572**、max **630**；
  - 每目标细胞单元 Δ（n=**30**）：min **9,047**、median **11,623**、max **11,623**；
  - 附目标细胞子口径（避免混淆）：per-context（n=2,149）mean 158.2541/max 630；per (cell,partner)（n=1,139）min 28/median 291/max 630。
- **v1 数字只保留在 `report_on2_1.md` §7 的 v1-vs-v2 披露表**，不进入任何 v2 描述统计。
- 核对 `report_on2.md:38` 的 batch1/batch3 pair-cell 表述：**315 个 32 行 pair-cell = 309 个在 batch1+batch3 各 16 行 + 6 个在 batch2+batch3 各 16 行**（`on2.json → cohort.pair_cell_rows_distribution_raw` 的 raw 分组是 per batch 的 16 行）。

### 2.2 ② v1.1 成员规则对齐 + 排除计数（FAIL → 已修）

- **二选一写死：选"≥95% 的 16 行 **且** ≥12/16"**（16 行下 ≥95% 即 16/16；≥12/16 作为冗余保留审计）。写入 `PROTOCOL_ON2.md` v2.1 §3.3(1)；**不再**只有"≥12/16"。
- **重算/重述（与 challenge 独立重算一致）**：
  - 成员上下文 **45,948 / 46,104 = 99.66%** 满足行内 ≥95%；
  - **失败上下文 156 个**，行内比例均为 **15/16 = 93.75%** —— **明确 93.75% 不满足行内 ≥95%**（只由上下文级 95% 容许）；对应 **78 个 k=1 行 × 2 个角色方向 = 156**；
  - **被排除成员/单元计数**：排除成员上下文 **156**（all batches all cells；batch1 目标 **118**）；被排除 Δ 单元 **3,727**（all）/ **2,852**（batch1 目标）；排除后上下文降到 <2 可用成员 = **0**；
  - 敏感性 Δ 单元 = **470,179 / 468,393 / 360,452**（all / batch1 / batch1-target）。
- **标签修正**：**98.44%（全表）与 99.81%（batch1-target）是 all-4 完整率（AMENDMENT v1.1 口径），不是 all-available 覆盖率**；all-available cohort（≥1 非空重复）覆盖率 = **100%（368,832/368,832；viability1 无缺失）**；行可用重复数 k 分布：k=1 **78**、k=2 **120**、k=3 **5,544**、k=4 **363,090**。

### 2.3 ③ MI 计划（FAIL → 已修）

- **原问题**：行均值插补是确定性的，m=20/seed 无意义、无 Rubin 方差。
- **修复（选"确定性单插补"路径）**：`PROTOCOL_ON2.md` v2.1 §3.3(2) 改为 **"确定性行均值单插补敏感性（不是多重插补）"**：单次确定性插补（缺失行值 = 非空技术重复行均值），**删除 m=20、seed `20261120`、Rubin within/between 方差声明**；结构约束 batch/cell/partner/dose-row（不跨端点/跨研究）；本轮不运行（metadata-only）；执行期作为敏感性、与 complete-case 主结果并列。

### 2.4 ④ σ_e 分半冻结（WEAK → 已写死）

`PROTOCOL_ON2.md` v2.1 §3.2 DSG2(b) 写死：
- **固定重复索引**：列序 `viability1, viability2, viability3, viability4`；每行只在非空重复索引中按固定列序取前 `h1=⌈k/2⌉` vs 余 `h2=k−h1`；**禁止按观测值排序/分半**；
- k=4 → {v1,v2} vs {v3,v4}（2+2）；k=3 → 前两可用索引 vs 余 1 个（2+1）；k=2 → {第一个可用} vs {第二个可用}（1+1）；**k=1 行（全表 78 行）不参与标定并计数**；
- `σ̂_e² = Σ(Δ_h1−Δ_h2)² / Σdenom`，`denom = Σ_{两成员}Σ_{16 行}(1/h1+1/h2)/16²`（complete-case 每单元 = 1/8）；`SE_unit=σ̂_e/√32`、`MDE80=2.801585·SE_unit/√n_eff`；**实测 MDE80>δ_min=0.10 → `design_invalid: precision_insufficient` 停**；
- **执行期顺序与 schema 冻结**：先输出标定报告（cohort、units_used、rows_used、rows_excluded_k1、units_excluded、σ̂_e、SE_unit、MDE80、n_eff），再判 MDE 门，最后才决定是否运行效果协议；
- σ_e 借用来源锚点：0.041 = A0/R4 σ_e=0.0408；0.058 = A2 `q2.json` single-key σ=√0.003351；0.109 = A2 `noise_variance_mean_per_observation`=0.011968 的平方根（**仅期望、不作资格证据**）。

### 2.5 ⑤ 门语义/冻结措辞（WEAK → 已修）

- `PROTOCOL_ON2.md` §3 标题与 DG3 改为：**DG1/DG2/DSG 阈值不变；DG3 由 v1 完整性门改为 complete-case 路径 A 的披露门——人群/门语义变更，不是阈值放宽**；DG3 通过条件 = 路径 A 人群已声明 + 缺失披露完整 + 不假设 MCAR/MAR + 无响应相关选择 + v1.1 敏感性闭合定义。
- `report_on2_1.md` 与 `on2.json` 的关系：**protocol frozen (post-observation) / qualification verdict provisional pending independent challenge**；挑战通过后才写 final。
- 保留：v1 `data_unavailable`、AMENDMENT_ON1-001 不冻结、v1.1 仅敏感性、无"资源足够"表述、不称独立确认/迁移/决策收益/机制/新算法、不运行效果/更新器比较。

## 3. 证据（只读重算）

- 脚本：`tmp/_on2_1_recompute.py`（complete-case 统计 + v1.1 规则变体 + 排除计数；wall 38.4 s）、`tmp/_on2_1_recompute2.py`（per-context/per-(cell,partner)/per-cell/σ 分布；wall 47.9 s）。均只读身份/剂量/viability 空值掩码，**未读响应数值做统计**。
- 与 challenge 数字逐项核对一致：158.3185/630、21/291/630、9,047–11,623/11,623、45,948/46,104、156、360,452、98.44%/99.81%、k 分布、排除单元 3,727/2,852。
- **on2.json 与 challenge 独立重算的门级数字一致**（340,088/2,149/30/30/11,623/96.91%/66,556–69,738）。

## 4. 剩余缺口

- 需**同一挑战者（endpoint-auditor）只读复核** v2.1 修订后，才可冻结 v2 资格判定（挑战 §7）。
- 执行期仍需：σ_e 实测 + MDE 认证（先于任何效果协议）；确定性单插补敏感性；缺失机制未知（不假设 MCAR/MAR）；batch3 全失、702 个 15 行 pair-cell、无暴露时间/assay 列、单药参照未用、技术重复≠独立培养。
- **冻结 ≠ 资源足够/关系成立/Stage 1/效果**；效果协议须另立预注册 + 独立挑战。
