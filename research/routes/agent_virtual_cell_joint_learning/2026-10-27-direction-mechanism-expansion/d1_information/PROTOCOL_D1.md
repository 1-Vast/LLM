# PROTOCOL_D1 —— R200-D1：独立信息上的条件规律（信息分解 + 目标资格 + 预注册评价设计草案）

2026-10-27。**在任何 `d1.py` 审计计算之前冻结。** 依据：[R200 BRIEF](../2026-10-27-innovation-round-r200/BRIEF.md)、[方向总报告](../2026-10-27-direction-mechanism-expansion/report.md)、[mechanisms_v3 M1](../2026-10-27-direction-mechanism-expansion/mechanisms_v3.md)、R197v2（`../2026-10-27-q-structure/report_r197_v2.md` 及其协议/挑战）、conditional-shift（`PROTOCOL_A0/A3`、`ERRATA_A3`、`q2.json`）、R196v2（`../2026-10-27-c130-audit/record_r196_v2.md`）、独立重审（`../2026-10-27-independent-reassessment/`）。
角色：独立审计/设计员（未参与 R197 模型开发）。**本轮只做构造/支撑/代数审计与资格判定，不运行效果模型、不拟合预测、不做效应统计。** 冻结后不再修改；实现偏离在 `record_d1.md` 披露。

## 0. 边界与不作的主张

- **不**声称新颖性、机制、迁移已成立、决策收益、算法独特性；**不**称 R197v2 的 0.7206 为已认证结论。
- **不**重跑/复活 R193-A1、R195-A3、旧 I-CD1；**不**用同一资源换聚合/换端点重编码充当"独立目标"。
- **不**改其它目录、INDEX/SYNTHESIS/git；只写 `research/2026-10-27-direction-mechanism-expansion/d1_information/` 与 `tmp/`。
- Q 的数值只用于**精确代数恒等式核验**（容差 1e-9）与"闭包重建误差"核验；不用于任何相关/预测/效应统计。元数据来自身份/设计列与既有冻结产物（SHA 见 §2）。

## 1. 研究问题与待检验对象（写死）

**问题**：R197v2 的 H197c 随机 Q 条目补全（B2 OOF Spearman 0.7206 vs B0 0.2073）中，有多少来自
①**派生对比的代数闭包**（同一原始证据的线性组合）、②**共享原始响应**（同 barcode/plate/键复用）、③**身份/批次/端点来源**，以及④去除这些之后**还剩多少独立信息**（条目数与按细胞/伙伴/条件的覆盖）；并回答**本地是否存在可迁移的独立操作性目标**来检验"闭包外结构"。

**待检验对象（不是结论）**：R197v2 0.7206 是**未认证描述性**（C179：B-D3 可辨识性 FAIL 含口径缺陷、B-D5 MDE80=0.0942>δ_min、非盲风险未登记）；只能作为 D1 的待检验对象，**不得**写成"信号已证明可迁移/结构成立"。

## 2. 输入（只读；SHA256 冻结）

| # | 输入 | 用途 |
|---|---|---|
| I1 | `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`（SHA256 `1188968C…`） | 原始证据/键/barcode；R197 Q 重建 |
| I2 | `research/2026-10-27-conditional-shift/matched_conditions.csv`（`73FD5085…`） | A0 匹配宇宙（96 细胞 / 291 条件 / 9,154 键） |
| I3 | `research/2026-10-27-q-structure/r197.py`（v1 冻结实现，SHA 见 `r197_v2.json`） | 只读复用 `build_q()` 重建 Q 结构（`sys.dont_write_bytecode=True`） |
| I4 | `research/2026-10-27-q-structure/r197_v2.json`（`B0DBE798…`） | A0 方差份额点估计、H197c 结果数字（只读引用） |
| I5 | `data/external/gdsc_combinations/jaaks2022_figshare/Validation screen_All tissues_fitted data.csv`（`DCBD4C31…`） | 独立 screen 候选目标（身份/设计列；响应列不用于本轮审计） |
| I6 | `research/2026-10-27-conditional-shift/a0.json`（`72BBAF6D…`） | 匹配资格、覆盖率、barcode 独立性事实（只读引用） |
| I7 | 其它候选资源目录（PRISM/BeatAML/GCP2020/DrugComb/空目录等） | 目标资格存在性/列名/规模核查（metadata-only） |
| I8 | `research/2026-10-27-q-structure/PROTOCOL_R197.md`、`AMENDMENT_R197*.md`、`challenge_R197_v2.md` | 切分/设计口径引用 |

## 3. 派生链与基本单位（冻结定义）

- **原始证据单位**：Original fitted 表一行 = 一次 `(BARCODE, cell_line, anchor_id, library_id, anchor_conc, library_conc)` 的测量（端点 `SYNERGY_DELTA_EMAX`）；`BARCODE` = 板（run）标识（每板单一细胞系、约 100 个条件组合）。
- **有效行规则**（与 A0/r197 一致）：非 composite-pipe、cell/anchor/library/浓度可解析、BARCODE 有限、端点有限。
- **聚合键 key** = `(cell_norm, condition)`，`condition = (anchor_id, library_id, anchor_conc, library_conc)`；`z_key`（观测引擎值）= 先板内均值、再跨板均值的两级均值（与 r197 `build_q()` 完全一致；本轮不重算 `z` 的数值用于统计）。
- **条件对（Q 行）** = 匹配宇宙内、同一 `(anchor_id, anchor_conc, library_conc)` 下按 `library_id` 升序的两两组对 `(p,q)`；要求同一细胞对共享 ≥2 个条件且该细胞对的组对数 ≥5（与 r197 一致）。
- **细胞对（Q 列）** = 96 个细胞的无序对（canonical 顺序）。
- **Q 条目** = `Q[i,j] = (z[ca,p] − z[ca,q]) − (z[cb,p] − z[cb,q])`（4 个聚合键的双差；**这是唯一的派生公式**）。观测数 `n_obs=92,039`，行 229，列 1,501（与 r197 结构断言一致，否则 `design_invalid` 停）。
- **H197c 折**（复现 R197v2 冻结分配）：`order = lexsort((cj, ci))`；`rng=default_rng(20261106)`；`assign[order]=permutation(n_obs)%5`；折 f 测试 = assign==f。

## 4. 审计指标（冻结定义与容差）

### A. 代数闭包（①）
- **A1 系数矩阵** `A ∈ {0,±1}^{n_obs × K}`，`K` = Q 实际使用的键数（预期 4,686）；每行 4 个非零（+1,−1,−1,+1）。
- **A2 独立信息上界**：`rank(A)` 数值秩（对 `G=AᵀA` 做 `eigvalsh`，`tol_rank = 1e-9·λ_max`）；同时报告 **加性核维数** `C_used + D_used − comp`（C/D = 用到的细胞/条件数，comp = 键二部图连通分量数）。报告 `redundancy = n_obs − rank`、`closure_fraction = redundancy/n_obs`。
- **A3 构造性同上下文重建**：
  - **行内**（同一条件对、细胞图）：对每行 i，细胞图边 = 观测细胞对；生成森林秩 `rank_i = V_i − comp_i`；可精确重建条目 = 三角形边 = `E_i − rank_i`（`Q(a,b)=Q(a,c)+Q(c,b)`，带符号）；
  - **列内**（同一细胞对、条件图）：同上（`Q(p,r)=Q(p,q)+Q(q,r)`）；
  - 报告行/列可重建条目数与比例、二者**并集**（去重）比例；用 Q 值对确定性抽样的重建条目做恒等式核验（`|recon−Q| ≤ 1e-9`，全部应通过）。
- **A4 H197c 冻结折的闭包重建率**：对每折，测试条目 t 可被训练条目精确重建 ⟺ `A_t ∈ rowspace(A_train)` ⟺ `‖A_t V_null(A_train)‖ / ‖A_t‖ ≤ 1e-7`（`V_null` = `G_train` 的近零特征向量，`tol=1e-9·λ_max`）。报告每折可重建条目数/比例、训练未用键数。并在 fold0 上做**精确闭包重建**：`z = Σ_{λ>tol} u (u·b)/λ`（`b=AᵀQ_tr`），`Q_pred_te = A_te z`，报告 `max|err|` 与 `|err|≤1e-9` 比例（代数核验，非效果模型）。

### B. 共享原始响应（②）
- **B1 条目原始支撑**：每条目 4 个键的原始行数之和、板数（union）、键数（固定 4）；分布（min/median/max）。
- **B2 键/板复用**：`m_k` = 使用键 k 的 Q 条目数（Σm_k = 4·n_obs）；每块板（BARCODE）进入的条目数 = 该板键的 `Σm_k`；报告分布。
- **B3 条目对重叠（精确）**：用键子集/板子集计数的**容斥恒等式** `#pairs sharing ≥1 = Σ_{T≠∅}(−1)^{|T|+1} C(c_T,2)`（`c_T` = 包含 T 全部键/板的条目数，T 大小 1–4；条目每行只有 4 键/≤4 板）；报告：期望共享键数（`Σ C(m_k,2)/C(n_obs,2)`）、共享 ≥1 键的条目对比例、**原始不相交（键集合无交）比例**；板级同法（含"4 键是否同板"）。

### C. 身份/批次/端点来源份额（③）
- **C1 构造事实核验**（对全部 229 行）：条目内 anchor_id 相同、anchor_conc 相同、library_conc 相同、library_p≠library_q、ca≠cb、端点列同一（`SYNERGY_DELTA_EMAX`）、screen 同一（Original）→ 报告布尔核验结果与比例。
- **C2 板/批次**：每条目板数分布、4 键同板/部分同板比例、涉及板数；并报告 A0 的 barcode 独立性事实（Original/Validation barcode 集合不相交）与本轮 Original 内部 barcode 结构（每板单细胞系、~100 条件；每键 1 板为主）。
- **C3 方差份额（只读引用 A0，不重算）**：`σ²_cond/σ²_total = 1.43%`（加性条件主效应）、`σ²_cellpair/σ²_total = 3.94%`（加性细胞对）、残差 94.63%；明确"这是 Q 方差的可解释份额，不是预测信号份额"；**不得**写成"1.43% 即可迁移规律总量"。
- **C4 端点来源**：100% 条目来自同一拟合端点列；披露其上游由单药 `LIBRARY_EMAX` 等构造（与 R197v2 B1/BMono 特征块构造重叠，R197v2 §5 已披露）→ 端点不存在第二个独立来源。

### D. 剩余"独立信息"（④）
- **D1 独立数**：`rank(A)`（上限、见 A2）；独立派生数 = rank；冗余数 = n_obs − rank。
- **D2 覆盖**：使用键/条目覆盖的细胞、条件、anchor、library、有向对、组织；按细胞/伙伴(anchor→library 方向)/条件的分层可重建比例（行内/列内/并集）；完全可重建的行/列数；**去除闭包后仍有信息的条目**（非重建）数量及其细胞/条件/伙伴覆盖。
- **D3 基条目数**：以 rank 为独立条目数上界；明确"未构造显式基"，不把 rank 当可解释条目清单。

## 5. 可迁移目标资格（冻结判据；逐项 qualified / qualified_with_conditions / not_qualified）

**A0 复用门槛（最小结构充分性）**：≥2 个独立组（原始证据不共享板/孔）∧ 共享细胞 ≥10 ∧ 有向条件对 ≥10 ∧ 匹配四元组 ≥500（A0 Q1–Q5 冻结阈值；不重设门槛）。
**独立性判据**：目标必须是**不同测量 / 不同培养 / 不同筛选**的 Δ 或功能读数，且**原始证据与 R197 Original 的 barcode/板/孔集合不相交**；**同一资源换聚合、换端点重编码、换 barcode 分半一律 not_qualified（same_resource_reencoding）**。
**操作性判据**：目标端点/派生量有冻结定义与聚合规则；可在预注册 split 上留出评估。
**失败类别**（冻结词汇）：`data_unavailable` / `same_resource_reencoding` / `no_operational_target` / `data_insufficient` / `design_invalid`。
候选清单（至少包含）：Jaaks Validation fitted screen；DrugComb v1.4/v1.5；PRISM 19Q4 单药；BeatAML2 单药；GCP2020；NCI-ALMANAC / O'Neil / VIS2024 / Nyman2020 / Hill2017 / JUMP-CP / BATCHIE（本地是否存在）；GDSC2 fitted；Original 同资源其它端点/barcode 分半；表达类扰动资源（Mix-seq/LINCS/SciPlex）；R193-A0 的 Validation 匹配四元组（作为上表的一项）。
**总体规则**：若 ≥1 个目标 qualified/qualified_with_conditions → D1 可进入"预注册评价设计"（§6）+ 提交独立挑战；若仅剩 same-resource → `data_unavailable` 停（记录所需测量规格）。

## 6. 预注册评价设计草案（只写设计，不执行）

- **主对比**：在**独立目标**上，`closure-excluded 结构模型`（只用源侧信息预测目标的**非闭包成分**）相对最强基线的增量。
- **基线（等信息系统/等预算）**：① 常数/均值；② 加性（行+列）模型；③ 充分调参树（DrEval 2026 标准：内层 CV 选预算，同搜索预算）；④ 矩阵补全/低秩（只用目标矩阵，训练内选秩）；⑤ GP/核方法（同元数据特征）；⑥ **精确闭包重建**（在派生条目目标上有定义；对"新键"目标其贡献按定义为 0，必须显式报告）；⑦ 直接响应预测（先预测原始键值再派生）。
- **目标分层（写死）**：T0 = 派生随机条目（H197c；闭包主导，量化 A4）；T1 = 同 screen 未测键（闭包不可能；结构插值）；T2 = 独立 screen 的同键重测（跨 screen 复验）；T3 = 独立 screen 的新键（跨 screen + 冷键）；T4 = 不同测量/培养（本地不存在则标注 `data_unavailable`）。主推断目标 = **T3（若有）→ T2 → T1**（按独立性优先，先资格后设计）。
- **切分**：留出按**细胞 / 伙伴 / 条件 / 键**分组（不按派生条目随机），并**预注册验证**：留出目标条目在训练中不可被闭包精确重建（A4 检查通过率 ≤5% 才可作为主目标；否则标 `design_invalid` 或换结构切分）。
- **信息/预算对等**：两臂使用相同源数据、相同特征块、相同调参预算（同 #config、同 CV 折、同计算时间上限）；报告计费对照。
- **指标**：主指标 = 目标条目 Spearman（键级；派生条目另报）；副指标 = R²、top-q 命中（描述性）；闭包/非闭包分层报告。
- **δ_min 与 MDE**：`δ_min = 0.05`（operational：ρ=0.05 ⇔ Kendall τ≈0.0318 ⇔ 随机对正确排序概率提高约 1.59 pp——近似换算，是"最小可靠秩信息量"，非决策效用阈值）；`MDE80 = 2.802 × SD_cluster_bootstrap(Δ)`；**设计门：MDE80 ≤ δ_min**，否则 `design_invalid` 停。
- **CI**：按目标侧的独立单元聚类（细胞/培养/板/键簇），并报双向/键级敏感性；不以派生条目数当独立 n。
- **零模型**：① 目标值在目标矩阵内置换（保 mask）；② 源-目标细胞/药物映射随机置换；③ 同维随机特征（容量对照）；④ 负对照：同资源换端点（量化真实泄漏，但不作目标）。
- **失败类别与停止条件**（冻结）：`data_unavailable`（无合格独立目标）→ 停 + 写测量规格；`design_invalid`（MDE>δ_min、闭包重建率>5%、覆盖/不可辨识）→ 停；`evaluation_cannot_distinguish`（目标/对照在结构上不可区分）；`no_increment`（主模型 ≤ 最强基线）；若增益只出现在闭包可重建条目 → 停"迁移"主张、保留评价成果。**不**因结果换端点/切分/δ/预算。
- **独立挑战**：设计草案须先经独立挑战（task 流程）通过后才可执行；本轮不执行。

## 7. 必须随结果一起读的校正

1. **R197v2 0.7206** = 未认证描述性（C179）；其 H197c 设计体检 FAIL（B-D3 可辨识性、B-D5 MDE80>δ_min）→ `inconclusive`；**不是**"低秩/条件结构成立"，也不是"结构不存在"。D1 **只把它当待检验对象**。
2. **R196v2** = `inconclusive`（drug 单位 MDE80=0.0857>δ_min、E9 超时）；**不**作为本方向正面证据。
3. **A3/C173**：DrugComb 条件级跨 screen 冻结设计 `not_qualified`；ERRATA_A3 只允许"更窄问题另定可测对比"，**不得**把 A3 的 `not_qualified` 当"结构不存在"，也不得用新切分伪造未暴露确认。
4. **A0**：Original/Validation `matching_qualified`（96 细胞/291 条件/130 共同有向对/6,223,367 匹配四元组/barcode 集合不相交；screen 与 batch 混淆不可分离）。
5. **方向报告与机制**：M1 是待证伪候选；线性可估性/GLS/GP/矩阵补全已是既有原则，**不**声称新数学。

## 8. 产物、确定性与边界

- 产物（`d1_information/`）：`PROTOCOL_D1.md`（本文件，先冻结）、`d1.py`（metadata/代数审计；不拟合预测）、`d1.json`、`report_d1.md`、`record_d1.md`、`usage_d1.json`。
- 确定性：固定种子/顺序；JSON 键排序、无时间戳、`allow_nan=False`；输入/脚本/协议 SHA256 写入 `d1.json`；连续两次运行 `d1.json` 逐字节一致；单命令 ≤20 min（超时记 `design_invalid` 并停，不缩审计范围）。
- 只写本目录与 `tmp/`；不用新下载；不读 Validation/其它资源的响应值做统计（Validation 只核身份/设计规模与 barcode 独立性，响应列不读）；不晋升代码。

## 9. 明确不做

不训练/不拟合任何预测模型；不做相关/效应/迁移统计；不判 R197 结果成立/不成立；不声称新颖性/机制/决策收益；不改门槛或事后选指标；不重开已停止路线；不把"没找到"写"不存在"（本地空缺记录为 `data_unavailable` 与所需规格）。
