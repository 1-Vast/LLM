# R199-ON3-C1 独立挑战（challenge_ON3.md）——O'Neil 开发性描述分析协议 DRAFT v0.1 复审

2026-10-27 · 挑战者：endpoint-auditor（与 ON1/ON2/ON2.1/ON2.2 同一独立挑战者；未参与 ON3 起草）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON3.md（DRAFT v0.1）, on3_design.md, record_on3_design.md, usage_on3_design.json}` + 只读参照 ON2 v2.2、ERRATA、report_on2_1、ON2-EX `exec_calibration/`、challenge_ON2_2_confirm、R199 BRIEF。
方式：**只读审查 + 纯设计/算术复核**；**本轮不运行效果/训练/更新器、不读响应值做统计、不运行任何 ON3 代码**；只写本文件与 `tmp/`。
完整性：`PROTOCOL_ON3.md` SHA `B78197F1…C25557A`、`on3_design.md` `34000CA1…D90D482`、`record_on3_design.md` `747AEC63…85DB0F`、`usage_on3_design.json` `05A1A8AF…E4DB9C2`；ON2/ON2-EX 冻结输入 SHA 与 record_on3_design §2 一致。

## 0. 总判决

**revise（≤5 必改；不是 stop）；当前不可提交 Lead 批准/冻结执行。** DRAFT 的范围、数据/切分、端点、B0–B6 的**框架**基本完整，且 σ_e/MDE 算术正确（实测 0.1422665081 → MDE80=0.0287644381 ≤ 0.10）；但存在 **1 个会直接使评价无效的设计级泄漏**（单元级 20% 掩码 + transductive 非掩码 context 可用线性组合精确重建被掩码 Δ），以及若干**协议级歧义**（掩码 per-cell vs per-fold、主比较器/多重性、rank 主指标与 MDE 尺度错位、B6/B5-shuf 不可执行）。修完 5 条后可 **approve_to_lead**；不需要本轮运行数据/效果。

**最致命 3 条**

1. **单元级掩码 + transductive context = 精确线性重建泄漏（设计级 FAIL）**：
   - 在同一上下文 `(batch,cell,partner,role)` 内，单元 Δ 是成员曲线均值之差：`Δ(a,b) = mean(a) − mean(b)`。对任意第三个成员 c，有 **`Δ(a,b) = Δ(a,c) + Δ(c,b)`**（符号按冻结的归一名顺序；即三者可加闭合）。
   - DRAFT 只掩码 **20% 的单元**，其余 80% **同上下文单元作为 transductive context**（§1 line25–30；on3_design §2）。上下文通常有 ≥3 个成员（ON2：中位 18 成员/上下文），因此被掩码的 `(a,b)` 几乎总能由两个非掩码单元 `(a,c)`/`(c,b)` **精确重建**（m≥4 时几乎必然；m=3 时概率约 64% 以上，且可选 c 多）。这不是"条件结构预测"，而是**算术恒等式泄漏**。
   - DRAFT 的泄漏审计第 1 项（掩码值 +1e6 后预测不变）**抓不到**它：模型没有直接读被掩码值，只是用非掩码 context 做线性组合；预测当然不变。必须增加**model-free 重建审计**（用同上下文非掩码 Δ 最小二乘/代数求解每个掩码 Δ，要求残差显著/泄漏率为 0），并重新设计掩码。
   - **建议修复**：把评价单位改为**整上下文掩码**（如 `(cell,partner,role)` 的 20% 确定性选择；被掩码上下文内无同上下文非掩码单元）或**整成员曲线掩码**（所有涉及被选成员的单元均掩码，确保不可由同上下文补齐），或把**纯冷细胞**作为 primary/确认性设计；transductive 只能用于 cell 级 offset，不能提供同上下文 pair Δ。无论选哪种，都要有重建审计与覆盖率重算。
2. **主指标是 Spearman，但 MDE/δ_min 是均值 Δ 尺度；且增量规则没有锁死唯一主比较器/多重性**：
   - `MDE80=0.028764` 是 **mean Δ 尺度**（SE_unit=σ/√32, n_eff=6）；主指标是**掩码单元 Spearman ρ**。DRAFT §4 既写"MDE 设计门前置"，又自认"rank 指标用 B6 零模型校准（不做参数检定力宣称）"——**不能用均值 Δ 的 MDE 认证 rank 主指标的精度**。把 0.02876 当"rank 精度通过"是尺度错位；`Δρ≥0.10` 也没有从 MDE/零分布推出，只是 pre-registered 描述阈值。
   - 增量规则写 "比较器 X 相对 B2"，但 DRAFT 有 B3/B4/B5 多个 X；若不预注册 **唯一 primary comparator（应为 B4）**，"哪个 X 过阈值报哪个"就是选择性比较/多重性；B3/B5 只能作 secondary/negative control，不能与 B4 并列争取增量判定。
   - 需补：rank 指标的 **null-calibrated 最小可检测 Δρ**（B6 置换/配对 bootstrap 分布）或明确"不宣称 rank 精度，只用 null 校准"；增量规则只用 B4 vs B2；所有其他比较只作描述性、不参与 `incremental` 判定。
3. **B6/B5-shuf/掩码覆盖的代码级定义不足以执行**：
   - **掩码 per-cell vs per-fold 矛盾**：§1 line25 说"对每个 held-out 细胞的单元 Δ 做 20% 掩码"，line27 说"每个 fold 内按 h 升序取前 ceil(0.20×N_fold) 个单元"；on3_design line33 又说"每 fold，ceil"。若按 fold 全局选，某些细胞可能 <500 掩码单元（覆盖门 FAIL）；若按 cell 选，则总掩码数略高于 20% 且 fold 计数不同。必须二选一并写死。
   - **B6 零模型只有一个"打乱"**：要算 95th 不成立；需明确置换次数/seed/每次是否重拟合 B4、95th 是单侧还是双侧、B4 null 覆盖 0 的判据。当前 "B6 打乱零模型 mean|ρ|≤0.10 且 B4 null 95th 覆盖 0" 无法从单次 shuffle 计算。
   - **B5-shuf 定义不成立**：DRAFT 说"B5 同容量，训练细胞 cell 标签打乱"；但 B5 的特征列明确**不含 cell id**（member-pair target-encoding、partner、role、cell offset、context size），训练 cell 标签不是 B5 的输入/分组变量，打乱它很可能不改变 B5。必须定义有意义的负控制（如打乱训练响应在 member-pair/partner 层内的对应、或打乱 member-pair 编码），或删除 B5-shuf。
   - **B5 target-encoding 的交叉拟合/泄漏细节**、**B4 ALS 初始化/seed/tolerance/λ 定义**、**bootstrap 的 paired 重采样 schema** 均未写；这些是冻结执行前必须补的代码级细节（见 §6）。

## 1. 逐项判决摘要（对照 on3_design 8 问）

| # | 复审项 | 判定 | 一句话依据 |
|---|---|---|---|
| ① | 问题范围仅开发性；不迁移/决策/机制/独立确认/更新器；阴性措辞 | **PASS** | §0 line13–16、§6 line98–103、on3_design §1/§10 明确仅开发性描述，不称迁移/决策收益/机制/独立确认/更新器；阴性写"本资源/本设计下未观察到描述性增量"，未把阴性当结构不存在的证明。 |
| ② | 数据/切分：363,090、batch1 357,876 primary、batch2 不进 primary、batch3 全失、继承 5 折、702 15-row、不插补/单插补仅敏感性 | **WEAK** | 数字/分折/702/不插补与 ON2 一致；但 **batch2 "仅披露/敏感性可选，不得进入训练或指标"自相矛盾**（敏感性若无指标无法报告；若进指标则违反不进 primary 的边界）；掩码 20% 的 per-cell/per-fold 口径也不定（见④）。 |
| ③ | 端点/聚合：viability 4 重复均值、k=1 排除、complete 4×4 Δ、角色分层、符号冻结、不拼 ΔEMAX、不插值剂量 | **PASS** | §1 line23、§2、on3_design §3 与 ON2 定义一致；complete-case 行、完整 16 行网格、归一名升序符号、role 分层、无插值、无 ΔEMAX；k=1 排除沿用 ON2。 |
| ④ | 掩码设计：20% 确定性 key/seed、掩码不进模型、transductive 披露、覆盖门槛 | **FAIL（设计级泄漏 + 口径歧义）** | key/seed/确定性/transductive 披露本身 PASS；但**单元级掩码可被同上下文非掩码单元的线性组合精确重建**（致命 1），泄漏审计第 1 项抓不到；且 per-cell vs per-fold 不一致、覆盖门槛未预计算。 |
| ⑤ | 比较器/指标/功效：B0–B6 pre-registered、不预设胜出；主 Spearman/MAE/top-k；Δρ≥0.10、4/5、bootstrap、B6 95th；MDE | **WEAK/FAIL** | B0–B6 列表/不预设胜出 PASS；但 **唯一 primary comparator 未锁死（B4 vs B2）**，**MDE 均值尺度 vs rank 主指标错位**，**B6 单次 shuffle 无法算 95th**，**B5-shuf 定义不成立**；Δρ≥0.10/4-of-5 只是 pre-registered 描述阈值，不是精度保证。 |
| ⑥ | 门控/泄漏/失败/流程：数据门/设计门、9 项泄漏审计、B6 null、失败类别、不换配、DRAFT→挑战→批准→冻结 | **WEAK** | 9 项审计/失败类别/流程/停止条件基本完整；但**缺 model-free 线性重建审计**（最关键泄漏）、B6 置换次数/单双侧未定、B5-shuf 定义不成立；batch2 措辞矛盾；代码级 schema 未冻结。 |
| ⑦ | 总判决 | **revise（≤5）** | 修复致命 1（掩码逻辑泄漏）、致命 2（主比较器/MDE 尺度）、致命 3（B6/B5-shuf/口径）与代码级细节后，可 approve_to_lead；当前不可冻结执行。 |

## 2. 关键设计缺陷详述

### 2.1 致命 1：单元级掩码的线性重建泄漏（必须先修）

**代数事实（不需要读数据即可验证）**：对任一上下文内三个成员 a,b,c：
`Δ(a,b) = mean(a) − mean(b)`
`Δ(a,c) + Δ(c,b) = [mean(a)−mean(c)] + [mean(c)−mean(b)] = mean(a) − mean(b) = Δ(a,b)`。

- DRAFT §1 line25–30 只掩码 **20% 单元**，其余 80% 同上下文单元是 transductive context；B3/B4/B5 都允许使用 held-out 非掩码 context（§3 line48–57）。
- 在 ON2 的 legal contexts 中，成员数中位 18（on2.json），m≥3 极常见；任意被掩码 `(a,b)` 只要找到未掩码的 `(a,c)` 与 `(c,b)` 即可精确重建；m 越大越必然。**这不是统计学习，而是恒等式**。
- **泄漏审计第 1 项（mask 值 +1e6）无法检测**：预测器不读 mask 值；它读的是非掩码 context，mask 值扰动当然不改变预测。必须新增：**
  1. **model-free reconstruction test**：对每个掩码单元，在**同上下文**用非掩码单元解线性方程（或按上述三项关系检查）；计算可精确重建比例、重建残差；若 >0 个可重建 → `design_invalid`；
  2. **context ablation**：对被掩码单元，禁止使用其同上下文任何非掩码 Δ（或其成员曲线）作为特征；或直接改为整上下文/整成员曲线掩码。
- **推荐修复**（任选、需写死）：
  - **A（推荐）整上下文掩码**：确定性选 20% 的 `(cell,partner,role)` 上下文整体掩码；被掩码上下文内没有同上下文非掩码单元；held-out 其他上下文只提供 cell 级 offset；再加重建审计。
  - **B 整成员曲线掩码**：选 20% 的成员曲线（或成员）并在所有 partner/role 上掩码其涉及单元；确保没有非掩码单元共享被掩码成员。
  - **C 纯冷细胞**：held-out 细胞不使用任何非掩码 context（或只作确认性 sensitivity）；这样最保守，但"条件结构"的可识别性下降，需在协议中说明。
- 修复后必须重算覆盖门槛：每 fold 掩码单元、每 held-out 细胞、每 fold 掩码上下文都 ≥原门槛（5,000/500/50）；若选上下文掩码，需预先计算 20% 上下文对应的单元数并冻结。

### 2.2 致命 2：主指标/MDE/比较器多重性

- **MDE80 尺度**：`MDE80 = 2.801585 × (σ̂_e/√32) / √6 = 0.0287644381` 是 **mean Δ** 的 80% 最小可检测差异；主指标是 **Spearman ρ**。DRAFT 一边把 MDE80≤0.10 当"设计门前置"，一边承认"rank 指标用 B6 null 校准"——**不能把 mean-Δ MDE 当作 rank 精度认证**。
- **建议**（二选一，写死）：
  - **A**（推荐）把 MDE80 只用于 **mean Δ/MAE 尺度**的精度门槛/报告；rank 主指标另外定义 **rank-specific null-calibrated 最小效应**（B6 置换分布 + 配对 bootstrap 的 Δρ 分布），不声称 MDE80 覆盖 rank 精度；或
  - **B** 把 **mean Δ/MAE 设为 co-primary**，MDE80 只对 mean Δ 生效；Spearman 仍为描述性主指标但不作为"精度认证"。
- **增量规则**：`Δρ(X−B2)≥0.10` 中的 X 只能是**唯一 pre-registered primary comparator B4**；B3/B5/B5-shuf 只能 secondary/negative control，不能参与 `incremental` 判定。否则比较多个 X 存在选择/多重性风险（即使描述性，也会造成"选最好的"解释）。
- **B6 95th/单双侧**：DRAFT 的"观测 ρ 落 B6 95% 范围内 → cannot_distinguish"与"Δρ>B6 95th"未定义单侧/双侧；建议**单侧上 95th（正向增量）**，并明确 zero distribution 的置换数（≥1,000）、seed、是否每次重拟合 B4、B4 null 覆盖 0 的定义。

### 2.3 致命 3：B6/B5-shuf/掩码口径的不可执行

- **掩码口径**：DRAFT line25 "每个 held-out 细胞 20%" vs line27 "每个 fold 内前 20% N_fold"；on3_design line33 "每 fold"; **三者不一致**。若 fold 全局选，per-cell ≥500 覆盖门可能 FAIL；若 cell 选，总单元数、fold 计数、coverage 都要重算。必须二选一并冻结算法/计数。
- **B6**：零模型"打乱"没有置换次数/seed/每次是否重拟合；单次 shuffle 无法给 95th。建议 B6 置换 B=1,000–5,000、固定 seed、每次重拟合/变换 context，保存 null 分布；B6 与 B4 的 null 覆盖 0 的判据要写清。
- **B5-shuf**：B5 特征明确不含 cell id（target-encoding member-pair、partner、role、cell offset、context size），"训练细胞 cell 标签打乱"不会改变 B5 的输入/分组；这个负控制很可能无效。改为**打乱训练响应在 member-pair（或 partner/role）层内的对应**、或打乱 member-pair target encoding，或删除 B5-shuf。必须写死。

## 3. 数据/切分/端点/scope 核对（PASS/WEAK）

- **cohort**：complete-case **363,090/98.44%**；batch1 **357,876**（358,560−684）；batch2 **5,214**（5,232−18）；batch3 **0/5,040**——与 ON2 一致。
- **5 折**：附录 A 的 5×6 细胞与 ON2 `on2.json.fold_design.folds` 完全一致（已逐折核对）；fold 单元 66,556–69,738；不重分折；PASS。
- **30 目标细胞/9 重叠排除**：与 ON2 一致（non-Jaaks 30）；PASS。
- **702 个 15 行 pair-cell**：作为不完整 member context 排除并计数；PASS（需执行时按 ON2 计数复核）。
- **主分析不插补**；确定性行均值单插补仅敏感性（非 MI、无 m/seed/Rubin）；与 ON2 v2.2 一致；PASS。
- **batch2 矛盾（WEAK）**：§1 line20 写 "batch2 不进主分析（仅披露/敏感性可选，不得进入训练或指标）"——若"敏感性"需要指标则与"不得进入指标"矛盾；若不允许指标则敏感性无意义。建议改成：**batch2 只作描述性披露，不进训练/指标/增量判定**；若要敏感性，须预注册为独立的非主分析、不与 primary 混报，且不改变 primary 结论。
- **端点**：viability 四重复均值、complete 4×4 网格、k=1 排除、角色分层、符号归一名升序、无 ΔEMAX、无剂量插值——PASS（与 ON2 定义一致）。
- **scope/negative wording**：仅开发性描述、不迁移/决策/机制/独立确认/更新器；PASS（§6/design §10 明确阴性只写"本资源/本设计下未观察到描述性增量"）。

## 4. 比较器/指标/功效核对（WEAK）

- **B0–B6 列表**：B0 全局均值、B1 静态可加、B2 静态强、B3 + cell offset、B4 层级+低秩、B5 HistGBM、B5-shuf、B6 null；pre-registered、不预设胜出；PASS（框架）——但 B5-shuf 实现不成立（见 §2.3），B6 置换未定。
- **B2 强度**：partner×member-pair 交互的 cell-blind lookup 是合理的强静态基线；需写死 backoff（未见 pair/partner → role×partner → 全局）与"绝不使用 held-out 非掩码单元"；B2 可作为主基线。B1/B0 更弱；**B2 不是"结构成立"证据**（protocol §6 已写）；PASS/WEAK。
- **指标**：Spearman pooled/per-fold/per-cell median、MAE、top-k 描述；**top-k 需明确 masked context 的 k/ties/context size**，并建议降为附录/描述性（protocol 已写无决策含义）；PASS/WEAK。
- **Δρ 规则**：0.10/4-of-5/paired bootstrap 95% CI/null 95th 是 pre-registered 描述阈值，但不是从 MDE 导出的 rank 精度；**4/5 folds 只看符号**，可被 5 折异质性放大；建议 B4-only、单侧、bootstrap 细节写死（重采样 held-out 细胞、是否重拟合/重算预测）。WEAK。
- **MDE**：算术正确（σ̂_e=0.1422665081、SE=0.0251494031、MDE=0.0287644381、n_eff=6、δ_min=0.10）；但主指标 rank 与 MDE 尺度错位；**MDE 只对 mean Δ/MAE 有效**，不能作为 rank 精度认证（致命 2）。

## 5. 门控/泄漏审计/失败/流程核对

- **数据门**：ON2 数据门已 PASS；ON3 追加 batch1/30 细胞/5 折/掩码覆盖/702/无 endpoint 缺失；框架 PASS；但覆盖门槛需按修复后的掩码口径重算。
- **设计门**：MDE≤0.10、掩码确定性、超参仅训练 CV、比较器 pre-registered、9 项泄漏审计；框架 PASS；**但 9 项审计缺最关键的单元重建泄漏（§2.1）**，B6/B5-shuf 不可执行（§2.3）。
- **9 项泄漏审计**：掩码扰动、cell identity、batch1 only、无 Jaaks/ΔEMAX、无剂量插值、无 test 调参、mask key/seed、单药不进 primary、折继承——方向正确；**需增加第 10 项 model-free reconstruction / context-ablation audit**；掩码扰动测试不能替代它。
- **零模型**：B6 mean|ρ|≤0.10 且 B4 null 95th 覆盖 0；目标合理，但置换次数/单双侧/每次是否重拟合未定；不能执行。
- **失败类别/停止**：`data_unavailable`/`design_invalid`/`evaluation_cannot_distinguish`/`no_increment`；不换指标/切分/端点/掩码/比较器、不重跑换 seed；PASS。
- **流程**：DRAFT→独立挑战→Lead 批准→冻结 execution protocol→执行；PASS（本挑战即为该步；当前不可跳过）。

## 6. 五条必改（≤5）

1. **修复掩码线性重建泄漏（最高优先，设计级）**：改为**整上下文掩码**（推荐 A；被掩码 context 内无同上下文非掩码单元）或**整成员曲线掩码**（B）；或纯冷细胞（C）。增加 **model-free reconstruction audit**（每个掩码 Δ 用同上下文非掩码 Δ 线性重建；可重建/残差过小 = 0 容忍）与 **context-ablation test**；重算/冻结覆盖门槛；更新协议 §1/§5.2/on3_design。
2. **锁死唯一 primary comparator + 多重性**：**B4 vs B2 为唯一增量判定**；B3/B5/B5-shuf 只作 secondary/negative control；B5-shuf 改为有意义的响应/编码打乱（或删除）；所有指标报告完整比较表，不允许"选最佳 X"。
3. **修正 MDE/rank 尺度**：MDE80 只用于 mean Δ/MAE 尺度，不再作为 rank 主指标精度认证；为 rank 明确定义 null-calibrated 最小 Δρ/配对 bootstrap 精度，或把 mean Δ/MAE 设为 co-primary；δ_min 只对 mean 尺度；单侧/双侧 95th 写死。
4. **冻结 B6/B5/B4/掩码的代码级 schema**：B6 置换数/seed/重拟合/单侧 95th；B5 HistGBM `random_state`、target-encoding 交叉拟合（LOO/K-fold）；B4 ALS 初始化/seed/tolerance/λ 定义、c_cell/U_cell 仅由非掩码 context 估计；bootstrap 按 held-out 细胞配对的 B/seed/百分位；mask key/排序/tie/selection scope；两跑逐字节一致、≤45 min、输出 JSON schema/单测。
5. **修正 batch2/覆盖/措辞并冻结执行协议**：batch2 只作披露（或预注册独立非主敏感性，不得混入 primary 指标/增量）；按修复后的掩码口径重算 per-fold/per-cell/context 覆盖门槛；top-k 上下文/tie 写死并降为附录；报告模板/阴性措辞/失败类别冻结；DRAFT→v0.2→挑战复核→Lead 批准→冻结 execution protocol，执行前不得改 mask/seed/fraction/超参。

## 7. 对 on3_design §11 的 8 问直接回答

1. **“细胞留出 + 20% 单元掩码 + transductive context” 是否可接受？** **按当前单元级掩码：不可接受**（线性重建泄漏，见 §2.1）；改为整上下文/整成员曲线掩码后可作为开发性描述设计；transductive 本身可披露，但**不是纯冷启动**，结论不得写迁移/新细胞。推荐增加纯冷细胞作为确认性 sensitivity（不是 primary）。
2. **20% 掩码/seed 改预注册随机还是分层？** 改为**确定性、分层（按上下文/成员）选择**，固定 20%/seed/hash，冻结后不改；优先**整上下文**选择（避免线性重建），而不是单元随机；需预计算覆盖。
3. **增量阈值（Δρ≥0.10/4-of-5/bootstrap/null 95th）是否合理？** 作为 pre-registered **描述性**阈值可保留，但必须 **B4-only**、单侧 null、bootstrap 细节写死；0.10 不是 MDE 导出的 rank 精度，不能宣称"有精度保障"；4/5 folds 仅作描述性稳健性。
4. **B2 是否足够强？** B2（cell-blind partner×member-pair 交互）是合理的强静态基线；需写死 backoff 且确保不用 held-out context；可作为主基线；B2 通过不证明"条件结构成立"（protocol 已写）。可另加 B1/B0 作为层级参照。
5. **单药工作簿是否应先资格？** **是**：primary 完全不用单药数值；若未来使用，必须另立单药资格协议+独立挑战，只能作为预先注册的敏感性，不得进 primary（与 ON2/ON3 现有边界一致）。
6. **B5 容量网格/特征是否足够？** 网格方向合理，但 **B5-shuf 目前无效**、target-encoding 交叉拟合/泄漏未写、`random_state` 未定；需补强/修正；容量对照不能替代 B4 的条件结构检验。
7. **top-k 是否降为附录？** **建议降为附录/纯描述**（协议已写无决策收益）；保留 base rate/context 数，避免被误读为选药/实验收益。
8. **B6 打乱粒度是否足够？** 跨细胞 context 打乱、保持 partner/role 分层方向合理，但**单次 shuffle 不足以给 95th**；需 ≥1,000 次置换/seed/单侧 95th，并明确 B6 对 B4 的零分布与覆盖 0 判据；B5 需单独的负控制（B5-shuf 修正）。

## 8. 保留项（DRAFT 的正确框架，不要回退）

- 仅开发性描述、不迁移/决策/机制/独立确认/更新器；阴性措辞"本资源/本设计下未观察到描述性增量"。
- complete-case 363,090/98.44%、batch1 357,876 primary、batch2 不进 primary、batch3 全失披露；30 目标细胞、5 折 6/6/6/6/6 继承 ON2；702 15-row pair-cell 排除计数；主分析不插补、单插补仅敏感性（非 MI）。
- viability 四重复均值、complete 4×4 网格 Δ、k=1 排除、角色分层、符号冻结、无 ΔEMAX、无剂量插值。
- B0–B6 框架、pre-registered、不预设胜出；主 Spearman/MAE/top-k 描述；失败类别/停止/不换配；9 项泄漏审计方向（补第 10 项重建审计）；DRAFT→挑战→Lead→冻结 flow。
- 实测 σ̂_e/MDE 算术（0.1422665081 → 0.0287644381≤0.10）正确；但只能作 mean Δ 尺度的 precision prior。

## 9. 复核证据与本轮边界

- 本挑战只读 `PROTOCOL_ON3.md`（SHA `B78197F1…C25557A`）、`on3_design.md`（`34000CA1…D90D482`）、`record_on3_design.md`（`747AEC63…85DB0F`）、`usage_on3_design.json`（`05A1A8AF…E4DB9C2`）；以及 ON2/ON2-EX 冻结产物、R199 BRIEF；**未运行数据/效果/训练/更新器、未读响应值做统计、未运行 ON3 代码**；只写本文件与 `tmp/`；未改 ON1/ON2/ON3 草案产物。
- 结论只审"是否可进入 Lead 批准/冻结执行协议"；不产生生物学/效果结论；DRAFT 仍不是执行依据。
