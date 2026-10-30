# AMENDMENT_R197-002 —— R197 v2 预注册修订（2026-10-27，**任何 v2 推断/留出预测运行之前**）

> 依据：R197 v1 独立挑战 [challenge_R197.md](challenge_R197.md)（task-30，判 **revise**）、Lead 的 [REVOCATION_R197.md](REVOCATION_R197.md)（v1 作废，须 AMENDMENT 重跑并通过 task-34 后才可解释）、R197 BRIEF、ERRATA_Q2/ERRATA_A3、PROTOCOL_R197 v1 及其 AMENDMENT-001。
>
> **本文件在任何 R197-v2 推断/预测统计运行之前冻结。** v1 状态如实登记：`PROTOCOL_R197.md`、`r197.py` 保留；**v1 从未产出 `r197.json`/`r197_rows.csv`/verdict**（一次 `--quick` 调试运行在写盘前被 Lead 作废通知终止；无 v1 结果可解释或采纳）。v2 只在 AMENDMENT-002 通过 task-34 挑战后才可解释；此前不改写任何 v1 文本。
>
> **v1 判定登记（Lead 已定）**：R197 v1 = `inconclusive / design_invalid（主问题未被可辨识地检验）`。不得据此写"Q 无可复用结构/条件规律不存在/反馈无用"，也不得写"条件结构可预测"。

## 0. 选择与主问题（预注册；二选一中的**方案 Q**）

- **选择方案 Q**：保留 BRIEF 的主问题——**Q 的预留出结构（交互/低秩）能否在留出条目上被可辨识的模型预测，而不只是噪声/加性基线**。v1 的错位（把主对比换成 B3 特征回归、B2 在冷细胞/冷条件设计不可辨识）不再成立：
  - **主设计 = H197c（随机留出 20% 观测条目，5 折）**：行与列在训练集中均有观测 → **B2（加性+低秩 ALS 矩阵补全）可辨识**，B2 作主模型。主对比 `Δ_primary = Spearman(B2) − Spearman(B0加性)`；B2 不含任何元数据/单药特征，只从 Q 矩阵学行/列/低秩结构。
  - **H197a（冷 cell-pair）与 H197b（冷 condition-pair）降为次设计、描述性**（不参与主 verdict）：它们检验的是"预购特征对冷行/列的增量"（B3−B0、B3−B1 等），**不检验低秩结构**（B2 在整列/整行留出下结构不可辨识，预测退化为 B0；该代数事实已在 AMENDMENT-001 与挑战中确认，v2 只报告不解释为结构）。
  - **主问题的可回答范围（写死）**：H197c 只检验"Q 的未观测条目能否被低秩+加性补全预测（相对加性基线）"，**不检验**冷细胞/冷条件迁移、不检验反馈可修正/迁移、不检验选药收益。若 H197c present，只能说"Q 的条目间低秩结构可被可辨识的矩阵补全预测（留出随机条目）"，**不得**写"条件规律可迁移/可复用跨细胞/反馈有用"。

## 1. 与 v1 的差异一览（全部为预注册的推理/可辨识性修正，非事后择优）

| 项 | v1 | v2（本修订） |
|---|---|---|
| 主问题 | BRIEF 问题，但主模型被换成 B3 | 保留 BRIEF 问题；主设计 H197c + 主模型 B2（可辨识） |
| H197a/b | 主张量 | **次设计、描述性**；B2 不可辨识只报告退化证明 |
| 主对比 | H197a: B3−B0 | **H197c: B2−B0**；另报 Δ(B2−BM)、Δ(B2−BMono)、Δ(B2−B3)、B2 vs B4 |
| 特征-端点构造重叠 | 未披露 | **披露**：B1/B3 的 LIBRARY_EMAX/AUC 与 ΔEMAX 期望项构造相关；主对比 B2 不含这些特征；做特征块消融 B0→BM→BMono→B3 |
| δ_min | 0.05（"很小"式理由） | **operational 冻结**：`δ_min = 0.10·sqrt(rel_entry)`，`rel_entry = 1 − share_noise`（A0 重校准的条目级信度；0.10 为 R193-A1 冻结的 latent 最小增量锚，不是 q2 0.868/旧 CI）；另报 `0.10·sqrt(R_split)` 敏感性；A0 计算先于 B 打分并冻结 |
| A0 依赖感知范围 | "依赖感知" | **限定为节点级**；新增**键级 V5 bootstrap 敏感性**（9,154 键重采样、键被多个 Q 复用）；置换交换性限制写死；R_split 覆盖/丢弃/集合稳定性报告，阈值用途限定为"条件主效应可靠性" |
| type-I | 20/10/10 次，精度问题 | **主设计 20 次 + 更严规则**：点估计>0.05 必须追加 20 次；合并后 >0.05 即设计体检失败（比冻结上限 0.10 更严）；报 Clopper–Pearson 95% 上界 |
| 措辞/谱系/预算 | 部分 | 写死句式、停止范围、不是新算子、缓存/降级顺序、实际墙钟、输入 SHA |
| 判定名 | predictive_structure_present / no_stable_increment | **`low_rank_structure_present` / `no_stable_low_rank_increment` / `inconclusive`**（次设计另有 `feature_increment_present/absent` 描述标签，不进主 verdict） |

## 2. 数据、重建与确定性（沿用 v1，且加以下断言）

- 数据重建与冻结口径同 PROTOCOL_R197 §0/v1（Original fitted + matched_conditions，Q 229×1,501、92,039 条目、96 细胞、291 条件、9,154 键）；结构断言不变，另断言 `unique(i,j)=92,039`。
- 输入 SHA256（全部写入 `r197_v2.json`）：Original fitted `1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278`；matched_conditions `73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF`；q2.json `94C5CD9B2C2FCACABCB7780A1F5CAAEBCCE81D23B926437682BE4F60D9793DE2`；PROTOCOL_R197 `36EF187318A44DBA7560F32B9C171D841E7B7B282920201864ED240FD5E76AD4`；challenge_R197 / REVOCATION_R197 / AMENDMENT 自身的 SHA 也记录。
- 确定性：固定 `PYTHONHASHSEED=0`；所有种子见 §5；JSON 键排序、无时间戳、`allow_nan=False`；`r197_v2.json` 与 `r197_v2_rows.csv` 连续两次运行逐字节相同（验收）。

## 3. A0 重校准（v2；节点级，降级披露 + 键级敏感性）

A0 的修正式代数、未加权 sanity、dyadic 原型、图感知置换的定义沿用 PROTOCOL_R197 v1 §2（挑战已独立核对代数正确）；v2 只做以下**降级/补充**（不改变点估计）：

1. **依赖感知范围限定（写死）**：V1–V4 只到 **节点级**（96 细胞 / 291 条件节点重采样）；Q 条目复用同一批 cell×condition 键与 barcode 均值，**V4 不保留键/barcode 级测量相关**。因此 v2 的"依赖感知"一律写作 **"节点级依赖感知"**。
2. **键级敏感性 V5（新增）**：对 **Q 实际使用的 4,686 个 (cell,condition) 键**（9,154 个匹配键的子集）有放回重采样（B=1,000，seed 新增 `20261112`；运行前实测子集大小，唯一断言 `n_used_keys<=9154`）；每个 Q 条目的权重 = 其 4 个键 multiplicity 之积（4 键不全被抽到的条目权重 0）；用修正式重算 σ²_cond/σ²_cellpair/σ²_total/share。报告 V5 的 SE/CI 与 V4 对照。**不把 V5 当"完整测量级模型"**：barcode 级相关仍未覆盖（噪声标定仅覆盖 1.43% 观测，写死披露）。
3. **置换交换性限制（写死）**：列内在已观测行集合内置换、行内在已观测列集合内置换，仅作为"结构保持的近似零分布"；不声称精确交换性/精确 p 值；与参数/节点 bootstrap 结论并列，不单独作为唯一证据。
4. **R_split 用途限定与覆盖报告**：仍用 cell 半分（20 splits）Spearman–Brown；新增报告每次 split 的（被纳入条件对数、每半 cp 阈值丢弃数、跨 split 的 condition-pair 集合两两 Jaccard 中位数）；**0.50 阈值只用于"条件主效应可靠性"的认证标签**，不推广到 c_ij/结构可预测性。
5. **A0 状态与 B 解释的继承规则（写死）**：
   - 若 A0 status = `q2_inference_not_robust_under_dependence` 或 R_split median<0.50 → B 的任何 present 词必须同时写"**条件级可靠性未认证**；B 的 present 不继承 Q2 的 condition_structure_present"，且不得写"条件规律"；
   - 若 A0 status = `q2_inference_robust` → B 的 present 仍**不得**升级为 A2 通过/条件规律可迁移；A0 只是推断重校准，非效果证据。
6. **δ_min 的 A0 依赖（冻结公式，见 §4.6）**：`rel_entry = 1 − share_noise_clipped` 与 `R_split` 均在 A0 段计算完成、写入日志后，才允许进入 B 打分（代码顺序 + 运行时断言）。

**A0 状态标签不变**：`q2_inference_robust` / `q2_inference_not_robust_under_dependence` / `q2_recalibration_inconclusive`（判据同 v1 §2.4，但依赖感知主口径 = V4 节点级；V5 键级只作敏感性，不进判据）。

## 4. B v2：模型、设计、指标、判定

### 4.1 特征块（消融用；仅次设计/控制用，主对比不用）

- 元数据块 **M**：细胞 tissue one-hot(3+3)+same_tissue；condition-pair 元数据（anchor_pathway one-hot、anchor type、library p/q pathway one-hot、library p/q type、same_library_pathway、anchor_conc、library_conc）。
- 单药块 **P**：`mono_emax/mono_auc` 的库间差（同 v1；缺失用同 library 在 96 匹配细胞的中位数填补）。**构造重叠披露（写死）**：`LIBRARY_EMAX/AUC` 是 ΔEMAX 端点期望项的输入，因此 P 块与端点部分机械相关；任何含 P 的模型的增量**不得**解释为"条件结构/可迁移规律"，只能记为"单药可解释部分/预购信息"。
- 交互块 **X**：细胞侧（tissue one-hot、same_tissue、单药差）× 条件侧（library type、same_library_pathway、anchor pathway one-hot）逐对乘积。
- 特征模型：**BM**=ridge(M)；**BMono**=ridge(M+P)（=v1 B1 改名）；**B3**=ridge(M+P+X)（=v1 B3）。特征块消融按 Spearman(B0)→BM→BMono→B3 报告增量。

### 4.2 模型（全部预注册；B2 为主模型）

- **B0 加性**：`Q_ij≈μ+a_i+b_j`，训练条目交替均值（tol 1e-9/≤200 迭代）；观测到的行/列效应；未见行/列效应=0。
- **B2 低秩矩阵补全（主模型）**：`Q_ij≈μ+a_i+b_j+(UV^T)_ij`，rank `r∈{1,2,3,5}`；**秩选择（预注册两层）：** 外层训练条目内 80/20 内层划分（seed 20261109 派生）；用**单步截断 SVD 代理**（对 B0 残差按训练条目观测填充 0 后做秩 r SVD，内层验证 MSE）选择 r；随后用 **ALS（λ_lr=0.1，25 次迭代，固定 seed）** 在外层训练条目上以所选 r 拟合。未见到行/列因子置 0。秩选择只用训练条目。**B2 不使用任何元数据/单药特征**。
- **B4 容量对照**：HistGradientBoostingRegressor(max_iter=200, lr=0.05, max_leaf_nodes=31, min_samples_leaf=20, l2=1.0, random_state=20261111)，输入=B3 特征+B0 预测列；不调参。

### 4.3 设计（预注册）

- **H197c（主）=随机留出 20% 观测条目**：92,039 条目按 `(row,col)` 排序后，用 seed 20261106 的随机置换 `i%5` 分 5 折；测试=该折条目，训练=其余。**可辨识性设计体检（先于打分）**：每行/每列在训练集至少有 1 个观测（要求 100%）；每行/每列训练观测 ≥20 且测试观测 ≥5（要求 100%）；每个测试条目所在行、列均在训练中出现。不满足 → `inconclusive`。
- **H197a（次，描述性）=冷 cell-pair**：96 细胞按规范化名排序 `index%5`；测试=两细胞均在折内、训练=两细胞均不在折内的观测；跨折细胞对不入训练/测试（计数报告）。**次设计的 primary_descriptive = B3**（特征增量），报告 Δ(B3−B0)、Δ(B3−BMono) 及其 CI；**不进入主 verdict**；B2 结构不可辨识只报告代数证明/退化检查。
- **H197b（次，描述性）=冷 condition-pair**：229 行按 `(anchor_id,library_p,library_q)` 排序 `index%5`；测试=该折行；训练=其余行。同样次设计/描述性、primary_descriptive=B3。

### 4.4 指标与推断

- 指标：每个设计×模型 **OOF Spearman**（全部测试条目）、每折 Spearman、OOF R²。
- **主对比（H197c）**：`Δ_primary = Spearman(B2) − Spearman(B0)`；另报 Δ(B2−BM)、Δ(B2−BMono)、Δ(B2−B3)、以及 B2 vs B4 的点比较。
- **CI**：聚类 bootstrap（B=1,000，seed 20261107）：H197c 双向按细胞+condition-pair 节点重采样、条目按重采样单元的多重性复制；H197a 按细胞、H197b 按行（次设计 B=500）。
- **MDE80**：`2.802·SD_boot(Δ_primary)`；主设计体检要求 **MDE80 ≤ δ_min**（H197a/b 记录不设门槛）。
- **置换零分布（先于判定）**：H197c 主对比，保持不变预测、随机置换测试条目观测 Q（B=1,000，seed 20261108）；报告 null mean/sd/q95、单侧 p。
- **完整规则 type-I（H197c 主规则）**：20 次零数据模拟（整体随机置换 92,039 个 Q 值，seed 20261110+s）；每次完整重跑 H197c 的**放宽规则**（Δ≥δ_min 且 cluster CI 下界>0；容量对照/置换-p 两个合取项省略 → 上界）。预注册精度规则：**点估计 >0.05 → 追加 20 次；合并估计 >0.05 即设计体检失败**（比 0.10 上限更严）；同时报 Clopper–Pearson 95% 上界。H197a/b 不做完整规则 type-I（次设计、描述性），只报置换零分布。

### 4.5 设计体检（H197c 主设计；任一失败 → `inconclusive`，不再判 present/absent；H197a/b 只记录不设门槛）

- **B-D1 覆盖**：测试条目 ≥10,000；每折测试 ≥1,000；所有模型 OOF 有限比例 ≥99%。
- **B-D2 无泄漏**：每折测试条目 ∩ 训练条目 = ∅；秩选择/λ 只用训练条目（代码断言）；H197a/b 的冷行/列不在训练中出现（断言）。
- **B-D3 可辨识性（H197c）**：见 §4.3 三条 100% 检查；B2 拟合后 U/V 对测试行/列非零（非退化证据）。
- **B-D4 零分布/type-I**：置换零分布 |mean|≤0.02；完整规则 type-I（§4.4 规则）≤0.05（点估计；>0.05 → 追加；合并 >0.05 fail）；报告上界。
- **B-D5 检定力**：MDE80(Δ_primary) ≤ δ_min。
- **B-D6 确定性/输入**：SHA 断言与双跑一致（record 记录）。

### 4.6 δ_min（operational，冻结在先；不用 q2 0.868/旧 CI）

- 锚：R193-A1 冻结的 `δ_min_latent = 0.10`（"可支持后续反馈实验的最小 latent 条件增量"；作为外部预注册锚引用，不作为 q2 结果）。
- 换算：条目级观测 = latent + 测量噪声；A0 的 `share_noise_clipped = σ²_noise_avg/σ²_total` → **条目级信度 `rel_entry = 1 − share_noise_clipped`**；`δ_min = 0.10 · sqrt(rel_entry)`。
- 先验预期（只作 sanity，不用真值调整）：share_noise≈0.46 → δ_min≈0.073。若 `rel_entry` 不可计算/不在 (0,1] → 主设计 `inconclusive` 停并记录。
- 敏感性（只报告，不改主 δ_min）：`δ_min_alt = 0.10·sqrt(R_split median)`（挑战建议的 A0 可靠性换算）；以及 `δ_min=0.05` 的旧 v1 口径（只用于说明结果对 δ 的敏感性，不进入判定）。
- **禁止**：从 q2 的 0.868、旧 CI/power 数字反推 δ_min；不得在见 B 结果后调整 δ_min。

### 4.7 判定（冻结）

- **`low_rank_structure_present`**（主，H197c）：B 设计体检（含 type-I、MDE、可辨识性）全部通过 **且** `Δ_primary ≥ δ_min` **且** CI 下界>0 **且** 置换 p<0.05。附字段：
  - `beyond_prepurchased_features` = 布尔：`Δ(B2−BMono) CI 下界>0` **且** `Spearman(B2) ≥ max(Spearman(BM), Spearman(BMono), Spearman(B3), Spearman(B4))` 点比较。若 false，present 词限定为"低秩补全优于加性基线，但未优于预购特征/容量对照；不得主张结构超出预购信息"。
- **`no_stable_low_rank_increment`**：体检通过但 present 条件不成立 → 只能写"**在本资源、本端点、H197c 随机条目留出与预注册模型下，未检出可辨识的低秩增量**"；**不得**写"Q 没有低秩/条件结构"，也不得关闭其他表示/其他留出/冷启动研究；H197a/b 的次设计结果只作描述。
- **`inconclusive`**：任一设计体检失败（可辨识性/覆盖/泄漏/置换零分布/type-I/MDE/确定性）→ 停，记录边界与解冻条件。
- 次设计标签（描述性，不参与主 verdict）：`feature_increment_present_descriptive` / `feature_increment_absent_descriptive`，基于 B3−B0 与 B3−BMono 的 CI/点估计；措辞必须写"预购特征在冷行/列的增量，不检验低秩结构、不检验迁移"。

### 4.8 措辞模板（冻结，报告中逐字引用）

- 允许：`low_rank_structure_present` = "在 Q 的随机留出观测条目上，可辨识的加性+低秩矩阵补全优于加性基线 [Δ=…, CI…]；这是留出条目预测的测量层结论，不是条件规律可迁移、不是反馈可修正、不是新算法，也不改变 A1/A2/A3 的地位。"
- 允许：`no_stable_low_rank_increment` = "在本资源/端点/H197c 设计/预注册模型与 δ_min 下未检出可辨识低秩增量；阴性不表示结构不存在，只限制该设计/该表示/该留出。"
- 禁止（全部写死）：写"可迁移条件规律/条件规律存在/反馈有用/机制/新算子/共同学习成立"；把 1.43% 当规律总量；用 H197a/b 的 present 冒充低秩结构；把任何阴性写成"该资源条件规律研究结束"。

## 5. 种子（v2 全部）

沿用 v1 种子并新增：键级 bootstrap `20261112`；H197c 折分配 `20261106`；秩选择代理内层 `20261109`；其余同 PROTOCOL_R197 §1（boot 20261102/20261103/20261107、perm 20261104/20261108、split 20261105、type-I 20261110、HGB 20261111、dyadic MC 20261102）。

## 6. 预算、缓存、降级与墙钟（≤20 min）

- 顺序：加载/断言 → A0（V1–V5、置换、R_split、δ_min）→ **断言 A0 已写入日志且 δ_min 冻结** → B（H197c 主 → H197a/b 次）→ type-I（H197c）→ 体检/判定 → 写盘。
- 缓存/降级顺序（超时按序执行，记录实际墙钟与降级）：
  1. 固定随机种子的中间量缓存（Q 矩阵、特征矩阵、RidgeSet 内层分解）只建一次，type-I 复用；
  2. 若预计 >18 min：先减 H197a/b 次设计的 CI B 到 200（主设计 CI 不变）；
  3. 再减 type-I 为 20 次后按 §4.4 精度规则处理（不预跑额外 sims）；
  4. 仍超 → 停并写 `inconclusive: runtime budget`（不静默降低主设计 B）。
- v1 已实测：单命令 ≥10 min 未完成（被终止；无产物）→ v2 用上述缓存设计与秩选择代理控制预算；实际墙钟写入 `usage_r197_v2.json` 与 `record_r197_v2.md`。

## 7. 谱系/纪律

- **不是新算法/新算子**：B0/B1/B3/B4 是标准加性/岭回归/GBM 容量对照；B2 是标准低秩+加性矩阵补全；本任务只做测量层资格与可预测性检验。
- 不是 A1/A2/A3 的通过/复活；不做跨 screen 复验；不启动反馈/Agent/acquisition/RSI；不做机制/临床主张；不按 Q 值挑层/挑 condition-pair；不换端点；不用测试集调参；不因结果改门槛/δ_min/措辞。
- 只写 `research/2026-10-27-q-structure/`（新增 v2 文件）与 `tmp/`；不改 v1 的 PROTOCOL/r197.py/challenge/REVOCATION、其它目录、INDEX、SYNTHESIS、git。

## 附：预注册文本的运行前更正（2026-10-27，v2 首跑之前）

- §2 的输入 SHA 表中，`q2.json` 与 `PROTOCOL_R197` 的 SHA 在我首次写入本文件时误填（分别误用了 a0.json 与 R190 PROTOCOL_A0 的哈希）。**在任何 v2 推断/预测运行之前**更正为实测值：`q2.json = 94C5CD9B2C2FCACABCB7780A1F5CAAEBCCE81D23B926437682BE4F60D9793DE2`，`PROTOCOL_R197.md = 36EF187318A44DBA7560F32B9C171D841E7B7B282920201864ED240FD5E76AD4`（本文件 SHA 由 r197_v2.json 运行时记录）。该更正不涉及数据/结果/门槛/δ_min/判定。\n- §3.2 的键级重采样对象：实测 **Q 实际使用的键是 4,686 个**（9,154 匹配键的子集；其余匹配键不出现在任何 Q 条目中）。V5 对 4,686 个使用键重采样；每观测权重=其 4 个键 multiplicity 之积。此为运行前事实更正，不改变方法/门槛。