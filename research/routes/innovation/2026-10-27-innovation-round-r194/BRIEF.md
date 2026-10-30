# R194 BRIEF（2026-10-27，Lead 起草；下一轮执行）

## 0. 入口状态

- **R193-A1 `inconclusive`**（C171）：跨 screen Q 复验在本资源上**不可检验**——controlled_anchor 92,039 四元组、1,501 细胞对，但只来自 96 个共享细胞；n_eff≈189，MDE80_obs=0.2042 > δ_min_obs=0.0893（rel 0.864/0.741、四元组数均不是瓶颈）。按协议停在主 Q 之前；**不是阴性**，0.10–0.30 latent 区间不可靠分类。
- A1 解冻条件：更多独立细胞/独立测量组、或不靠旧 CI 反推的更小 δ_min、或**有效独立样本更大的分析单元**；明确**不能只是把同一 96 细胞换聚合**来救 A1。
- R192 的 DrugComb 外部复现同样 `not_replicated` 且功效未校准（C167）；更早的 I003/AL 停止不变。独立重审（C168）的核心提示仍有效：当前最强正结果可能是"药物平均组合倾向"，**细胞×组合条件结构从未被可靠估计过**。

## 1. R194 的唯一问题（与 A1 不同的问题，不是换聚合救 A1）

> **在匹配四元组上，条件偏移 Q 是否存在可估的"条件级"结构（而非完全被细胞×条件交互/测量噪声淹没）？**

- Q 定义与 R193 一致（controlled_anchor 主分层，`SYNERGY_DELTA_EMAX`，barcode 均值聚合、有向条件、无序药对不同）。
- **H194a（主）**：交叉随机效应分解 `Q_{ij} = μ + a_i(condition-pair) + b_j(cell-pair) + e_{ij}` 中，**condition-pair 方差分量 σ²_cond > 0 且条件级 Q 的可靠性（相对 barcode 重复噪声）≥ 预注册阈值**（建议 ≥0.50，先冻结）。
- **H194b（诊断）**：报告 σ²_cond 与 σ²_cellpair 的相对份额；若条件级份额可忽略（如 <10%），则条件结构主要是细胞特异的，**后续反馈/迁移/Agent 研究不应以"条件级共享规律"为前提**。
- **对照/零模型**：打乱 condition-pair 标签（保持 cell-pair 结构）、打乱 cell-pair 标签；barcode 分半噪声估计；条件级 Q 的 half-split 可靠性。
- **明确不做**：不把本分析当作 A1 的"通过"；不做跨 screen 复验（留给更大的独立资源）；不启动 B/C/acquisition；不换 δ_min 或端点；不按 Q 大小挑层。

## 2. 设计（冻结前先做 A2 design-check，不读"效果"结论）

1. **宇宙**：Original screen 为主（barcode 重复提供噪声标定）；Validation 只作**样本外条件级一致性**的探索性交叉检查（不作主判定）。
2. **方差分量估计**：crossed random effects（condition-pair × cell-pair），用矩估计/ANOVA 型估计或 statsmodels MixedLM（冻结实现选择）；Q 的双差结构使 cell/condition 加性主效应精确消去；**必须报告 Q 对称性/重复单元处理与边界**。
3. **噪声标定**：within-screen barcode 分半（有 ≥2 barcode 的键），Q_half1 vs Q_half2，估计 σ²_noise；条件级 Q 的可靠性 = σ²_cond/(σ²_cond + σ²_estimation)，其中 σ²_estimation 由每 condition-pair 的 (cell-pair 数, barcode 数) 与噪声/其他分量推算（公式先冻结）。
4. **功效/MDE（先于 H194a 判定）**：在冻结的零模型与备择（σ_cond/σ_total ∈ {0.2, 0.4}）下模拟；要求对备择 0.4 的检定力 ≥0.80；type-I ≤0.10；不过 → `inconclusive` 停（不救）。
5. **判定**：
   - `condition_structure_present`：σ²_cond 显著 >0 且条件级 Q 可靠性 ≥ 阈值，且高于打乱标签零分布；
   - `condition_structure_absent`：可靠性与分量分析表明条件级结构不可估/可忽略（**这是"条件结构不可估"的证据，不是"不存在"的普遍结论**；措辞按协议写死）；
   - `inconclusive`：design-check 或功效不过。
6. **停止/分支（冻结）**：`condition_structure_absent` → 条件结构线停止（不启动 B/C/Agent；接受"现有资源只能支持静态/平均效应"的边界）；`condition_structure_present` → 下一轮设计"在更大独立资源上做条件级跨 screen 复验"的资格审计（不再用同一 96 细胞）；`inconclusive` → 记录设计边界。

## 3. 代理、预算与交付

- 1 名独立设计/执行 runner（建议复用 endpoint-auditor；先冻结 `PROTOCOL_Q2.md` 再跑 design-check）；1 名独立挑战者审协议（必做，尤其：方差分量可估性、噪声/聚类口径、功效模拟、与 A1 的关系声明、不能当 A1 复活）。
- 数据：`data/external/gdsc_combinations/jaaks2022_figshare/` 的 Original/Validation fitted 表（A0 的 matched_conditions/quadruples 可复用；SHA 已录）；CPU；单次 ≤45 min；不下载新数据。
- 交付：`research/2026-10-27-conditional-shift/` 下 `PROTOCOL_Q2.md`、`q2.py`、`q2.json`、`q2_rows.csv`、`report_q2.md`、`record_q2.md`、`usage_q2.json`；轮次记录与登记。
- 纪律：判定/措辞先冻结；不拿 Q 结果反推模型选择；不晋升代码；阴性/不可估同样完整记录。

## 4. 明确不做

不把 A1 的"conclusive"重写为通过；不把"96 细胞换聚合/换分层"当解冻路径；不启动反馈/Agent/元学习/RSI；不做机制/临床主张。
