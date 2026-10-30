# R199-ON2 审计记录（record_on2）

角色：独立设计/资格复核 runner（非提案者；不参与效果设计）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-core-module-design/oneil_dev/`（v2 新文件）与 `tmp/`；**未改** v1 文件（PROTOCOL_ON1.md/on1.py/on1.json/on1 报告记录）、AMENDMENT_ON1-001、challenge_ON1_amendment.md、Q0 产物、其它目录、INDEX、SYNTHESIS、git。

## 1. 范围与依据

- 对象：**R199-ON2 —— O'Neil complete-case v2 协议（设计 + 资格重算；不运行效果/不训练/不比较更新器）**。
- 依据（只读）：ON1-C1 独立挑战 `challenge_ON1_amendment.md`（revise；**AMENDMENT_ON1-001 不冻结**；推荐路径 A=complete-case；其独立只读重算：363,090 行/340,088 单元/2,149 上下文/每折 66,556–69,738/DG2 96.91%/30 细胞）；Lead 采用指令（task-61）；R199-Q0（PROTOCOL_Q0/q0.json/report_q0）；R199 BRIEF；SYNTHESIS C178–C181；v1 on1.json/on1.py。
- 冻结协议：本目录 `PROTOCOL_ON2.md`（v2，**在任何 ON2 资格计数之前冻结**；性质=post-observation protocol revision，非预注册）。
- 边界：metadata-only；viability1–4 仅作**空值掩码**（cohort/缺失模式），响应数值未进入任何统计；不运行效果/更新器；不写机制/迁移/决策收益/新颖性。

## 2. 时间线（本机，Asia/Shanghai）

| 时间 | 事件 |
|---|---|
| 20:14 | 读 task-61 与 `challenge_ON1_amendment.md`（ON1-C1：revise；AMENDMENT 不冻结；路径 A=complete-case；其重算数字） |
| 20:15 | 写 **`PROTOCOL_ON2.md`（v2 FROZEN）**：complete-case cohort、缺失披露、DG1/DG2/DG3/DG4/DG5 复算、DSG1、σ_e/MDE 执行条款、缺失机制/敏感性、边界/措辞 |
| 20:16–20:19 | 写 `on2.py`；修复 1 个实现错误（分支统计的成员列名）并成功运行（~39 s）→ v2 资格数 |
| 20:19 | 修 **严格同 partner-dose 行**口径实现错误（初版 `n_mdose==n_rows` 会把 complete-case 下 3/4 行误当"完整"）；改为要求 **4/4** member-dose 行；仅影响 strict-row 披露数，不改门/主资格数；重跑 |
| 20:20:10 | **确定性重跑**：`on2.json` 与上一跑**逐字节一致**（SHA256 `AD7E6D13…`）；wall 39.7 s |
| 20:2x | 写 `report_on2.md`、本 record、核对 SHA/双跑一致 |

## 3. 命令、预算与实际耗时

| 命令 | 实测 |
|---|---|
| `D:\anaconda\envs\maestro\python.exe -X utf8 research\2026-10-27-core-module-design\oneil_dev\on2.py`（`PYTHONHASHSEED=0`） | wall **39.1 s / 39.7 s**（成功两跑，含读 38 MB OOXML）；≤45 min 预算 |
| `python -m py_compile on2.py` | <1 s |

- CPU-only；无 GPU；无网络；输入总字节 239,550,399（见 usage_on2.json）；响应数值未读（仅空值掩码）。

## 4. 观测（关键事实，均写入 on2.json）

1. **complete-case cohort**：**363,090 / 368,832 = 98.44%**；batch1 357,876（丢 684）、batch2 5,214（丢 18）、**batch3 0（原 5,040 全失）**。缺失 viability1–4 = 0/78/198/5,742；共缺失模式：complete 363,090；`v2;v3;v4` 78；`v3;v4` 120；`v4` 5,544。
2. **pair-cell 结构**：complete-case 后 **702 个 pair-cell 仅剩 15 行**、315 个=0 行（batch3）、22,035 个=16 行；缺失 grid 位置（member-dose 位 × partner-dose 位 1–4）缺失率 1.37–1.87%（大致均匀）。
3. **DG1（complete-case、batch1、目标 30 细胞）**：**340,088** 单元 Δ / **2,149** 上下文 / **30/30** 贡献细胞 / 跨 ≥3 目标细胞上下文 **11,623**（v1 数字 363,304/12,430 仅披露、不沿用）。全 batch 442,996/2,927；batch1 全细胞 441,867/2,791；batch2 1,129/136。严格 partner-dose 行口径：batch1 目标 **1,429,518** 行级单元/8,596 上下文。
4. **DG2**：complete-case 成员上下文 **44,070/45,474 = 96.91%**（v1 为 100%）。
5. **跨细胞/每细胞**：11,623 个 `(p,ρ,{a,a'})` 在 batch1 覆盖 33–39 细胞（目标口径 25–30，全部 ≥3）；目标细胞单元 9,581–12,430/细胞；上下文 68–72/细胞。
6. **DSG1 5 折**（30 细胞 → 6/6/6/6/6）：每折单元 **[68,152, 66,743, 66,556, 69,738, 68,899]**（66,556–69,738）、严格行级 279,479–293,376、上下文 427–432。
7. **缺失机制/敏感性**：不假设 MCAR/MAR；complete-case 主 + v1.1 all-available 敏感性（闭合定义）：行级完整率双分母 98.44%（全表）/ **99.81%**（batch1-target 分析人群 275,412/275,936）；上下文级双 95%：**45,948/46,104=99.66%**；**156 个成员上下文行内比例 15/16=93.75%，不满足行内 ≥95%**（已单独计数；只在上下文级 95% 规则下被容许）；敏感性单元 470,179 / 468,393 / 360,452（仅敏感性）。MI 计划冻结（m=20、seed 20261120）但 metadata-only 不运行（需响应值）。
8. **σ_e/MDE**：借用先验表（σ_e∈{0.041,0.058,0.109}×n_eff∈{6,12,24,30}），保守格 0.02204（**仅期望，非资格证据**）；执行期 O'Neil viability1–4 分半标定条款（含缺失配对规则、complete-case k=4→2+2、all-available k≥2、1 重复行排除计数）与"MDE>δ_min→`design_invalid` 停"已冻结。
9. **v1 vs v2**：v1 363,304/71,004–74,580/100%/12,430（`data_unavailable`）vs v2 **340,088/66,556–69,738/96.91%/11,623**（v2 = `design_frozen_qualified_with_conditions`，post-observation，待独立挑战）。
10. **门控结果**：数据门 DG1/DG2/DG3/DG4/DG5 全 PASS；设计门 DSG1/DSG2a/DSG2b/DSG3/DSG4 全 PASS。无失败类别。

## 5. 决定

1. **路径 A = complete-case 主分析**（ON1-C1 推荐；不改 v1 数据完整性门槛、不做响应相关行选择；只按空值掩码限制人群）。
2. **v1 保持 `data_unavailable`**；AMENDMENT_ON1-001 **不冻结**（仅记录）；v2 = **post-observation protocol revision**（明写"不是预注册"）。
3. **所有资格数字 complete-case 重算**（340,088/2,149/66,556–69,738/96.91%/11,623）；**不沿用** v1 的 363,304/71,004–74,580/100%/12,430（只作披露对照）。
4. **缺失机制**：不假设 MCAR/MAR；complete-case 主；all-available 敏感性**闭合定义**（双分母/16 行单位/双 95% 分子分母/156 个 93.75% 失败上下文计数、"93.75% 不满足"表述修正）；MI 计划冻结、执行期运行。
5. **σ_e/MDE**：借用先验只作期望；执行期必须 O'Neil 分半实测（含缺失配对）并重算 MDE，>δ_min 即 `design_invalid` 停；不把 0.02204 当资格证据。
6. **措辞**：删除"资源足够"表述；只写"v1 DG3 是唯一阻塞；v2 complete-case 重算后资格门通过，但是否可用须经独立挑战与执行期实测 MDE"；不写独立确认/迁移/决策收益/机制/新算法。
7. **批次/边界**：batch1 主分析、batch2 披露、batch3 全失披露；9 个 Jaaks 重叠细胞排除、目标 30；仅 viability；不与 Jaaks ΔEMAX 拼接；技术重复≠独立培养。

## 6. 确定性与产物 SHA

- `PYTHONHASHSEED=0`；JSON 键排序、无时间戳、`allow_nan=False`；`on2.py` 从原始文件重算全部数字。
- 两跑 `on2.json` **逐字节一致**（SHA256 `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8`）。

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_ON2.md`（v2 FROZEN） | `D990BD0ABD73E4C2CF59ADA6962509DEB3C91AB7B549F259D34164394CDEFF51` |
| `on2.py` | `59ED8FFAAD9D0874E85AB52DF46B1E5BDA74B8C950FDC5963C79B7B5A93B745B` |
| `on2.json` | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` |
| `usage_on2.json` | `F23FECC27C8494E70E03A75B9B8666CB0D24B24535C6145309BE615BAF3D37BF` |
| `report_on2.md` / `record_on2.md` | 本报告/本记录（SHA 由审计方重算） |

- `on2.json → inputs`：组合工作簿 `A0E2E002…C14818`、单药工作簿 `4A0622C0…ED66DEC`、Jaaks（仅细胞名）`1188968C…FFA278`、PROTOCOL_ON1/ON2、on1.json、challenge_ON1_amendment、AMENDMENT_ON1-001、PROTOCOL_Q0/q0.json、R199 BRIEF、脚本 SHA。

## 7. 偏离/实现修正（终版前，已披露）

- **严格同 partner-dose 行口径实现修正**：初版用 `n_mdose==n_rows` 判定成员-行完整，在 complete-case 下会把 3/4 行的成员误当完整；终版要求 **4/4** member-dose 行。仅影响 strict-row 披露数（1,429,518 等），不改变任何门/主资格数/判定。
- **v2 性质**：属看到 v1 DG3 失败后的**新协议（post-observation revision）**，不称预注册；v1 记录保留。
- 未读响应值做统计（viability 仅空值掩码）；未运行效果/训练/更新器；未使用单药工作簿数值。
- MI 敏感性未运行（metadata-only 限制；计划冻结于 on2.json）。
- 未改 v1/AMENDMENT/challenge/Q0/其它目录/INDEX/SYNTHESIS/git；未联网。

## 8. 未做 / 明确不做

- 未训练/未拟合/未估效果/未比较更新器/未做 acquisition/Agent/反馈实验；未声称新颖性；未写机制/迁移/决策收益；阴性/不足完整记录。
- 未对 v2 作出最终解释（须经独立挑战）；未运行执行期 σ_e 标定/MDE 认证/MI 敏感性。
