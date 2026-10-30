# 阶段 2 复现协议独立挑战（R192-C2）：DrugComb both-unseen 粗注释替代身份

2026-10-27。角色：独立挑战者（非提案者、不执行、不润色）。对象：[PROTOCOL_STAGE2.md](PROTOCOL_STAGE2.md)（v1，标注 FROZEN）。本轮**不运行任何效果代码**（不拟合 identity/annotation/随机对照臂，不评估任何效应）；只做只读计数核验与协议审查。未改协议、其它目录、INDEX、SYNTHESIS、git。

## 0. 结论先行

**总判决：revise —— 必须在运行任何效果代码之前完成 ≤5 条硬性修订并重新冻结（AMENDMENT）；否则不得运行。**
这不是 stop：协议的骨架（先 pre-flight 后效果、端点/映射/切分先冻结、对照与停止条件齐备）是 190 轮来最接近可执行外部复现的一次；风险集中在"可复现目标量的定义"与"pre-flight 是否真的对齐判定规则"，都是运行前可修的。若 Lead 拒绝修订 1–3，则本轮不应运行，应降级为 `inconclusive/not_run` 并记录设计缺口。

**先确认做对的部分（不是放水，是核验结果）**：协议 §2/§3 的全部 pre-flight 预期数字，我用只读脚本从冻结输入独立重算，**逐项命中**：测试池 **32,299 单元 / 5,342 药对 / 108 细胞**；strict 训练池 **27,230 单元**；可分析水平 **93**；映射药 **1,800**；v2 表 SHA `705a5e64…686ed015` 与 summary SHA `e08e3d35…` 均与协议一致；r=0.20 的 v2 交叉核对 **3,056 单元 / 83,684 strict 训练**亦与 P-A2 一致（详见附录 A；脚本 [tmp/challenge_stage2_counts.py](../../../tmp/challenge_stage2_counts.py)，只读身份/计数，未拟合模型）。

**三个最致命问题：**

1. **主臂不是原冻结结论的估计量。** 原结论的"通路臂"是 **identity one-hot + pathway one-hot（Xboth）**，"增益"= ρ(Xboth)−ρ(identity)（[e163_tuned_headline.py:97-101,115-116](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:97)）。本协议主臂 `annotation` 只有 pathway one-hot（[PROTOCOL_STAGE2.md:44](PROTOCOL_STAGE2.md#L44)），少了 identity 列：训练设计、λ 选择与系数收缩都不同，**测的不是同一个量**。另外原注释是项目 38 水平通路模板（[SYNTHESIS.md:95](../SYNTHESIS.md#L95)），这里是 MSigDB KEGG 186→argmax 的 93 个可分析水平（[report_pa2.md:59](../2026-10-27-drugcomb-annotation/report_pa2.md#L59)），**注释体系本身也不同**。这两条使"δ_min=原 CI 下界"的跨端点/跨注释/跨 r 迁移失去基准。
2. **判定规则在运行前就没有被检定力覆盖。** F3 只对"ρ̂>1.96·SE"这一简化检验算 power，而主判定是 **点估计≥0.0947 且 CI 下界>0 且优于两个随机对照**（[PROTOCOL_STAGE2.md:64](PROTOCOL_STAGE2.md#L64)、[38](PROTOCOL_STAGE2.md#L38)）。点估计阈值在真值=δ_min 时通过率**恒为 50%**；把两个对照的 CI>0 也算进去，用协议自己的预期 MDE≈0.075 估算**完整规则在真值 0.1183 下的联合通过率只有约 0.63**，若 F3 实测 MDE 落在其门限边界 0.0947 则约 0.37（附录 B）。即：**即使原效应真的复现，本设计也大概率先给出 partial/not_replicated**——这是假阴性风险，不是保守。F3 必须模拟完整判定规则（含对照），否则 gate 与判定两张皮。
3. **BRIEF 强制披露/基线与 P-B 条件缺失，且 δ_min 与 BRIEF 冲突。** R192 BRIEF 冻结的决策规则是 `δ_min=0.1183`，要求 design gate `MDE80 ≤ 0.1183 且 power@0.1183≥0.80`（[BRIEF:18-19](../2026-10-27-innovation-round-r192/BRIEF.md#L18)），并要求阶段 2 协议写入：**"不假定跨 r 效应相等" + 训练有注释单元变化披露 + "本设计只能检验 ≳0.10、更小效应不可判定"**（[BRIEF:27](../2026-10-27-innovation-round-r192/BRIEF.md#L27)）；P-B 条件要求 **study/剂量代理分层敏感性**（[report.md:28](../2026-10-27-drugcomb-endpoint/report.md#L28)、[C164](../EVIDENCE_REGISTER.md#L202)）。协议 v1 **一条都没有**，却把主判定 δ_min 改成 0.0947（[PROTOCOL_STAGE2.md:10,68](PROTOCOL_STAGE2.md#L68)），没有 AMENDMENT 记录。在独立挑战看来这不是"更保守"，而是**换了判定目标**：BRIEF 目标是"复现头条效应量级"，协议目标是"点估计达到原 CI 下界"，两者对假阴性/假阳性的含义不同（见 §2.1/§2.5）。

## 1. 逐条判决表（task-11 第 1–10 条）

| # | 挑战项 | 判决 | 一句话理由 |
|---|---|---|---|
| 1 | 设计是否真的检验原命题；r=0.20→0.50 与 δ_min=0.0947 的正当性 | **FAIL** | "对应检验"只到假设类型层面；缺 BRIEF 强制的跨 r 声明/训练规模披露、"≥0.10 才可判定"声明；δ_min 与 BRIEF 的 0.1183 冲突且无 AMENDMENT；跨端点（ΔEMAX→bliss 矩阵均值）与跨注释体系（38→93 水平）迁移未论证。 |
| 2 | Pre-flight 数学：F3 on v2 池、F1 的门槛、F3 失败是否只能停、顺序是否固定 | **WEAK** | 顺序固定 ✓、预期数字全部实测命中 ✓、F3 在 v2 池重算 ✓；但 F1 的 14,387 是 Tier B（对 0.1183）下限，与协议自己的 Tier A 目标（22,451）不一致（F3 兜底，可接受）；F3 只对简化检验算 power（见第 5 条）；`r=0.55` 作为"预先声明敏感性"实际是词典序前缀切分（附录 A），且 v2 下 both-unseen 单元反而更少（32,076<32,299），不能当更大检定力的敏感性；F3 失败后 `r=0.55` 能否顶上的规则未写死。 |
| 3 | 泄漏与切分：内层 λ 按药分组、标准化、测试药、随机对照、F4 | **FAIL** | λ 按药分组 ✓、测试药不进标准化 ✓；但**标准化"在训练池拟合"=在外层训练池先算再切内层折**，正是 R163 被审计出的缺陷的一半（[handoff audit:7](../2026-10-27-handoff-method-audit/report.md#L7)；[e163:58-63](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:58) 同样在折划分前拟合 μ/σ）。F4 只有 4 条浅检查，不足以发现该泄漏与随机对照实现偏差；随机对照 5 次抽样的种子/算法/聚合规则未预注册；`r=0.55` 前缀切分本身是结构化切分偏差。 |
| 4 | 特征与模型：两侧单标签 one-hot、水平集合、共线性、λ、identity=0 的可比性 | **FAIL** | 主臂少了 identity 列（与冻结估计量不同，见 §0-1）；one-hot 与截距的共线/惩罚约定未写；λ 求解器/标准化后的惩罚尺度未写（原实现是 `G+diag(λ+1e-9(d+1))`，[e163:49-54](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:49)）；单位为"无序药对"而原分析按 anchor+library 定向键（[e163:86-90](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:86)），定向→无序的合并影响未披露。identity ρ=0 与原始 ρ=0.0001 的并列 sanity 写法 ✓。 |
| 5 | 统计推断：主判定过宽/过严、聚类 bootstrap 是否覆盖依赖、是否需 TOST/等价检验、对照多重性 | **FAIL** | 主 CI 用"按留出药聚类"，F3/MDE 用"药对×细胞双向"——判定与 gate 不同口径（[PROTOCOL_STAGE2.md:62](PROTOCOL_STAGE2.md#L62) vs [38](PROTOCOL_STAGE2.md#L38)）；未算完整判定规则的联合检定力（附录 B：约 0.63/0.37，<0.80）；点估计阈值不是"检验 δ_min"；5 次随机抽样的聚合规则未定义，两对照近乎同一种零模型（都保留大小多重集），实际是 10 次同分布抽样而非两类独立对照；缺"capacity 对照（同维随机块）"（原冻结结论的三对照之一，[SYNTHESIS.md:98](../SYNTHESIS.md#L98) C152/C97）。 |
| 6 | 混杂与选择偏差：44% 注释子集、study/剂量 η²=0.12–0.29、Jaaks 重合、tissue/细胞构成 | **FAIL** | BRIEF/P-B 要求的分层敏感性整段缺失；η²(study 代理)=0.1165、η²(block_id 分位)=0.2948、η²(细胞)=0.1891（[report.md:28,183](../2026-10-27-drugcomb-endpoint/report.md#L28)）与目标效应同量级，注释臂完全可以靠"哪些 study/细胞测了哪些药对"制造 ρ；只读核验显示注释测试池只占全宇宙 both-unseen 的 **36.5%**（32,299/87,989），且注释单元的多 block 比例（12.5%）是全体（6.1%）的 2 倍 → 选择偏差与暴露差异都真实存在，未披露、未处理。 |
| 7 | 失败/阴性解释边界 | **WEAK** | §8 已禁止机制/临床/独立确认 ✓；但未预注册"not_replicated 不得归因于条件结构不存在（construct mismatch vs power vs 真阴性三选一未定）"，也未写"replicated 只能称第二资源 r=0.50 子集上的方向性一致、不得称量级复现"。 |
| 8 | 预算与可执行性 | **WEAK** | 无 CPU/内存/单命令时限、无缓存/分步产物、无"preflight.json 通过才允许 stage2.py 运行"的运行时断言；identity 2×1,800 维可解析为常数（F4 已断言），但协议未说明避免稠密拟合；10 次随机对照 × 3 折 × 9 λ 的成本可接受但未写。 |
| 9 | 协议完整性：停止条件、失败类别、AMENDMENT、交付物、看结果后可调的漏洞 | **WEAK** | 停止条件/失败类别/交付物齐 ✓；但 AMENDMENT 只在页首一句、无流程约束；缺 BRIEF 强制披露三项（第 1 条）；随机对照聚合/种子、F3 完整规则 power、r=0.55 替补规则未定 = 存在"运行后按结果挑规则"的空间；F4 未覆盖第 3 条所列不变量。 |
| 10 | 总判决 | **revise** | 骨架可用、数字可核、但主臂估计量与判定规则必须先修；见 §3。 |

## 2. 逐条理由与证据锚点

### 2.1（第 1 条）它检验的是"同类条件结构"，不是"原估计量"；δ_min 迁移有三重未论证

1. **r 的 regime 改变没有写进协议。** 原效应 +0.1183 是在 Jaaks 的 **r=0.20 留药**下测得（[e163:107](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:107)；[report.md:7-9](../2026-10-27-agent-cell-identifiability-r163/report.md#L7)），40 次划分、平均评估键 4,457、MDE80=0.0344。协议改成 r=0.50：v2 下 strict 训练单元从 r=0.20 的 **83,684 → 27,230（−67.5%）**（我的实测；P-A2 的 r=0.20 数字 [report_pa2.md:66](../2026-10-27-drugcomb-annotation/report_pa2.md#L66)），both-unseen 单元从 3,056 → 32,299。P-B2 明确要求"**不假定跨 r 效应相等**……只保证若效应为 0.1183 则 80%+ 检定力，不保证效应一定存在或同样大"（[report_pb2.md:109](../2026-10-27-drugcomb-endpoint/report_pb2.md#L109)），BRIEF 也把它列为冻结时必须披露项（[BRIEF:27](../2026-10-27-innovation-round-r192/BRIEF.md#L27)）。**协议 v1 通篇没有这句披露，也没有训练单元变化的数字**——这不是措辞问题：协议随后用 δ_min=原效应 CI 下界作为主判定阈值（[PROTOCOL_STAGE2.md:10,68](PROTOCOL_STAGE2.md#L68)），实际上就是在假定 r=0.50 下至少达到 r=0.20 的保守效应。

2. **δ_min 与 BRIEF 的冻结决策规则冲突。** BRIEF §1b/§1c 写死 `δ_min=0.1183`（复现目标效应量级），gate 是 `MDE80≤0.1183 且 power@0.1183≥0.80`（[BRIEF:18-19](../2026-10-27-innovation-round-r192/BRIEF.md#L18)）。协议改成 `δ_min=0.0947` 并要求 F3 `MDE80≤0.0947 且 power@0.1183/power@0.0947 各≥0.80`（[PROTOCOL_STAGE2.md:38](PROTOCOL_STAGE2.md#L38)、[63-68](PROTOCOL_STAGE2.md#L63)）。后果是**设计门槛更严、判定门槛更松**：F3 要过需要比 BRIEF 更强的设计，但主判定允许在点估计 0.0947 时就宣布 replicated（比头条低 20%）。这在 P-B2 里是 Tier A（保守敏感性），不是主判据（[report_pb2.md:67-70](../2026-10-27-drugcomb-endpoint/report_pb2.md#L67)）。**改判定目标必须走 AMENDMENT 并由 Lead 明确重写 BRIEF 决策记录**；否则阶段 2 无论结果如何都会被质疑"赛前换靶"。

3. **δ_min 的"最保守可复现目标"说法在统计上不成立。** 0.0947 是原 95% CI 下界，不是"保守的复现目标"：若真值恰为 0.0947，点估计≥0.0947 的通过率恒为 50%；若真值为 0.1183，在协议预期 MDE≈0.075 下约 81%，实测 MDE 若在其门限 0.0947 附近则约 76%——再叠加两个对照比较，完整判定规则的联合通过率约 0.63/0.37（附录 B）。所以把 0.0947 写成"δ_min"会系统性地把"复现了但没达到点阈值"标成 partial，**下一步很容易被误读成"未复现"**。正确写法是 BRIEF 要求的那句："本设计只能检验 ≳≈0.10 的效应；更小效应不可判定"，并把量级判定明确降为"与原始 CI 的重叠/一致性描述"。

4. **跨端点 + 跨注释体系的双重构造差异。** `synergy_bliss`（整张剂量矩阵逐点 Bliss 残差均值）与 `ΔEMAX`（拟合 Emax 的效能对比）**不是同一统计量**，P-B 已书面写明（[report.md:146](../2026-10-27-drugcomb-endpoint/report.md#L146)）且不主张等价；原注释是项目 38 水平通路模板（[SYNTHESIS.md:95](../SYNTHESIS.md#L95)），DrugComb v2 是 KEGG 186 单标签 argmax 且 59.56% 并列、50.39% 单基因命中（[report_pa2.md:67-68](../2026-10-27-drugcomb-annotation/report_pa2.md#L67)）。因此"δ_min=原 CI 下界"同时假设了 r、端点、注释体系三重可比。协议 §0 只说"在 DrugComb v1.4 上的对应检验"（[PROTOCOL_STAGE2.md:10](PROTOCOL_STAGE2.md#L10)），没有把这三重差异写进判定与解释边界。

**判决 FAIL。** 可执行修改见 §3-1/§3-2。

### 2.2（第 2 条）Pre-flight 数字全部可核、顺序固定，但 gate 与判定规则未对齐

- **顺序与可核性（PASS）：** §3 明确"运行任何模型前必须先过"（[PROTOCOL_STAGE2.md:34](PROTOCOL_STAGE2.md#L34)），F1–F4 → §4 特征 → §5 模型；F3 用 P-B2 冻结方法在 **v2 实际池**重算而不是照搬 v1 数字（[PROTOCOL_STAGE2.md:38](PROTOCOL_STAGE2.md#L38)），符合 BRIEF（[BRIEF:27](../2026-10-27-innovation-round-r192/BRIEF.md#L27)）。只用零模型/端点结构、不拟合臂的 MDE 预计算也符合 P-B2 方法（[PROTOCOL_PB2.md:57-63](../2026-10-27-drugcomb-endpoint/PROTOCOL_PB2.md#L57)）。
- **数字核验（PASS，见附录 A）：** 协议 §2/§3 的 32,299 / 5,342 / 108 / 93 / 27,230 / 1,800 / 3,056 / 83,684 全部与冻结输入重算一致；SHA 一致。
- **F1 门槛（WEAK）：** 14,387 是 P-B2 Tier B（δ_min=0.1183）的外推下限，而 Tier A（δ_min=0.0947）对应 22,451（[report_pb2.md:57-62](../2026-10-27-drugcomb-endpoint/report_pb2.md#L57)）。协议 F1 用 14,387、F3 用 0.0947，两者在"最小可接受池"上不自洽；虽然 F3 是实际 gate，但 F1 的说明文字应改成"Tier B 下限；Tier A 目标见 F3"，避免运行者/F3 失败时用 F1 通过来救。
- **`r=0.55` 敏感性（FAIL 子项）：** 切分规则 `step=max(1,N//k)`（[PROTOCOL_STAGE2.md:29](PROTOCOL_STAGE2.md#L29)）在 N=1,800、r=0.55 时 `k=990, step=1` → 留出集 = **字典序前 990 个药**（我的核验：holdout 名字字母 0-9/a–l，train 只剩 m–z；[tmp/challenge_stage2_counts.py](../../../tmp/challenge_stage2_counts.py) → `r55_prefix_check.holdout_is_first_k_sorted=true`）。这不是准随机切分，是系统性前缀块；且 v2 下 both-unseen 单元 **32,076 < r=0.50 的 32,299**，比主设计还少，作为"更大检定力的敏感性"是反向的。P-B2 的 v1 PA_r55（23,014 单元、MDE 0.0912）按同一切分公式也会得到 `k=780, step=max(1,1418//780)=1` 的前缀切分（算术直接可得，[PROTOCOL_PB2.md:31-35](../2026-10-27-drugcomb-endpoint/PROTOCOL_PB2.md#L31)），所以 Tier A 的"r=0.55 可达"结论部分建立在一个有偏切分上——协议若把 r=0.55 当 fallback，必须先修切分定义（例如：按预注册种子的随机置换取 55%，或确定性 hash 排序后取前 k；并重算 F2/F3）。
- **F3 失败能否改用 r=0.55（未写死）：** §8 写"不换设计救"（[PROTOCOL_STAGE2.md:79](PROTOCOL_STAGE2.md#L79)），但 §2 把 r=0.55 预先声明为敏感性（[PROTOCOL_STAGE2.md:32](PROTOCOL_STAGE2.md#L32)），执行者完全可以在 F3@r50 失败后把 r=0.55 提为主设计。必须写死："F3 只在 r=0.50 主设计上计算；失败即停，r=0.55 不得替补"（或者反过来：若 Lead 想保留 fallback，必须在**任何 F3 计算之前**冻结一个唯一的"r=0.50→r=0.55 依次尝试"选择规则及其切分定义，并且只允许一次切换——见 §3-2）。

**判决 WEAK。**

### 2.3（第 3 条）防泄漏：λ 分组做对了，标准化时序重犯 R163 审计缺陷

1. **λ 内层 CV 按药物分组（PASS）：** §5 写"内层 3 折、按药物分组；内层验证 = 两药都在内层留出药的单元（both-unseen）"（[PROTOCOL_STAGE2.md:53](PROTOCOL_STAGE2.md#L53)），这正是 handoff audit 对 R163 的处置要求（[handoff audit:7,13](../2026-10-27-handoff-method-audit/report.md#L7)）。
2. **标准化时序（FAIL）：** §5 写"特征标准化（均值/方差只在训练池拟合）"（[PROTOCOL_STAGE2.md:52](PROTOCOL_STAGE2.md#L52)）。"训练池"是外层训练集；随后才切内层 3 折（[PROTOCOL_STAGE2.md:53](PROTOCOL_STAGE2.md#L53)）→ 内层验证折的标准化统计量来自包含它的外层训练池。这正是 R163 原实现的缺陷之一（[e163:58-63](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:58)：先对全训练集算 μ/σ、再 `rng.permutation` 切折），audit 原句点名"标准化在内层折划分前拟合"（[handoff audit:7](../2026-10-27-handoff-method-audit/report.md#L7)）。对 one-hot 特征、固定 λ 网格而言影响可能不大，但这是**已被审计点名、容易机械修好的泄漏**，没有理由保留；应改为"每个内层训练折内重新拟合 μ/σ；最终模型只用外层训练集拟合 μ/σ；测试集只变换"。
3. **测试药不进标准化/调参（PASS）：** 测试药只在最终打分出现（[PROTOCOL_STAGE2.md:54,73-74](PROTOCOL_STAGE2.md#L54)），设计意图正确。
4. **随机对照的抽样（WEAK/FAIL）：** §4.3/§4.4 写了"5 次抽样、保留大小多重集"（[PROTOCOL_STAGE2.md:45-46](PROTOCOL_STAGE2.md#L45)），但**没有预注册随机种子、抽样算法、以及 5 次结果如何合成主判定**（§6 只写"两个随机对照的 (annotation−对照) CI 下界>0"，[PROTOCOL_STAGE2.md:64](PROTOCOL_STAGE2.md#L64)）。这给"运行后挑一次能过/不能过的抽样"留下空间，且 10 次同分布抽样被当成两类独立对照（详见 §2.5）。
5. **F4 设计体检不足（FAIL）：** 现有 4 条（identity 常数、annotation 非常数、随机对照非常数、测试药不在训练、内层按药分组，[PROTOCOL_STAGE2.md:39](PROTOCOL_STAGE2.md#L39)）都太浅：无法发现标准化时序泄漏、随机指派是否精确保留大小多重集、spearman 的并列/midrank 处理、单位聚合是否与 P-B 一致、F3/CI 是否真用了同一聚类口径、测试标签是否参与任何选择（如切分/种子/对照抽样）。应把 F4 扩成"不变量断言 + 代码结构审计"，每条写进 preflight.json。
6. **`r=0.55` 前缀切分本身是切分偏差（FAIL）：** 见 §2.2；若作为敏感性出现在报告里，会让"敏感性一致"这一结论不可信。

**判决 FAIL。**

### 2.4（第 4 条）主臂估计量与冻结结论不同构；模型细节未冻结到可复现

1. **主臂缺少 identity 列（FAIL，最重要）：** 原"通路臂"= `Xboth = hstack([Xid, Xpath])`，原"增益" = ρ(Xboth) − ρ(Xid)（[e163:97-101,115-116](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:97)）；identity 在 both-unseen 测试上全 0 ⇒ 原 path 臂的测试预测实际由 pathway 系数承担，但系数是在"identity 列存在"的训练设计下估的。协议主臂 `annotation` 只有 pathway（[PROTOCOL_STAGE2.md:44](PROTOCOL_STAGE2.md#L44)），是一个不同的正则化/不同 λ/不同系数收缩的模型；没有 Xboth 臂就没有"与冻结结论同构"的主对比。可执行修改：主臂改为 `identity_plus_annotation`（features 同 R163：两侧 identity one-hot + 两侧 pathway one-hot；λ 同网格、同内层分组；测试时 held-out 药物的 identity 列全 0 但列仍存在），`annotation`（pathway-only）降为次臂；identity 臂仍作 ρ=0 对照。
2. **注释体系不同（必须在结果与解释里写死）：** 原 38 水平项目通路模板（[SYNTHESIS.md:95](../SYNTHESIS.md#L95)）vs 这里 KEGG 186 argmax 的 93 可分析水平（[report_pa2.md:59](../2026-10-27-drugcomb-annotation/report_pa2.md#L59)）；P-A2 已声明标签是"靶点基因集共属"粗代理、并列 59.56%、单基因 50.39%、taxane→tubulin 家族偏置仍在（[report_pa2.md:146,176](../2026-10-27-drugcomb-annotation/report_pa2.md#L146)）。判"复现"必须写成"同一假设类型（粗注释替代缺失身份）在另一注释体系/另一资源上的方向性一致"，不能写成"原通路块复现"。
3. **单位方向性（WEAK）：** 原分析键 `cell|ANCHOR_NAME + LIBRARY_NAME` 是 **anchor/library 定向**（[e163:86-90](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:86)）；协议用**无序药对**（[PROTOCOL_STAGE2.md:22](PROTOCOL_STAGE2.md#L22)）。DrugComb 的 block 有 row/col 语义，方向合并会把两种顺序的剂量安排平均在一起；应披露该差异，并做"仅 row→col 方向"或"有向键"的敏感性（若数据支持）。
4. **λ/求解器/截距/惩罚约定（WEAK）：** 协议给了 λ 网格（与原实现同，[PROTOCOL_STAGE2.md:52](PROTOCOL_STAGE2.md#L52)）但没写：是否惩罚截距、标准化后 `1e-9*(d+1)` 对角修正、one-hot 共线时解的唯一性、solver（原实现 [e163:49-54](../2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:49)）。这些不写，另一实现者复跑可能得到不同 λ/不同 ρ，尤其 one-hot 与 intercept 共线时。
5. **identity=0 的可比性（PASS）：** 协议"ρ 按定义 0、另报 ridge 数值 sanity"（[PROTOCOL_STAGE2.md:43](PROTOCOL_STAGE2.md#L43)）与原 identity ρ=+0.0001≈0 一致（[report.md:18](../2026-10-27-agent-cell-identifiability-r163/report.md#L18)），写法可接受。但需在报告里并列"常数预测/ρ 未定义"的数值证据，而不是只写 0。

**判决 FAIL。**

### 2.5（第 5 条）统计主线：CI 与 gate 不同口径；完整判定规则的检定力没有被算过；随机对照聚合未定义

1. **聚类口径不一致（FAIL）：** §6 主区间 = "bootstrap 按留出药聚类 1,000 次"（[PROTOCOL_STAGE2.md:62](PROTOCOL_STAGE2.md#L62)），另"按细胞双向聚类敏感性"；F3/MDE 用 P-B2 的**药对×细胞双向聚类**（[PROTOCOL_STAGE2.md:38](PROTOCOL_STAGE2.md#L38)、[PROTOCOL_PB2.md:53](../2026-10-27-drugcomb-endpoint/PROTOCOL_PB2.md#L53)）。问题是：**判定用的 CI 与 gate 验证过的 SE 不是同一个量**。只按留出药聚类不能覆盖"同一药对多细胞""同一细胞跨药对"的依赖（本池 90.6% 药对只有 1 个细胞、但少数药对带 89 个细胞；细胞不参与切分，108/108 测试细胞同时出现在训练池——我的核验，附录 A）。两种口径都可能偏低或偏高，但必须**同口径**：建议主 CI = 药对×细胞双向聚类（与 F3 一致），药聚类作敏感性；并把重采样算法写死（重采样药对+细胞后单元权重、midrank、并列处理），否则同一"bootstrap"可以做出不同 CI。
2. **完整判定规则的检定力缺失（FAIL，见 §0-2/附录 B）：** F3 只算 `ρ̂ > 1.96·SE` 的 power（[PROTOCOL_STAGE2.md:38](PROTOCOL_STAGE2.md#L38)、[PROTOCOL_PB2.md:59-62](../2026-10-27-drugcomb-endpoint/PROTOCOL_PB2.md#L59)），而主判定是复合规则（点估计≥0.0947、CI 下界>0、优于两个对照），[PROTOCOL_STAGE2.md:64](PROTOCOL_STAGE2.md#L64)。复合规则的 power 必须模拟：在 ρ=0.1183 下分别算"仅显著性""点估计通过""对照比较通过""全部同时通过"的经验概率；在 ρ=0.0947 下算点估计通过率（应≈50%）。用粗略近似（附录 B）预期约 0.6–0.8，**若 <0.80，F3 必须判 gate 不过或改判定规则**，不能只报单个 power 就放行。
3. **点估计阈值不是检验 δ_min（FAIL）：** "点估计≥δ_min"没有抽样误差控制；"CI 下界>0"只检验 >0。要声称"效应至少达到原 CI 下界"需要非劣性/等价检验（H0: ρ≤0.0947，单侧），但本设计 MDE≈0.075 时该检验对 ρ=0.1183 的 power 只有约 22%（需要 SE≈0.0095 才有 80%），不可行（见 §2.1-3）。因此正确做法不是加检验，而是**如实把 0.0947 判定降为描述性一致性、并在报告里显式写"本设计不能检验更小或等量级"**。
4. **随机对照聚合与多重性（FAIL）：** "两个随机对照 5 次抽样"实际是 10 次同分布抽样（shuffled_mapping 与 size_matched_random 都保留大小多重集；见 §2.7），协议却没写：(a) 每个对照取哪一次/均值/最大？(b) 若每抽一次都算一个比较，familiy-wise 水平未控；(c) 两对照高度相关，独立校正也不对。建议预注册：**主对照对比 = annotation − mean(10 次随机指派)**（或 10 次全部分布中位），用同一双向聚类 bootstrap 给一个 CI，并把逐次结果作敏感性；这样把"结构特异性"变成一个可检定的对比，同时避免 10 次比较的多重性与随机抽样挑结果。
5. **容量对照缺失（FAIL）：** 原冻结结论的对照清单是"同维随机块（容量）、打乱映射（结构）、死块（内控）"（[SYNTHESIS.md:98](../SYNTHESIS.md#L98)、C152/C97）；协议的 size_matched_random 与 shuffled_mapping 都保留大小多重集，**只覆盖"结构"一侧，缺"同维随机块/容量"对照**（随机块列数同真注释、但不保大小）。至少把其中一个改成 same-dim random block（不保大小），否则"win over random"不能排除容量/大小效应之外的替代（虽然 size-matched 已针对大小，但原结论的三对照设计是有意的）。
6. **单个确定性切分的抽样不确定性（WEAK）：** 主设计只有一个 r=0.50 确定性切分（PA，[PROTOCOL_STAGE2.md:29](PROTOCOL_STAGE2.md#L29)），原效应是 40 次随机划分的均值（[report.md:7-9](../2026-10-27-agent-cell-identifiability-r163/report.md#L7)）。单个切分上的 ρ 与"40 划分均值"不是同一估计量；不能因此拒绝，但应预注册"报告该单切分 + 按留出药的 uncertainy"，并在解释里写明。

**判决 FAIL。**

### 2.6（第 6 条）study/剂量/细胞构成混杂与注释子集选择偏差：协议一条都没处理

1. **BRIEF/P-B 要求的 study/剂量分层敏感性整段缺失。** P-B 明确写"阶段 2 必须披露并以分层敏感性处理"（[report.md:28](../2026-10-27-drugcomb-endpoint/report.md#L28)），P-B2 把它列为阶段 2 条件之一（[report_pb2.md:110](../2026-10-27-drugcomb-endpoint/report_pb2.md#L110) 附近 §6.2、以及 [C164](../EVIDENCE_REGISTER.md#L202)）。协议 §2 敏感性只有 r=0.55/E1/v1 映射/Jaaks 重合（[PROTOCOL_STAGE2.md:32](PROTOCOL_STAGE2.md#L32)），§6/§7 也没有。**这不是可选的**：v1.4 无 study 列，但 P-B 用 block_id 窗与 block_id 20 等分位做出了 study/design 代理，η²(study)=0.1165、η²(block_id 分位)=0.2948、η²(细胞)=0.1891（[report.md:183](../2026-10-27-drugcomb-endpoint/report.md#L183)）——三者都与目标效应 0.1183 同量级或更大。注释臂的预测只随药对变；只要"哪些药对出现在哪些 study/细胞矩阵"与 pathway 水平相关（DrugComb 的组合来自多个研究，药物组合的纳入本身有研究设计偏好），annotation 就能通过 study/细胞构成预测 y，而这不是"注释替代身份"的假设检验。**因此结果"显著"与"不显著"都在混杂未分层时不可解释。**
2. **细胞构成同样未处理。** 108 个测试细胞全部同时出现在训练池（我的核验：shared 108/108，train 109 cells），且 η²(细胞)=0.1891。预测是药对的（C141 同类），细胞构成决定 y 的构成；应至少预注册"按细胞分层/去细胞均值后"的敏感性。
3. **选择偏差在协议里零披露。** 只读核验：注释宇宙的 both-unseen r=0.50 测试池 32,299 单元 vs 全宇宙同切分 **87,989 单元** → 覆盖率 **36.5%**（药对 5,342/13,420=39.8%）；映射药 1,800/4,088=44.03%。注释子集不是随机抽样：P-A2 自己就声明"分析宇宙仅 23.16% 组合单元（选择偏差须披露）"（[C163](../EVIDENCE_REGISTER.md#L201)）。另外注释测试池的暴露更强：**12.5% 单元有 ≥2 个 block，而全宇宙 both-unseen 是 6.1%**（我算的；附录 A）——说明注释子集系统性偏向被重复研究过的药对/study。协议必须披露这两组数，并解释"复现只在 44% 注释子集的 36.5% 单元上成立"。
4. **Jaaks 重合（PASS 一半）：** 18 细胞/40 药/241 键作外部敏感性排除（[PROTOCOL_STAGE2.md:32](PROTOCOL_STAGE2.md#L32)、[C161](../EVIDENCE_REGISTER.md#L199)）——量级上可接受（241/32,299<1%），但它只是实体重合的下界（名称归一后的重合），且不影响"同一项目/同一注释体系"的独立性问题：DrugComb 的数据来自多个研究，但注释体系与模型是本项目的，这最多是"第二资源"复现，不是"独立确认"。

**判决 FAIL。**

### 2.7（第 7 条）阴性/阳性解释边界：原则对，但把"能说什么"写细

- 已有（PASS）：§8 禁止机制/临床证据、禁止把 DrugComb 复现写成 Jaaks 独立确认、禁止把 annotation 收益归因到 identity 之外（[PROTOCOL_STAGE2.md:81](PROTOCOL_STAGE2.md#L81)）；不换端点/指标（§7、§10）。
- 缺（WEAK）：
  - `not_replicated` 时**不能**说"该条件结构不存在"：必须并列三种未分辨解释——construct mismatch（端点/注释体系/r 变化/单切分）、power（本设计 MDE≈0.08–0.10，且复合判定功率不足）、真阴性；并报告本期 F3 的实际 MDE 与 CI 宽度。P-B/P-B2 已经写过"本判定不等于 DrugComb 不能复现"（[report.md:226](../2026-10-27-drugcomb-endpoint/report.md#L226)），协议应继承。
  - `replicated` 时只能写"在 DrugComb v1.4、synergy_bliss、v2 KEGG 映射、r=0.50 子集上的方向性一致"，不能写"效应量级复现"（除非另行说明量级 CI 与原始 CI 的关系）、不能写"独立确认"、不能写"注释有生物学/机制意义"（标签是靶点基因集共属粗代理，[report_pa2.md:176](../2026-10-27-drugcomb-annotation/report_pa2.md#L176)）。
  - `partial` 不要在报告标题/摘要里被折叠成成功或失败，应保留"显著性成立但量级/对照未过"的完整信息。

**判决 WEAK。**

### 2.8（第 8 条）预算与可执行性：可跑，但协议没写死

- 规模：训练池 27,230 行 × annotation 特征 2×93+intercept ≈ 187 维；identity 臂 2×1,800=3,600 维（27,230×3,600 float64 稠密≈784 MB，不建议稠密；且 identity 在测试集是常数，可解析处理）。随机对照 10 次 × 3 折内层 × 9 λ：annotation 维度小，ridge solve 27k×187 的 Gram 是 187²，成本秒级；总时间可接受。
- 缺（WEAK）：无 CPU/内存/单命令时限（BRIEF 是 ≤45 min，[BRIEF:38](../2026-10-27-innovation-round-r192/BRIEF.md#L38)）；无内存策略（稀疏 one-hot、identity 常数化）；无分步缓存（加载 193 MB CSV 一次、复用单位表）；无"preflight.json 判定通过 → stage2.py 才允许运行"的运行时断言（应写进代码：读 preflight.json，gate 不通过直接退出并记 `inconclusive`）。
- 建议在 AMENDMENT 里补：预算上限、内存策略、`preflight.json` schema（F1–F4 每项 pass/fail + 实测值 + SHA），以及 stage2.py 的 gate 断言。

**判决 WEAK。**

### 2.9（第 9 条）协议完整性：有骨架，但有"看结果后可调"的口子

- 已有（PASS）：F1–F4 停止条件（[PROTOCOL_STAGE2.md:34-39](PROTOCOL_STAGE2.md#L34)）、判定四档与 failure categories（[PROTOCOL_STAGE2.md:63-67](PROTOCOL_STAGE2.md#L63)）、"不换端点/指标/不加模块"（[PROTOCOL_STAGE2.md:79-81](PROTOCOL_STAGE2.md#L79)）、交付物列表（[PROTOCOL_STAGE2.md:85-90](PROTOCOL_STAGE2.md#L85)）。
- 缺口/漏洞（WEAK→需修）：
  - AMENDMENT 只在页首一句（[PROTOCOL_STAGE2.md:3](PROTOCOL_STAGE2.md#L3)），没有"哪些改动必须 AMENDMENT、谁批准、必须在何时（看效果前）重新冻结"的流程约束。本挑战 §3 的修订应作为 AMENDMENT-001 记录并升版本，然后**重新跑一次独立挑战或至少 Lead 复核**，否则协议仍是 v1 冻结但已悄悄变形。
  - BRIEF 强制披露三项缺失（§2.1-1/2）。
  - 随机对照 5 次的种子/算法/聚合、F3 完整规则 power、r=0.55 替补规则未定（§2.3/2.5/2.2）。
  - F2 的"映射表与 v2 表 SHA 一致"只校验了一个输入，未把 summary/pb2 的 SHA 与数值断言写进 preflight.json（建议照 PB2 的做法）。
  - "F3 不过 → 停"与"r=0.55 敏感性"并列，存在运行后选择设计空间（§2.2）。
- 注意：原 P-B/P-B2 的交付纪律（确定性、SHA、无时间戳、preflight 断言）做得很严，本协议 §9 只列文件名，没有继承这些约定；建议把 PB2 的确定性/哈希/断言模板搬过来。

**判决 WEAK。**

## 3. 运行前必改项（≤5；全部完成并写 AMENDMENT-001、升协议版本、由 Lead 重新冻结后才可运行）

> 排序按"若不改则结果不可解释"的严重程度；每项都可在**不跑效果**的前提下完成（只涉及设计文本、preflight 代码与只读统计）。

**必改 1｜把主臂改回与冻结结论同构的估计量，并明确"复现"的定义层级。**
- 主臂改为 `identity_plus_annotation`（features = 两侧 identity one-hot + 两侧 S1 pathway one-hot；λ 网格/内层 3 折按药分组同协议；held-out 药物 identity 列在测试集全 0 但列保留），与 `identity` 臂（ρ=0 约定）作主对比；`annotation`（pathway-only）降为次臂/敏感性。
- 在 §0/§6 写死复现定义：本实验只能检验"**同一假设类型**（粗注释替代缺失身份、both-unseen 排序）在第二资源、不同注释体系（KEGG 186 argmax，93 可分析水平 vs 项目 38 通路模板）、不同端点（synergy_bliss 矩阵均值 vs ΔEMAX）、不同 r（0.50 vs 0.20）上的**方向性/结构一致**"；量级判定只作描述性一致性。
- 正文补"注释体系差异 + 端点非同一统计量 + 定向/无序药对差异"三条构造披露（可抄 P-B §8.3/C4，[report.md:146](../2026-10-27-drugcomb-endpoint/report.md#L146)）。

**必改 2｜解决 δ_min 与 BRIEF 的冲突，把"本设计能检验什么"写死。**
- Lead 二选一并记录：(a) 遵守 BRIEF，主判定 δ_min=0.1183（Tier B）；0.0947 只作 Tier A 敏感性；或 (b) 明确 AMENDMENT 把主判定改为 δ_min=0.0947（Tier A），同时把复现目标重写为"点估计达到原始 CI 下界 + 方向一致"，并在摘要禁止"复现头条量级"表述。
- 无论哪条，补 BRIEF 强制三句：**"不假定跨 r 效应相等"**；**训练有注释单元变化披露**（v2 r=0.20 strict 83,684 → r=0.50 strict 27,230，−67.5%；both-unseen 3,056 → 32,299）；**"本设计只能检验 ≳≈0.10 的效应；更小效应不可判定"**。
- 写明主判定点的统计含义：0.0947 是"点估计阈值 + CI>0"，**不是**"效应≥0.0947 的检定"；报告必须并列 annotation ρ、95% CI、与原始 CI [+0.0947,+0.1409] 的重叠/差距。

**必改 3｜统一 CI 与 gate 的聚类口径，并把 F3 改成"完整判定规则的检定力"。**
- 主 CI 用与 F3 相同的**药对×细胞双向聚类 bootstrap**（B=2,000，同 PB2 算法；单元权重、midrank、并列处理写死）；药聚类作敏感性；两口径都必须报。
- F3 增加：在 ρ∈{0, 0.0947, 0.1183}` 下模拟**完整判定规则**（annotation ρ 点估计≥δ_min、CI 下界>0、优于对照）的联合通过率；要求 `P(完整判定 = replicated | ρ=0.1183) ≥ 0.80`。用协议自己预期 MDE(≈0.075) 的粗算已在 §0-2/附录 B 显示可能只有约 0.63（对照若按 95% CI 双侧）——**F3 若不过，停在 F3，不进入效果**；或按下面"对照聚合"修改后再算。
- 随机对照改为**一个主对比**：annotation − mean(10 次随机指派) 的双向聚类 CI>0（逐次结果作敏感性）；预注册 10 个种子与指派算法；至少把一个对照改成 **same-dim random block（不保大小）** 以覆盖原冻结结论的"容量"对照（[SYNTHESIS.md:98](../SYNTHESIS.md#L98)）。
- 修 `r=0.55`：若保留敏感性，切分定义改为预注册随机置换（种子固定）后取 55%，并在 preflight 重算 F2/F3；同时写死"F3@r=0.50 失败即停，r=0.55 不得替补"（或提前冻结唯一 fallback 规则）。

**必改 4｜修标准化泄漏 + 强化 F4 为不变量断言。**
- 标准化：每个内层训练折内重新拟合 μ/σ（内层验证折、外层测试集只做变换）；最终模型只用外层训练集拟合 μ/σ。与 R163 审计原句对齐（[handoff audit:7](../2026-10-27-handoff-method-audit/report.md#L7)）。
- F4 增加断言（写进 preflight.json）：① 内层折药物互斥且每折验证单元>0；② 标准化统计量只由该折训练行计算（代码级断言/审计）；③ 随机指派精确保留真实水平大小多重集（逐水平计数相等），固定种子、10 次独立；④ shuffled/size-matched 不读取任何 y（代码级白名单审计）；⑤ identity/constant 测试预测逐行相等（常数）；⑥ 单位聚合与 P-B 冻结一致（每单元 block 均值，missing 处理；核对 blocks/units 数）；⑦ 测试药不出现在任何训练/标准化/λ 选择中；⑧ 输入 SHA 与协议表一致（mapping v2 `705a5e64…686ed015`、summary `e08e3d35…`，已核）。
- 报告与 stage2.py 必须读取 preflight.json 的 gate；gate 不通过直接 `inconclusive` 退出（代码断言，不只是文档）。

**必改 5｜补 study/剂量/细胞构成混杂与选择偏差处理（BRIEF/P-B 条件，缺则结果不可解释）。**
- 预注册分层敏感性：用 P-B 的 block_id 20 等分位与 study 代理窗口（[report.md:169-185](../2026-10-27-drugcomb-endpoint/report.md#L169)）对测试单元分层，报每层 annotation ρ（样本不足的层合并并披露）；并报"y 减去 study 代理/细胞均值后"的 annotation ρ（去混杂敏感性）。
- 披露选择偏差：注释测试池占全宇宙 both-unseen r=0.50 的 **36.5%**（32,299/87,989；药对 39.8%）；注释子集单元的多 block 暴露 12.5% vs 全宇宙 6.1%；映射药 44.03%。解释写死"结论只适用于注释子集/该端点/该 r"。
- 细胞构成：报 cell 覆盖（108/112、108 个测试细胞全部也出现在训练池）、按细胞分层或去细胞均值的敏感性；说明预测为药对级（C141 同类），细胞构成是混杂/方差来源。
- `not_replicated`/`replicated` 的措辞按 §2.7 写死；`partial` 不得折叠。

## 4. 若 Lead 不采纳必改 1–3 的处置

- 不得运行效果代码。记录 `inconclusive / design_not_ready`（失败类别：`evaluation_cannot_distinguish` + `design_mismatch`），把本挑战列出的三项（主臂不同构、判定规则未检定力化、δ_min/BRIEF 冲突）作为明确缺口；下一资源/下一轮再冻结。
- 若只采纳 1–2 而不采纳 3（F3 完整规则 power），仍不得运行：因为 gate 通过也不能保证判定规则可执行。
- 若 Lead 决定把本阶段降级为"探索性/描述性"，必须在协议里明确写死"本轮不宣称 replicated，只报 ρ 与 CI"，并按 BRIEF §1c 的"更小效应不可判定"披露；不接受"跑完再看结果决定叫不叫复现"。

## 5. 声明与边界

- **本轮不运行效果实验**：本挑战未拟合 identity/annotation/随机对照臂、未评估任何效应、未改协议/PROTOCOL/INDEX/SYNTHESIS/git/其它研究目录；只写本文件与 `tmp/` 只读脚本。
- 只读核验的性质：计数与 SHA 核验（`tmp/challenge_stage2_counts.py`）只使用身份列、映射表与 `synergy_bliss` 的存在/块计数，用于核对协议 §2/§3 的预期数字与结构；**没有**用这些计数估计任何臂的效应或与注释相关的相关。
- 本挑战的判定以**运行前可完成**的修改为准；不代替 Lead 决定 δ_min 方向，只要求"选了哪一种就必须显式记录并重写 BRIEF 决策记录"。

---

## 附录 A：只读计数核验（脚本 [tmp/challenge_stage2_counts.py](../../../tmp/challenge_stage2_counts.py)；输出 `tmp/challenge_stage2_counts.json`）

**与协议 §2/§3 的预期逐项对照（全部命中）：**

| 量 | 协议预期（PROTOCOL_STAGE2） | 我实测 | 一致 |
|---|---|---|---|
| 映射药 N | 1,800 | 1,800 | ✓ |
| 测试池 units / pairs / cells（r=0.50 PA） | 32,299 / 5,342 / 108 | 32,299 / 5,342 / 108 | ✓ |
| strict 训练 units | 27,230 | 27,230 | ✓ |
| 可分析水平（PA r=0.50，G2 定义） | 93 | 93 | ✓ |
| both-unseen v2 r=0.20（交叉核对 P-A2） | 3,056 | 3,056 | ✓ |
| strict 训练 v2 r=0.20（P-A2） | 83,684 | 83,684 | ✓ |
| 组合块 / cell×pair 单元 / U / 细胞 / 药对 | 466,033 / 380,418 / 4,088 / 112 / 62,826 | 同 | ✓（P-B） |
| 注释宇宙单元（两药均映射） | 120,162（P-A2） | 120,162 | ✓ |
| mapping_table_v2 SHA256 | `705a5e64…686ed015` | `705a5e6476319b58…686ed015` | ✓ |
| summary_table_v1.4 SHA256 前缀 | `e08e3d35…` | `e08e3d35bfa4bea0…08037a2f` | ✓ |

**协议未写、但运行前应知道的四个结构事实（我算的；只读计数，非效应）：**

1. **`r=0.55` 敏感性切分是词典序前缀，不是准随机**：N=1,800、k=990、step=max(1,1800//990)=1 → 留出 = 排序后前 990 个药；留出名字字母 `12346789abcdefghijkl`，训练只剩 `mnopqrstuvwxyz`。且 v2 下 r=0.55 的 both-unseen 单元 **32,076 < r=0.50 的 32,299**，药对 6,917/训练 27,111；它不能当"更大检定力"的敏感性，更不能当 F3 失败后的替补（见 §2.2）。
2. **选择偏差量化**：全宇宙（4,088 药）PA r=0.50 的 both-unseen = **87,989 单元 / 13,420 药对 / 110 细胞**；注释测试池 32,299 = **36.5%**（药对 39.8%）。注释子集的多 block 暴露：**12.5%** 单元有 ≥2 blocks，全宇宙同池 **6.1%**；strict 训练池 5.8%。
3. **测试池药对稀疏**：5,342 个测试药对里 **4,839 个（90.6%）只有 1 个细胞**（每对细胞数中位 1、最大 89）；所以 32,299 单元的有效独立结构与 5,342 对/108 细胞的双向聚类强相关，CI 必须按双向聚类检查（§2.5）。
4. **细胞不参与切分**：108 个测试细胞全部也出现在训练池（训练池 109 细胞），细胞级 η²=0.1891（[report.md:183](../2026-10-27-drugcomb-endpoint/report.md#L183)）→ 需要细胞构成/去细胞均值敏感性（§2.6）。

## 附录 B：完整判定规则联合检定力的近似（仅数量级；正式值须由 F3 按冻结算法模拟）

判定规则（[PROTOCOL_STAGE2.md:64](PROTOCOL_STAGE2.md#L64)）：replicated ⇔ ρ̂ ≥ 0.0947 ∧ 95% CI 下界 >0（≈ρ̂ > 1.96·SE）∧ 两个随机对照的 (annotation−对照) 95% CI 下界 >0。假设检验近似：ρ̂ ~ N(ρ, SE²)，对照真值 0、SE 与 annotation 同量级（`SE_diff≈√2·SE`，忽略相关；正式值需要按药对×细胞双向聚类模拟，见必改 3）。

| F3 实测 MDE80(双向) | SE=MDE/2.8016 | ρ=0.1183 下"点估计≥0.0947" | ρ=0.1183 下每对照 CI>0（双侧 1.96） | 两对照联合 | **完整规则（近似）** |
|---:|---:|---:|---:|---:|---:|
| 0.075（协议预期） | 0.0268 | 0.811 | 0.878 | 0.771 | **≈0.63** |
| 0.0947（F3 门限边界） | 0.0338 | 0.757 | 0.697 | 0.486 | **≈0.37** |
| 0.085（介于两者） | 0.0303 | 0.786 | 0.797 | 0.635 | **≈0.50** |

（点估计阈值在真值=δ_min=0.0947 时通过率恒为 50%——这是构造性的，不是样本量问题；所以"δ_min"不能读作"设计能检出的最小效应"。）

**含义：** 若 Lead 保留当前复合判定，F3 必须证明完整规则在 ρ=0.1183 下 ≥0.80；按上表，协议预期的 MDE 也不够（≈0.63，除非随机对照按"annotation−mean(10 次)"聚合后差异 SE 变小、或删去点估计阈值）。这是运行前必须解决的设计量，不是结果解释问题。

---

**一句话给 Lead：数都对、骨架可用，判 revise 不是 stop——但主臂少了 identity 列、δ_min 与 BRIEF 冲突且跨 r/端点/注释体系迁移未声明、完整判定规则从未被 F3 检定力化（按协议自己的预期 MDE 也只有约 0.63 的通过率）、标准化时序重犯 R163 审计缺陷、study/剂量混杂与 36.5% 注释子集选择偏差整段缺失。五条必改完成后写 AMENDMENT-001、升版本、Lead 重新冻结，再运行。**
