# R199-ON2.1/ON2.2 审计记录（record_on2_1；含冻结文本草案）

角色：ON1/ON2 执行者（非挑战者，未参与 challenge_ON1/challenge_ON2/challenge_ON2_1 评审）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-core-module-design/oneil_dev/`（v2.1/v2.2 文件 + `PROTOCOL_ON2.md` 的 v2.1/v2.2 补丁）与 `tmp/`；**未改** ON1 产物、`on2.py`、`on2.json`、`usage_on2.json`、`report_on2.md`/`record_on2.md`（v2.0 历史记录保留）、其它目录/INDEX/SYNTHESIS/git。

## 1. 范围与依据

- 对象：**R199-ON2.1**（按 `challenge_ON2.md` 5 条必改修报告/定义/执行条款，task-63）与 **R199-ON2.2**（按 `challenge_ON2_1.md` 3 条文档/披露必改修规范文件/supersession/基线，task-65）。**不重跑效果、不改门级资格数字、不重跑 on2.py。**
- 依据：`challenge_ON2.md`（ON2 挑战：revise ≤5；核心数字成立）；`challenge_ON2_1.md`（ON2.1 复核：revise，3 条文档/披露必改；核心 5 条实质与门级数字 PASS；修完可 approve_freeze）；Lead 采用指令（task-63/task-65）。
- 边界：不运行效果/训练/更新器比较；viability1–4 只作空值掩码；不读响应数值做统计；不改 on2.json 门级数字。

## 2. 时间线（本机，Asia/Shanghai）

| 时间 | 事件 |
|---|---|
| 20:30 | 接手 task-63；读 `challenge_ON2.md`（5 条必改 + 独立重算对照） |
| 20:31–20:35 | ON2.1 只读重算：`tmp/_on2_1_recompute.py`（38.44 s）、`tmp/_on2_1_recompute2.py`（47.94 s）；与 challenge 数字逐项核对一致 |
| 20:35–20:37 | `PROTOCOL_ON2.md` v2→v2.1；写 `REVISION_ON2_1.md`、`report_on2_1.md`、`record_on2_1.md`、`usage_on2_1.json` |
| 20:44 | 接手 task-65；读 `challenge_ON2_1.md`（3 条必改：on2.json 旧 MI/verdict supersession；v1.1 排除基线/b1-all/315=309+6；§6 交付清单） |
| 20:45–20:46 | ON2.2 只读重算 `tmp/_on2_2_check.py`（wall **40.52 s**）：rule B vs rule A units、b1-all 排除成员上下文、315=309+6 来源 |
| 20:46 | 写 `ERRATA_ON2_1.md`（规范文件/supersession/基线勘误） |
| 20:47 | `PROTOCOL_ON2.md` v2.1→v2.2（§3.3(1) 闭合基线、§6 交付/规范清单、v2.2 errata 注记；old SHA `8A3E065F…` → new `7B34DB79…`）；`report_on2_1.md` v2.2（canonical/supersession、成员上下文定义、315=309+6 来源、基线表、MI 措辞限定、SHA 表） |
| 20:48 | 更新 `usage_on2_1.json`；写本 record（含 §10 冻结文本草案）；核对 SHA |

## 3. 命令、预算与实际耗时

| 命令 | 实测 |
|---|---|
| ON2.1 `tmp/_on2_1_recompute.py` | wall **38.44 s**（只读） |
| ON2.1 `tmp/_on2_1_recompute2.py` | wall **47.94 s**（只读） |
| ON2.2 `tmp/_on2_2_check.py` | wall **40.52 s**（只读：rule B/A、b1-all、315=309+6） |
| patch/diagnostic 脚本 | ≈2.4 s |
| **合计（ON2.1+ON2.2）** | ≈**129.3 s**（见 `usage_on2_1.json`）；**未重跑 `on2.py`** |

- **未运行**任何效果/训练/更新器比较；未读响应值做统计；未联网。

## 4. ON2.1：5 条必改的落实（摘要）

1. **描述统计改 v2 实测**：158.3185/630、21/291/630、9,047–11,623/11,623；v1 值只留 v1-vs-v2 披露表。
2. **v1.1 规则写死 rule A**（≥95% 的 16 行 且 ≥12/16）：45,948/46,104=99.66%；156 个 15/16=93.75%；排除计数；all-4 完整率 98.44%/99.81% vs all-available 覆盖 100%；k=1 78 行。
3. **MI → 确定性行均值单插补**：删 m=20/seed/Rubin（仅协议/报告层面；on2.json 历史字段见 §5.1/ERRATA）。
4. **σ_e 分半冻结**：固定重复索引（viability1–2 vs 3–4，禁按值排序）；k=4→2+2、k=3→2+1、k=2→1+1、k=1 排除（78 行）计数；denom/SE/MDE/执行顺序/stop 写死。
5. **DG3 路径 A 披露门**（DG1/DG2/DSG 阈值不变，门语义变更非阈值放宽）；verdict 标 provisional pending challenge；保留 v1 `data_unavailable`、AMENDMENT 不冻结、v1.1 仅敏感性、无"资源足够"。

## 5. ON2.2：3 条文档/披露必改的落实（本轮新增）

### 5.1 规范文件 / supersession（必改 1）

- `PROTOCOL_ON2.md` v2.2 §6 交付清单更新：**v2.1 规范（冻结后引用）** = `PROTOCOL_ON2.md`（v2.2）、`REVISION_ON2_1.md`、`report_on2_1.md`（规范报告）、`record_on2_1.md`（记录+冻结文本）、`usage_on2_1.json`、`ERRATA_ON2_1.md`；**v2.0 历史（不得作为冻结引用）** = `on2.py`/`on2.json`/`usage_on2.json`（未改、门级数字有效）、`report_on2.md`/`record_on2.md`（含 v1 描述统计）、`AMENDMENT_ON1-001.md`（不冻结记录）。
- 新增 **`ERRATA_ON2_1.md`** 明确：`on2.json → missingness_and_sensitivity.multiple_imputation_plan`（m=20/seed 20261120/Rubin）与 `on2.json → verdict.verdict`（无 provisional）是 **v2.0 历史字段**；v2.1 以协议/报告为准；**不得引用/执行旧 MI，不得把旧 verdict 当 final**。
- `report_on2_1.md` 中"已删除 MI"**限定为"从 v2.1 协议/报告中删除"**；`on2.json` 保留历史字段但 superseded（本文件 + ERRATA）。

### 5.2 v1.1 排除 Δ 基线 / b1-all / 315=309+6（必改 2）

- **闭合定义**：**排除 Δ 单元 = rule B（仅 ≥12/16，诊断基线、无排除）units − rule A units**。
- **数字（与 challenge 核对一致）**：

| scope | rule B（诊断基线） | rule A（敏感性） | 排除 Δ = B−A | 排除成员上下文 |
|---|---:|---:|---:|---:|
| all batches all cells | 473,906 | 470,179 | **3,727** | **156** |
| batch1 all cells (b1-all) | 472,116 | 468,393 | **3,723** | **154** |
| batch1 target cells | 363,304 | 360,452 | **2,852** | **118** |

- **rule B 仅诊断基线**：其 b1-target **363,304 与 v1 同数**，仅披露、**不是资格数/资格规则**；v2.1 资格数 = complete-case DG1 340,088。
- **b1-all 排出口径**：只读重算为 **154**（batch1；batch2 为 2；all=156；b1-target=118）；**"152" 无法复现、不采用**（已在协议/报告写明）。
- **成员上下文定义**：`(batch,cell,partner,role,member)` 的 **16 行**（4×4 网格）；156/154/118 是**成员上下文数**，不是 member pair/成员数。
- **315=309+6 来源**：315 个 pair-cell 跨两个 BatchID 各 16 行（32 行）——309 个 batch1+batch3、6 个 batch2+batch3（来源：on2.json batch pair_cells 22,410/327/315 + `cohort.pair_cell_rows_distribution_raw`，split 来自 `tmp/_on2_2_check.py` 只读重算）；complete-case unique raw 分组 22,737=22,410+327；**315 是 pair-cell 数，不是成员上下文数**。
- 0 个上下文在排除后降到 <2 可用成员（三 scope 均 0）。

### 5.3 冻结记录同步（必改 3）

- 规范文件清单、on2.json supersession、v1.1 基线写入本 record 的 §7–§10 与 ERRATA；冻结文本草案见 §10。
- 保留：v1 `data_unavailable`、AMENDMENT_ON1-001 不冻结、v1.1 仅敏感性、无"资源足够"、不运行效果/更新器。

## 6. 验证与数字（与 challenge/on2.json 一致；门级未变）

- 门级：363,090/368,832=98.44%；缺失 0/78/198/5,742；batch1 357,876 / batch2 5,214 / batch3 0；702×15 行 pair-cell；DG1 **340,088 / 2,149 / 30-30 / 11,623**；DG2 **44,070/45,474=96.91%**；5 折 **66,556–69,738**（427–432）；strict-row 1,429,518/8,596；σ 先验保守格 0.02203838。
- 描述统计：158.3185/630；21/291/630；9,047–11,623/11,623。
- v1.1：45,948/46,104=99.66%；156 个 15/16；rule B/A units 473,906/472,116/363,304 − 470,179/468,393/360,452 = 3,727/3,723/2,852；成员上下文排除 156/154/118；排除后 <2 可用成员 0；"152" 不采用。
- **未重跑 on2.py；on2.json/on2.py 未改**（hash 见 §8）。

## 7. 决定

1. **ON2.1 的 5 条实质保持**（描述统计、rule A、确定性单插补、σ_e 分半、DG3 语义）。
2. **ON2.2 为文档/披露修补**：on2.json 保持 v2.0 历史（不重写、不重跑），以 ERRATA/supersession 消除矛盾；v1.1 排除基线闭合到 rule B−rule A；补 b1-all（154，152 不采用）与 315=309+6 来源；§6 交付清单改为 v2.1 规范文件 + v2.0 历史标注。
3. **冻结状态**：qualification verdict = `design_frozen_qualified_with_conditions`，**provisional pending independent challenge**；修完 3 条后由同一挑战者只读确认即可 approve_freeze（无需再跑数据/效果）。
4. 保留 v1 `data_unavailable`、AMENDMENT 不冻结、v1.1 仅敏感性、无"资源足够"；不运行效果/更新器；不称独立确认/迁移/决策收益/机制/新算法。

## 8. SHA（v2.2 更新后）

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_ON2.md`（v2.2；原 v2 `D990BD0A…`、v2.1 `8A3E065F…`） | `7B34DB796C9E1B7362722A553B155285E4E1E84686A7DE1A8B33CEF5120B2BA7` |
| `ERRATA_ON2_1.md`（新） | `3C6138DF7BA1ACCDC7088FC78070F835D6DF61D0E7BBF77EF6B4DE0E0FE7870B` |
| `report_on2_1.md`（v2.2） | `C6CF64677658AB18F91EA956F236E34DFE0B890431456F5908A30D47B7D569EE` |
| `usage_on2_1.json`（v2.2） | `97A96FCCDB0F0858C68351D2A28531D8ECCB2303A9142E7FA1930B63CE44BC60` |
| `REVISION_ON2_1.md`（未改） | `65B8FFF98334594EAD69E3BB3DF96923E55A286B4C681E4FE1757FCCF4694D42` |
| `record_on2_1.md` | 本文件（SHA 由复核方重算） |
| `on2.py`（未改，v2.0 数据产物） | `59ED8FFAAD9D0874E85AB52DF46B1E5BDA74B8C950FDC5963C79B7B5A93B745B` |
| `on2.json`（未改，v2.0 数据产物；MI/verdict 字段历史） | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` |
| `usage_on2.json`（未改，v2.0 历史） | `F23FECC27C8494E70E03A75B9B8666CB0D24B24535C6145309BE615BAF3D37BF` |
| `report_on2.md` / `record_on2.md`（v2.0 历史） | `BEFB0B83…FDDCA01` / `B29050AA…E50700A`（不变；不得作为冻结引用） |
| `on1.json`（未改） | `2E793902395C1902C80E8C3D936DE0815AF5B023EB42DD94BC8CDB5F776A3412` |
| `PROTOCOL_ON1.md`（未改） | `3C27CB94C68D40D24FCF736F6107AD76FE5C6599A1AFB04DB75D3BBA099E9EEC` |
| `AMENDMENT_ON1-001.md`（未改；不冻结） | `E13489B95603B3CA5EE0BD4D08377E3A824195D92DC6BBFB1514F3927A6FD290` |

- 只读重算/检查脚本 SHA（`tmp/`）：`_on2_1_recompute.py` `736337F7…42C43DF`、`_on2_1_recompute2.py` `0BDF8173…6242BFF8`、`_on2_2_check.py` `94A03CEA…1AF76993`；输入组合工作簿 `A0E2E002…C14818`。

## 9. 偏离/限制

- `PROTOCOL_ON2.md` 经 v2.1→v2.2 两次补丁（原 v2 SHA `D990BD0A…` 保留为历史，v2.1 `8A3E065F…` 保留为历史，v2.2 `7B34DB79…` 为现行）；`report_on2_1.md` 同步 v2.2；`on2.py`/`on2.json` 未重跑未改。
- 未运行效果/训练/更新器/反馈；未读响应数值；未改其它目录/INDEX/SYNTHESIS/git；未联网。
- 剩余缺口：**还需同一挑战者（endpoint-auditor）只读确认 v2.2 后 approve_freeze**；执行期 σ_e 实测 MDE 认证先于效果协议；确定性单插补敏感性执行期运行；缺失机制未知、batch3 全失、702 个 15 行 pair-cell；无暴露时间/assay 列；单药参照未用；技术重复≠独立培养。
- **冻结 ≠ 资源足够/关系成立/Stage 1/效果证据**。

## 10. 冻结文本草案（approve_freeze 版；待同一挑战者只读确认后生效）

> **ON2 v2.1/v2.2 判定：`design_frozen_qualified_with_conditions`（post-observation protocol revision；frozen after independent challenge）。**
> 本判定是**看到 ON1 v1 DG3 失败后的新协议（v2/v2.1/v2.2）**，**不是预注册**；v1 `data_unavailable` 记录保留；`AMENDMENT_ON1-001` **不冻结**；v1.1 **仅敏感性**；**无"资源足够"表述**。
> **规范文件（v2.2）**：`PROTOCOL_ON2.md`（SHA `7B34DB79…0B2BA7`）、`report_on2_1.md`、`record_on2_1.md`、`REVISION_ON2_1.md`、`usage_on2_1.json`、`ERRATA_ON2_1.md`；`on2.py`/`on2.json`/`usage_on2.json` 未改（v2.0 历史产物，门级数字有效）；**`on2.json` 的 MI（m=20/seed/Rubin）与旧 verdict 为 v2.0 历史字段，v2.1 以协议/报告为准，不得引用/执行旧 MI**。
> **complete-case 主分析**：363,090/368,832=98.44%；DG1 340,088/2,149/30/11,623；DG2 44,070/45,474=96.91%；DSG1 66,556–69,738/427–432；DG3 为路径 A 披露门（DG1/DG2/DSG 阈值不变；人群/门语义变更，非阈值放宽）。
> **v1.1 敏感性（rule A）**：45,948/46,104=99.66%；156 个 15/16 失败上下文；排除成员上下文 156（all）/154（b1-all）/118（b1-target）；**排除 Δ = rule B−rule A：473,906/472,116/363,304 − 470,179/468,393/360,452 = 3,727/3,723/2,852**；rule B 仅诊断基线（b1-target 363,304 与 v1 同数、仅披露、非资格数）；"152" 不采用；成员上下文 = `(batch,cell,partner,role,member)` 的 16 行；315=309+6 来源见 `ERRATA_ON2_1.md`。
> **条件**：仅 O'Neil 内部开发性、仅 viability；技术重复≠独立培养；不称独立确认/迁移/决策收益/机制/新算法；不与 Jaaks ΔEMAX 拼接；执行期必须先做 σ_e 固定索引分半标定 + MDE 认证（MDE>0.10 → `design_invalid: precision_insufficient` 停）；确定性行均值单插补敏感性执行期运行；缺失机制未知（不假设 MCAR/MAR）；batch3 全失、702 个 15 行 pair-cell；无"资源足够"。
> **冻结 ≠ 资源足够/关系成立/Stage 1/效果证据；不运行效果/更新器比较；效果协议须另立预注册 + 独立挑战。**

## 11. 未做 / 明确不做

- 未训练/未拟合/未估效果/未比较更新器/未做 acquisition/Agent/反馈实验；未重跑 `on2.py`/数据/效果；未改 `on2.json`/`on2.py`/ON1 产物；未声称新颖性；未写机制/迁移/决策收益；阴性/不足完整记录。
