# R196 PROTOCOL 回顾性独立挑战（task-29）：C130 审计级可靠性重估

2026-10-27。角色：独立挑战者（非 runner、未参与开发）。对象：[PROTOCOL_R196.md](PROTOCOL_R196.md)（冻结版）、实现 [r196.py](r196.py)、运行产物 [r196.json](r196.json)、[r196_rows.csv](r196_rows.csv)；参照 R196 BRIEF、HANDOFF 方法审计、C130/R163 原协议。**本挑战在结果被解释/采纳之前给出；不运行效果代码、不改 R196 产物、只写本文件与 `tmp/`。** 按 Lead 规则：**判 revise → R196 现有结果作废，需 AMENDMENT 重跑后方可解释**；判 proceed 才可解释。

## 0. 结论先行

**总判决：revise（≤5 必改；R196 现有 verdict `replicated_under_audit` 在修正前不得解释/采纳）。**

原因不是"结果小"或"阴性"，而是**冻结协议的主推断单位与审计目标不匹配，判决由此建立在一个过窄的聚类口径上**，且**该口径下必需的功效门槛在审计目标单位上不达标**。R196 自己的 JSON（`reliability_qualifier`）已把这一点写出来了，但 verdict 仍是 `replicated_under_audit`：

- 主增益 **0.144657**；预注册主 CI（**细胞聚类**）**[0.121304, 0.166746]**、MDE80_cell=0.032 → 按 §9 判 `replicated_under_audit`（[r196.json:331-347](r196.json#L331)；[r196.py:648-657](r196.py#L648)）。
- 但**留出药物重采样**（drug-cluster，审计目标"未见药物"的抽样单位）CI **[0.0139, 0.223292]**、**MDE80_drug = 0.152731 > δ_min=0.05**；双向聚类 MDE=0.0783，药对聚类 MDE=0.0721（[r196.json:318-340](r196.json#L318)）。
- **5 个外层折的 per-fold 增益 = [0.0820, 0.2952, 0.2682, 0.0661, 0.0118]**，fold SD=0.1281、se=0.0573、t 区间 **[-0.0144, 0.3037]（含 0）**（[r196.json:284-302](r196.json#L284)）——即"药物划分"这一层的不确定性完全没进主 CI，而它恰好是 C130 结论的外推对象。
- JSON 的 `reliability_qualifier` 原文承认："sign/positive direction is robust across all four clusterings; the **MAGNITUDE is not pinned at delta_min under held-out-DRUG resampling** (MDE80_drug > 0.05); only 5 held-out drug folds and 13 held-out drugs per fold. The pre-registered primary (cell-clustered) MDE is <= delta_min."（[r196.json:679-690](r196.json#L679)）——**这是协议设计的缺口，不是结果的解释空间**：对"药物总体"的审计结论，主单位必须是药物/划分，而不是细胞。

**给 Lead 的最致命 3 条：** ① 主推断单位错误：cell-cluster 主 CI/MDE 不覆盖 held-out 药物/划分不确定性；drug-cluster MDE=0.153≫δ_min=0.05、fold t-CI 含 0 → 按审计目标应判 `inconclusive`（MDE 超 δ_min）或至少 `weakened`，不能写 `replicated_under_audit`；② 只有**一个** 5 折药物划分，不能估计"换一批留出药物"的方差（fold 增益 0.012–0.295 已示警），C130 原用 40 划分（虽重叠、审计已批评不能当独立 CI），R196 至少需预注册多划分/药物重采样作为主单位；③ 内层 λ 选择用**跨内层折拼接原始预测的 pooled Spearman**（[r196.py:136-158](r196.py#L136)），而 row-level 对照用**折均 Spearman**（[r196.py:190-195](r196.py#L190)）→ H196b 的 rowlevel−grouped 差把"内层聚合口径"和"λ 方案"混在一起；同时 λ 网格扩到 10000 后，row-level 对照全部触上限 10000，已经不是 C130 的 λ 网格（≤1000），"复现 C130 口径"的措辞越界。

## 1. 逐条判决表（task-29 ①–⑦）

| # | 挑战项 | 判决 | 一句话理由 |
|---|---|---|---|
| ① | 药物分折是否真无泄漏（内层/外层/测试标签只用最终打分） | **PASS** | 外层按 65 药并集 5 折；训练=两药都不在 held、测试=两药都在 held、one-seen 排除；`y_train` 只在训练行非 NaN，λ 选择/预测函数只拿训练与内层数组；测试标签只在 `rho(pred, y[o['test']])` 读一次（[r196.py:265-312,365-391](r196.py#L365)）；D2/D3 断言内层 held 与 inner-train 药物互斥、内层验证行两药均在 inner-held；scaler 在每个内层训练折内拟合（[r196.py:136-144](r196.py#L136)），修掉了 HANDOFF 指出的折前标准化泄漏（[handoff audit:7](../2026-10-27-handoff-method-audit/report.md#L7)）。D5 计数 135=5×27 臂·折，一致。 |
| ② | 内层调参是否药物分组 | **WEAK** | 分组本身 ✓（内层 3 折按 52 训练药分组、内层验证 both-unseen、scaler 折内）。但**内层指标口径不一致**：grouped 用"3 个内层折预测拼接后的 pooled Spearman"（[r196.py:147-152](r196.py#L147)），row-level 对照用"3 折 Spearman 的均值"（[r196.py:190-195](r196.py#L190)）——H196b 的差值因此不是纯"行级 vs 分组"；且拼接来自 3 个不同训练集/不同截距的模型，pooled 排序可能由折间尺度差驱动、不是折内排序质量。另 λ 网格扩到 {…,10000} 使 row-level 5 折 λ 全=10000/3000（[r196.json:632-640](r196.json#L632)），"C130 口径"复现不成立（C130 网格≤1000）。 |
| ③ | 主统计量 gain 的 CI/MDE/δ_min/稳定带是否有 operational 理由 | **FAIL** | (a) 主 CI/MDE 用**细胞聚类**，不覆盖 held-out 药物/划分（审计目标单位）；drug MDE=0.153>δ_min=0.05、fold t-CI 含 0 → verdict 不成立（见 §0/§2.3）。(b) δ_min=0.05 的理由只是"项目反复使用的同类最小有意义差值（R195/A0）+ BRIEF 建议"（[PROTOCOL_R196.md:107](PROTOCOL_R196.md#L107)），不是从审计问题/决策意义推出来的 operational 定义；稳定带上界 0.20="C130 点估计 1.69 倍"（[:108](PROTOCOL_R196.md#L108)），为什么更大反而判不 replicated 没有理由（若用"可能泄漏/偏置"应写明并配诊断）。 |
| ④ | 对照（identity 常数、capacity、打乱标签、annotation-only）是否足够 | **PASS（附一条注意）** | 四类对照齐：identity 常数按显式约定记 0 且报告 constant 计数；capacity 10 seeds、shuffle 10 seeds（同角色药物层置换，保持水平大小多重集）；zero 校准 D6 通过（shuffle mean 0.0077、含 0；capacity mean 0.0009）；annotation-only 也报（0.1488）（[r196.json:229-250,905-1073](r196.json#L229)）。注意：capacity 只以"vs 0"的 gain 报告（因为 identity=0），没有额外"annotation 超过 capacity 的 CI"作为决策项——虽非必需，但报告应并列（这是 H196a 的零模型特异性证据）。 |
| ⑤ | 判定/措辞是否越界（replicated_under_audit 不能写外部复现/独立确认；weakened 不能写 C130 被推翻） | **WEAK** | 协议 §0 已把"不是外部复现/不是独立确认/不是决策/机制"写死（[PROTOCOL_R196.md:10-12](PROTOCOL_R196.md#L10)），词汇只有三档 ✓。但**当前 verdict 本身需要降级**（见 ③），否则 `replicated_under_audit` 会被读成"C130 审计后仍成立/量级稳定"；必须写死报告模板：replicated 只能说"在审计修正协议 + 固定药物划分/具体推断口径内增益为正且落在预注册带内"，不得写"C130 复现/确认/量级恢复/决策有用"；weakened 不得写"C130 被推翻"。 |
| ⑥ | 与 C130 原协议可比性（数据/端点/特征一致，不换指标/切分） | **WEAK** | 数据（Jaaks Original、SHA 一致）、端点 `SYNERGY_DELTA_EMAX`、聚合（cell×directed-combo mean）、特征（130 维 ID + 38 维双侧通路 one-hot）、65 药/125 细胞/2,025 有向对与 C130 同构 ✓（[r196.json:2-67](r196.json#L2)；[PROTOCOL_R196.md:16-24](PROTOCOL_R196.md#L16)）。但**协议不同**：R196=5 个确定性药物折、λ 网格扩到 10000、内层药物分组；C130=40 个重叠随机划分、λ≤1000、行级内层。**C130 的 CI [0.0947,0.1409] 不能当 R196 的参照区间**；R196 的 row-level 对照也不是精确 C130（网格/折数不同），必须在报告中写清"同数据/同端点/同特征，不同切分与调参协议"，并把 row-level 对照定位为"同一 R196 外层划分下的桥接诊断"而非"复现 C130"。 |
| ⑦ | 总判决 | **revise** | 见 §3；结果在 AMENDMENT 重跑前不得解释。 |

## 2. 关键理由与证据锚点

### 2.1 泄漏审计（①）：实现与协议一致，无测试标签泄漏

- 外层：`fa,fb=fold_of[a_idx],fold_of[b_idx]`；`te=(fa==f)&(fb==f)`、`tr=(fa!=f)&(fb!=f)`、one-seen 排除（[r196.py:265-280](r196.py#L265)）。药物按名称并集分折，anchor/library 同角色共留出（65 药、每折 13）。
- 内层：只在 `o['train']` 行上构造（`trmask`，[r196.py:292-306](r196.py#L292)）；held_j 与 inner-train 药物互斥（D2/D3 断言）；scaler 在每个内层训练折内拟合（[r196.py:139-144](r196.py#L139)）。
- 标签：`y_train = nan; y_train[o['train']] = y[o['train']]`，λ 选择/`fit_predict` 只接收 `y_train`；测试标签只在 `rho(pred, y[o['test']])` 读一次（[r196.py:369-380](r196.py#L369)）；D5 计数 135=5 folds×27 arms ✓（[r196.json:221-228](r196.json#L221)）。
- **唯一未覆盖的风险**：外层只有**一个**划分；泄漏检查没问题，但"无泄漏"≠"估计量对药物总体无偏/有功效"（见 2.3）。

### 2.2 内层口径（②）：药物分组正确，但 pooled 内层指标与 row-level 对照不可比

- `select_grouped` 把每个 inner fold 的验证预测与真值**拼接后算一个 Spearman**（[r196.py:147-152](r196.py#L147)）。三个内层模型训练集不同（34–35 药）、截距/尺度不同；拼接后的跨折排序会被折间偏移主导。λ 选择的 objective 因此不是"both-unseen 排序质量"的无偏估计。更稳妥的预注册方式：**折均 Spearman**（与 row-level 相同）或折内先标准化/秩变换再合并。
- `select_rowlevel` 的 `c130` 变体用折均（[r196.py:190-195](r196.py#L190)），`foldscaled` 变体又用 pooled（[r196.py:161-180](r196.py#L161)）→ H196b 的 rowlevel−grouped 差**同时**混入 scheme 与 inner metric 两种差异；`r196.json` 的 difference [−0.001018,−0.000118] 不能解释为"行级 λ 不乐观"的干净证据（[r196.json:617-641](r196.json#L617)）。
- λ 网格扩大到 10000 后，row-level 对照 5 折全选 10000/3000（[r196.json:632-640](r196.json#L632)），也不是 C130 的 λ≤1000 口径。H196b 的结论（无物质乐观）**只在"R196 外层划分 + 扩展网格"下成立**，不能回写为"C130 的行级内层没问题"。

### 2.3 主推断单位与判决（③，核心 FAIL）

- 预注册主单位=**细胞聚类**（[PROTOCOL_R196.md:79-81](PROTOCOL_R196.md#L79)；BRIEF 也写"CI 按细胞聚类（并报告按药物/双向聚类敏感性）"，[BRIEF:19](../2026-10-27-innovation-round-r196/BRIEF.md#L19)）。实现按协议执行（[r196.py:551-559](r196.py#L551)）。
- 但**审计的问题是"未见药物上的通路替代身份是否仍可靠"**（[BRIEF:5-9](../2026-10-27-innovation-round-r196/BRIEF.md#L5)），外推单位是药物/划分；`r196.json` 自己把 drug-cluster 与 fold dispersion 都算出来了，且显示：
  - drug-cluster CI **[0.0139, 0.2233]**（下界>0，但宽度≈0.21）；**MDE80_drug=0.1527 > δ_min=0.05**；
  - 5 个 held-out 药物 fold 的增益范围 **0.0118–0.2952**，fold t-CI **含 0**；
  - `reliability_qualifier` 明说 MDE80_drug>0.05、只有 5 折/每折 13 药（[r196.json:679-690](r196.json#L679)）。
- 按协议 §9 的"inconclusive = … MDE80_scoring > δ_min"（[PROTOCOL_R196.md:112](PROTOCOL_R196.md#L112)），实现把 `mde_scoring` 取成 cell MDE=0.032（[r196.py:650](r196.py#L650)）；若按审计目标单位取 drug MDE=0.153，则结论应为 **`inconclusive`**。当前 `replicated_under_audit` 相当于"用最窄的聚类口径通过、把最宽的口径放进 sensitivity"，这是**推断单位选择造成的结论翻转**。
- 另：δ_min=0.05 是"项目先例+BRIEF 建议"，不是 operational 定义（[PROTOCOL_R196.md:107](PROTOCOL_R196.md#L107)）；稳定带上界 0.20=0.1183×1.69 没有理由（[:108](PROTOCOL_R196.md#L108)）。上界本可用来标记"偏大可能是泄漏/偏置"，但协议没配任何诊断；作为先验可以保留，但必须写理由并报告"fold/药物异质性下的上界行为"。
- **5 折单划分**：C130 用 40 个（重叠）划分取均值；R196 只用一个 5 折划分，fold 间 SD 0.128 已显示"换一批药物"的波动，但协议没有预注册"划分/药物重采样"的主方差。审计"可靠性"必须包含这一层。

### 2.4 对照（④）：充分，但需并列"annotation vs capacity"的 CI

- 零模型校准 D6：shuffle mean 0.0077 含 0、capacity mean 0.0009 含 0（[r196.json:229-250](r196.json#L229)）；10+10 seeds；identity 常数显式约定（[PROTOCOL_R196.md:77](PROTOCOL_R196.md#L77)）；annotation-only 作为机制诊断（0.1488，[r196.json:1073](r196.json#L1073)）。
- 建议（非阻塞）：报告并列 `ρ(annotation) − ρ(capacity_seed0)` 的同一聚类 CI，以及 shuffle 分布的分位，作为"注释增益超过零模型"的直接对照；否则 `replicated_under_audit` 只有"vs 常数 0"的证据，capacity 只作校准。

### 2.5 措辞/可比性（⑤⑥）

- 协议已把"不是外部复现/独立确认/决策/机制"写死（[PROTOCOL_R196.md:10-12](PROTOCOL_R196.md#L10)），且判定只有三档（[:11](PROTOCOL_R196.md#L11)）。但**当前 verdict 需要降级**；报告模板必须写死：
  - `replicated_under_audit` 只能："在审计修正协议下、**在固定 5 折药物划分与声明的推断口径内**，both-unseen 增益点估计落在预注册带、主 CI 下界>0"，并**必须并列 drug-cluster CI/MDE 与 fold 离散**；若按审计目标单位（drug）应写 `inconclusive`（MDE>δ_min）或 `weakened`（fold t-CI 含 0）。
  - 不得写"C130 被复现/独立确认/量级恢复/决策有用"；`weakened` 不得写"C130 被推翻/注释无用"。
- 可比性：数据/端点/特征/单位同构 ✓，但切分与调参协议不同（5 确定性折 vs 40 随机、λ≤10000 vs ≤1000、内层药物分组 vs 行级）；**C130 的 [0.0947,0.1409] 不是 R196 的参照区间**；row-level 对照是"同一 R196 划分下的桥接诊断"，不是 C130 复现（[r196.json:617-641](r196.json#L617)）。
- 预注册诚实性：协议 §2 披露了**冻结前原型跑过 annotation-only 且 per-fold mean ρ≈0.149**（[PROTOCOL_R196.md:31-33](PROTOCOL_R196.md#L31)），最终 annotation-only=0.1488（[r196.json:1073](r196.json#L1073)）。规则（δ_min/band/λ 网格/折数）可追溯到 BRIEF/task-20（BRIEF 也写 0.05–0.20、0.1183 参照），因此**主 arm/identity/row-level 是未见过的**；但报告必须把这一"结果相邻的预冻结 peek"写成限制，不能写成"协议在读取任何响应之前冻结"。

## 3. 运行前必改（≤5；AMENDMENT + 重跑后才可解释 R196 结果）

> 由于主推断单位是冻结协议的一部分，这些修改属于 AMENDMENT；按 Lead 规则，**R196 现有 `replicated_under_audit` 在 AMENDMENT 重跑前作废**，不得写入解释/登记为"审计后仍成立"。

1. **主推断单位改为 held-out 药物/药物划分**：预注册主 CI/MDE = drug-cluster（或等价的"多药物划分 × 划分内均值"）；判决规则改为：`replicated_under_audit` 需 **drug-cluster CI 下界>0 且 drug-cluster MDE80 ≤ δ_min**（并报告 cell/pair/twoway 作敏感性）；按现有数字 drug MDE=0.153>0.05 → 重跑后应判 `inconclusive`（或按"fold 含 0"判 weakened），不得判 replicated。若 Lead 坚持 cell 聚类为主，则 verdict 必须限定为"固定药物划分内的细胞水平推断"，且禁止"C130 可靠/审计后成立"措辞。
2. **预注册多药物划分/划分方差**：至少 ≥10 个独立药物划分（或对 5 折划分做药物重采样/子采样并预注册统计量），主报告给出跨划分的分布/CI；fold dispersion 从"descriptive"升级为正式 sensitivity（当前 per-fold 0.012–0.295、t-CI 含 0，[r196.json:284-302](r196.json#L284)）。
3. **统一内层 λ 选择口径并隔离 H196b**：grouped 与 row-level 都用**折均 Spearman**（或都折内标准化后 pooled），预注册同一个 inner metric；row-level 另加 **C130 原网格（≤1000）**变体，作为"C130 口径桥接"；报告 λ 选择稳定性（当前 row-level 全触 10000，[r196.json:632-640](r196.json#L632)）。H196b 的"物质乐观"标记不能再用跨口径差异。
4. **δ_min/稳定带的 operational 理由 + 判决门槛联动**：δ_min=0.05 要写清它对应的审计/决策含义（不是"项目习惯"）；稳定带上界 0.20 要么给理由（如"超过原效应 1.69 倍提示偏置/泄漏"并配诊断），要么改为"不设上界，>0.20 只记录"。MDE 门槛必须在主推断单位上检查（与必改 1 联动）。
5. **措辞/可比性/预注册披露写进报告模板**：`replicated_under_audit`/`weakened`/`inconclusive` 的允许句式（§2.5 那三条）；明确"同数据/端点/特征，但 5 折、扩展 λ 网格、药物分组内层 → C130 的 CI 不是参照区间"；披露 §2 的预冻结 peek（annotation-only ≈0.149）并声明主 arm/identity/row-level 未在原型中运行；不得把 R196 写成外部复现/C130 复现/决策收益。

## 4. 声明与边界

- **不运行效果**：本挑战未重跑 R196、未改其任何产物；只读协议/代码/JSON，未读取除 R196 产物外的数据；脚本未写（复核均在阅读层完成）。
- **结果解释状态**：R196 结果**在 AMENDMENT 重跑前不得解释/采纳**；本挑战给出的是"当前冻结协议的主推断单位不匹配审计目标 + 内层/对照口径混用 + 措辞/可比性需固定"的判决，不改写 R196 的数字，也不否定"在同一固定划分内增益为正"这一观察。
- 若 Lead 选择不改：不得把 R196 登记为"C130 审计后 replicated"，只能登记为"inconclusive（审计目标单位 MDE 超 δ_min）"或"weakened（fold 含 0）"，并保留原始数字与本文档为记录。

**一句话：R196 的实现本身没有发现测试标签泄漏（① PASS），但冻结协议的"主 CI/MDE=细胞聚类"与审计目标"未见药物"不匹配——drug MDE=0.153>δ_min=0.05、fold t-CI 含 0；按协议自己的规则本应 `inconclusive`/`weakened`，现 verdict 是靠最窄口径通过的。判 revise：改主推断单位/多划分、统一内层口径、固定 δ/措辞后 AMENDMENT 重跑，结果才可解释。**
