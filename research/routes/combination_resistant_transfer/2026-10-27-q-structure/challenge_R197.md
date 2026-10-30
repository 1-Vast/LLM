# R197 PROTOCOL 回顾性独立挑战（task-30）：Q 结构可预测性重审

2026-10-27。角色：独立挑战者（非 runner、未参与 A1/A2/Q2 开发）。对象：[PROTOCOL_R197.md](PROTOCOL_R197.md)（v1 FROZEN + AMENDMENT-R197-001）、实现 [r197.py](r197.py)；参照 R197 BRIEF、`research/2026-10-27-conditional-shift/{ERRATA_Q2.md, ERRATA_A3.md, q2.json, q2.py}`、`research/2026-10-27-cross-domain-directions/{report.md, late_results_audit.md}`、R194/R195 记录。**本挑战在结果被解释/采纳之前给出；不运行效果代码、不改 R197 产物、只写本文件与 `tmp/`。** 按 Lead 规则：**判 revise → R197 结果作废，需 AMENDMENT 重跑后方可解释**；判 proceed 才可解释。复核时 `research/2026-10-27-q-structure/` 只有协议与 `r197.py`（无 `r197.json/r197_rows.csv`），本文按协议与代码审；若 runner 已产出结果，同样以重跑为准。

## 0. 结论先行

**总判决：revise（≤5 必改；R197 现有/将出的 verdict 在 AMENDMENT 重跑前不得解释）。**

核心问题不是 A0 的修正代数（那部分设计是对的），而是 **B 主实验的主模型已经被"结构可辨识性"换成 B3（元数据/单药特征回归），于是它检验的命题不再是"Q 的残差/低秩结构是否可复用预测"，而是"预购元数据+单药特征能否预测冷细胞对的 Q"**；同时 B3 的单药特征与端点构造重叠、B0 在冷细胞对下缺少细胞级项（基线弱），"present" 的语义会被误读为"条件结构存在/可迁移"。

具体地：

- **主问题 vs 主模型错位（最致命）**：AMENDMENT-R197-001 自己承认 H197a/H197b 下 B2 低秩的留出行/列不可辨识、预测退化为 B0（[PROTOCOL_R197.md:156-164](PROTOCOL_R197.md#L156)）；于是主对比改成 **H197a：B3−B0**（[:160-163](PROTOCOL_R197.md#L160)），而 B3 是"B1 特征 + 细胞侧元数据 × 条件侧元数据交互"的岭回归（[PROTOCOL_R197.md:97-98,106](PROTOCOL_R197.md#L97)；[r197.py:1198-1201,1259](r197.py#L1198)），**不含任何从 Q 矩阵学到的低秩/潜因子**。B2 只在 H197c（随机条目，次设计）可辨识（[PROTOCOL_R197.md:120,162](PROTOCOL_R197.md#L120)）。因此即使 `predictive_structure_present`，它支持的也只是"元数据/单药特征对冷细胞对 Q 有增量"，**不能支持"Q 的低秩/背景依赖结构可复用"**（BRIEF 的主问题，[BRIEF:8-10](../2026-10-27-innovation-round-r197/BRIEF.md#L8)）。
- **B1/B3 特征与端点构造部分循环**：特征用 `LIBRARY_EMAX`/`LIBRARY_AUC` 的单药拟合均值（[PROTOCOL_R197.md:94-95](PROTOCOL_R197.md#L94)；[r197.py:832-840](r197.py#L832)），而端点 `SYNERGY_DELTA_EMAX` 本身是"观测 Emax − 由单药曲线得到的期望 Emax"（ERRATA/P-B 已书面记录不是独立统计量）。用单药 Emax 差去预测 ΔEMAX，等于用期望项的一部分去预测"观测−期望"，**增益可以来自机械重构而非可复用结构**；协议称"非 Q"是对的，但没有披露这层构造重叠，也没有做特征块消融。
- **B0 冷细胞对基线偏弱**：H197a 测试列的 cell-pair 在训练中完全无观测 ⇒ B0 的列效应对测试为 0（[PROTOCOL_R197.md:103](PROTOCOL_R197.md#L103)），测试预测 ≈ μ+行均值；B3/B1 却带有 tissue/单药等细胞级信息 → `Δ=B3−B0` 把"细胞级信息"和"结构增量"混在一起；present 规则只做 B3≥B1/B4 的**点比较**（[PROTOCOL_R197.md:138](PROTOCOL_R197.md#L138)），不要求 Δ 相对 B1 的 CI>0。
- **δ_min=0.05 的 operational 理由不成立**：理由写"噪声尺度 0.109、0.05 对应可解释秩方差<0.3%、低于此不足以支持后续反馈/选药实验"（[PROTOCOL_R197.md:125](PROTOCOL_R197.md#L125)）——前两句只是"很小"的另一种说法，不是决策/效用推导；"与 A1 δ_min_latent=0.10 在观测层折半一致"隐含 rel=0.25，而 Q2 的可靠性是 0.868（未认证）；按 rel≈0.868 折半应是 δ_obs≈0.093。**δ_min 需要可审计的 operational 定义（或按预注册 reliability 做 latent→observed 换算）**。
- **A0（修正式/依赖感知）设计基本正确，但"依赖感知"只到节点层**：V4 重采样 96 细胞与 291 条件、权重 m_p m_q m_a m_b（[PROTOCOL_R197.md:57-65](PROTOCOL_R197.md#L57)），确实比 q2 的 229×1,501 独立重抽前进；但 Q 条目复用同一批 cell×condition 键/barcode（ERRATA_Q2 §4：噪声标定只覆盖 1.43% 观测，[ERRATA_Q2.md:25](../2026-10-27-conditional-shift/ERRATA_Q2.md#L25)），V4 不保留键/barcode 级相关；graph-aware 置换只在行/列已观测集合内打乱，破坏跨节点依赖、exchangeability 也未论证。这些作为"依赖感知"主张需要降级/补敏感性。
- **措辞/停止规则过宽**：`no_stable_increment → 停止该资源上的"条件规律"研究`（[PROTOCOL_R197.md:139](PROTOCOL_R197.md#L139)）在设计只能检验 B3（冷细胞）的前提下过宽——它不能关闭"低秩结构"（B2 在冷细胞不可辨识）或"其他表示/其他留出"的问题；同样 `predictive_structure_present` 不能写"条件规律可迁移/反馈有用"（协议已写不是 A1/A2 通过 ✓，但 verdict 名称本身需要限定句）。

**给 Lead 的最致命 3 条：** ① 主模型被换成 B3（特征回归）后，R197 不能检验 BRIEF 的"Q 低秩/背景结构可复用"命题；要么把命题重写为"预购特征能否预测冷细胞对 Q"，要么预注册一个 B2 可辨识的主设计（H197c 为主或等效）。② B1/B3 的单药特征与 ΔEMAX 端点的期望项构造重叠、B0 冷细胞对缺细胞级项 → `present` 的增益可来自机械/细胞信息，不是结构；必须披露+块消融+增强基线/以 B1 为对照 CI。③ δ_min=0.05 的 operational 理由（含"与 A1 0.10 折半一致"）不成立；A0 的节点级依赖感知/置换交换性需降级或补键级敏感性。

## 1. 逐条判决表（task-30 ①–⑥）

| # | 挑战项 | 判决 | 一句话理由 |
|---|---|---|---|
| ① | A0 重校准：修正式加权矩、未加权 sanity、依赖感知 bootstrap/置换、dyadic 反例、旧/新对照 | **WEAK** | 修正式代数我已独立推导核对（`A=½(S²−Σw²y²)`、`B=WS−Σw²y`、`C=½(W²−Σw²)`、`num=A−μB+μ²C` 恰为不同观测对加权残差积；w≡1 与旧式恒等）；协议自检锚点（ERRATA 例 −8/9 vs −37/18、q2 的 σ²_cond=0.000371/σ²_cellpair=0.001023/σ²_total=0.025944/σ²_resid=0.024551、σ²_single=0.003351/noise=0.011968）与 q2.json 一致（[q2.json:145-148,66,78,288-291](../2026-10-27-conditional-shift/q2.json#L145)）；dyadic 闭式 `4(n+1)/(3n(n−1))` vs 独立近似 `2/C(n,2)` 的比 = (n+1)/3 → n=30 恰 10.33 ✓。**但**：V4 只是节点级（cell/condition）重抽，不保留键/barcode 级复用与测量依赖（噪声标定覆盖 1.43%）；graph-aware 置换的交换性未论证；R_split 的 0.50 阈值沿用 q2 未认证口径、且只测条件主效应可靠性（不测 c_ij）；旧/新对照诚实（旧式只作对照、点估计不变）✓。 |
| ② | B 留出设计：H197a 按细胞分组防泄漏、rank 只训练内选、B0/B1/B4 基线、CI 聚类、δ_min、MDE/零分布先于判定 | **FAIL** | 防泄漏/训练内选择/B-D 体检形式上齐（H197a 测试细胞不出现于训练、rank/λ 只用训练、CI 按细胞/行、MDE/置换/type-I 先于判定）；但主模型=**B3 特征回归**（B2 低秩在 H197a/H197b 结构不可辨识、退化为 B0），使主检验不检验"低秩/背景结构"；B1/B3 单药特征与端点期望项构造重叠；B0 冷细胞对无细胞级项、基线弱；δ_min=0.05 operational 理由不成立（见 §0/§2.2）。 |
| ③ | 判定/措辞：present 不得写可迁移/反馈有用；no_stable_increment 不得写规律不存在；明确不是 A1/A2 通过、不启动反馈/Agent | **WEAK** | 协议 §0 已写不是 A1/A2 通过、不启动反馈/Agent/RSI ✓；§3.7 有"阴性≠结构不存在"的措辞约束 ✓（[PROTOCOL_R197.md:141](PROTOCOL_R197.md#L141)）；但 `no_stable_increment` 的"停止该资源条件规律研究"过宽（设计测不到低秩结构），`predictive_structure_present` 名称需要强制限定句；A0 状态（robust/not）与 B 的解释没有预注册耦合。 |
| ④ | 是否采纳"1.43% 仅加性主效应份额"更正、是否避免用 A2 int/noise 分割排除结构 | **PASS（附一条）** | 采纳：`share_cond` 只叫"加性 condition 主效应份额"，秩 1 反例纳入 §2.2，禁止"1.43% 是可迁移规律总量"表述（[PROTOCOL_R197.md:55,83](PROTOCOL_R197.md#L55)）；A2 的 int/noise 分割只作为误差模型下的分割、不作为排除结构的理由（[:83](PROTOCOL_R197.md#L83)）✓。附：**A0 状态与 B 判定无耦合**——若 A0 判 `q2_inference_not_robust` 或 R_split<0.5，B 仍按原规则判 present/absent，报告必须继承"条件级可靠性未认证"的限定（建议写死）。 |
| ⑤ | 谱系/预算/确定性 | **WEAK** | 谱系：不是 A1/A2 通过、不跨 screen、不启动反馈/Agent ✓（[PROTOCOL_R197.md:7](PROTOCOL_R197.md#L7)）；但需补"不是新算子/新算法：B3/B4 是标准回归与容量对照；present 只说明可用预购信息预测 Q"；预算：单命令≤20 min，但 H197a 的完整规则 type-I 20 次 ×（5 折 × B0/B1/B2/B3/B4 重拟合 + 内层 CV + B=200 CI + B=200 置换）可能超时，协议无分步/缓存/降 B 方案；确定性种子/JSON/双跑 ✓；输入 SHA 表里 q2.json 写"…"（[PROTOCOL_R197.md:15](PROTOCOL_R197.md#L15)），需补全。 |
| ⑥ | 总判决 | **revise** | 见 §3；修完 AMENDMENT 重跑前结果不得解释。 |

## 2. 关键理由与证据锚点

### 2.1 A0（①）：代数正确，但"依赖感知"到节点为止

- 修正式（[PROTOCOL_R197.md:40-47](PROTOCOL_R197.md#L40)）：`A_g=½(S_g²−T2_g)`（不同观测对的 `Σ w_j w_k y_j y_k`）、`B_g=W_gS_g−S2_g`（`Σ_{j<k}w_jw_k(y_j+y_k)`）、`C_g=½(W_g²−W2_g)`（`Σ_{j<k}w_jw_k`）、`num=A−μB+μ²C`；展开即为不同原始观测对的加权残差积，正确。w≡1 时 `T2=S2=Σy²`、`W2=W`，与旧式恒等（我按代数展开核对），所以"未加权点估计不变、仅 CI/SE 需重算"的定位诚实；q2.json 的四个点估计与协议自检锚点逐项一致（[q2.json:145-148](../2026-10-27-conditional-shift/q2.json#L145)）。
- dyadic 原型（[PROTOCOL_R197.md:49-55](PROTOCOL_R197.md#L49)）：全对比均值系数 `(n−1−2i)/C(n,2)`，真实方差 `4(n+1)/(3n(n−1))σ²`，独立近似 `2/C(n,2)σ²`，比 = (n+1)/3；n=30 10.33 ✓，n=4 1.667、n=10 3.667；协议要求 MC 与闭式差≤3 MC-SE，合理。
- **依赖感知** V1–V4（[:57-65](PROTOCOL_R197.md#L57)）：V2 重抽细胞、V3 重抽条件、V4 两者，权重乘积 —— 这保留了"同细胞/同条件"的共享结构，比 q2 的 229×1,501 独立重抽前进；但 **Q 条目由同一批 cell×condition 键的 barcode 均值构成，同一键被多个 Q 复用；V4 没有重抽键/barcode**，所以它仍不是键/测量级的依赖感知。协议应把"依赖感知"限定为"节点级"，并补一个键级（或 barcode 级、用 q2 的重复键结构）敏感性/at least 报告该局限；噪声标定仅覆盖 1.43% 观测（[ERRATA_Q2.md:25](../2026-10-27-conditional-shift/ERRATA_Q2.md#L25)）也支持这个限定。
- graph-aware 置换（[:67-70](PROTOCOL_R197.md#L67)）：列内在已观测行集合置换（保列稀疏/值多重集）与行内置换（保行）——比 q2 的逐观测打乱好，但列内置换破坏了条件对之间通过共享条件/药物的依赖，且交换性没有被论证；只能作为"结构保持的近似零分布"，报告应写明。
- R_split（[:74-78](PROTOCOL_R197.md#L74)）：cell 半分、每半 ≥40 细胞、条件对每半 ≥10 cp、20 次分半、Spearman–Brown；设计合理，但 (i) 0.50 阈值沿用 q2 未认证口径；(ii) 丢弃每半 cp<10 的条件对会改变跨条件对相关的目标集（不同 split 参与 i 不同）；(iii) 它测的是条件**主效应**的可靠性，不是 `c_ij` 可预测性。须报告覆盖数/丢弃数、i 集合稳定性，并把 0.50 的用途限定为"条件主效应可靠性认证"，不推广到结构。

### 2.2 B（②，核心）：主模型不是低秩/结构模型；特征与端点构造重叠；B0 冷细胞基线弱

- **主模型错位**：AMENDMENT-R197-001 的代数事实成立：H197a 留出 cell-pair 列的细胞全部不入训练 → B2 的列因子不可辨识、预测退化为 B0（[PROTOCOL_R197.md:156-163](PROTOCOL_R197.md#L156)）；H197b 同理行因子。于是 H197a/H197b 主对比改为 B3−B0（[:160-162](PROTOCOL_R197.md#L160)）。但 B3 的特征是：细胞 tissue one-hot、`mono_emax`/`mono_auc` 差、condition-pair 的 pathway/drug-type/conc、以及 tissue×条件交互（[:94-98](PROTOCOL_R197.md#L94)）——**没有任何来自 Q 矩阵的行/列低秩因子**（B2 才是）。所以：
  - 若 H197a 判 present，正确表述只能是"**预购元数据+单药特征**能在冷细胞对上预测 Q 超过加性基线"，不是"Q 的低秩/背景结构可复用"（BRIEF 的主问题，[BRIEF:8-10](../2026-10-27-innovation-round-r197/BRIEF.md#L8)）。
  - 若 H197a 判 absent，也只能停止"该特征集在冷细胞对的增量"，**不能**停止"低秩结构"研究（B2 在冷细胞设计不可辨识，H197c 才用 B2 且是次设计）。`no_stable_increment → 停止该资源条件规律研究`（[PROTOCOL_R197.md:139](PROTOCOL_R197.md#L139)）因此过宽。
  - 建议二选一：(a) 把 R197 主问题重写为"预购特征对冷细胞对 Q 的增量"，verdict 改名（如 `metadata_predictive_increment_present`），并明确 B2 结构问题留待可辨识设计；(b) 预注册 B2 可辨识的主设计（H197c 随机条目为主，或"留出细胞对但用 side-information 学 cell embedding"的预注册变体），B2 作主模型。
- **特征构造循环**：`SYNERGY_DELTA_EMAX` = 组合观测 Emax − 期望 Emax（期望由单药曲线/Emax 计算；P-B 已记录 ΔEMAX 不是独立于单药拟合的量）。B1/B3 的 `mono_emax`/`mono_auc` 来自同表 `LIBRARY_EMAX/AUC`（[r197.py:832-840](r197.py#L832)），`d_emax` 等特征直接是两 library 单药 Emax 差 → 与 Q 的"期望项"部分机械相关。协议把它们称"非 Q"（字面对，但不是"与端点无关"）。**必须**：披露该构造重叠；预注册特征块消融（B0、B0+metadata、+mono、+interaction），报告 Δ(B3−B1)（metadata-only vs +mono）；若主增益在 mono 块，present 措辞必须限定为"单药可解释部分"。
- **B0 冷细胞基线**：H197a 的测试 cell-pair 列在训练中无观测，B0 的列效应（未见到置 0，[:103](PROTOCOL_R197.md#L103)）对测试全部为 0 → B0 预测≈μ+行均值；B3/B1 有 tissue/单药细胞级信息。`Δ=B3−B0` 会把"细胞级可用信息"与"结构增量"混在一起。建议：预注册一个**增强 B0**（B0+细胞 tissue/单药细胞效应，全部来自非 Q 元数据）作主基线，或把 B1 作 co-primary 基线并要求 Δ(B3−B1) CI 下界>0；present 规则现在的"B3≥B1 点比较"（[:138](PROTOCOL_R197.md#L138)；[r197.py:1550-1554](r197.py#L1550)）不足以排除这一点。
- **δ_min=0.05**：operational 理由（[:125](PROTOCOL_R197.md#L125)）是"噪声 0.109、0.05⇒秩方差<0.3%、低于此不足以支持后续反馈实验"。"很小"不等于 operational；与 A1 δ_min_latent=0.10 的"折半一致"需要 rel=0.25，而 q2 可靠性 0.868（未认证；即使按 0.868 折半也是 ≈0.093），自相矛盾。需给出可审计定义：例如由"后续反馈实验最小可行动增量"反推，或按预注册 reliability（A0 R_split）做 latent→observed 换算并冻结；不得用事后 rel 调整。
- **MDE/零分布/type-I**：B-D4 要求 H197a 主对比 MDE80≤0.05，B-D3 要求置换零分布 |mean|≤0.02 与完整规则 type-I≤0.10（[PROTOCOL_R197.md:127-133](PROTOCOL_R197.md#L127)）；这些先于判定 ✓。但 type-I 的完整重跑在 H197a 用 20 次模拟（[:124](PROTOCOL_R197.md#L124)）——20 次下 2 次失败=10%，无法区分 0.05 与 0.10 的合格线；协议说"报告精确二项上界"✓，但应预注册"若点估计>0.05 就需增加 sims/判 inconclusive"的更严规则。
- **H197a 覆盖边际**：Q 92,039 观测、1,501 cell-pair；留出 19 细胞折的 cell-pair 约 171/1,501≈11.4%，测试条目≈10.5k，B-D1 要求≥10,000（[:129](PROTOCOL_R197.md#L129)）——边际通过，须报告实际数并在 pre-flight 断言；20 细胞折更宽。

### 2.3 判定/措辞（③）与 A0 耦合（④）

- `predictive_structure_present` 必须带定义句："在 H197a 冷细胞对留出、预注册特征与容量对照下，存在超过增强加性基线的增量"；不得写"条件规律可迁移/反馈有用/新算子"（协议 §0 已写不是 A1/A2、不启动反馈/Agent ✓）。
- `no_stable_increment` 的"停止该资源条件规律研究"应改为"停止**该特征集/该留出设计**上的增量研究；低秩/其他表示与可辨识留出仍可另立预注册问题"；并保留 A0 若显示条件主效应 robust 时的描述性观察（不矛盾：主效应小≠无结构，见 ERRATA_Q2 §1）。
- **A0↔B 耦合缺失**：若 A0 判 `q2_inference_not_robust_under_dependence` 或 R_split<0.5，B 的 present 仍可成立（预测结构不依赖推断口径），但报告必须写"条件级可靠性未认证，B 的 present 不继承 Q2 的 condition_structure_present"；反之 A0 robust 也不把 B 的 present 升级为 A2 通过。协议没有写死这个继承规则，应补。
- 采纳 1.43% 更正 ✓、避免用 A2 int/noise 排除结构 ✓（[:83,155](PROTOCOL_R197.md#L83)）。

### 2.4 谱系/预算/确定性（⑤）

- 谱系：不是 A1/A2 通过、不跨 screen、不启动反馈/Agent/RSI、不按 Q 值挑层、不换端点/δ ✓（[:7,151-155](PROTOCOL_R197.md#L151)）。补一句"**不是新算法/新算子**：B3/B4 是标准特征回归/GBM 容量对照；present 只支持'预购信息可预测 Q'这一测量层结论"。
- 预算：单命令 ≤20 min（[:149](PROTOCOL_R197.md#L149)）但 H197a type-I 20 次 × 全流程（5 fold × B0/B1/B2/B3/B4 重拟合 + 内层 CV + B=200 CI + B=200 置换）+ A0 的 B=1,000×4 变体 + R_split 20 次；没有给出运行时间估计/缓存/分步产物/降 B 方案。需预注册"若单命令超 20 min 的降级顺序"（先减 type-I sims 到协议允许的最小值并报精度，再缓存 A0 产物），并把实际墙钟写入 record。
- 确定性：种子表 ✓（[:19-32](PROTOCOL_R197.md#L19)），JSON 键排序/无时间戳/`PYTHONHASHSEED=0`/双跑一致 ✓；输入 SHA 表中 q2.json 为"…"（[:15](PROTOCOL_R197.md#L15)），须补全 SHA（r197.py 已读 q2.json? 应断言）。

## 3. 运行前必改（≤5；AMENDMENT + 重跑后才可解释 R197）

1. **主问题/主模型对齐（最重要）**：二选一并写死：(a) 把 R197 主命题重写为"**预购元数据+单药特征能否在冷细胞对预测 Q 超过增强加性基线**"，verdict 改名（如 `metadata_predictive_increment_present`），明确**不检验低秩结构**；或 (b) 预注册 B2 可辨识的主设计（H197c 随机条目为主，或带 side-information 的 cell embedding 变体），H197a/b 降为次设计。无论哪种，`no_stable_increment` 不得关闭"低秩/背景结构"研究；B2 在冷细胞对不可辨识的事实写进报告。
2. **消除/披露特征-端点构造重叠并强化基线**：写死 B1/B3 的 `LIBRARY_EMAX/AUC` 是 ΔEMAX 期望项的输入（构造重叠），预注册特征块消融（B0 → +metadata → +mono → +interaction）与 Δ(B3−B1) 报告；present 需满足 Δ(B3−B1) CI 下界>0（或主基线改为增强 B0 = B0+细胞级元数据，且 Δ vs 它作主对比）；禁止把 mono 可解释的增量写成"条件结构"。
3. **δ_min/MDE/type-I 的 operational 化**：δ_min=0.05 给出可审计定义（决策/效用或按预注册 reliability 的 latent→observed 换算，并用 A0 R_split 的 median 值冻结，不能用 q2 的未认证 0.868 或事后 rel）；MDE80≤δ_min 与置换/完整规则 type-I 的预注册检查保留；type-I 20 次模拟的精度处理写死（点估计>0.05 时必须加模拟或判 inconclusive；报告精确二项上界）。
4. **A0 依赖感知范围与耦合**：把 V4 的"依赖感知"限定为节点级，补键/barcode 级敏感性（或至少披露未覆盖键级复用+噪声标定仅 1.43%）；graph-aware 置换的交换性写限制；R_split 报告覆盖/丢弃/不同 split 的 i 集合，并把 0.50 用途限定为条件主效应可靠性；写死 A0 状态与 B 解释的继承规则（A0 not robust → B 的 present 不得升级为条件级结论）。
5. **措辞/谱系/预算/确定性**：冻结 present/absent/inconclusive 的允许句式（不写可迁移/反馈有用/机制/新算法；阴性不写结构不存在；停止范围限定）；补"不是新算子、B3/B4 是标准基线"；给出 ≤20 min 的预算/缓存/降级方案并把实际墙钟写入 record；补 q2.json 等输入 SHA；若 r197 结果已在 AMENDMENT 前产生 → 按 Lead 规则作废重跑。

## 4. 声明与边界

- **不运行效果**：本挑战未运行 R197、未改其产物；只读协议/代码/相关产物，未运行推断/预测统计；复核仅阅读与代数核对（附录给出我独立推导的修正式与 dyadic 比值，未写脚本）。
- **结果解释状态**：R197 结果在 AMENDMENT 重跑前**不得解释/采纳**；本文不改写其数字，也不否定 A0 修正代数的正确性——否定的是"B 主实验能否检验 BRIEF 的低秩结构命题"以及 present/absent 的语义与基线/δ_min 的预注册质量。
- 若 Lead 选择不改：只能把 R197 登记为"描述了预购特征在冷细胞对的增量（若 present）"或"inconclusive（MDE/type-I/设计体检不过）"，**不得**登记为"条件规律可复用/低秩结构存在"或"该资源条件规律研究结束"。

**一句话：A0 的修正式代数是正确的（我已独立核对且与 q2.json 锚点一致），但 B 的主模型在 AMENDMENT 后被换成 B3 特征回归——R197 能测的只是"预购元数据+单药特征在冷细胞对有没有增量"，测不了 BRIEF 的低秩/背景结构；加上单药特征与 ΔEMAX 期望项构造重叠、B0 冷细胞基线弱、δ_min 理由不成立，判 revise：改主命题/主设计、补块消融与增强基线、operational 化 δ_min、限定 A0 依赖范围与措辞后 AMENDMENT 重跑，结果才可解释。**
