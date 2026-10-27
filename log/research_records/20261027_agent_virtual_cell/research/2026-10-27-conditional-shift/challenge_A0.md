# R193-A0 匹配资格审计独立挑战（task-14）：条件偏移 Q 可复验性

2026-10-27。角色：独立挑战者（非提案者、不执行 A1、不读响应估 Q）。对象：[PROTOCOL_A0.md](PROTOCOL_A0.md)（冻结版）、[a0.py](a0.py)、[a0.json](a0.json)、[matched_conditions.csv](matched_conditions.csv)、[matched_quadruples.csv](matched_quadruples.csv)、[report.md](report.md)、[record.md](record.md)，以及（审查执行面时一并读的）[PROTOCOL_Q_DRAFT.md](PROTOCOL_Q_DRAFT.md)。**本轮不运行 Q/效果**：未拟合任何模型、未估计任何 Q/相关/预测性能、未读取任何响应值；只做只读计数与元数据核验。未改 A0 产物、其它目录、INDEX、SYNTHESIS、git；只写本文件与 `tmp/` 脚本。

## 0. 结论先行

**总判决：revise —— A0 匹配合格本身成立、头部门槛全部独立复现；但 A1（PROTOCOL_Q）在冻结前还有必须写死的设计选择与功效/混杂预注册，当前 DRAFT 不能公正执行。改完 ≤5 条必改即可 proceed；本轮不运行 Q。**

**独立复核（只读）先给正面结论**——A0 的资格结论不是空话：我用独立实现从冻结输入重算，**以下全部逐项命中**：结构计数（Original 296,707 行/剔除 5,527/有效 291,180；Validation 23,505/158/23,347；125/97 细胞、1,975/130 有向药对、4,528/295 条件、3,106/454 barcode）、重叠（96 细胞/130 有向药对/**9,154** cell×condition 共同键、barcode 集合交集 0、范围 14,482–39,392 vs 33,044–63,257）、复制层级（R0 4,034,637,772 / R1 177,515,510 / R2 214,664,684 / **R3 802,445** / **R4 6,223,367**）、R4 覆盖（**96 细胞/291 条件/98 有向药对/3,418 细胞对**、组织 33/35/28）、R4 分层（controlled_anchor **92,039**、same_anchor_any_conc 568,029、same_library 309,351、same_tissue 6,217,553 / cross_tissue 5,814）、barcode 分半 R4 **43,208,857**、`matched_conditions.csv` 与原始共同键**完全等价**、五份产物 SHA256 与 report 声明**逐字节一致**。响应盲也经代码审计：`a0.py` 的 `META_COLS` 不含任何响应列，端点只做空串存在性检查、不做数值转换（[a0.py:21-27,58-76](a0.py#L21)）。

**但发现三处必须先处理的实质问题：**

1. **A1 DRAFT 仍是一个"选择菜单"，不是一个冻结协议（最致命）。** [PROTOCOL_Q_DRAFT.md](PROTOCOL_Q_DRAFT.md) 的主统计量、聚合方式、条件对分层、零分布、δ_min 理由、MDE 算法都还开着：P1/P2/P3"挑战后定"（[:21-24](PROTOCOL_Q_DRAFT.md#L21)）、median 或 mean"先冻结"（[:22](PROTOCOL_Q_DRAFT.md#L22)）、δ_min=0.10 只是"建议"且无理由（[:30](PROTOCOL_Q_DRAFT.md#L30)）、零分布列两个候选未定主次（[:25-28](PROTOCOL_Q_DRAFT.md#L25)）、MDE"用置换/解析"未写死（[:30](PROTOCOL_Q_DRAFT.md#L30)）、也没有对**完整判定规则**（点≥δ_min ∧ CI>0 ∧ 优于零分布）做功效模拟。R192 的教训正是这一步没做：null MDE 只是设计步，实际拟合臂 realized SE 可差 2 倍以上（MDE 0.067 vs ≈0.150），且联合规则功效必须单独模拟（[R192 record:11,29,46](../2026-10-27-innovation-round-r192/record.md#L11)；[stats_audit:121-129,199](../2026-10-27-independent-reassessment/stats_audit.md#L121)）。**在 A1 冻结前不把这些写死，就存在"看到 Q 再选统计量/分层/δ"的空间，R192 已证明这类协议不能作为可引用结果。**
2. **Q 的构造天然保留 cell×单药/剂量项，"可复验"很可能是普通药理学稳定性，而不是条件结构。** 2×2 回路只消去**加性 cell 主效应 + 加性 condition 主效应**；展开后 Q 仍含 (i) cell×单药效应（p,q 共享 anchor 时：cell×libB−cell×libC；p,q 不共享药时：四个 cell×药项）、(ii) p,q 剂量不同的 cell×剂量效应、(iii) 端点/拟合误差、(iv) screen×condition 项。A0 §5/§7 已诚实指出单药参照在 A0 为 DENY、H193b 需要 A1 解禁（[report.md:81-88](report.md#L81)），但 **A1 DRAFT 只把 H193b 写成"次要但先冻结"且"若不可用则记录限制、不强行"**（[PROTOCOL_Q_DRAFT.md:8,29](PROTOCOL_Q_DRAFT.md#L8)）。我核验了单药列：两个 fitted 表都含 `ANCHOR_VIABILITY`/`LIBRARY_EMAX` 等 7 列且**空值为 0、无非数值哨兵**（附录 B），所以"不可用"不成立——A1 必须把 additive/single-agent adjusted Q 写成**必做的主解释项**，并写死调整公式，否则 Q 复验成立也只能读作"单药敏感性/剂量设计跨 screen 稳定"。
3. **A0 产物有两处可复现的计数/口径不一致（不改资格，但 A1 会直接复用，必须先勘误）。** (a) `disjoint_pairs`：report/a0.json 报 **5,345,987**，但按"不共享任何 drug id（含反向 p.anchor=q.library 等）"应为 **4,612,633**（差 733,354；a0 公式 `u−same_anchor−same_library` 漏掉了跨朝向共享，[a0.py:310](a0.py#L310)）。(b) G1-only/G2-only 用的是"同一**有向**药对才剔除"（[a0.py:183-204](a0.py#L183)），而冻结定义 M3 是"同一**无序**药对剔除"（[PROTOCOL_A0.md:52](PROTOCOL_A0.md#L52)）；M3 一致口径是 **4,412,540,421 / 7,234,325**，不是报告的 **4,415,971,041 / 7,301,337**。两处都不改变 R4≥500 等四个 gate（R4 用无序口径，我已复现 6,223,367 正确），但 A1 若按分层/单组计数选子设计会被误导。另：`matched_conditions.csv` 的条件级有向药对是 **129** 个（不是 130；一个共同有向药对没有匹配到共同剂量条件元组），report §4 的 130 是药对级重叠，A1 必须写清用的是 129。

**给 Lead 的最致命 3 条：** ① PROTOCOL_Q 仍是开放菜单（主统计量/聚合/分层/零分布/δ_min/MDE 未冻结，且无完整规则功效模拟）→ 冻结前必须写死并校准；② Q 保留 cell×单药/剂量项，H193b adjusted-Q 当前是可选的"若不可用则不强行"，必须升级为必做主解释项（单药列实测可用）；③ A0 有两处计数口径错误 + 129/130 不一致，以及 Validation 选择偏差未披露（R31 已说验证筛"极可能就是挑过的子集"）——A1 复用前先勘误并预注册选择偏差诊断。

## 1. 逐条判决表（task-14 第 1–6 条）

| # | 挑战项 | 判决 | 一句话理由 |
|---|---|---|---|
| 1 | 匹配是否响应无关；剂量/方向/端点/screen 是否真可比；无序聚合是否掩盖方向/剂量 | **WEAK** | 响应盲已代码+计数核验 ✓；方向/端点/screen 都按冻结口径匹配 ✓；但剂量只到已发布设计列（完整 library 浓度点集不可得，且 R28/R31 已知 Validation 浓度与 Original 不同，匹配实际落在"共享设计元组"子集），孔级等价不可验证 → 只能当"设计列层面可比"；条件 p,q 之间剂量可不同，Q 会混入剂量对比（A1 必须分层/写死）；A0 的 `disjoint_pairs` 口径另有错（见 §0-3）。 |
| 2 | 四元组门槛≥500、独立组、2×2 回路可估性/残留项、MDE 先写死 | **WEAK** | R4=6.22M≫500 且两独立组 barcode 不相交（我已复现）✓；2×2 回路确能消去加性 cell/condition 主效应 ✓；但 500 只是被明确标注的 floor，不是 Q 复验功效；Q 残留 cell×单药、剂量、屏幕×条件、拟合噪声，A1 DRAFT 的 MDE/完整规则功效仍是占位；6.22M 是嵌套计数、有效单元≈96 细胞/129 有向药对/291 条件层面，A1 必须先冻结聚类与 MDE（R192 教训）。 |
| 3 | 批次/日期与细胞可分性、单药参照可用性、主张降级 | **WEAK** | A0 正确报告 screen 与批次完全混淆、只能主张"跨 screen 条件稳定性" ✓；单药列存在但 A0 DENY，我已核验两表 7 个单药列**空值 0、无非数值** → A1 可执行，但 DRAFT 把它写成可选、不强行 → 必须升级为必做；A0 未披露已知的 **Validation 选择偏差**（R31：验证筛仅 4.4% 键、"极可能就是挑过的子集"；F9：96/125 细胞、组织构成偏移）与回归到均值风险——这会直接抬升/压低 Q_A 与 Q_B 的相关，A1 必须预注册诊断与限定。 |
| 4 | δ_min/MDE/零分布/停止规则是否先冻结；事后择优漏洞 | **FAIL** | PROTOCOL_Q_DRAFT 未冻结且留 6 个以上开放选择（P1/P2/P3、median/mean、条件对分层、零分布主次、δ_min 理由、MDE 算法），且无完整判定规则的功效/假阳校准；δ_min=0.10 无 operational 定义与理由（BRIEF 要求"最小有用条件偏移"，不能用旧 CI 倒推，[BRIEF:31](../2026-10-27-innovation-round-r193/BRIEF.md#L31)）；无 q1.py 运行时 gate（MDE 通过才允许算 Q）；无 within-screen barcode-split 参照（A0 已给，但只覆盖 46 细胞/583 细胞对，见附录 A）。 |
| 5 | 是否只是旧有限交互筛选/R5 反序改名 | **WEAK** | 结构上不是：本设计不做"两个固定交互族选一个"（[eight_directions_20261026/report.md:27,31](../eight_directions_20261026/report.md#L27)）、不重跑 R5 反序、Q 不要求反转、不做模型/算法选择、也不做 acquisition/Agent；A1 DRAFT §0 已写"不用大间隔/反序挑四元组" ✓。但 A0/report **没有写谱系声明**，且"Q 复验成立"很容易被读成"支持某个交互模型/算子"——必须在 PROTOCOL_Q 写死：不是旧路线重启、不得用 Q 结果反推交互族选择、不得称新算法（BATCHIE 类细胞嵌入×药物交互模型已是直接强先例，[independent-reassessment/report.md:85](../2026-10-27-independent-reassessment/report.md#L85)）。 |
| 6 | 总判决 | **revise** | A0 资格成立且可复现，但 A1 协议尚未冻结、功效/混杂/选择偏差的预注册缺口是运行前可修的；见 §4。若 Lead 不采纳必改 1–3 → 不得运行 A1，记 `design_not_ready` 并回"普通加性/静态先验"解释，不开新算子。 |

## 2. 逐条理由与证据锚点

### 2.1（第 1 条）匹配合格是"设计列层面"的：响应盲 ✓、方向/端点/screen ✓、剂量等价 ✗

- **响应盲（PASS，双证据）**：协议 §1 允许/禁止列写得很清楚（[PROTOCOL_A0.md:15-21](PROTOCOL_A0.md#L15)）；代码里 `META_COLS` 只有身份/设计/screen 列、端点只做空串存在性（[a0.py:21-27,58-76](a0.py#L21)）；我独立复核端点列**空值 0、非数值哨兵 0**（附录 B），并且 `matched_conditions.csv` 与我从原始元数据重建的 9,154 个共同键**集合完全相等**——匹配确实是身份/方向/剂量列/端点存在性驱动的，没有按 Q/效应挑单位。
- **方向与端点（PASS）**：条件是**有向** `ANCHOR_ID→LIBRARY_ID` + `ANCHOR_CONC` + `LIBRARY_CONC`（[PROTOCOL_A0.md:30-36](PROTOCOL_A0.md#L30)），四元组要求四键条件元组相同（[:48-54](PROTOCOL_A0.md#L48)）；端点固定 `SYNERGY_DELTA_EMAX`（与 C130 一致）。M3 用"不同无序药对"排除同对的反向/多剂量重复（[:52](PROTOCOL_A0.md#L52)），所以**不存在把方向合并掉的旧式无序聚合**——这正好修掉了 R28/R31/R32 跨筛 .593/.689 用无序药对聚合的缺陷（[independent-reassessment/report.md:50](../2026-10-27-independent-reassessment/report.md#L50)）。
- **剂量（WEAK）**：条件定义只用 `ANCHOR_CONC`（uM）+ `LIBRARY_CONC`（**library 最高浓度**）；A0 自己承认 fitting 表不发布完整 library 浓度点集、本机无 Validation raw 布局 → 孔级剂量等价不可验证（[PROTOCOL_A0.md:92-94](PROTOCOL_A0.md#L92)；[report.md:79,114-115](report.md#L79)）。更关键的**已知事实**：R28/R31/R32 已查明 Validation 与主筛"浓度不同"（[R28 report:14](../2026-10-27-agent-cell-identifiability-r28/report.md#L14)；[R31 report:3,32](../2026-10-27-agent-cell-identifiability-r31/report.md#L3)），A0 的匹配因此实际是"落在两筛共同设计元组上"的一个**子集**（9,154 键=Validation 键的 94.87%，见 [report.md:76-79](report.md#L76)）。这个子集不是随机子集：它由剂量设计重叠决定。**A1 必须在报告中把"匹配四元组宇宙"限定为"共享设计列子集"，并报告与未匹配部分的元数据差异**；不能把它当作 Validation 全体的代表。
- **条件 p,q 之间的剂量差异（A1 必须处理）**：四元组只要求 p 在四键同条件、q 在四键同条件；**p 与 q 之间允许剂量不同**（`same_anchor_any_conc` 就是同 anchor 不同浓度；`disjoint_pairs` 更可能全不同）。因此 Q 会把"条件差"与"剂量差"混在一起。A1 DRAFT 的主统计量 P1 是"对每个细胞对，median over condition pairs"（[PROTOCOL_Q_DRAFT.md:21-23](PROTOCOL_Q_DRAFT.md#L21)）——**没有限制 condition pair 的剂量关系**，会把不同剂量的 condition pair 混进同一个 median；必须预先指定主分层（建议 `controlled_anchor`：同 anchor、同 anchor conc、同 library conc、仅 library 不同——A0 已报 92,039 个，够 n）或对剂量差做协变量/分层，其他分层只作次级。
- **`disjoint_pairs` 口径错误（A0 勘误）**：report §3/§4 与 a0.json 报 5,345,987；我按"p,q 不共享任何 drug id（任意朝向）"复算是 **4,612,633**。原因是 a0.py 只减 same_anchor+same_library（[a0.py:288-310](a0.py#L288)），漏掉 `p.anchor==q.library` 或 `p.library==q.anchor` 的跨朝向共享（实测差 733,354）。A0 用它做"最干净的 disjoint 分层"会误导 A1。

**判决 WEAK**：响应盲/方向/端点/screen 的匹配是真的，A0 也对剂量不可验证做了披露；但"剂量设计差异+共享设计子集"和 p/q 剂量混入 Q 没有被处理，A1 必须先冻结分层与限定。

### 2.2（第 2 条）门槛与独立组不是功效保证；2×2 只消去加性主效应，残留项必须建模

- **门槛与独立组（结构 PASS，功效 WEAK）**：R4=6,223,367≫500，96 细胞/98 有向药对/291 条件；G1/G2 barcode 集合交集 0（我已复现）；A0 明确 500 只是 floor、6.22M 是嵌套计数非独立 n（[PROTOCOL_A0.md:70-79](PROTOCOL_A0.md#L70)；[report.md:72,92](report.md#L72)；[a0.json:134-138](a0.json#L134)）。这些都对。但 **500 这个门槛对 Q 复验几乎没有信息量**：Q 的统计量不是"单臂 ρ 对 0"的 Spearman，而是"Q_A vs Q_B 的配对相关"（或聚合后的相关）；其零分布/SE 取决于 Q 的可靠性（两侧拟合误差）、细胞对/条件对的聚类结构、以及 screen×batch 共享项。A0 的 MDE 备注只是 iid 下 n=500↔ρ≈0.125 的教科书提示，不能拿来当 Q 的功效。**A1 必须在任何 Q 读值前冻结 MDE/完整规则功效**（详见 2.4）。
- **2×2 回路（正确但不完整）**：y=μ+a_c+b_p+ε 时 Q=0，所以回路确实消去"加性细胞/条件主效应"；A0 的"树不能识别非可加性、2×2 是最小闭环"（[PROTOCOL_A0.md:81-83](PROTOCOL_A0.md#L81)；[a0.json:91-97](a0.json#L91)）是正确可估性陈述。**但 Q 不消去的项**：
  1. **cell×单药**：p=(A,B)、q=(A,C) 时 Q 里的 (cell×B−cell×C) 在 c 与 c' 之间再次相减，只剩"cell 特异的 B/C 单药差异"，跨 screen 稳定是完全可能的——这是 H193b 必须扣掉的项；p,q disjoint 时残留四个 cell×药项。
  2. **cell×剂量**：p、q 剂量不同时，Q 含剂量×cell 项；不同 cell 的剂量敏感性差异同样可跨 screen 稳定。
  3. **screen×condition / 批次×condition**：两 screen 的拟合/批次不同，Q_A 与 Q_B 的系统差可来自 screen×condition；只能当"跨 screen 稳定性"，不能当纯 test–retest（A0 已说）。
  4. **端点估计误差**：ΔEMAX 是拟合量（Emax 对比），两侧拟合误差不等；Q_A vs Q_B 的相关会被误差衰减（attenuation）。Original 有重复板（31,019 个键 ≥2 barcode），Validation 也有 9,438 个键 ≥2 barcode（[a0.json:540-621](a0.json#L540)），A1 应**用同 screen 内重复板估计 Q 的可靠性/衰减**（只作测量噪声参照，不能当独立重复），并在报告里把 raw 相关与 reliability/attenuation 解释分开。
- **判决 WEAK**：结构资格没问题，但 A0 的"门槛/回路"回答不了 Q 的可检验性；A1 的 MDE/功效/残留项处理是冻结前提（2.4）。

### 2.3（第 3 条）批次不可分是硬限制（已披露）；单药列可用（A1 必须用）；Validation 选择偏差缺失

- **批次/日期与细胞不可分（A0 已正确报告）**：G1/G2 是两次独立筛（barcode 不相交），但 screen 身份与批次完全混淆，无法把"跨 screen 差异"分解为批次 vs 条件不稳定；A0 明确只能主张"跨 screen 条件稳定性"（[report.md:85](report.md#L85)；[PROTOCOL_A0.md:94](PROTOCOL_A0.md#L94)）。这与 BRIEF 的降级要求一致 ✓。
- **单药参照（A0 DENY → A1 必须解禁；可用性我已核验）**：拟合表有 `ANCHOR_VIABILITY`、`LIBRARY_EMAX/XMID/XMID_uM/AUC/fAUC` 等单药列（[report.md:84](report.md#L84)），但 A0 按协议 DENY。我做了存在性/缺失性检查：**两表都含这 7 列，且空值均为 0、端点与单药列都没有非数值哨兵**（附录 B）——所以 H193b 的 adjusted Q **不是"做不到"**。A1 DRAFT 现在写"若不可用则记录限制，不强行"（[PROTOCOL_Q_DRAFT.md:29](PROTOCOL_Q_DRAFT.md#L29)）**不成立**：必须把单药 adjusted Q 写成必做（公式、用哪几列、如何在两 screen 分别/对称拟合、缺失去向都要冻结）。
- **Validation 选择偏差（A0 未披露，A1 必须预注册）**：R28/R31/R32 已查明验证筛只覆盖 4.4% 的键（4,725/108,259），且**"极可能是挑选过的子集"**（[R31 report:30-32](../2026-10-27-agent-cell-identifiability-r31/report.md#L30)；[EVIDENCE_REGISTER:57-58](../EVIDENCE_REGISTER.md#L57) F8/F9：96/125 细胞、组织构成略偏 Pancreas、同键一致性只与全量差 +0.003）。A0 报告只在 §9 说"匹配宇宙只覆盖 Validation 子集、不等于全宇宙"（[report.md:117](report.md#L117)），**没有说"选择偏差/回归到均值"**。后果：Q_A（Original）与 Q_B（Validation）的相关若为正，可能被 Validation 按 Original 结果挑选而**衰减（回归到均值）或扭曲**；若为负也可能来自选择。A1 必须预注册：(i) 用元数据比较 matched vs unmatched 的 Original 键（细胞/药对/设计列分布）；(ii) 用 Original 内部随机子集对照（R31 的建议）检验选择效应；(iii) 报告 Q 的 reliability/衰减上限；(iv) 措辞限定"在该 Validation 子集上"。
- **判决 WEAK**：A0 的批次/单药两条回答基本正确（单药还需 A1 明确解禁与用法），但选择偏差这条已知风险没进 A0 报告/局限，A1 必须补预注册。

### 2.4（第 4 条）A1 冻结前必须关掉的开放选择与事后择优漏洞（本轮唯一 FAIL）

对照 BRIEF 的冻结要求（[BRIEF:29-37](../2026-10-27-innovation-round-r193/BRIEF.md#L29)）与 R192 的功效教训（[R192 record:11,29,46](../2026-10-27-innovation-round-r192/record.md#L11)；[stats_audit:121-129,199](../2026-10-27-independent-reassessment/stats_audit.md#L121)），PROTOCOL_Q_DRAFT 的缺口：

1. **主统计量未定**：P1（细胞对级 median/mean 聚合，n≈3,418）是"推荐"、P2/P3 是"次"，但 "两种候选（预注册选其一，挑战后定）"（[:21-24](PROTOCOL_Q_DRAFT.md#L21)）——**冻结前必须只留一个主统计量**；否则看到 Q 结果后再选 P1/P2/P3 就是事后择优。
2. **聚合方式未定**："median（或 mean；先冻结）"（[:22](PROTOCOL_Q_DRAFT.md#L22)）——两者对零分布/CI 不同，必须现在写死；还要写死同号/零 Q/非有限值的处理（Q 可能极大值、Q=0、Q 依赖删失）、平局规则。
3. **条件对分层未定**：P1 的"median over condition pairs"没有指定是否限制 `controlled_anchor`/同剂量；不同分层的 Q 含义不同（`disjoint_pairs` 残留四个单药项）；必须在 PROTOCOL_Q 里预注册"主分层"，其余次级。
4. **δ_min 无 operational 定义**：DRAFT 写"建议 Spearman δ_min=0.10，且在冻结前写明理由"（[:30](PROTOCOL_Q_DRAFT.md#L30)），但**现在没有理由**；BRIEF 要求"由最小有用条件偏移定义，不能用旧 CI 倒推"（[BRIEF:31](../2026-10-27-innovation-round-r193/BRIEF.md#L31)）。A1 需要一个可审计的定义（例如：给定 Q 的用途/后续决策意义，0.10 对应什么；或引用 prior 的复现相关量级并声明是规划值），不能只写"建议"。
5. **零分布/负对照未定主次**：打乱细胞标签、打乱条件标签、符号一致率三个并列（[:25-28](PROTOCOL_Q_DRAFT.md#L25)），没有写主零分布、置换保留哪些结构（screen/细胞/条件）、如何给 CI（bootstrap 单位=细胞对？细胞？条件对？）、多重性如何处理（主统计量 1 个，但端点/分层/统计量多版本）。必须现在冻结"主零分布 + 主 CI 单位"，其他作敏感性。
6. **MDE/功效未写死，且缺完整规则校准**：DRAFT 只写"MDE80 按实际聚类与样本量计算，必须先于效果报告"（[:30](PROTOCOL_Q_DRAFT.md#L30)），没有写算法（置换/解析）、没有写 MDE 与 δ_min 的比较规则细节、**没有模拟完整判定规则**（点≥δ_min ∧ CI>0 ∧ 优于零分布）在零假设与备择下的 type-I/power。R192 已证明"null MDE 通过≠实际拟合臂有功效"（[R192 record:11,46](../2026-10-27-innovation-round-r192/record.md#L11)）：A1 必须报告 realized SE 与 pre-flight SE 的差异、以及完整规则的 joint power；若 joint power@δ_min<80% → `inconclusive`（停，不救）。
7. **没有运行时 gate**：DRAFT §7 有"设计体检"，但没有把"MDE80≤δ_min 且联合功效通过"写成 q1.py 的运行时断言（MDE 未过不得计算 Q）；需要代码级 abort，防止"先偷偷算 Q 再解释"。
8. **缺 within-screen 参照**：A0 提供了 barcode 分半 R4=43,208,857（但只覆盖 46 细胞/583 细胞对，见附录 A），可作为**同 screen 参照**（cross-screen 稳定性应和 within-screen 稳定性比，而不是只对 0/零分布）；DRAFT 没有把它写进计划。R31/R32 的"同筛换浓度基线 vs 跨筛"就是正确形态。

**判决 FAIL**：当前 DRAFT 不是"待启封的冻结协议"，而是一组还没选定的候选；按 BRIEF 的冻结纪律，A1 不能开跑。

### 2.5（第 5 条）谱系：不是旧路线改名，但必须把"不是新算子"写死

- **不是旧"两个固定交互族选一个"的有限交互筛选**：八方向那轮明确以两个固定交互族做选择且无独立决策收益（[eight_directions_20261026/report.md:27,31](../eight_directions_20261026/report.md#L27)），BRIEF 也把它列为明确排除（[BRIEF:8](../2026-10-27-innovation-round-r193/BRIEF.md#L8)）。R193 的 Q 是**一个预冻结的 2×2 条件偏移量**，不做交互族选择、不做模型比较、不做 acquisition/Agent；A0/A1 设计里没有"赢家交互族"要选。所以结构上不是重命名。
- **也不是 R5 反序**：R5 量的是跨背景"排序反转比例"（且独立重审已更正：约 4% 是**动作比较层**的反序比例、不是 4% 药物/药对/细胞，也无证据可预测——[independent-reassessment/report.md:66](../2026-10-27-independent-reassessment/report.md#L66)）。Q 不要求反转、不按大间隔筛单位（A1 DRAFT §0 已写"不用大间隔/反序挑四元组" ✓，[:9](PROTOCOL_Q_DRAFT.md#L9)）。
- **但风险在解释**：如果 Q 可复验，最自然的解释是"cell×condition interaction 的某个可学习部分"——BATCHIE 的细胞嵌入×药物主效应/交互+offset 已是直接强先例（[independent-reassessment/report.md:85](../2026-10-27-independent-reassessment/report.md#L85)），**不能把"Q 可复验"写成新算子/新算法收益**。A0/report 没有谱系声明；PROTOCOL_Q 必须写：不是旧路线重启、不用 Q 反推交互族、不宣称新算法、B/C（反馈/策略）未启动。

**判决 WEAK**。

### 2.6（第 6 条）总判决：revise（≤5 必改，运行前完成）

见 §3。**本轮不运行 Q/效果**；即使 A1 冻结，也只跑 A1（Q 复验），不跑 B/C/acquision/Agent。

## 3. 运行前必改项（≤5；全部完成后才冻结 PROTOCOL_Q 并交给独立 runner）

> 顺序按"不修则 A1 不可解释"排序；均可在不读 Q/效应的情况下完成（只涉及协议文本、A0 勘误、pre-flight 代码与元数据/零模型）。

**必改 1｜A0 勘误（不改资格、不改 A0 冻结文件本体，由 Lead/runner 出 errata/adendum，A1 引用 errata 数字）**
- `disjoint_pairs` 由 5,345,987 改为 **4,612,633**（定义：p,q 不共享任何 drug id，任意朝向）；把 a0.py 的 `u−same_anchor−same_library` 口径写进勘误说明（漏跨朝向共享 733,354）。
- G1-only/G2-only 改为 M3 一致口径 **4,412,540,421 / 7,234,325**（或明确标注原数字是"同有向对剔除"口径、不用于 A1 选择）。
- 披露 `matched_conditions.csv` 条件级有向药对 **129**（不是 130；130 是药对级重叠）；A1 用 129。
- 在 A0/report 局限里补 Validation 选择偏差（引用 R31/F9）与 barcode-split 覆盖仅 **46 细胞/583 细胞对**（A0 只写了 31,019 键，未写覆盖细胞数，见附录 A）。

**必改 2｜PROTOCOL_Q 只留一个主设计并现在写死（关掉"挑战后定"）**
- 主统计量：从 P1/P2/P3 中**固定一个**（建议 P1 细胞对级，n≈3,418；若选 P1，必须写死 aggregation=median 或 mean、以及"哪个条件对分层进入 median"）；其他两个降为预注册次级报告。
- 主条件对分层：建议 `controlled_anchor`（同 anchor、同 anchor conc、同 library conc、仅 library 不同；A0 92,039 个，n 足够）或"仅 dose-matched condition pair"；`same_anchor_any_conc`/`same_library`/`disjoint`/`same_tissue` 全作次级。**不允许**主统计量混入任意剂量差的 pair 而不分层。
- 主端点固定 `SYNERGY_DELTA_EMAX`；其他 Δ 端点列为预注册敏感性但不得择优替换主判定。写死 tie/非有限/Q=0/删失处理、barcode 聚合（重复板均值）与固定种子。

**必改 3｜δ_min、MDE、零分布、完整规则功效先于 Q 冻结，并写成运行时 gate**
- δ_min=0.10 要写 operational 理由（"最小有用条件偏移复验相关"的可审计定义；不得用旧 CI 下界倒推；[BRIEF:31](../2026-10-27-innovation-round-r193/BRIEF.md#L31)）。若写不出理由，改用更保守/更宽的预注册目标和对应 MDE 要求。
- 写死 MDE 算法（对**选定的主统计量**、固定聚类单位：细胞对 + 细胞 + 条件对；Q_A/Q_B 配对相关；必要时用 split-sample/block bootstrap）与零分布（主零：保持 screen/细胞/条件结构的置换标签，具体写死），并在读任何 Q 前计算 MDE80 与完整规则（点≥δ_min ∧ CI 下界>0 ∧ 优于主零分布）在零假设与 δ∈{δ_min, 0.15, 0.20} 下的 type-I/joint power。
- 若 MDE80>δ_min 或 joint power@δ_min<0.80 → **`inconclusive` 停，不救**；q1.py 里写运行时断言（未过 preflight 不得算 Q）。报告必须并列 pre-flight SE 与 realized SE（R192 教训），不得把 null MDE 当"已充分检定力"。
- 用 Original/Validation 的重复板（31,019 / 9,438 键）估计 Q 的测量可靠性/衰减，作为解释参照（不是独立重复）。

**必改 4｜混杂与选择偏差写进主协议（H193b 升级为必做）**
- **H193b（adjusted Q）从"次要/可选"升级为必做主解释项**：写死公式（用 `ANCHOR_VIABILITY` 与 `LIBRARY_EMAX/XMID/XMID_uM/fAUC` 等单药列，分别对两 screen 拟合/取出 cell×单药项后从 y 扣除，再算 Q；对称处理 anchor/library、缺失与剂量）；报告 adjusted Q 的 Spearman 与主 Q 并列；主判定之外**不得**在 adjusted 失败时仍宣称"条件结构"（`confounded_unresolved`）。
- 剂量：主分析用 dose-matched strata（必改 2），报告不同剂量差 condition pair 的 Q 敏感性；不把 `LIBRARY_CONC` 最高浓度等价当完整剂量等价（报告限制）。
- 批次：主措辞只允许"跨 screen 条件稳定性"（A0 已要求）；within-screen barcode-split 作参照（46 细胞/583 细胞对，注明同 screen、无日期、独立性弱）。
- 选择偏差：预注册 (i) matched vs unmatched Original 键的元数据比较；(ii) Original 内随机子集对照（R31 建议）；(iii) 报告"结论仅适用于 Validation 覆盖的 96 细胞/129 有向药对/291 条件/共享设计子集"；(iv) 不得用 Validation 响应挑任何单元。

**必改 5｜解释/停止/谱系写死（防止阳性被读成新算法、阴性被读成"无结构"）**
- 判定与分支按 BRIEF：`reproducible` = 点≥δ_min ∧ CI 下界>0 ∧ 优于主零分布；`not_reproducible` = CI 含 0/点≤0；`inconclusive` = MDE>δ_min 或设计体检失败（停，不救）。
- 词句：`not_reproducible` **不得**写成"该资源没有条件结构/生物学交互不存在"（construct/剂量/power/选择/批次未分离，参考 A0 局限与 R31/R32）；`reproducible` **不得**写 mechanism/transfer/新算法，只能写"在该匹配子集上、跨 screen 的条件结构可复验"；普通加性/层级/BATCHIE 类模型可解释时记普通学习，不设计新算子（[BRIEF:35-37](../2026-10-27-innovation-round-r193/BRIEF.md#L35)；[independent-reassessment/report.md:107](../2026-10-27-independent-reassessment/report.md#L107)）。
- 谱系：PROTOCOL_Q 写明不是旧有限交互筛选/R5 反序重启（引用 eight_directions_20261026:27,31 与 R5 更正）；不用 Q 结果反推交互族/算法；B/C 与 acquisition/Agent 不启动；不改 r/δ/端点重试。

## 4. 本轮声明与边界

- **本轮不运行 Q/效果**：本挑战未估计任何 Q、相关、预测性能或模型；未读取响应数值（A0 的端点只做存在性/空串检查，我另外只做了列存在性与空值/哨兵计数；两者均不产生响应值）。未改 A0 产物、协议、其它目录、INDEX/SYNTHESIS/git。
- 只读脚本（我自己的独立实现，放在 `tmp/`）：[challenge_a0_verify.py](../../tmp/challenge_a0_verify.py)（结构/重叠/R0–R4/分层/barcode-split 复算）、[challenge_a0_quality.py](../../tmp/challenge_a0_quality.py)（列存在性与空值/哨兵计数）、[challenge_a0_barcode.py](../../tmp/challenge_a0_barcode.py)（barcode 分半 R4 与覆盖）。输出在 `tmp/challenge_a0_verify.json` / `challenge_a0_quality.json` / `challenge_a0_barcode.json`；未写任何响应值。
- 本挑战不代替 Lead 决定 A1 的科学目标，只要求"可执行、可证伪、先冻结、失败可解释"。

---

## 附录 A：独立复核（只读，已复现 vs A0 报告）

| 项目 | A0 报告 / a0.json | 我的独立重算 | 一致 |
|---|---:|---:|---|
| Original 行/剔除复合行/有效行 | 296,707 / 5,527 / 291,180 | 同 | ✓ |
| Validation 行/剔除/有效 | 23,505 / 158 / 23,347 | 同 | ✓ |
| 细胞（原/验/共同） | 125 / 97 / 96 | 同 | ✓ |
| 有向药对（原/验/共同） | 1,975 / 130 / 130 | 同 | ✓ |
| 条件（原/验） | 4,528 / 295 | 同 | ✓ |
| barcode（原/验） | 3,106 / 454 | 同 | ✓ |
| cell×condition 共同键 | 9,154 | 同；且等于 `matched_conditions.csv` 集合 | ✓ |
| barcode 集合交集 | 0；范围 14,482–39,392 / 33,044–63,257 | 同 | ✓ |
| R0/R1/R2/R3/R4 | 4,034,637,772 / 177,515,510 / 214,664,684 / **802,445** / **6,223,367** | 同（逐项精确） | ✓ |
| R4 覆盖 | 96 细胞 / 291 条件 / 98 有向药对 / 3,418 细胞对 | 同 | ✓ |
| R4 组织（B/C/P） | 33 / 35 / 28 | 同 | ✓ |
| controlled_anchor / same_anchor_any_conc / same_library | 92,039 / 568,029 / 309,351 | 同 | ✓ |
| same_tissue / cross_tissue | 6,217,553 / 5,814 | 同 | ✓ |
| **disjoint_pairs** | **5,345,987** | **4,612,633**（任意朝向不共享 drug id） | ✗（见必改 1） |
| G1-only 四元组 | **4,415,971,041** | a0 口径可复现；M3 无序口径 **4,412,540,421** | ✗口径（见必改 1） |
| G2-only 四元组 | **7,301,337** | a0 口径可复现；M3 无序口径 **7,234,325** | ✗口径（见必改 1） |
| barcode 分半 R4 | 43,208,857 | 同；**但只覆盖 46 细胞 / 583 细胞对** | ✓（覆盖数 A0 未写） |
| `matched_conditions.csv` 条件级有向药对 | （report 只给药对级 130） | **129** | A0 未写 |
| 五份产物 SHA256 | 见 report/record | 逐字节一致（PROTOCOL_A0 `D77316ED…AA93`、a0.py `444E939C…C3525`、a0.json `72BBAF6D…ECA22`、matched_conditions `73FD5085…153FF`、matched_quadruples `881A0DFC…1CCF9`） | ✓ |

## 附录 B：列存在性/缺失性检查（不读响应值，只计空值/非数值哨兵）

| 文件 | 行数 | SYNERGY_DELTA_EMAX/AUC/fAUC/XMID 空值 | 非数值哨兵 | 单药列（ANCHOR_VIABILITY, LIBRARY_EMAX/XMID/XMID_uM/AUC/fAUC/RMSE）存在 | 单药列空值 |
|---|---:|---:|---:|---|---:|
| Original fitted | 296,707 | 0/0/0/0（4 列） | 0 | 7/7 存在 | 0（逐列） |
| Validation fitted | 23,505 | 0/0/0/0（4 列） | 0 | 7/7 存在 | 0（逐列） |

→ A0 的"端点 0 空值"与 H193b 所需单药列**均可用**；A1 的 adjusted-Q 是执行问题，不是数据缺口。

## 附录 C：A1 DRAFT 需要补的"数字占位"清单（与 §3 对应）

1. 主统计量（P1/P2/P3 选一）、聚合（median/mean）、条件对主分层（controlled_anchor 还是其他）、平局/删失/非有限规则 → §2.4-1/2/3。
2. δ_min=0.10 的 operational 理由、主零分布、置换单位、bootstrap 单位 → §2.4-4/5。
3. 主统计量的 MDE 算法与数值、完整规则 joint power（零/δ_min/0.15/0.20）、pre-flight SE vs realized SE → §2.4-6。
4. adjusted-Q 公式（单药列、两 screen 对称、缺失规则）、剂量/选择偏差敏感性、barcode-split 参照（46 细胞/583 细胞对）→ §2.4-8、§2.3。
5. 判定措辞/谱系/不重开条款 → §2.5。

**一句话给 Lead：A0 资格与头部门槛经独立复现成立（含 SHA 与 9,154 键完全一致），判 revise 不是 stop——但 A1 冻结前必须关掉 DRAFT 的开放菜单（主统计量/聚合/分层/零分布/δ_min/MDE/完整规则功效）、把 H193b adjusted-Q 升级为必做（单药列实测可用）、并勘误 A0 两处计数口径（disjoint 4,612,633；G1/G2-only 4,412,540,421 / 7,234,325）与 Validation 选择偏差。五条必改完成后写 PROTOCOL_Q（FROZEN）再运行 A1；本轮不运行 Q/效果。**
