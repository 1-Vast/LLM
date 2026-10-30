# R196 v2 独立挑战（task-32）—— 第一部分：**结果前预审**（2026-10-27）

> 状态：**结果前预审（pre-result review）**。R196v2（AMENDMENT-001）正在运行、结果尚未解释。本文只对 [AMENDMENT_R196.md](AMENDMENT_R196.md) 是否**预先写死** challenge_R196 的 5 条必改做核对；**不是结果审**。结果出来后（T32 正式挑战）在本文追加"§5 结果审"再出最终 verdict。
> 依据：[challenge_R196.md](challenge_R196.md)（v1 挑战，revise，5 必改）、[AMENDMENT_R196.md](AMENDMENT_R196.md)、[REVOCATION_R196.md](REVOCATION_R196.md)、v1 `r196.json`（已撤回但数字存在）。只读；未改 AMENDMENT/结果/其它目录；未运行效果。

## 0. 预审结论（一句话）

**5 条必改中 4 条已预注册、1 条部分；另发现 2 个必须在"结果解释前"补写的漏洞（partition 级推断未进判定、E9 预算声明与预冻结 peek 披露不准确）。建议 runner/Lead 在解释前补 AMENDMENT-002（两段式、不改已跑数据即可写），否则 T32 结果审只能判"部分预注册"。**

- 已预注册：① 主推断单位=drug-cluster CI + MDE80_drug≤δ_min（AMENDMENT §4–§5、E7）；② 10 个独立药物划分 ×5 折 + fold/partition dispersion（§2、§4）；③ 统一内层指标=3 折 Spearman 算术平均、L_EXT/L_C130 双网格、H196b 对称桥接（§3、§5 H196b、E3/E4）；④ δ_min=0.05 operational（Kendall τ 换算）+ 与 drug MDE 硬联动 + 稳定带上界取消（§5）；⑤ 措辞模板/C130 非参照/不是外部复现（§7）——大部分。
- 部分/仍缺：partition 级推断只在"敏感性"、不参与 verdict；E9「单命令 ≤15 min」与当前 CPU≈40 min 的关系未交代；预冻结 peek 披露不准确（v1 主臂/row-level 已运行并写入 `r196.json`，v2 是**已知 v1 结果的审计重分析**，不是盲验）。
- 需补 AMENDMENT：**是**（2 项，见 §2）。可在结果解释前补写，不要求重跑（除非 E9 按冻结规则判失败）。

## 1. 5 条必改逐条对照

| 必改（challenge_R196 §3） | AMENDMENT 落点 | 状态 |
|---|---|---|
| 1. 主推断单位改为 held-out 药物/划分（drug-cluster 主 CI + MDE80_drug≤δ_min；若坚持 cell 主则限制措辞） | §4：主 CI=drug-cluster bootstrap（65 药双侧 anchor×library 角色重抽、m_anchor·m_library 复制测试行、50 折均值、B=2,000、seed 20261027+700000）；主 MDE80=2.802×SD(drug-bootstrap Δ)；§5 硬条件 `replicated_under_audit` 要求 **主 MDE80（药物单位）≤δ_min**；cell/pair/twoway/partition 全部降为敏感性（§4） | **已预注册** |
| 2. 预注册 ≥10 个独立药物划分，fold dispersion 升级为正式 sensitivity | §2：10 划分 ×5 折（`SEED_PART=20261027+100·p`），每划分 13 药/折；每折测试行≥2,500；§4：partition 级（10 划分均值/SD/t-CI df=9/percentile）与 fold 级（50 折 SD/t-CI df=49/leave-one-partition-out）**正式敏感性**；E1 冻结折结构 | **已预注册（但见 §2-①：partition 级仍不进判定）** |
| 3. 统一 grouped/row-level 内层 λ 指标；row-level 加 C130 ≤1000 网格桥接；隔离 H196b | §3：内层指标统一为 **3 折 Spearman 算术平均**（不用 pooled）；L_EXT（11 值）与 L_C130（9 值 ≤1000）双网格；臂：`rowlevel_ext`/`rowlevel_c130_grid`/`grouped_c130_grid`；§5 H196b：`rowlevel_ext−grouped(ext)` 与 C130 网格对称桥接，差值 CI=配对 drug-cluster bootstrap，`material_optimism_flag` 只作可靠性标记；E3/E4 设计体检代码审计 | **已预注册** |
| 4. δ_min/稳定带 operational 化并与 drug MDE 联动 | §5：δ_min=0.05 的 operational 定义（Kendall τ≈(2/π)arcsin(ρ)：ρ=0.05⇔τ≈0.0318⇔排序正确概率相对机会 +1.59pp），明确"不是决策效用"；`replicated` 要求主 drug-MDE≤δ_min；**稳定带上界取消**（>0.20 只记 `large_gain_flag`，不参与判定）；三档判定写死 | **已预注册** |
| 5. 固定措辞模板 + 披露预冻结 peek + C130 CI 非参照 + 可比性 | §7：replicated/weakened/inconclusive 允许句式；必须并列 drug CI/MDE 与折/划分；不得写 C130 复现/独立确认/决策；C130 CI 非参照；披露 v1 原型 annotation-only≈0.149 与零模型；不是外部复现 | **部分**（peek 披露对象不准确，见 §2-②；其余 ✓） |

## 2. 结果解释前必须补的漏洞（要求 runner/Lead 在**看 v2 结果之前**写 AMENDMENT-002）

### ① partition 级不确定性不进判定（最重要）
- AMENDMENT §4 把"划分级（10 个划分增益的均值/SD/t-CI df=9）"明确列为"次级/敏感性（不作判定）"；§5 的 `replicated_under_audit` 只看 **drug-cluster CI 下界>0 + 点≥δ_min + MDE80_drug≤δ_min**。
- 问题：50 个折级增益来自 10 个**共享同一 65 药的划分**，不是独立重复；drug-cluster bootstrap 重抽药物但固定划分。若 10 个划分均值之间差异大、t-CI（df=9）含 0，而 drug-cluster CI 因把 50 折当重抽样而变窄，v2 仍会判 replicated——这正是 v1「用最窄口径通过、把更宽口径放 sensitivity」的同类漏洞，只是从 cell→drug 换了一层。
- 要求（二选一，**预先写死**）：
  (a) 把 **partition 级 95% CI（df=9 或 percentile，预注册其一）下界>0** 加入 `replicated_under_audit` 的合取条件；或
  (b) 明确"若 partition 级 CI 含 0（或 partition 间符号不一致数 >0）则 verdict 最多 `weakened`，并在报告并列 partition 分布"。
- 同时写死 `Δ=mean_{p,f}` 的 50 折**不是独立单位**（应按 partition 嵌套/两阶段 bootstrap），并说明 drug-bootstrap 的"50 折均值"如何避免把 10 划分当独立重复（建议：先每划分内 5 折均值，再对 10 个划分做 block bootstrap/两阶段）。

### ② E9 预算与"预冻结 peek"披露
- **E9 写死"单命令 ≤15 min"**（§6），但当前 v2 运行 CPU 已约 **40 min**（Lead 通报）。若 wall-clock >15 min：按冻结规则 E9 **不通过 → 任一设计检查失败 → `inconclusive`**；不能事后把 15 min 改 45 min 而不留记录。要求 runner 在 `record_r196_v2.md` 记录 **wall-clock 与 CPU-time**；若 wall >15 min，先写 AMENDMENT-002 说明"实现性能不改变统计性质，E9 的预算条款按 X 处理"，并预注册后果（如视为 `inconclusive` 或记录为 deviation 但不改变统计判定——**须二选一写死**，不得由报告事后选）。若 CPU 40 min 是多进程累计、wall 仍 ≤15，须在 record 明示。
- **peek 披露不准确**：§7 写"v1 机制原型曾跑 annotation-only（≈0.149）与零模型；主臂 annotation/identity/row-level 未在冻结前运行"。事实是 **v1 已跑出 `r196.json`（含 annotation mean 0.1447、rowlevel 0.1441、cell CI、drug MDE 0.1527 等）并被撤回**；v2 是在**已知 v1 数字**之后写的修订。应写死披露："v2 是已知 v1 结果的审计重分析（v1 结果已撤回但可见）；v2 的预注册只约束 v2 流程与判定，**不构成盲验/独立复现**；v2 的规则/阈值/网格/划分种子来自挑战+撤回文本+v1 协议，不按 v2 结果调整。" 这条应进 AMENDMENT 或至少 `report_r196_v2.md` 的显式段。

### 结果前小项（不要求补 AMENDMENT，但应写入 record/report 检查清单）
- E7 的 `MDE80_design` 只用 `shuffle_seed0` 的 drug-bootstrap SD；正式 MDE 由主增益的 drug-bootstrap 报（§5），二者关系写清（E7 是设计门，§5 是判定门）。
- `identity` 臂 v2 不拟合、只在 partition 0 做常数性检查后全沿用：合理，但报告需给"50 折全部常数"的构造性论证/计数。
- H196b 的 `rowlevel_c130_grid` 用折内 scaler（不是 v1 C130 的折前 scaler）；§7 已把它当"桥接诊断"而非 C130 复现，报告须保留该限定（不得把差值当"C130 的乐观量"）。
- §5 δ_min 的 Kendall 换算 `(2/π)arcsin(ρ)` 是双变量正态近似；把它当 operational 理由可以，但报告应注明近似性质，不写成精确换算。

## 3. 结果出来后（T32 正式结果审）必须核对的清单（预登记，避免事后补理由）

1. **E1–E9 全部**：逐项 pass/fail + 实测值；E7 MDE_design、E9 wall-time 与预算声明。
2. **主 CI 与 MDE**：drug-cluster CI [lo,hi]、`MDE80_drug`、点估计；是否满足 §5 合取；若入 ①，partition 级 CI/t-CI 与符号一致性。
3. **H196b**：`rowlevel_ext−grouped(ext)` 与 `rowlevel_c130_grid−grouped_c130_grid` 的配对 CI、`material_optimism_flag`；确认内层指标已统一（E3 代码审计记录）。
4. **零模型**：shuffle 10 seeds 的折均 ρ 校准（E6）与 `annotation−capacity_seed0` 描述性 CI；capacity/shuffle 各自的 λ 选择。
5. **措辞**：report 是否引用 §7 模板、是否并列折/划分离散、是否避免"C130 复现/独立确认/决策/机制"、pre-freeze peek 披露是否修正。
6. **偏离**：`record_r196_v2.md` 的实现偏离清单；v1/v2 差异是否都已声明；产物 SHA 与确定性双跑。
7. **与 v1 的关系**：v2 结果不得覆盖/改写 v1 数字；v1 已撤回状态保持。

## 4. 声明

- 本文是**结果前预审**；未运行效果、未改 AMENDMENT/结果/其它目录；不构成 T32 最终 verdict。
- **是否需 runner 在结果解释前补 AMENDMENT：需要（2 项：partition 级判定门槛、E9/peek 披露）**。补写不改变已跑的统计量（除 ① 的判定门槛可能需要按预注册重新判 verdict；若 v2 结果已出但未解释，仍可在解释前补写）。
- 待 v2 结果出：在本文追加 §5 结果审（逐项核对上述清单）后给最终 verdict（proceed/revise/stop）。

**预审一句话：AMENDMENT_R196 已把 5 条必改的 4 条写死（drug 主单位/10 划分/统一内层/δ_min operational/措辞），但 partition 级不确定性仍只作敏感性、E9 的 ≤15 min 与当前 40 min CPU 冲突、peek 披露仍按"v1 主臂未跑"写（实际 v1 已跑并撤回）——这三点需在结果解释前补 AMENDMENT/披露，否则 T32 只能判"部分预注册"。**

---

## 5. 结果审（T32，2026-10-27，v2 已落盘后）

> 本节的依据：`AMENDMENT_R196.md`（001，SHA `6986b008…`）、`AMENDMENT_R196_002.md`（002，SHA `fe1836bd…`）、`r196_v2.py`（SHA `3e4bae43…`）、`r196_v2.json`（SHA `bd0ada7b…`）、`r196_v2_rows.csv`（SHA `576fb155…`）、`report_r196_v2.md`、`record_r196_v2.md`、`usage_r196_v2.json`、`tmp/r196_v2_stage_*.json`/`run1`。只读复核；未运行效果、未改 R196v2 产物。

### 5.0 结果审判决：**PASS（结果可解释，但附 3 条记录更正；不需要重跑、不改变 verdict）**

**可解释边界（写死）：**R196 v2 **只能**写"在预注册审计协议（001+002）下，因审计目标单位（held-out 药物）MDE80>δ_min、E7 设计门失败、E9 预算门失败，verdict=`inconclusive`（未决）"；**不得**写 C130 被复现/确认/可靠/量级恢复，也不得写 C130 被推翻/注释无用，不得写阴性、外部复现、决策收益、机制；不得因 partition CI/四个聚类 CI 下界>0 改判 replicated（002 §D 明确 E9 失败优先 inconclusive）。C130 状态保持"冻结但未被外部/审计级确认"；R196 v2 不进入 SYNTHESIS"成立"类。

### 5.1 verdict 是否被机械正确应用（PASS）

| 门 | 预注册规则 | 实测 | 后果 |
|---|---|---|---|
| E7 设计门 | 001 §6 E7：`MDE80_design=2.802×SD_drugboot(shuffle_seed0)` ≤ δ_min=0.05（002 §C.2 明确 E7≠主 MDE80） | **0.082267 > 0.05**（r196_v2.json `design_checks.E7…pass=false`；report §3.4/§4） | 设计体检失败 → 002 §D-1 `inconclusive`（子类型 `design_check_failed`） |
| 主 MDE80（held-out 药物） | 001 §5：主 MDE80_drug ≤ δ_min | **0.085720 > 0.05**（JSON `judgment.primary_mde80`；report §0/§3.1） | `inconclusive`（子类型 `primary_mde80_gt_delta_min`） |
| E9 预算门 | 001 §6 E9：单命令 ≤900 s；002 §B：wall>900 s ⇒ `inconclusive`，不得改记为 deviation 放行 | **run-1 wall=1119.7 s（run-2 1078.6 s）>900 s**；`usage.budget.e9_pass=false`、`stage_5` 同 | `inconclusive`（子类型 `e9_wall_gt_900s`） |
| partition 合取 | 002 §A：partition 95% t-CI（df=9）下界>0 | **[0.123826, 0.159102]，下界>0；10 个 partition 全为正**（report §3.2；JSON `partition_dispersion`） | 该合取条件**满足**，但 E7/MDE/E9 已失败 → **不得**据此改判 replicated；报告/JSON 未改判 ✓ |

**结论：verdict `inconclusive` 与 001 §5 + 002 §D 的机械顺序一致；四项数字（增益、drug CI、partition CI、MDE）均不支持 replicated。** 报告 §0"方向为正且四个聚类 CI 下界>0"是**数字描述**，且报告标注"含义（仅机械）"+§7 措辞限制，未越界；未见把 partition CI 正当作翻案理由。

### 5.2 数字、SHA、确定性（PASS，已独立核对）

- 我独立计算：`r196_v2.json` SHA=`bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4`，`r196_v2_rows.csv` SHA=`576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84`，与 report §8/record §5/`tmp/r196_v2_run1.*` **逐字节一致**；001 SHA `6986b008…`、002 SHA `fe1836bd…`、脚本 SHA `3e4bae43…` 均与报告/JSON/usage 一致 ✓。
- 确定性：run-1 保留副本与最终产物 SHA 相同；两次完整运行 wall 1119.7/1078.6 s，`r196_v2.json`/rows 两次逐字节一致 ✓；固定种子/无时间戳/JSON 键排序（report §5、record §6、usage.runs）。
- 数字：point 0.141464；drug CI [0.062468,0.182579]；drug MDE 0.085720；cell/pair/twoway CI/MDE（report §3.1）；partition per-partition [0.145022,0.115611,0.174600,0.138670,0.125094,0.158891,0.154888,0.129675,0.099101,0.173085]、t-CI [0.123826,0.159102]；fold formal sensitivity SD 0.083518、t-CI [0.117723,0.165204]（min −0.03248、max 0.301134）；H196b ext −0.000199、CI [−0.001013,0.00034]，C130-grid +0.000061、CI [−0.000113,0.00033]，material_optimism_flag=false；E6 shuffle mean −0.006231（含 0）、capacity +0.000874；E5 800/800、E8 max diff 7.0e-13——均与 JSON/report 一致。
- v1 未改：v1 `r196.json`/`r196.py` 等保持撤回口径；v2 产物为新增（record §0/§8）。

### 5.3 披露/措辞（PASS，附 1 条格式条件）

- **peek 更正已落实**：002 §C.1 与 report §6.1 明写"v2 不是盲验/独立复现；v1 全部结果（annotation 0.1447、rowlevel 0.1441、drug CI [0.0139,0.2233]、MDE80_drug=0.1527 等）在 001 冻结前已知，v2 是已知 v1 结果的审计重分析"✓；001 §7 旧表述被 002 更正，报告/记录不再写"任何响应读取前冻结"。
- **C130 CI 非参照**：002 §C/报告 §6.3 明写 [0.0947,0.1409] 不是参照区间（切分/λ/内层不同）✓；**rowlevel_c130_grid 仅桥接诊断、非 C130 复现**（002 §C.4、report §3.5/§6.3）✓。
- **E7 与主 MDE 区分**：002 §C.2、report §3.4/§6.4 写清 E7=打分前设计门（shuffle_seed0，B=1,000），§5 主 MDE=处理臂（B=2,000），两者均>δ_min → 两重依据 ✓。
- **Kendall 近似**：002 §C.5/report §6.5 注明 τ≈(2/π)arcsinρ 是近似，δ_min=0.05 用于判定是按冻结口径、不用于换算 ✓。
- **identity 不拟合**：002 §C.3 + report/JSON 记录 partition 0 的 5/5 折实拟合常数验证 + 构造性论证 ✓（结构上 both-unseen 身份列在训练全 0，系数=0）。
- **措辞边界**：report §7 明确"inconclusive 只写审计目标单位功效不足/设计体检未过→未决；不写 C130 复现/推翻/外部复现/决策/机制/阴性；不进入 SYNTHESIS 成立类；C130 状态不变" ✓。
- 条件：002 冲突条款写"两者冲突时以 002 为准（**仅限 verdict 规则与 E9 后果**）"（002 首页），但 §C 同时更正了 peek/rowlevel/Kendall 等披露；建议把"以 002 为准"的覆盖范围扩到 §C（否则严格读者可主张 001 §7 旧 peek 文本未被正式取代）。这是记录条件，不影响 verdict/数字。

### 5.4 仍有的记录级不一致（3 条；不改变 verdict，但应在正式引用/入库前补一份 ERRATA/AMENDMENT-003）

1. **机器可读产物漏了 E9**：`r196_v2.json` 的 `design_checks` 只有 E1–E8（无 E9），`judgment.subtypes` 为 `["design_check_failed","primary_mde80_gt_delta_min"]`，**缺 `e9_wall_gt_900s`**；而 002 §D-1 要求"记录子类型"，report §0/§4 有 E9 行、usage/stage_5 有 e9_pass=false/wall=1119.7。另 `r196_v2.json` 的 `deviations=[]`，与 record §3 记录的"post-hoc 分步缓存（运行时偏离）"不一致；JSON 的 `protocol` 只记录 001，未记录 002。→ 需在 JSON 旁补 `r196_v2_ERRATA.json`（或 AMENDMENT-003）登记 E9 子类型/E9 design check/002 SHA/deviations，不改数字与 verdict。
2. **冻结设计数字与实际折行数不一致**：001 §2 写"每折测试行 **≥2,500**、每划分 ≈20,700"；实测每折最小 **1,791**（E1 的冻结检查阈值是 **≥300**，所以 E1 通过；各划分总行 19,484–20,819）。这属于"文档预期值 vs 实际"的偏离：需在 report/record 明写"§2 的 2,500 是旧预期、E1 的 300 是实际门槛；实际折行 1,791–7,476"，不能只写"均 ≥ 预注册的 300"而不提 001 §2 的 2,500。**该偏离不改变 verdict**（E7/MDE/E9 已失败）。
3. **H196b 的 C130-grid 桥接受 λ 上限影响**：report §3.5 给出 λ 触上限次数（annotation 26/50、grouped_c130 29/50、rowlevel_ext 31/50、**rowlevel_c130 43/50**），但未在 H196b/C130-grid 结论处提示：43/50 触 1000 上限 → C130-grid 桥接只能作诊断，"material_optimism_flag=false"只对本协议/扩展网格成立，不能用来说"C130 的行级内层不乐观"；002 §C.4 已限"不是 C130 复现"，报告应在 H196b 表下补一句 λ 上限说明（记录条件）。
另附：002 声称 frozen at 18:34，但文件 mtime 18:28:55；record/usage 与 mtime 不一致，建议 record 记精确冻结时刻/方式（不影响内容；002 §B 的 E9 后果规则本身只引用 001 E9 + 002 §B，verdict 正确）。

### 5.5 可解释边界（最终，供 Lead/登记）

- **允许**："R196 v2 在预注册审计协议（001+002）下 verdict=`inconclusive`：主推断单位（held-out 药物）MDE80=0.0857>δ_min=0.05、E7 设计门 MDE80_design=0.0823>0.05、E9 wall=1119.7 s>900 s；因此未达到审计级可靠的最低标准，结果未决。点估计 +0.1415、drug CI [0.0625,0.1826]、partition CI [0.1238,0.1591] 等为数字，不构成 replicated/确认。"
- **禁止**：C130 被复现/可靠/确认/量级恢复；C130 被推翻/注释无用；阴性；外部复现；决策收益；机制；任何"R196 v2 支持 C130"或"R196 v2 否证 C130"的表述；用 partition CI/四聚类 CI 正改判 replicated；把 E9 超时写成 deviation pass。
- **登记**：R196 v2 不进入 SYNTHESIS 成立类；C130 保持"冻结但未被外部/审计级确认"；v1 撤回状态不变；H196b 结论仅限本协议（扩展网格）；C130-grid 桥接受 λ 上限影响，只作诊断。

**§5 结果审一句话：verdict `inconclusive` 被 001+002 机械正确应用（E7=0.0823>0.05、主 MDE=0.0857>0.05、E9 wall=1119.7>900 三门均失败；partition CI 正但未改判），数字/SHA/确定性/peek 披露/措辞均核验通过——判 PASS（可解释）；但 r196_v2.json 缺 E9 子类型/E9 design check、deviations 与 record 不一致、001 §2 的"每折≥2,500"与实测 1,791 未披露、H196b C130-grid 桥接 43/50 触 λ 上限——这 3 条记录级更正应在正式引用/入库前补 ERRATA，不改 verdict、不重跑。**
