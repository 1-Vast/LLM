# R199-ON2 报告：O'Neil **complete-case** 开发性内部细胞留出协议 v2（设计 + 资格复核，**不运行**）

2026-10-27。角色：独立设计/资格复核 runner（非提案者；不参与效果设计）。依据：ON1-C1 独立挑战 `challenge_ON1_amendment.md`（revise；**AMENDMENT_ON1-001 不冻结**；推荐路径 A=complete-case）、Lead 采用指令、R199-Q0（`qualification/{PROTOCOL_Q0.md, q0.json, report_q0.md}`：总体 `not_qualified`，O'Neil 唯一 `qualified_with_conditions`，仅开发性内部细胞留出）、R199 BRIEF、SYNTHESIS C178–C181。

- 交付：[PROTOCOL_ON2.md](PROTOCOL_ON2.md)（v2 FROZEN，**post-observation protocol revision；不是预注册**）· [on2.py](on2.py) · [on2.json](on2.json)（SHA `AD7E6D13…`）· [record_on2.md](record_on2.md) · [usage_on2.json](usage_on2.json)
- v1 记录保持：[PROTOCOL_ON1.md](PROTOCOL_ON1.md)（v1 FROZEN）、[on1.json](on1.json)（v1 verdict=`data_unavailable`）、[AMENDMENT_ON1-001.md](AMENDMENT_ON1-001.md)（**不冻结**，仅存记录）。**本任务不修改任何 v1/AMENDMENT/challenge 文件。**
- **本任务不运行效果、不训练、不比较更新器、不选药；viability1–4 只用作空值掩码（cohort/缺失模式），响应数值未进入任何统计。**

## 0. 判定（一屏）

**v2 判定 = `design_frozen_qualified_with_conditions`**（complete-case 主分析下全部数据门与设计门 PASS）；**性质 = 看到 v1 DG3 失败之后的新协议（post-observation revision），不是预注册**；**必须经独立挑战后才可解释/冻结**；不运行效果/更新器比较。

| 门 | v2 实测（complete-case） | 门槛 | 判定 |
|---|---|---|---|
| DG1 单元 Δ（batch1、目标 30 细胞） | **340,088** | ≥5,000 | PASS |
| DG1 贡献目标细胞 | **30/30** | ≥30 | PASS |
| DG1 `(cell,partner,role)` 上下文 | **2,149** | ≥200 | PASS |
| DG1 跨 ≥3 目标细胞 `(p,ρ,{a,a'})` 上下文 | **11,623** | ≥10 | PASS |
| DG2 完整成员上下文 | **44,070/45,474 = 96.91%** | ≥95% | PASS |
| DG3 缺失披露（不假设 MCAR/MAR） | 覆盖率 **98.44%**；缺失 78/198/5,742；batch3 全剔；**702** 个 pair-cell 只剩 15 行 | 披露完整 | PASS |
| DG4 目标细胞 / 30 全贡献 | **30 / 30** | 30 / 30 | PASS |
| DG5 目标 ∩ Jaaks | **0/30**（9 个重叠细胞排除） | 0 | PASS |
| DSG1 5 折（各 6 细胞）单元/折 | **66,556–69,738**（[68,152, 66,743, 66,556, 69,738, 68,899]） | ≥1,000 | PASS |
| DSG1 上下文/折 | **427–432** | ≥5 | PASS |
| DSG2a 借用 σ_e 先验期望（σ=0.109, n_eff=6） | **0.02204**（**仅期望，非资格证据**） | ≤δ_min=0.10 | PASS |
| DSG2b 执行期 σ_e 标定条款 | **已冻结**（O'Neil viability1–4 分半，含缺失配对；实测 MDE>δ_min→`design_invalid` 停） | 条款冻结 | PASS |
| DSG3/DSG4 端点/独立性边界 | 冻结 | — | PASS |

- **明确不写"资源足够"**：v1 仍是 `data_unavailable`；v2 只是"complete-case 人群下资格重算通过"的新协议结果，**须经独立挑战**，且不运行效果。
- **v1 数字不得沿用**：v1 的 363,304 / 71,004–74,580 / 100% / 12,430 只作披露对照（见 §5），**不是 v2 资格数**。

## 1. 主分析人群 = complete-case（冻结）

- **定义**：viability1–4 **四列全部非空**的行（只看空值掩码；不按响应/缺失与响应关系选择）。
- 行数：**363,090 / 368,832 = 98.44%**；batch1 **357,876**（原 358,560；丢 684）、batch2 **5,214**（原 5,232；丢 18）、**batch3 0**（原 5,040，viability4 全缺 → 整体消失，如实披露）。
- **缺失数**：viability1 **0**、viability2 **78**、viability3 **198**、viability4 **5,742**。
- **共缺失模式**（仅列名模式）：complete 363,090；`viability2;viability3;viability4` 78；`viability3;viability4` 120；`viability4` 5,544。
- **pair-cell 结构**：complete-case 后 **702 个 pair-cell 只剩 15 行**（另有 315 个 pair-cell=0 行，全部来自 batch3；其余 22,035 个=16 行）；原始（batch 分组）每个 pair-cell 16 行（23,052 组；315 对在 batch1/batch3 各 16 行）。
- **缺失 grid 位置**（member-dose 位 × partner-dose 位，1–4）：缺失 315–432 行/位；位置缺失率 **1.37%–1.87%**（大致均匀，未见单格结构性偏）。
- **缺失 by cell**：高缺失细胞 354 行（如 a2058、a375、hct116、ht29 等，含 batch3 测量）、其余 18 行；**by partner-role**：38 个 partner-role 有缺失（如 azd1775|A 720、azd1775|B 558、bez235|B 279 等）。
- **缺失机制**：**不假设 MCAR/MAR**（metadata-only 无法验证，也不假设 MNAR）；主分析 complete-case（仅空值掩码）；执行期必须报告缺失模式并做 MI 敏感性。

## 2. Δ(c;a,a';b) 资格（complete-case 重算并冻结）

- **上下文** `(batch,cell,partner,role)`；成员 = 伙伴另一角色上的药；**成员完整 = 16 行齐全（complete-case）**；单元 Δ = 完整 4×4 网格均值之差（符号按归一名升序），等价于 4 个 partner-dose 行 Δ 的均值。
- **规模**：全 batch 全细胞 **442,996 单元 Δ / 2,927 上下文**；batch1 全细胞 **441,867 / 2,791**（中位 18 成员）；**batch1 目标 30 细胞 = 340,088 / 2,149**；batch2 仅 1,129 / 136（披露，不进主设计）。
- **严格"同 partner-dose 行"口径**：batch1 目标 **1,429,518 行级单元 / 8,596 上下文**（完整成员-行要求 4/4 member-dose 行）；全 batch 1,862,498。
- **每 (cell,partner,role) 可替换对数**：n=2,791；min 1、median 153、mean 169.2、max 666；每 (cell,partner) 合并角色 n=1,481（min 28、median 324、max 666）。
- **跨细胞覆盖**（batch1）：`(partner,role,{a,a'})` 共 **11,623** 个上下文，覆盖 33–39 细胞（中位 38）；**目标 30 细胞口径覆盖 25–30（中位 30）**，全部 ≥3。
- **每目标细胞单元 Δ**：9,581–12,430（中位 12,430）；每细胞上下文 68–72。
- **5 折设计**（30 目标细胞按归一名升序 `index%5`）：5 折 × 6 细胞（清单见 `on2.json → fold_design.folds`）；每折单元 **66,556–69,738**、严格行级 279,479–293,376、上下文 427–432、`(partner,role)` 72；held-out 与训练不相交。

## 3. σ_e / MDE（冻结条款；实测认证在执行期）

- **借用先验（仅期望，非资格证据）**：`SE_unit=σ_e/√32`、`MDE80=2.801585·SE_unit/√n_eff`；σ_e∈{0.041,0.058,0.109}×n_eff∈{6,12,24,30} 表；保守格（0.109,6）**0.02204 ≤ δ_min=0.10**。
- **执行前实测条款（写死）**：必须用 **O'Neil viability1–4 分半**标定（complete-case 主 cohort：每行 4 重复 → 2+2；all-available ≥2 重复行按 ⌈k/2⌉/余；1 重复行不参与并计数）；`σ̂_e² = Σ_units (Δ_half1−Δ_half2)² / Σ_units denom`（denom = Σ两成员Σ16 行 (1/h1+1/h2)/16²；complete-case 每单元=1/8）；用实测 `SE_unit=σ̂_e/√32`、`MDE80=2.801585·SE_unit/√n_eff` 重算；**若实测 MDE80 > δ_min_provisional=0.10 → `design_invalid: precision_insufficient` 停（不运行效果）**。技术重复只作精度，**不作独立 n**（n_eff=held-out 细胞数=6）。
- **不得**把 0.02204 当实测检定力/资格证据。

## 4. 缺失机制与敏感性（冻结；不进 v2 主判定）

- **机制假设**：metadata-only **不能假设 MCAR/MAR**；主分析 complete-case 只按空值掩码限制人群，不按响应选择。
- **v1.1 all-available 仅敏感性（闭合定义）**：cohort=有 ≥1 非空重复的行；行值=可用重复均值；**成员上下文单位=16 行（分母 16）**；成员可用=16 行齐全 **且 ≥95% 的 16 行含 ≥2 重复 且 ≥12/16 行含 ≥2 重复**；Δ=同上下文两可用成员之差。
  - **行级完整率双分母**：全表 363,090/368,832=**98.44%**；**batch1-target 分析人群 275,412/275,936=99.81%**。
  - **上下文级双 95%**：分子 **45,948** / 分母 **46,104** = **99.66%**（≥95%）。
  - **失败上下文计数（修正表述）**：**156 个成员上下文**的行内比例为 **15/16=93.75%**，**不满足**"行内 ≥95%"条件；它们只在上下文级 95% 规则下被容许——已单独计数并列出（不再写"93.75% 满足"）。
  - 敏感性 Δ 单元数：全 batch 470,179；batch1 全细胞 468,393；**batch1 目标 360,452**（仅敏感性，不用作 v2 资格数）。
- **多重插补（MI）敏感性**：预注册计划冻结（m=20，seed `20261120`；以 batch/cell/partner/dose-row 结构插补行值；不跨端点/跨研究；报告 Δ 单元集合与均值 Δ 敏感性）；**ON2 metadata-only 不读响应数值 → 本轮不运行**，执行期须与 complete-case 主结果并列报告。
- **技术重复**：精度/标定用，**不作独立 n**。

## 5. v1 vs v2（仅披露；v1 数字不得沿用）

| 项 | v1（完整网格存在性口径，`data_unavailable`） | v2（complete-case，本协议资格数） |
|---|---|---|
| batch1-target 单元 Δ | 363,304 | **340,088** |
| batch1-target 上下文 | 2,149 | **2,149** |
| 每折单元 | 71,004–74,580 | **66,556–69,738** |
| 完整成员上下文 | 100% | **96.91%（44,070/45,474）** |
| 跨 ≥3 目标细胞上下文 | 12,430 | **11,623** |
| 判定 | `data_unavailable`（DG3） | **`design_frozen_qualified_with_conditions`**（post-observation，待独立挑战） |

## 6. 边界/措辞（写死）

- **v2 是 post-observation protocol revision，不是预注册**；v1 `data_unavailable` 记录保留；AMENDMENT_ON1-001 不冻结（ON1-C1 判"事后门槛放宽"）。
- 仅 O'Neil **内部开发性**细胞留出；**不得**称独立确认/迁移/决策收益/机制/新算法；不比较更新器（须另立效果协议+独立挑战）；不做 acquisition/Agent/反馈实验。
- 仅 **viability** 端点（`mu/muMax`、`X/X0` 为派生，不作独立功能读数）；**不得与 Jaaks ΔEMAX 拼接/换算**；技术重复≠独立培养（3 BatchID 同 lab）；9 个 Jaaks 重叠细胞排除、目标 30；batch1 主分析，batch2 披露，batch3 全失披露。
- **不写"资源足够"**：只能说"在其他门 PASS 的前提下，v1 的 DG3 是唯一阻塞；v2 用 complete-case 重算后资格门通过，但是否可用须经独立挑战与执行期实测 MDE"。
- 不声称新颖性；阴性/不足同样完整记录；不改 v1/AMENDMENT/challenge/其它目录/INDEX/SYNTHESIS/git。

## 7. 剩余缺口与解冻条件

1. **独立挑战**：v2 须经独立挑战后才可解释/冻结；本轮不运行效果/更新器。
2. **σ_e 实测 + MDE 认证**：执行前用 O'Neil viability1–4 分半标定并重算；MDE>δ_min → `design_invalid` 停。
3. **MI 敏感性**：执行期运行（m=20/seed 冻结），报告与 complete-case 并列。
4. **缺失机制未知**：不能假设 MCAR/MAR；complete-case 覆盖 98.44%；batch3 全失、702 个 15 行 pair-cell 作为设计限制。
5. **合法暴露部分可验证**：无暴露时间/assay 方法列；只能写"部分可验证的合法暴露"。
6. **单药参照未用**：单药工作簿只登记元数据；若未来用作对照须另立预注册与资格。
7. **技术重复≠独立培养**：batch 3 个同 lab ID；不得当独立证据。

## 8. 复现与确定性

```powershell
cd D:\MAESTRO
$env:PYTHONHASHSEED="0"
& D:\anaconda\envs\maestro\python.exe -X utf8 research\2026-10-27-core-module-design\oneil_dev\on2.py
```
- metadata-only（viability 只作空值掩码）；单跑 wall **39.1 / 39.7 s**，CPU-only；两跑 `on2.json` **逐字节一致**（SHA256 `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8`）。
- 产物 SHA：`PROTOCOL_ON2.md` `D990BD0A…DEFF51`、`on2.py` `59ED8FFA…A93B745B`、`on2.json` `AD7E6D13…81F7C8`、`usage_on2.json` `F23FECC2…3D37BF`。
- `on2.json → inputs`：组合工作簿 `A0E2E002…C14818`、单药工作簿 `4A0622C0…ED66DEC`、Jaaks（仅细胞名）`1188968C…FFA278`、PROTOCOL_ON1/ON2、on1.json、challenge/AMENDMENT、PROTOCOL_Q0/q0.json、R199 BRIEF、脚本 SHA。`usage_on2.json`：wall=39.73 s，输入 239,550,399 B。
- 实现修正（终版前，见 record）：严格"同 partner-dose 行"口径要求每成员在该 partner 剂量行 **4/4** member-dose 行齐全（初版 `n_mdose==n_rows` 会把 3/4 行误当完整）；该修正只影响 strict-row 披露数字，不改变任何门／主资格数。

## 9. 限制（必须随判定一起读）

1. metadata-only；**响应数值未读**；σ_e/MDE 是借用先验，不是实测；实测认证在执行期。
2. complete-case 覆盖 98.44%；batch3 全失；702 个 pair-cell 只剩 15 行；缺失机制未知（不假设 MCAR/MAR）。
3. 无暴露时间/assay 方法列；合法暴露仅部分可验证（conditional）。
4. 仅 viability 派生端点；无独立功能读数；不得与 Jaaks ΔEMAX 拼接。
5. 技术重复≠独立培养；3 BatchID 同 lab；n_eff 用细胞数（保守），well 不作独立 n。
6. 单药参照未用；MI 敏感性未运行（计划冻结）。
7. **v2 未通过独立挑战前不得解释/采纳；不运行效果/更新器比较。**
