# R199-ON2 独立挑战（challenge_ON2.md）——O'Neil complete-case v2 资格/设计复审

2026-10-27 · 挑战者：endpoint-auditor（未参与 ON1/ON2；task-62）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON2.md, on2.py, on2.json, report_on2.md, record_on2.md, usage_on2.json}` + 只读参照 `PROTOCOL_ON1.md`、`on1.json`、`AMENDMENT_ON1-001.md`、`challenge_ON1_amendment.md`、R199-Q0。
方式：**只读审查 + 独立 metadata-only 重算**（`tmp/challenge_on2_checks.py`、`tmp/challenge_on2_checks2.py`；只读身份/剂量/viability 空值掩码，不读响应值做任何统计）；**不运行效果/训练/更新器比较，不运行 on2.py（避免改写 ON2 产物）**。
完整性：`on2.json` SHA256 `AD7E6D13…81F7C8`、`PROTOCOL_ON2.md` `D990BD0A…DEFF51`、`on2.py` `59ED8FFA…A93B745B`、`usage_on2.json` `F23FECC2…3D37BF` 与 report/record 登记一致；组合工作簿 `A0E2E002…C14818` 与 on2.json 输入登记一致；**未改 ON1/ON2 产物**。

## 0. 总判决

**revise（≤5 必改）；当前不可冻结 v2 的资格判定；修完 5 条后可冻结 v2（post-observation 性质保留、不运行效果）。**

核心资格数字**独立重算全部成立**：363,090/368,832=98.44%；缺失 0/78/198/5,742；batch1 357,876 / batch2 5,214 / batch3 0；702 个 15 行 pair-cell、315 个 0 行、22,035 个 16 行；DG1 340,088 单元 / 2,149 上下文 / 30/30 / 11,623 跨细胞；DG2 44,070/45,474=96.91%；5 折 66,556–69,738 / 427–432；strict-row 1,429,518/8,596；v1.1 45,948/46,104=99.66%、156 个 15/16=93.75%、Δ 470,179/468,393/360,452；σ_e 先验保守格 0.02203838。**这些与 on2.json/report 的门级数字一致，且没有沿用 v1 的 363,304/71,004–74,580/100%/12,430。**
但有三类必须修的问题：**report/record 把 v1 的描述性统计当成 v2 重算结果**；**v1.1 成员可用规则在 protocol 与实现/报告之间不一致且缺"被排除成员/单元计数"**；**MI 计划不是 MI（行均值插补是确定性的）、σ_e 分半"排序"未冻结**。它们不推翻门级 PASS，但足以使当前 v2 不能作为"可冻结"的资格判定。

**最致命 3 条**

1. **report/record 沿用了 v1 数字（直接违反其自己写的"v1 数字不得沿用"）**：
   - `report_on2.md:48` 写 "每 (cell,partner,role) … mean **169.2**、max **666**；每 (cell,partner) … min **28**、median **324**、max **666**"；`report_on2.md:50` 写 "每目标细胞单元 Δ：**9,581–12,430**（中位 **12,430**）"；`record_on2.md:38` 同写 "9,581–12,430/细胞"。
   - 这些正是 **on1.json 的 v1 值**（`per_context_pair_counts_batch1` mean 169.1566/max 666；`per_cell_partner_union` min 28/median 324/max 666；`units_per_cell_batch1_target_cells` min 9581/max 12430/median 12430）。
   - **v2 实测（on2.json 与我独立重算）**：per-context mean **158.3185**、max **630**；per (cell,partner) min **21**、median **291**、max **630**；per target cell units min **9,047**、max **11,623**、median **11,623**。→ 必须改正，否则报告在"post-observation 重算"上不可审计。
2. **v1.1 成员可用规则不一致 + 缺排除计数**：`PROTOCOL_ON2.md:62` 写 "成员可用 = 16 行齐全 **且 ≥12/16 行有 ≥2 非空重复**"；但 report §4、on2.json `definitions` 和 on2.py 实现要求 **"≥95% 的 16 行有 ≥2 重复 AND ≥12/16"**（`av_usable = frac_ge2 >= 0.95`，在 16 行下即 ≥16/16 行；≥12/16 冗余）。报告中的 45,948/46,104、156 个 15/16、Δ 360,452 都是按**严格版**算的；若按 protocol 字面的 ≥12/16，Δ 单元会不同。**协议与实现必须对齐并重算/重述**；且 protocol 明确要求"被排除的成员/单元计数随 Δ 一起报告"，report/on2.json 只有 sensitivity scopes，没有排除计数。
3. **MI 与 σ_e 执行条款不可执行**：
   - **MI**：`PROTOCOL_ON2.md:67`、report §4、on2.json `multiple_imputation_plan` 都写 "**行均值插补**、m=20、seed 20261120"。**行均值插补是确定性的单次插补**；在没有残差抽样/后验抽样时，m=20 个"插补数据集"完全相同，无法给出 MI 方差（Rubin 规则无对象）。要么定义真正的随机插补模型（如按 batch/cell/partner/dose-row 残差分布抽 draw，PMM 或 normal，m=20 独立 seed，报告 within/between 方差），要么如实改称"确定性行均值单插补敏感性"并删掉 MI/m=20 的说法。
   - **σ_e 分半**：`PROTOCOL_ON2.md:50` 写 "每行按 viability 重复**排序**取前 ⌈k/2⌉ vs 其余"；"排序"未说明是按重复**列序**还是按**观测值**。若按观测值排序，两半会系统性高低分开，`σ̂_e²` 被抬高（偏保守但不再是 well-level 噪声的无偏估计），MDE 认证不可解释。必须冻结为固定重复索引（如 viability1–2 vs 3–4）或预注册随机分半 seed；并写清 complete-case k=4→2+2、all-available k=2/3/4 的 h1/h2、k=1 行排除计数。

## 1. 六项判决摘要

| # | 复审项 | 判定 | 一句话依据 |
|---|---|---|---|
| ① | post-observation 定性 | **WEAK（实质 PASS，措辞需修）** | protocol/report/record 明写"看到 v1 DG3 失败后的新协议、不是预注册"；v1 保持 `data_unavailable`、AMENDMENT 不冻结、v1.1 仅敏感性——这些 PASS；但 `PROTOCOL_ON2.md:33` "阈值沿用 v1、不因数据结果改动"与 DG3 从 v1 完整性门改写为披露门矛盾（见必改 5）；report:5 把 v2 写成 "FROZEN" 早于独立挑战，应标"protocol frozen / verdict provisional"。 |
| ② | complete-case 资格（不得沿用 v1） | **WEAK：门级数字 PASS；report/record 描述统计 FAIL** | 门级数字我独立重算全部吻合（见 §2）；但 report/record 三处把 v1 描述统计当 v2 重算（致命 1）——直接违反"v1 数字不得沿用"。 |
| ③ | 缺失规则/敏感性 | **FAIL** | 不假设 MCAR/MAR、complete-case 主、all-available+MI 计划、156 个 93.75% "不满足"表述均 PASS；但 protocol 与实现/报告的 v1.1 成员规则不一致、缺排除计数（致命 2）、MI 非 MI（致命 3）。 |
| ④ | σ_e/MDE 条款 | **WEAK** | 公式/先验表正确（0.02203838；SE=σ/√32；MDE=2.801585·SE/√n_eff；MDE>0.10→design_invalid 条款存在）；但分半"排序"未冻结、all-available k 细节未写死（致命 3），执行期 MDE 认证不可靠。 |
| ⑤ | 边界/措辞 | **WEAK（多数 PASS）** | 仅 viability、9 个 Jaaks 重叠排除、不与 ΔEMAX 拼接、技术重复≠独立培养、仅内部开发性、不比较更新器、不写独立确认/迁移/决策收益/机制/新算法、"资源足够"已删除——PASS；但 DG3 重定义/阈值措辞、v2 FROZEN/verdict 提前、report/record v1 数字需修。 |
| ⑥ | 总判决 / 是否可冻结 v2 | **revise（≤5 必改）；当前不可冻结；修后可冻结** | 见 §0/§5；核心数字成立，问题在披露/定义/执行条款，不是资源或门级失败。 |

## 2. 独立重算（与 on2.json 的对比）

我按 protocol §1–§3 的定义，从原始组合工作簿重新计算（只读身份/剂量/viability 空值掩码；未读响应值），得到：

| 量 | 我的重算 | on2.json / report | 判定 |
|---|---|---|---|
| raw rows | 368,832 | 368,832 | ✓ |
| complete-case rows | 363,090（98.4432%） | 363,090 / 98.44% | ✓ |
| missing by col | 0 / 78 / 198 / 5,742 | 同 | ✓ |
| co-missing patterns | 363,090 / 78 / 120 / 5,544 | 同 | ✓ |
| batch1 raw→cc（drop） | 358,560→357,876（684） | 同 | ✓ |
| batch2 raw→cc（drop） | 5,232→5,214（18） | 同 | ✓ |
| batch3 raw→cc | 5,040→0 | 同 | ✓ |
| pair-cell rows dist | 22,035×16 / **702×15** / 315×0（raw groups 23,052） | 同 | ✓ |
| DG1 units / contexts | **340,088 / 2,149** | 同 | ✓ |
| DG1 contributing target cells | **30/30** | 同 | ✓ |
| DG1 cross ≥3 target cells | **11,623** | 同 | ✓ |
| DG2 complete member contexts | **44,070 / 45,474 = 0.96912521** | 同 | ✓ |
| folds units | 68,152 / 66,743 / 66,556 / 69,738 / 68,899（66,556–69,738） | 同 | ✓ |
| folds contexts | 432 / 427 / 427 / 432 / 431（427–432） | 同 | ✓ |
| strict-row target | 1,429,518 / 8,596 | 同 | ✓ |
| v1.1 row completeness | full 363,090/368,832=98.44%；batch1-target 275,412/275,936=99.81% | 同 | ✓ |
| v1.1 context 95% | **45,948 / 46,104 = 99.66%** | 同 | ✓ |
| v1.1 failing contexts | **156 个，min 15/16=0.9375** | 同 | ✓ |
| v1.1 Δ units | 470,179 / 468,393 / 360,452 | 同 | ✓ |
| σ_e prior conservative | **0.02203838**（σ=0.109, n_eff=6） | 同 | ✓ |
| target/overlap/Jaaks | 30 target；9 overlap | 同 | ✓ |
| **per-context pair mean/max** | **158.3185 / 630** | report/record 写 169.2 / 666 | **✗ 报告用了 v1 数字** |
| **per (cell,partner) pairs min/median/max** | **21 / 291 / 630** | report/record 写 28 / 324 / 666 | **✗ 报告用了 v1 数字** |
| **per target-cell units min/max/median** | **9,047 / 11,623 / 11,623** | report/record 写 9,581–12,430 / 12,430 | **✗ 报告用了 v1 数字** |

- 门级/资格数字**全部匹配**（可复现）；report/record 的三处描述统计必须按 v2 值改（或删除），并把 v1 数字只保留在 §5 v1-vs-v2 披露表。
- 另：`report_on2.md:46` 的 "每折 strict-row 279,479–293,376" 与 on2.json fold 的 strict 值一致（286,358/280,683/279,479/293,376/289,622），✓；`report_on2.md:47` 的 strict 总量 ✓。
- 输入 hash：组合工作簿 `A0E2E002…C14818`、PROTOCOL_ON2 `D990BD0A…`、on2.py `59ED8FFA…`、on2.json `AD7E6D13…`、usage `F23FECC2…` 与 report/record 一致 ✓。
- 我**没有重跑 on2.py**（会改写 ON2 产物）；"两跑逐字节一致"只核对了登记 SHA，未独立复跑；但独立重算与其门级数字一致。

## 3. 逐项细节

### 3.1 ① post-observation（WEAK，实质 PASS）

- **PASS**：`PROTOCOL_ON2.md:1/3`、`report_on2.md:11/83`、`record_on2.md:48`、`on2.json → verdict.{not_pre_registered=true, post_observation_revision=true, requires_independent_challenge_before_interpretation=true}` 都明确"看到 v1 DG3 失败后的新协议、不是预注册"；v1 `data_unavailable` 保留（on1.json）；AMENDMENT_ON1-001 不冻结；v1.1 只作敏感性。
- **WEAK（措辞）**：
  1. `PROTOCOL_ON2.md:33` "阈值沿用 ON1 v1 的设计要求，不因数据结果改动"——**DG3 实际上被重定义**：v1 DG3 是 "viability1–4 四列存在且非空计数=行数" 的完整性门（v1 因此 FAIL），v2 DG3 改为"缺失披露与缺失机制"（disclosure）。这是路径 A（complete-case 人群）的合理选择，但应写清"DG1/DG2/DSG 阈值不变；DG3 由完整性门改为披露门，属人群/门语义变更，不是阈值放宽"，不能笼统写"阈值沿用"。
  2. `report_on2.md:5` 写 "PROTOCOL_ON2.md（v2 FROZEN…）"；protocol 本身可在计数前冻结，但 **verdict `design_frozen_qualified_with_conditions` 在独立挑战前只能标 provisional**；建议写"protocol frozen (post-observation); qualification verdict pending challenge"。
  3. `on2.json → verdict.verdict` 已经是 `design_frozen_qualified_with_conditions`，虽有 `requires_independent_challenge_before_interpretation=true`；冻结前应保留该 provisional 标记，挑战通过后才写 final。

### 3.2 ② complete-case 资格（门级 PASS；报告 FAIL）

- 门级数字见 §2，全部 PASS；**没有沿用 v1**（DG1 340,088 vs v1 363,304；DG2 96.91% vs v1 100%；fold 66,556–69,738 vs v1 71,004–74,580；cross 11,623 vs v1 12,430）✓。
- **FAIL（report/record）**：`report_on2.md:48/50`、`record_on2.md:38` 的 mean169.2/max666、min28/median324/max666、9,581–12,430/median12,430 全是 **on1.json 的 v1 值**；v2 on2.json 对应值是 158.3185/630、21/291/630、9,047–11,623/11,623。报告自己在 line 30 写"v1 数字不得沿用"，却在 §2 用了 v1；必须改。
- **minor**：`report_on2.md:38` 的"315 对在 batch1/batch3 各 16 行"表述需核对（on2.json batch table：batch1 pair_cells_raw=22,410、batch3=315；"各16行"是否指同一 pair-cell 在两 batch 都出现需说明；不影响门）。

### 3.3 ③ 缺失规则/敏感性（FAIL）

- **PASS**：不假设 MCAR/MAR（protocol §3.3、on2.json mechanism_assumption、report §4）；complete-case 主分析；v1.1 all-available 敏感性定义闭合（双分母、16 行单位、双 95%、156 个 15/16 "不满足"表述已修正）；MI 计划与执行期并列报告；技术重复只作精度；n_eff=held-out 细胞数。
- **FAIL**：
  1. **v1.1 成员可用规则不一致**：protocol §3.3(1) 只要求 ≥12/16 行有 ≥2 重复；report §4/on2.json/on2.py 要求 ≥95% 行有 ≥2 重复（16 行下=16/16）且 ≥12/16；45,948/46,104、156、360,452 都按严格版计算。必须二选一并重算/重述；若按 protocol 字面，Δ 单元数会变化。
  2. **排除计数缺失**：protocol §3.3(1) 明确要求"被排除的成员/单元计数随 Δ 一起报告"；report/on2.json 只有 sensitivity scopes（470,179/468,393/360,452），没有排除的成员上下文/单元数（例如 46,104−?、不满足 ≥95% 的成员数、n_rows_ge2<12 的成员数、上下文 n_usable<2 的计数）。必须补。
  3. **MI 不是 MI**：见致命 3；行均值插补确定性，m=20/seed 无意义；应定义随机插补或改称确定性单插补敏感性。
  4. **行级"完整率"标签**：98.44%/99.81% 是 **all-4 完整率**（AMENDMENT v1.1 口径），不是 all-available（≥1 重复）行覆盖率（后者=100%，因 viability1 无缺失）；report §4 的"行级完整率双分母"应显式注明是 all-4 completeness，避免与 all-available cohort 混淆。

### 3.4 ④ σ_e/MDE（WEAK）

- **PASS**：借用先验 σ_e∈{0.041,0.058,0.109}×n_eff∈{6,12,24,30} 表；保守格 **0.02203838**（σ=0.109,n=6）；`SE_unit=σ_e/√32`、`MDE80=2.801585·SE/√n_eff`；不把先验当资格证据；执行期 O'Neil 分半标定；`MDE>δ_min_provisional=0.10 → design_invalid: precision_insufficient` 条款写死；σ_e 校准含 complete-case k=4→2+2、all-available k≥2、1 重复行排除并计数。
- **WEAK（必须写死）**：
  1. **分半"排序"歧义**（致命 3）：必须冻结为固定重复索引（如 viability1–2 vs 3–4）或预注册随机 half split seed；**不得按观测值排序**（会系统性分开高低两半、抬高 σ̂_e）。
  2. **all-available h1/h2 细节**：k=2→1+1、k=3→2+1、k=4→2+2 写死；k=1 行排除计数；denom 公式的 h1/h2 对应关系写清。
  3. **MDE 认证执行顺序**：先 σ_e 标定报告（含单元数/排除数/σ̂_e/MDE），再决定是否运行效果；该 gate 目前只在条款中，执行期须冻结脚本与输出 schema。
  4. 借用 σ_e 的来源（A0/A2 哪两个估计）未在报告给出锚点；建议补一行来源（不改变"仅期望"）。

### 3.5 ⑤ 边界/措辞（WEAK，多数 PASS）

- **PASS**：仅 O'Neil 内部开发性；仅 viability（mu/muMax、X/X0 派生不作独立读数）；9 个 Jaaks 重叠排除（30 target）；不与 Jaaks ΔEMAX 拼接/换算；技术重复≠独立培养；3 BatchID 同 lab；batch1 主分析、batch2 披露、batch3 全失披露；不比较更新器、不运行效果、不写独立确认/迁移/决策收益/机制/新算法；"资源足够"已删除；v1/v1.1 状态保留。
- **WEAK**：DG3 阈值/门语义措辞（见 3.1）；report:5/on2.json verdict 的 frozen/provisional 区分；report/record v1 数字（见 3.2）。

## 4. 保留项（v2 的实质进步，不要回退）

- complete-case 人群与全部资格数字的重算（门级 363,090/340,088/2,149/30/11,623/44,070/45,474/96.91%/66,556–69,738 全部核过）。
- 不假设 MCAR/MAR；complete-case 主 + all-available 敏感性 + MI 计划（方向正确，需修执行定义）。
- v1.1 闭合定义（双分母、16 行单位、双 95%、156 个 15/16 不满足的单独计数与措辞修正）。
- σ_e 执行期标定 + MDE>δ_min stop 条款（方向正确，需修分半规则）。
- 借用先验只作期望；不把 0.02204 当资格证据。
- 9 重叠排除/viability-only/不拼 ΔEMAX/技术重复边界/不比较更新器/不写资源足够/不声称新颖性。
- v1 `data_unavailable` 与 AMENDMENT 不冻结的记录保持。

## 5. 五条必改（≤5）

1. **修 report/record 的 v1 数字复用**：`report_on2.md:48/50`、`record_on2.md:38` 改为 v2 实测（per-context mean 158.3185/max630；per (cell,partner) min21/median291/max630；per target cell units 9,047–11,623/median11,623），v1 数字只留在 §5 v1-vs-v2 披露表；同时核对 report:38 的 batch1/batch3 pair-cell 表述。
2. **对齐 v1.1 成员可用规则并补排除计数**：二选一——protocol §3.3(1) 改为"≥95% 的 16 行有 ≥2 重复 且 ≥12/16"，或实现改为只要求 ≥12/16；据最终规则重算 45,948/46,104、156、Δ 单元数；补"被排除的成员/单元计数"（协议明确要求）；行级完整率注明是 all-4 completeness。
3. **修 MI 计划**：定义真正的随机插补（batch/cell/partner/dose-row 残差抽样或 PMM；m=20 独立 seed；报告 within/between 方差与 Rubin 区间），或改称"确定性行均值单插补敏感性"并删掉 MI/m=20；同步 protocol/report/on2.json。
4. **冻结 σ_e 分半规则**：固定重复索引（viability1–2 vs 3–4）或预注册随机 seed；禁止按观测值排序；写清 k=2/3/4 的 h1/h2、k=1 排除计数、denom 公式；执行期标定脚本/输出 schema/stop rule 先行冻结。
5. **修 post-observation/门语义/冻结措辞**：protocol 中"阈值沿用 v1、不因数据结果改动"改为"DG1/DG2/DSG 阈值不变；DG3 由 v1 完整性门改为 complete-case 路径 A 的披露门（人群/门语义变更，不是阈值放宽）"；report:5 与 on2.json verdict 标"protocol frozen / qualification verdict provisional pending challenge"；挑战通过后再写 final；保留 v1 `data_unavailable`、AMENDMENT 不冻结、v1.1 仅敏感性、无"资源足够"。

## 6. 复核证据与本轮边界

- **脚本**：`tmp/challenge_on2_checks.py`（complete-case rows/missing/batch/pair-cell/DG1/DG2/folds/v1.1/σ 表）、`tmp/challenge_on2_checks2.py`（per-cell/per-context/strict-row/grid 位置/on2.json 对照）→ `tmp/challenge_on2_checks*.json`。
- **关键数字**：见 §2 表；v1 对照值来自 on1.json（disclosure only），v2 值来自 on2.json 与我重算。
- **输入/产物 SHA**：见页首；与 report/record/on2.json 登记一致；组合工作簿 SHA `A0E2E002…`。
- **未运行**：on2.py（避免改写 ON2 产物）、任何效果/训练/更新器、任何响应值统计；只读身份/剂量/空值掩码。
- **边界**：本挑战只审"资格/设计/披露/执行条款是否可冻结"，不产生任何生物学/效果结论；v1 的 `data_unavailable` 保持；v2 是 post-observation 协议，冻结后也不得称独立确认/迁移/决策收益/机制/新算法。

## 7. 给 Lead 的建议

- **当前不可冻结 v2**；修完 5 条（其中 1–4 是文档/定义/条款修复，5 是措辞）后，由同一挑战者只读复核（不必再跑数据）即可**冻结 v2 的资格判定**（`design_frozen_qualified_with_conditions`，post-observation，附条件；不运行效果）。
- 冻结**不等于**资源"足够"、不等于关系成立、不等于 Stage 1/效果证据：完整病例主分析仍受 98.44% 覆盖、batch3 全失、702 个 15 行 pair-cell、缺失机制未知、技术重复≠独立培养的限制；执行期仍需 σ_e 实测 MDE 认证与 MI 敏感性。
- 若 Lead 要求先跑"v2 效果协议"，本挑战建议**不要**：v2 只完成资格/设计；效果协议须另立 pre-registration + 独立挑战，且执行前必须完成 σ_e 实测 MDE 认证（MDE>0.10 → design_invalid 停）。
