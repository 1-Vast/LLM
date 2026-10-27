# R199-ON2.1 复核（challenge_ON2_1.md）——同一挑战者对 ON2.1（v2.1 补丁）的只读复核

2026-10-27 · 挑战者：endpoint-auditor（与 `challenge_ON2.md` 同一人；未参与 ON2.1 修订）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON2.md（v2.1）, REVISION_ON2_1.md, report_on2_1.md, record_on2_1.md, usage_on2_1.json}` + 未改的 `on2.py`/`on2.json`/`usage_on2.json`/ON1 产物。
方式：**只读审查**（文档/SHA/on2.json/on2_1 执行者的只读重算日志 `tmp/on2_1_recompute1.log`、`tmp/on2_1_recompute2.log`）；**本轮不运行数据、不运行效果/训练/更新器、不重跑 on2.py**；未读响应值。
完整性：v2.1 协议 SHA `8A3E065F…84CCFF`；`REVISION_ON2_1` `65B8FFF9…694D42`、`report_on2_1` `C98D398E…4E11E5`、`record_on2_1` `02C89AA6…8DD4F3`、`usage_on2_1` `733DB458…D762BC`；`on2.py` `59ED8FFA…`、`on2.json` `AD7E6D13…`、`usage_on2.json` `F23FECC2…`、`on1.json` `2E793902…` 均未变；与 record/REVISION 的 SHA 声明一致。

## 0. 总判决

**revise（≤5 必改，均为文档/披露修补；无需重跑数据/效果；核心 5 条实质已落实）；当前仍不可冻结 v2；修完 3 条即可 approve_freeze。**

- **5 条必改的实质内容已落实**：v2 描述统计已改用 v2 实测；v1.1 规则写死为 rule A（≥95% 的 16 行 **且** ≥12/16）并有 45,948/46,104、156 个 15/16、排除计数、all-4 vs all-available 标签、k 分布；MI 改为确定性行均值单插补（删 m=20/seed/Rubin）；σ_e 分半固定重复索引（禁按值排序，k=4/3/2/1 规则、78 个 k=1 行排除、denom/SE/MDE、执行顺序与 stop）；DG3 改为路径 A 披露门、verdict 标 provisional、v1/AMENDMENT/v1.1 状态与"无资源足够"均保留。**门级数字未变**（与 on2.json 及我此前独立重算一致：363,090/98.44%、340,088/2,149/30/11,623、44,070/45,474=96.91%、66,556–69,738/427–432、σ 先验 0.02203838）。
- **但仍有 3 处会污染"冻结"的文档/披露问题**：
  1. **`on2.json`（未改）仍保留 v2.0 的旧 MI 计划（m=20、seed、Rubin 声明）与未加 provisional 的旧 verdict**；v2.1 报告/记录没有明确写"on2.json 的这两个字段是历史、被 v2.1 取代"，而 `report_on2_1.md:74` 还写"已删除"（对 on2.json 而言不成立）。冻结的机器可读产物与协议/报告矛盾。
  2. **v1.1 "排除 Δ 单元 3,727/2,852" 没有定义基线**：这两个数是 **rule B（仅 ≥12/16）无排除 units（all **473,906** / b1 **472,116** / b1-target **363,304**）减去 rule A units（470,179/468,393/360,452）**的结果；基线未写，且 **b1-all 排除成员上下文 152 在 v2.1 文件中完全没有出现**（文件只给 all=156、b1-target=118；Lead 问的"152"无法在文档中核实）。"v1 数字只留 §7"的说法也因此需要限定（rule B units 恰与 v1 数字相同，是诊断基线，不是资格数）。
  3. **`PROTOCOL_ON2.md` v2.1 §6 的交付清单仍是旧的**：仍写"交付：本协议、on2.py、on2.json、**report_on2.md、record_on2.md**、usage_on2.json"，没有列 `REVISION_ON2_1.md`/`report_on2_1.md`/`record_on2_1.md`/`usage_on2_1.json`，也没有把仍含 v1 数字的旧 `report_on2.md`/`record_on2.md` 标为历史。冻结文本若引用协议 §6，会指向错误/含 v1 数字的旧报告。
- 以上 3 条都是**文档/披露层**，不改变门级资格数字、不需要重跑 on2.py/数据/效果；修完可立即 approve_freeze。**当前不冻结**是为了避免把矛盾/未定义数字写进冻结记录。

**最致命 3 条**

1. **on2.json 旧 MI/verdict 未被明确 supersede（③ 自洽性缺口）**：`on2.json → missingness_and_sensitivity.multiple_imputation_plan` 仍是 **m=20 / seed 20261120 / "frozen plan"**，`on2.json → verdict.verdict` 仍是 `design_frozen_qualified_with_conditions`（无 provisional）。v2.1 协议/report 已改，但报告 §4 写"已删除"只对 protocol/report 成立；冻结记录必须明确"on2.json 的 MI/verdict 字段是 v2.0 历史值，v2.1 以协议/报告为准，不得引用/执行旧 MI"，否则读者会从 on2.json 取到矛盾计划。
2. **v1.1 排除 Δ 基线未定义 + b1-all 152 缺失（② 闭合性缺口）**：`PROTOCOL_ON2.md:72`/report §3 写"排除 Δ 单元 = 3,727/2,852"，但未说明 = rule B（≥12/16-only，无排除）units **473,906/472,116/363,304** − rule A units **470,179/468,393/360,452**。其中 rule B 的 b1-target units 恰是 v1 的 **363,304**（v1 只应 §7 披露），必须把基线标为"诊断基线（rule B/无排除，非资格数）"。另：v2.1 只报 **all=156 / b1-target=118** 排除成员上下文；**b1-all 的 152 未出现**（执行者 `tmp/on2_1_recompute1.log` 也只算 all 与 b1-target，没有 b1-all）。Lead 问的"156/152"应明确：文档给的是 156（all）和 118（b1 target）；152（若指 b1 all）缺失，需要补或删去该口径。
3. **协议 §6 交付清单仍指向旧 report/record（⑤ 冻结引用缺口）**：`PROTOCOL_ON2.md:93` 仍写 `report_on2.md`/`record_on2.md` 为交付；这两个旧文件仍含 v1 描述统计（169.2/666、28/324/666、9,581–12,430），而 v2.1 的规范报告是 `report_on2_1.md`。冻结协议必须更新交付/引用清单并把旧文件标为历史；否则冻结文本引用的"报告"就是错的那份。

## 1. 六项判决摘要

| # | 复核项 | 判定 | 依据 |
|---|---|---|---|
| ① | 描述统计改 v2 实测；v1 只披露；315=309+6 | **PASS（minor caveat）** | `report_on2_1.md` §2.1：per-context mean **158.3185**/max **630**（n=2,791）、per (cell,partner) min **21**/median **291**/mean 298.3572/max **630**（n=1,481）、per target-cell **9,047–11,623**/median **11,623**（n=30）；v1 数字只在 §7。旧 report/record 由 report_on2_1 取代（line5）。315=309+6：on2.json batch1 pair-cell 22,410 + batch2 327 = complete-case 22,737；batch3 315 全部重叠，309+6=315 算术一致（split 来自执行者重算，报告/记录未列全；见必须 2）。 |
| ② | v1.1 规则写死 + 重算 + 排除计数 | **WEAK（规则/数字 PASS；基线/152 缺口）** | 规则 A 写死（≥95% 的 16 行且 ≥12/16）；45,948/46,104=99.66%；156 个 15/16；78 k=1×2 角色；排除成员上下文 156（all）/118（b1 target）；排除 Δ 3,727/2,852；0 个上下文降到 <2；敏感性 units 470,179/468,393/360,452；all-4 完整率 98.44%/99.81%；all-available 覆盖 100%；k 分布 78/120/5,544/363,090——与执行者只读重算日志一致。缺口：排除 Δ 基线未定义；b1-all 152 未列；315=309+6 未在规范报告说明。 |
| ③ | MI→确定性单插补（删 m=20/Rubin） | **WEAK（协议/报告 PASS；on2.json 旧字段未 supersede）** | `PROTOCOL_ON2.md:73`、report §4 已改称"确定性行均值单插补（不是 MI）"，无 m/seed/Rubin；但 on2.json 旧 `multiple_imputation_plan`（m=20/seed/Rubin）与旧 verdict 未标注历史；report:74 "已删除"未限定 artifacts。 |
| ④ | σ_e 分半冻结（固定索引/禁排序、k=4/3/2/1、78 k=1、denom/SE/MDE、执行顺序/stop、来源仅期望） | **PASS** | `PROTOCOL_ON2.md:52-58`：固定列序 viability1..4；k=4 2+2、k=3 2+1、k=2 1+1、k=1（78 行）排除并计数；禁按值排序；denom=Σ_{两成员}Σ_{16行}(1/h1+1/h2)/16²（complete-case 每单元 1/8）；SE=σ̂/√32；MDE80=2.801585·SE/√n_eff；MDE>0.10→design_invalid；执行 schema/顺序/stop 写死；来源锚点 0.041=A0/R4 σ=0.0408、0.058=√0.003351、0.109=√0.011968，仅期望。 |
| ⑤ | DG3 路径 A 披露门、verdict provisional、v1/AMENDMENT/v1.1 状态、无"资源足够" | **WEAK（语义/措辞 PASS；交付清单旧）** | 协议 §3/§3.1 DG3 明确"DG1/DG2/DSG 阈值不变；DG3 由完整性门改为路径 A 披露门——人群/门语义变更，不是阈值放宽"；§4 标 provisional；v1 `data_unavailable`、AMENDMENT 不冻结、v1.1 仅敏感性、无"资源足够"均保留。但协议 §6 仍把旧 report_on2/record_on2 当交付，且未列 v2.1 新文件；旧文件仍含 v1 数字。 |
| ⑥ | 总判决 / 是否可冻结 v2 | **revise（≤5；3 条文档修补）；当前不可冻结；修完可 approve_freeze** | 核心 5 条实质已落实、门级数字未变；但 on2.json 旧 MI/verdict、v1.1 排除基线/152、协议交付清单 3 处必须修；不涉及数据/效果重跑。 |

## 2. 逐项取证与细节

### 2.1 ① 描述统计（PASS）

- `report_on2_1.md:37` 与 §2.1 表（lines 55–59）给出的 v2 值与我 challenge_ON2 的独立重算/on2.json 完全一致：
  - per-context（batch1 全细胞，n=2,791）：min 1、median 153、**mean 158.3185**、max **630**；
  - per (cell,partner)（n=1,481）：min **21**、median **291**、mean 298.3572、max **630**；
  - per target-cell units（n=30）：min **9,047**、median **11,623**、max **11,623**。
- v1 数字（169.2/666、28/324/666、9,581–12,430）只在 `report_on2_1.md` §7 的 v1-vs-v2 披露表；`report_on2.md`/`record_on2.md` 保留为历史、由 `report_on2_1.md` 明确取代（line 5）。
- **315=309+6**：`REVISION_ON2_1.md:33`、`record_on2_1.md:34` 写"315 个 32 行 pair-cell = 309 个 batch1+batch3 各 16 行 + 6 个 batch2+batch3 各 16 行"。与 on2.json 的 batch pair_cells_raw（22,410 / 327 / 315）及 complete-case unique groups（22,737=22,410+327）一致；315=309+6 算术成立，batch3 全重叠。**caveat**：split 309/6 不在 on2.json，规范报告 `report_on2_1.md` 未列；若冻结记录引用，需注明来自执行者重算（见必须 2）。
- 旧报告/记录仍含 v1 数字，但已在 report_on2_1 前置说明取代；不是本轮 FAIL，但见必须 1 的协议交付清单问题。

### 2.2 ② v1.1（WEAK：规则/数字 PASS；排除定义/b1-all 缺口）

- **规则写死**：`PROTOCOL_ON2.md:67` 与 report §3 均写"成员可用 = 16 行齐全 **且 ≥95% 的 16 行有 ≥2 非空重复 且 ≥12/16 行有 ≥2 非空重复**"（16 行下 ≥95%=16/16；≥12/16 冗余保留审计）；不再是 v2 原稿的仅 ≥12/16。✓
- **重算数字**（与 `tmp/on2_1_recompute1.log`/`recompute2.log` 一致）：
  - 成员上下文 **45,948 / 46,104 = 99.66%** 满足行内 ≥95%；失败 **156** 个，全部 15/16=93.75%（明确不满足 ≥95%）；对应 **78 个 k=1 行 × 2 角色方向 = 156**；
  - 排除成员上下文 **156**（all batches all cells）/ **118**（batch1 target）；排除 Δ 单元 **3,727**（all）/ **2,852**（b1 target）；排除后上下文降到 <2 可用成员 = **0**；
  - 敏感性 Δ 单元 **470,179 / 468,393 / 360,452**（all / b1 / b1-target；仅敏感性）；
  - **all-4 完整率**（不是 all-available 覆盖率）98.44%/99.81%；**all-available 覆盖率 100%**（viability1 无缺失）；k 分布 **78/120/5,544/363,090**。
- **缺口（必须修）**：
  1. **排除 Δ 单元的基线未定义**：3,727/2,852 = rule B（≥12/16-only，无排除）units **473,906/472,116/363,304** − rule A units **470,179/468,393/360,452**（我从执行者日志核对：rule B = B_ge12_only；rule A = A_ge95_and_ge12）。协议 line72/report §3 只给结果，没写基线；且 rule B 的 b1-target units 363,304 与 v1 数字相同，必须在"v1 仅 §7"的声明中注明这是诊断基线、不是资格数。
  2. **b1-all 152 未列**：v2.1 只给 all=156、b1 target=118；执行者的 recompute 日志也只算 all 与 b1-target，**没有 b1-all 数**。Lead 问的"156/152"在 v2.1 文件中无法核实；若 152 指 b1-all，需补；若不用 b1-all 口径，需明确写"只报 all/b1-target，152 不适用"。
  3. **315=309+6** 只在 REVISION/record，不在规范报告；建议在 report §2 加一行来源（on2.json batch counts + 执行者重算）。
  4. 排除"成员上下文"定义应写清：成员上下文 = `(batch,cell,partner,role,member)` 的 16 行；156 是成员上下文数，不是 member pair/成员数；避免"排除成员 156"与"排除成员对 152"混淆。

### 2.3 ③ MI（WEAK：协议/报告 PASS；on2.json 未注解）

- `PROTOCOL_ON2.md:73` 已改为 **"确定性行均值单插补敏感性（不是多重插补）"**：单次确定性插补、无随机、无 m、无 seed、无 Rubin；结构约束 batch/cell/partner/dose-row；执行期作为敏感性、与 complete-case 主结果并列；本轮不运行。report §4（lines 72–75）同步。✓
- **但**：`on2.json → missingness_and_sensitivity.multiple_imputation_plan` 仍是 v2.0 的 **m=20、seed 20261120、frozen plan**（JSON 未改，SHA 不变），`on2.json → verdict.verdict` 仍是 `design_frozen_qualified_with_conditions`（无 provisional）。report_on2_1:74 "已删除"只是从协议/报告删除，**on2.json 的旧字段未删除也未标注**。冻结记录必须加 supersession 注记（见必须 1），否则"MI 改称确定性单插补"在机器可读产物上不自洽。
- on2.json 是 v2.0 数据产物，保持 SHA 不变是合理的；不需要重跑，但需要 errata/supersession 说明（可写进 report_on2_1/record_on2_1 或新 `ERRATA_ON2_1.md`）。

### 2.4 ④ σ_e/MDE（PASS）

- `PROTOCOL_ON2.md:52-58` 与 report §5 一致：固定列序 `viability1..4`；每行在非空索引中按固定列序取前 h1=⌈k/2⌉ vs 余 h2=k−h1；**明确禁止按响应值排序/分半**；k=4→{v1,v2} vs {v3,v4}（2+2）、k=3→前两可用 vs 余 1（2+1）、k=2→{第一个可用} vs {第二个可用}（1+1）；**k=1（78 行）不参与标定并计数**。
- 估计量/公式：`σ̂_e² = Σ(Δ_h1−Δ_h2)² / Σdenom`；`denom = Σ_{两成员}Σ_{16行}(1/h1+1/h2)/16²`（complete-case 每单元 1/8）；`SE_unit=σ̂_e/√32`；`MDE80=2.801585·SE_unit/√n_eff`；**实测 MDE80>δ_min=0.10 → design_invalid: precision_insufficient 停**；执行 schema 含 cohort、units_used、rows_used、rows_excluded_k1、units_excluded、σ̂_e、SE_unit、MDE80、n_eff；先标定报告→MDE 门→才决定是否效果协议。✓
- 来源锚点（仅期望）：0.041=A0/R4 σ_e=0.0408（我在 R4/cell-state 产物中找到 0.0408）；0.058=√0.003351≈0.05789；0.109=√0.011968≈0.1094；协议/report 明确"仅期望、非资格证据"。✓
- 小 caveat：0.058 的实际 sqrt 是 0.05789，按 3 位小数保留为 0.058；0.041 取 3 位；不构成阻断。

### 2.5 ⑤ DG3/verdict/状态（PASS；交付清单旧）

- `PROTOCOL_ON2.md:36` 明确 **DG1/DG2/DSG 阈值不变；DG3 由 v1 完整性门改为 complete-case 路径 A 的披露门——人群/门语义变更，不是阈值放宽**；§3.1 DG3 要求披露完整、不假设 MCAR/MAR、无响应相关选择；report §6 同。
- 判定：`PROTOCOL_ON2.md:78`、`report_on2_1.md:12` 标 **`design_frozen_qualified_with_conditions`（provisional pending independent challenge）**；protocol frozen (post-observation)，挑战通过后才写 final；v1 `data_unavailable` 保留；AMENDMENT_ON1-001 不冻结；v1.1 仅敏感性；无"资源足够"；仅内部开发性/仅 viability/9 重叠排除/不拼 ΔEMAX/技术重复≠独立培养/不比较更新器/不声称新颖性——均写死。
- **WEAK**：`PROTOCOL_ON2.md:93` §6 交付清单还是旧的（report_on2.md/record_on2.md/usage_on2.json），没有 v2.1 新文件；旧 report/record 仍含 v1 数字。冻结前必须更新（见必须 1）。

## 3. 三条必改（≤5；文档/披露，不需重跑数据/效果）

1. **规范文件与 supersession（③/⑤）**：更新 `PROTOCOL_ON2.md` §6 交付/引用清单，列入 `REVISION_ON2_1.md`、`report_on2_1.md`、`record_on2_1.md`、`usage_on2_1.json`，并把 `report_on2.md`/`record_on2.md`（及 `usage_on2.json`）标为 v2.0 历史；在 report_on2_1/record_on2_1（或新 `ERRATA_ON2_1.md`）明确写：`on2.json` 的 `missingness_and_sensitivity.multiple_imputation_plan`（m=20/seed/Rubin）与 `verdict.verdict` 是 v2.0 历史字段，v2.1 以协议/report 为准，不得引用/执行旧 MI；把 report_on2_1:74 "已删除"限定为"从协议/报告删除，on2.json 保留历史字段但 superseded"。
2. **v1.1 排除 Δ 基线 + b1-all 152 + 315=309+6 来源（②）**：在 protocol §3.3(1)/report/record 写清：排除 Δ 单元 = rule B（≥12/16-only，无排除）units **473,906/472,116/363,304** − rule A units **470,179/468,393/360,452**；明确 rule B 为诊断基线（其 b1-target 363,304 与 v1 数字相同，仅披露、不作资格数）；补 b1-all 排除成员上下文数（**152**，若该口径采用；当前只报 all=156/b1-target=118；否则明确写"只报 all/b1-target，b1-all 不采用"）；在 report §2 注明 315=309+6 的来源（on2.json batch counts + 执行者重算）与成员上下文定义（`(batch,cell,partner,role,member)` 16 行）。
3. **冻结文本/记录同步**：上述两处修完后，把 v2.1 的规范文件清单、on2.json 历史字段说明、v1.1 排除基线写入 record/freeze 文本；保留 v1 `data_unavailable`、AMENDMENT 不冻结、v1.1 仅敏感性、无"资源足够"、不运行效果/更新器；然后由同一挑战者只读确认即可 approve_freeze。**不需要重跑 on2.py/数据/效果。**

## 4. 通过项（保留，不应回退）

- 5 条必改的实质：描述统计 v2 实测（158.3185/630、21/291/630、9,047–11,623/11,623）；v1.1 rule A 与 45,948/46,104、156、排除计数、all-4 vs all-available 标签、k 分布；MI→确定性单插补；σ_e 固定索引分半/禁排序/k 规则/78 k=1/denom/SE/MDE/执行顺序与 stop；DG3 路径 A 披露门、provisional、v1/AMENDMENT/v1.1 状态、无"资源足够"。
- 门级数字未变且可复现：363,090/98.44%；340,088/2,149/30/11,623；44,070/45,474=96.91%；66,556–69,738/427–432；strict-row 1,429,518/8,596；σ 先验 0.02203838；与 challenge_ON2 的独立重算一致。
- v2.1 SHA 与未改的 on2.py/on2.json/ON1 SHA 全对；未运行效果/训练/更新器；未读响应值。

## 5. 若修完，建议的冻结文本（approve_freeze 版）

> **ON2 v2.1 判定：`design_frozen_qualified_with_conditions`（post-observation protocol revision；frozen after independent challenge）。**
> 本判定是**看到 ON1 v1 DG3 失败后的新协议（v2/v2.1）**，**不是预注册**；v1 `data_unavailable` 记录保留；AMENDMENT_ON1-001 不冻结；v1.1 仅敏感性。
> 规范文件：`PROTOCOL_ON2.md`（v2.1 SHA `8A3E065F…`）、`report_on2_1.md`、`record_on2_1.md`、`REVISION_ON2_1.md`、`usage_on2_1.json`；`on2.py`/`on2.json`/`usage_on2.json` 未改，`on2.json` 的 MI（m=20/seed/Rubin）与旧 verdict 为 v2.0 历史字段，v2.1 以协议/报告为准。
> complete-case 主分析：363,090/368,832=98.44%；DG1 340,088/2,149/30/11,623；DG2 44,070/45,474=96.91%；DSG1 66,556–69,738/427–432；DG3 为路径 A 披露门（DG1/DG2/DSG 阈值不变；人群/门语义变更，非阈值放宽）。
> 条件：仅 O'Neil 内部开发性、仅 viability；技术重复≠独立培养、不称独立确认/迁移/决策收益/机制/新算法；不与 Jaaks ΔEMAX 拼接；执行期必须先做 σ_e 固定索引分半标定 + MDE 认证（MDE>0.10 → `design_invalid: precision_insufficient` 停）；确定性行均值单插补敏感性执行期运行；缺失机制未知（不假设 MCAR/MAR）；batch3 全失、702 个 15 行 pair-cell；无"资源足够"。
> **冻结 ≠ 资源足够/关系成立/Stage 1/效果证据；不运行效果/更新器比较；效果协议须另立预注册 + 独立挑战。**

## 6. 边界

- 本轮只读文档/SHA/执行者只读重算日志，**未运行数据/效果/训练/更新器，未重跑 on2.py，未读响应值**；只写 `challenge_ON2_1.md` 与 `tmp/`；未改 ON2/ON1 产物。
- 结论只审"资格/设计/披露/执行条款是否可冻结"，不产生生物学/效果结论；v1 `data_unavailable` 保持；v2.1 是 post-observation，不是预注册。
