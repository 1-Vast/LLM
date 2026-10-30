# ERRATA_ON2_1 —— ON2 v2.1 的规范文件 / supersession / v1.1 基线勘误（ON2.2）

2026-10-27。角色：ON1/ON2 执行者（非挑战者）。依据：`challenge_ON2_1.md`（ON2.1 复核：**revise，3 条文档/披露必改；当前不可冻结；修完可 approve_freeze**；核心 5 条实质与门级数字均 PASS）、Lead 采用指令（task-65）。**本轮只做文档/披露修补：不重跑 on2.py、不改 on2.json/门级数字、不运行数据/效果/训练/更新器；未读响应值。**

## 0. 用途

本文件是 ON2 的 **supersession（取代关系）勘误**，用于消除"机器可读产物（on2.json）"与"v2.1 规范协议/报告"之间的不一致，并闭合 challenge_ON2_1 的 3 条必改：
1. 规范文件清单与 v2.0 历史文件标注；
2. `on2.json` 旧 MI 计划与旧 verdict 的 supersession 声明；
3. v1.1 排除 Δ 单元的**诊断基线**、scope 口径（all / b1-all / b1-target）、b1-all 排除成员上下文数、以及 315=309+6 与成员上下文定义。

**冲突裁决规则：任何歧义以 `PROTOCOL_ON2.md`（v2.1）与 `report_on2_1.md` 为准；`on2.json` 仅作为 v2.0 门级资格数字的机器记录保留（其门级数字有效且未改），其 MI/verdict 字段是历史，不得引用/执行。**

## 1. 规范文件（v2.1，冻结后引用这些）

| 文件 | 状态 | SHA256 |
|---|---|---|
| `PROTOCOL_ON2.md` | **v2.1 规范协议**（含 v2.1 补丁；post-observation，不是预注册） | 见 §4（v2.2 更新后） |
| `REVISION_ON2_1.md` | v2.1 修订记录（5 条 before/after、SHA 对照） | `65B8FFF98334594EAD69E3BB3DF96923E55A286B4C681E4FE1757FCCF4694D42` |
| `report_on2_1.md` | **v2.1 规范报告**（取代 report_on2.md） | 见 §4 |
| `record_on2_1.md` | v2.1 审计记录 + 冻结文本 | 见 §4 |
| `usage_on2_1.json` | v2.1 复现预算/取证 | 见 §4 |
| `ERRATA_ON2_1.md` | 本文件（supersession/基线勘误） | 见 §4 |
| `on2.py` / `on2.json` / `usage_on2.json` | **v2.0 数据产物，未改**（门级数字有效；MI/verdict 字段历史，见 §2） | `59ED8FFA…` / `AD7E6D13…` / `F23FECC2…` |
| `report_on2.md` / `record_on2.md` | **v2.0 历史文件**（含 v1 描述统计 169.2/666、28/324/666、9,581–12,430；**不得作为冻结引用**） | `BEFB0B83…` / `B29050AA…`（未改） |
| `PROTOCOL_ON1.md` / `on1.py` / `on1.json` / `report_on1.md` / `record_on1.md` / `usage_on1.json` | v1 历史（v1 verdict `data_unavailable` 保留） | 未改 |
| `AMENDMENT_ON1-001.md` | **不冻结**（ON1-C1 判事后门槛放宽；仅历史记录） | `E13489B9…`（未改） |
| `challenge_ON1_amendment.md` / `challenge_ON2.md` / `challenge_ON2_1.md` | 独立挑战文件（挑战者产物；只读引用） | 未改 |

## 2. `on2.json` 的 supersession（必改 1）

- **历史字段（v2.0，不得引用/执行）**：
  - `on2.json → missingness_and_sensitivity.multiple_imputation_plan`：仍含 `m=20`、`seed=20261120`、"frozen plan"、Rubin 相关措辞——这是 **v2.0 历史**。
  - `on2.json → verdict.verdict`：仍写 `design_frozen_qualified_with_conditions`（**无 provisional 标记**）——这是 **v2.0 历史**。
- **v2.1 规范（以协议/报告为准）**：
  - 插补敏感性 = **确定性行均值单插补（不是多重插补）**：单次确定性插补、无随机、无 m、无 seed、无 Rubin 方差；执行期运行、与 complete-case 主结果并列（见 `PROTOCOL_ON2.md` v2.1 §3.3(2) / `report_on2_1.md` §4）。
  - 判定 = `design_frozen_qualified_with_conditions` **（provisional pending independent challenge；挑战通过后冻结）**（见协议 §4、report §0/§8）。
- `report_on2_1.md` 中"已删除 MI"的措辞**限定为：从 v2.1 协议/报告中删除**；`on2.json` 保留 v2.0 历史字段但 **superseded**（本文件），不重跑、不改写 on2.json。

## 3. v1.1 排除 Δ 基线 / scope / b1-all / 315=309+6（必改 2）

### 3.1 定义

- **成员上下文** = `(batch, cell, partner, partner_role, member)` 的 **16 行**（4 partner doses × 4 member doses）网格；"排除 156 个"是**成员上下文数**，不是 member pair 数、不是成员数。
- **rule A（资格敏感性规则，写死）**：成员可用 = 16 行齐全 **且 ≥95% 的 16 行有 ≥2 非空重复（=16/16）且 ≥12/16 行有 ≥2 非空重复**。
- **rule B（仅 ≥12/16；诊断基线，不是资格规则）**：成员可用 = 16 行齐全 **且 ≥12/16 行有 ≥2 非空重复**。rule B 下无成员被排除（45,948+156 = 46,104 全可用）。
- **排除 Δ 单元数 = rule B（无排除，诊断基线）units − rule A units**。

### 3.2 数字（只读重算，与 challenge 核对一致）

| scope | rule B units（诊断基线，无排除） | rule A units（敏感性） | 排除 Δ 单元 = B−A | 排除成员上下文 |
|---|---:|---:|---:|---:|
| all batches all cells | **473,906** | **470,179** | **3,727** | **156** |
| batch1 all cells (b1-all) | **472,116** | **468,393** | **3,723** | **154** |
| batch1 target cells | **363,304** | **360,452** | **2,852** | **118** |

- **rule B 仅诊断基线**：其 b1-target units **363,304 与 v1 的 363,304 相同**（v1 只应出现在 v1-vs-v2 披露表），**不是 v2.1 资格数**；v2.1 资格数 = DG1 的 340,088（complete-case），与 rule B 无关。
- **b1-all 口径**：只读重算得排除成员上下文 **154**（batch1；batch2 为 2；all=156；b1-target=118）——**Lead/challenge 提到的"152"无法复现**（可能口径差异）；本文件按重算 **154** 记录并采用 all/b1-all/b1-target 三口径；**152 不采用**。排除后上下文降到 <2 可用成员 = **0**（三个 scope 均 0）。
- **all-4 完整率 vs all-available 覆盖率**（v2.1 标签）：98.44%（全表 363,090/368,832）与 99.81%（batch1-target 275,412/275,936）是 **all-4 完整率**；all-available cohort（≥1 重复）覆盖率 = **100%**（368,832/368,832）；k 分布 1:78、2:120、3:5,544、4:363,090。

### 3.3 315 = 309 + 6（来源）

- 原始数据里 **315 个 pair-cell 跨两个 BatchID 各测 16 行（32 行）**：其中 **309 个在 batch1+batch3**、**6 个在 batch2+batch3**（`on2.json` 的 `cohort.pair_cell_rows_distribution_raw` 与 batch pair-cells 计数：batch1 22,410 / batch2 327 / batch3 315；309+6=315；complete-case unique raw 分组 22,737 = 22,410+327，batch3 的 315 全部与 batch1/2 重叠）。该 split **不在 on2.json**，来自执行者只读重算（`tmp/on2_1_recompute2.log`/`tmp/_on2_2_check.py`）；引用时注明来源。**315 是 pair-cell 数，不是成员上下文数。**

## 4. 文件 SHA（本 errata 写入时）

| 文件 | SHA256（v2.2 更新后） |
|---|---|
| `PROTOCOL_ON2.md` | 见 `record_on2_1.md` §8（v2.2；旧 v2.1 `8A3E065F…84CCFF`） |
| `report_on2_1.md` | 见 `record_on2_1.md` §8（v2.2；旧 v2.1 `C98D398E…4E11E5`） |
| `record_on2_1.md` | 见 `record_on2_1.md` §8 |
| `usage_on2_1.json` | 见 `record_on2_1.md` §8 |
| `ERRATA_ON2_1.md` | 见 `record_on2_1.md` §8 |

## 5. 边界

- 未运行效果/训练/更新器比较；未重跑 on2.py、未改 on2.json/on2.py/ON1 产物；未读响应值做统计。
- **冻结 ≠ 资源足够/关系成立/Stage 1/效果**；v1 `data_unavailable` 保留；AMENDMENT_ON1-001 不冻结；v1.1 仅敏感性；不称独立确认/迁移/决策收益/机制/新算法；不与 Jaaks ΔEMAX 拼接；技术重复≠独立培养；仅 O'Neil 内部开发性、仅 viability。
- 本文件修完 3 条后，由**同一挑战者（endpoint-auditor）只读确认**即可 approve_freeze（无需再跑数据）。
