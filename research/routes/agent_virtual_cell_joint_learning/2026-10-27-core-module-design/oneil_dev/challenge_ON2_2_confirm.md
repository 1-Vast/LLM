# R199-ON2.2 同一挑战者确认（challenge_ON2_2_confirm.md）——ON2.2 文档/披露修补复核

2026-10-27 · 挑战者：endpoint-auditor（与 `challenge_ON2.md`/`challenge_ON2_1.md` 同一人；未参与 ON2.2 修订）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON2.md（v2.2）, ERRATA_ON2_1.md, report_on2_1.md, record_on2_1.md, usage_on2_1.json}` + 未改的 `on2.py`/`on2.json`/`usage_on2.json`/ON1 产物。
方式：**只读审查**（文档/SHA/on2.json 历史字段核对；不运行数据/效果/训练，不重跑 on2.py，不读响应值）；只写本文件与 `tmp/`。
完整性：v2.2 协议 SHA `7B34DB79…0B2BA7`；`ERRATA_ON2_1` `3C6138DF…E7870B`；`report_on2_1` `C6CF6467…D569EE`；`record_on2_1` `789A0114…484694`；`usage_on2_1` `97A96FCC…44BC60`；`REVISION_ON2_1` 未改 `65B8FFF9…694D42`；`on2.py` `59ED8FFA…`、`on2.json` `AD7E6D13…`、`usage_on2.json` `F23FECC2…`、ON1 `on1.json` `2E793902…` 均未变——全部与 record §8/usage 声明一致。

## 0. 总判决

**approve_freeze。** ON2.1 复核提出的 3 条文档/披露必改已全部落实且自洽；5 条实质修订（v2.1）与门级资格数字保持不变；无需再跑数据/效果/on2.py。**v2 资格判定可冻结为 `design_frozen_qualified_with_conditions`（post-observation）；冻结文本见 §5（即 record_on2_1 §10 草案，经本确认后生效）。**

- **无剩余必改。** 仅有一处不影响冻结的版本文案小瑕疵（见 §6）：ERRATA §1/§0、protocol/report 标题仍把当前版本称作"v2.1"（实际文件为 v2.2 errata 层）；建议下次文档整理时统一为 v2.2，但 §6 已列 v2.2 规范文件与 SHA、冻结文本也已写 v2.2，故不阻断。
- **明确边界**：冻结 ≠ 资源足够/关系成立/Stage 1/效果证据；不运行效果/更新器比较；执行期仍需 σ_e 实测 MDE 认证与确定性单插补敏感性。

## 1. 逐条确认（PASS/FAIL）

### ① §6 交付清单 + on2.json 旧 MI/verdict superseded —— **PASS**

- `PROTOCOL_ON2.md` v2.2 §6（lines 95–98）已列出 **v2.1/v2.2 规范文件**：本协议（v2.1 + v2.2 errata 注记）、`REVISION_ON2_1.md`、**`report_on2_1.md`（规范报告）**、**`record_on2_1.md`（记录+冻结文本）**、`usage_on2_1.json`、**`ERRATA_ON2_1.md`**；并列出 **v2.0 历史（不得作为冻结引用）**：`on2.py`/`on2.json`/`usage_on2.json`（未改、门级数字有效）、`report_on2.md`/`record_on2.md`（含 v1 描述统计）、`AMENDMENT_ON1-001.md`（不冻结记录）。
- `ERRATA_ON2_1.md` §2 明确：`on2.json → missingness_and_sensitivity.multiple_imputation_plan`（m=20/seed/Rubin/"frozen plan"）与 `on2.json → verdict.verdict`（无 provisional）是 **v2.0 历史字段**；v2.1 以协议/报告为准，**不得引用/执行旧 MI**；旧 verdict 不是 final（v2.1 判定为 provisional pending challenge）。
- `report_on2_1.md:8` 与 `record_on2_1.md §5.1` 同步该 supersession；"已删除 MI"已限定为"从 v2.1 协议/报告删除；on2.json 保留历史字段但 superseded"（ERRATA §2 line38、report line86）。`on2.json` 未重写/未重跑，SHA 未变，符合"历史数据产物"处理。**PASS。**

### ② v1.1 排除基线/152/成员上下文/315 —— **PASS**

- 协议 §3.3(1) line74、report §3 lines74–80、record §5.2、ERRATA §3 均写清：
  - **排除 Δ 单元 = rule B（仅 ≥12/16，诊断基线、无排除）units − rule A units**；
  - **all 473,906 − 470,179 = 3,727**；**b1-all 472,116 − 468,393 = 3,723**；**b1-target 363,304 − 360,452 = 2,852**；
  - 排除成员上下文 **156（all）/154（b1-all）/118（b1-target）**（batch2=2；**"152" 无法复现、明确不采用**）；
  - **rule B 只是诊断基线，不是资格规则/资格数**；其 b1-target 363,304 与 v1 同数，只在披露表出现；
  - **成员上下文 = `(batch,cell,partner,role,member)` 的 16 行**（4 partner doses × 4 member doses；156/154/118 是成员上下文数，不是成员 pair/成员数）；
  - **315=309+6 来源**：315 个 pair-cell 跨两个 BatchID 各 16 行（32 行），309 个 batch1+batch3、6 个 batch2+batch3；来源 on2.json batch pair-cells 22,410/327/315 + `cohort.pair_cell_rows_distribution_raw`，split 来自执行者只读重算 `tmp/_on2_2_check.py`；complete-case unique raw 分组 22,737=22,410+327；**315 是 pair-cell 数，不是成员上下文数**；
  - **排除后上下文降到 <2 可用成员 = 0（三 scope）**。
- 数字与 challenge_ON2_1 的核对一致（all 3,727/3,723/2,852；156/154/118；rule B units 473,906/472,116/363,304；rule A 470,179/468,393/360,452）；b1-all 154 与 all 156/b1-target 118 的差值（batch2=2）自洽。**PASS。**

### ③ record §8/§10 冻结记录同步 —— **PASS**

- `record_on2_1.md` §8（lines 88–106）列出 v2.2 规范文件 SHA（协议/ERRATA/report/usage/REVISION/record）、v2.0 历史文件（on2.py/on2.json/usage_on2.json/report_on2/record_on2）、v1 与 AMENDMENT 未改；§10（lines 115–123）给出**冻结文本草案**，含规范文件/SHA、on2.json 历史 MI/verdict 说明、v1.1 rule B−rule A 基线、315=309+6、152 不采用、成员上下文定义、执行期条件与"冻结≠资源足够/关系成立/Stage1/效果"。
- 保留：v1 `data_unavailable`、AMENDMENT_ON1-001 不冻结、v1.1 仅敏感性、无"资源足够"、不运行效果/更新器。**PASS。**

### ④ 数字一致性 / 未变产物 —— **PASS**

- complete-case **363,090/368,832=98.44%**；缺失 0/78/198/5,742；batch1 357,876 / batch2 5,214 / batch3 0；702×15 pair-cell；DG1 **340,088 / 2,149 / 30/30 / 11,623**；DG2 **44,070/45,474=96.91%**；DSG1 **66,556–69,738 / 427–432**；strict-row 1,429,518/8,596；σ 先验保守格 **0.02203838**——report/record/protocol 与 on2.json 一致，v2.1 门级数字未变。
- `on2.py`/`on2.json`/`usage_on2.json`/ON1 SHA 未变；v2.2 只改文档/披露，未重跑 on2.py、未改门级数字。**PASS。**

### ⑤ 总判决 —— **approve_freeze**

- 3 条必改全部闭合；5 条实质（v2.1）保持；边界/措辞（仅开发性、仅 viability、技术重复≠独立培养、不称独立确认/迁移/决策收益/机制/新算法、不拼 ΔEMAX、v1/AMENDMENT/v1.1 状态、无"资源足够"）完整。
- **可以冻结 v2 资格判定**；冻结文本见 §5（与 record §10 一致，经本确认后由 Lead 记录生效）。
- 无需要再跑数据/效果/on2.py；若未来发现版本文案（见 §6）可做非阻断整理，不影响冻结。

## 2. 关键证据摘要

- 协议 v2.2 §6 交付清单 lines 95–98；§3.3(1) line74 基线表；§3.2 σ_e lines 53–60；§4/§5 provisional/边界 lines 80–91。
- `ERRATA_ON2_1.md` §2 supersession lines 30–38；§3 基线/152/315 lines 40–63；§5 边界 lines 75–79。
- `report_on2_1.md` §2.1 描述统计 lines 57–66；§3 基线表 lines 74–81；§4 MI lines 84–87；§5 σ_e lines 89–94；§8 边界 lines 112–118；§10 SHA lines 129–140。
- `record_on2_1.md` §5.1/§5.2 lines 46–67；§6 数字 lines 74–79；§8 SHA lines 88–106；§10 冻结文本 lines 115–123。

## 3. 通过项（保留，不应回退）

- 5 条 v2.1 实质：v2 描述统计（158.3185/630、21/291/630、9,047–11,623/11,623）；v1.1 rule A（≥95% 且 ≥12/16）与 45,948/46,104、156、排除计数、all-4 vs all-available 标签、k 分布；MI→确定性单插补（删 m=20/seed/Rubin，on2.json 历史字段 superseded）；σ_e 固定索引分半/禁排序/k 规则/78 k=1/denom/SE/MDE/执行顺序/stop；DG3 路径 A 披露门（DG1/DG2/DSG 阈值不变）、provisional、v1/AMENDMENT/v1.1 状态、无"资源足够"。
- v2.2 新增：§6 规范文件/v2.0 历史清单；on2.json 旧 MI/verdict supersession；v1.1 rule B−rule A 基线（3,727/3,723/2,852；156/154/118；152 不采用）；成员上下文定义；315=309+6 来源；record §8/§10 冻结文本同步。

## 4. 数字核对（approve 依据）

| 量 | 值 | 状态 |
|---|---:|---|
| complete-case | 363,090/368,832 = 98.44% | ✓ |
| DG1 units / contexts / cells / cross | 340,088 / 2,149 / 30-30 / 11,623 | ✓ |
| DG2 complete member contexts | 44,070/45,474 = 96.91% | ✓ |
| DSG1 fold units / contexts | 66,556–69,738 / 427–432 | ✓ |
| strict-row target | 1,429,518 / 8,596 | ✓ |
| σ_e prior conservative | 0.02203838 | ✓ |
| v1.1 rule A usable / total | 45,948 / 46,104 = 99.66% | ✓ |
| v1.1 failing contexts | 156 × 15/16 = 93.75% | ✓ |
| v1.1 excluded Δ (B−A): all / b1-all / b1-target | 3,727 / 3,723 / 2,852 | ✓ |
| v1.1 excluded member contexts: all / b1-all / b1-target | 156 / 154 / 118 | ✓ |
| rule B units (diagnostic): all / b1-all / b1-target | 473,906 / 472,116 / 363,304 | ✓ |
| rule A units (sensitivity): all / b1-all / b1-target | 470,179 / 468,393 / 360,452 | ✓ |
| "152" | 无法复现、不采用 | ✓ |
| 315 pair-cell split | 309 (batch1+batch3) + 6 (batch2+batch3) | ✓ |
| k distribution | 78 / 120 / 5,544 / 363,090 | ✓ |

## 5. 冻结文本（approve_freeze；与 record §10 一致）

> **ON2 v2.1/v2.2 判定：`design_frozen_qualified_with_conditions`（post-observation protocol revision；frozen after independent challenge）。**
> 本判定是**看到 ON1 v1 DG3 失败后的新协议（v2/v2.1/v2.2）**，**不是预注册**；v1 `data_unavailable` 记录保留；`AMENDMENT_ON1-001` **不冻结**；v1.1 **仅敏感性**；**无"资源足够"表述**。
> **规范文件（v2.2）**：`PROTOCOL_ON2.md`（SHA `7B34DB796C9E1B7362722A553B155285E4E1E84686A7DE1A8B33CEF5120B2BA7`）、`report_on2_1.md`（SHA `C6CF64677658AB18F91EA956F236E34DFE0B890431456F5908A30D47B7D569EE`）、`record_on2_1.md`（SHA `789A01149D7874BED454B6F5EC9F0CC274529438779B384E8EC11A1B07484694`）、`REVISION_ON2_1.md`、`usage_on2_1.json`、`ERRATA_ON2_1.md`（SHA `3C6138DF7BA1ACCDC7088FC78070F835D6DF61D0E7BBF77EF6B4DE0E0FE7870B`）；`on2.py`/`on2.json`/`usage_on2.json` 未改（v2.0 历史产物，门级数字有效）；**`on2.json` 的 MI（m=20/seed/Rubin）与旧 verdict 为 v2.0 历史字段，v2.1 以协议/报告为准，不得引用/执行旧 MI**。
> **complete-case 主分析**：363,090/368,832=98.44%；DG1 340,088/2,149/30/11,623；DG2 44,070/45,474=96.91%；DSG1 66,556–69,738/427–432；DG3 为路径 A 披露门（DG1/DG2/DSG 阈值不变；人群/门语义变更，非阈值放宽）。
> **v1.1 敏感性（rule A）**：45,948/46,104=99.66%；156 个 15/16 失败上下文；排除成员上下文 156（all）/154（b1-all）/118（b1-target）；**排除 Δ = rule B−rule A：473,906/472,116/363,304 − 470,179/468,393/360,452 = 3,727/3,723/2,852**；rule B 仅诊断基线（b1-target 363,304 与 v1 同数、仅披露、非资格数）；"152" 不采用；成员上下文 = `(batch,cell,partner,role,member)` 的 16 行；315=309+6 来源见 `ERRATA_ON2_1.md`。
> **条件**：仅 O'Neil 内部开发性、仅 viability；技术重复≠独立培养；不称独立确认/迁移/决策收益/机制/新算法；不与 Jaaks ΔEMAX 拼接；执行期必须先做 σ_e 固定索引分半标定 + MDE 认证（MDE>0.10 → `design_invalid: precision_insufficient` 停）；确定性行均值单插补敏感性执行期运行；缺失机制未知（不假设 MCAR/MAR）；batch3 全失、702 个 15 行 pair-cell；无"资源足够"。
> **冻结 ≠ 资源足够/关系成立/Stage 1/效果证据；不运行效果/更新器比较；效果协议须另立预注册 + 独立挑战。**

## 6. 非阻断小瑕疵（不影响 approve_freeze）

- **版本文案**：`ERRATA_ON2_1.md` §0 line12/§1 表仍称 `PROTOCOL_ON2.md`/`report_on2_1.md` 为 "v2.1 规范协议/报告"；protocol/report 标题仍写 "v2 + v2.1 补丁"（实际文件含 v2.2 errata 注记）。§6 已列 v2.2 规范文件与 SHA，record/冻结文本也写 v2.2；建议下次文档整理统一为 "v2.2（v2.1 + errata）"，**不阻断冻结**。
- `record_on2_1.md` 中 v2.2 patch 脚本 `tmp/_on2_2_patch.py` 未在 SHA 清单列出（仅 `_on2_2_check.py` 列出）；不影响冻结，可后续补登。
- 其余无。

## 7. 边界

- 本轮只读文档/SHA/on2.json 历史字段；**未运行数据/效果/训练/更新器，未重跑 on2.py，未读响应值**；只写本文件与 `tmp/`；未改 ON2/ON1 产物。
- 冻结只针对"资格/设计/披露/执行条款"；不产生生物学/效果结论；v1 `data_unavailable` 保持；v2.2 是 post-observation，不是预注册。
