# PROTOCOL_Q（R193 分析 A：条件偏移可复验性）——**DRAFT v1，未冻结**

> 状态：草稿。待 R193-A0 独立挑战（`challenge_A0.md`）通过、且 Lead 处理其必改后，本文件写死数字并改 `FROZEN`；冻结前**不得**读取任何 Q/效应。依据：R193 BRIEF、A0 匹配合格（PROTOCOL_A0 / a0.json）。

## 0. 问题与假设

- **H193a（主）**：在**匹配四元组**上，测量组 A（Original）估计的条件偏移 `Q=(y[c,p]−y[c,q])−(y[c',p]−y[c',q])` 能预测测量组 B（Validation）的 Q。
- **H193b（解释，次要但先冻结）**：Q 的剩余结构不能由加性/单药/批次/剂量解释（用 `ANCHOR_VIABILITY`/`LIBRARY_*` 单药读数与四元组内剂量设计对照；必要时 partial）。
- 明确**不**做：机制/临床主张；acquisition/Agent；用大间隔/反序挑四元组；换 δ/换聚合制造收益。

## 1. 数据与单位（来自 A0，冻结）

- 输入：Jaaks Original/Validation fitted 表（SHA 见 A0 report）、A0 的 `matched_conditions.csv`（9,154 个双组可用 (cell,condition) 键）、`matched_quadruples.csv`（审计子集 200,000 行；全量 6,223,367 以 a0.py 重生成）。
- 端点：主 `SYNERGY_DELTA_EMAX`；敏感性：其它三个 Δ 端点（分别预注册，不择优）。
- 单元：**匹配四元组**（c≠c'、条件 p≠q、四键在两测量组均可用、方向/剂量设计元组一致；定义见 PROTOCOL_A0 §5）。
- **独立性警告（A0）**：6.22M 四元组大量共享边，不是独立样本；本协议必须用聚类/聚合口径，禁止把 6.22M 当 n。

## 2. 分析设计（冻结候选，待挑战确认）

1. **四元组级 Q**：对每个 R4 四元组，分别在 Original 与 Validation 估计 `Q_A`、`Q_B`（同一单元、同一端点；原始行���重复板先按 barcode 均值聚合，冻结）。
2. **主统计量**：`Spearman(Q_A, Q_B)` 在**不重叠抽样**或**分层聚合**后的单元上计算。两种候选（预注册选其一，挑战后定）：
   - **P1（主，推荐）细胞对级聚合**：对每个细胞对 cp，令 `Q_cp = median over condition pairs`（或 mean；先冻结），得到 n≈3,418 细胞对；`Spearman(Q_A^cp, Q_B^cp)`；CI 按细胞对聚类（细胞对间仍共享细胞 → 追加按细胞聚类敏感性）；MDE80 用置换/解析并按实际聚类估计。
   - **P2（次）条件对级聚合**：对每个条件对，`Q_cond = mean over cell pairs`，n≈C(291,2)且受匹配限制；同法。
   - **P3（次）四元组级**：全量/固定种子抽样（如 200k），two-way cluster bootstrap（细胞对×条件对）；只作支持性。
3. **零分布/对照（预注册）**：
   - 打乱细胞标签（在 screen 内保持条件结构）→ Q_null_A vs Q_B；期望 0；
   - 打乱条件标签；
   - **符号一致率**（Q_A 与 Q_B 同号比例）作为副指标；
   - **单药/加性对照**：H193b 用 ANCHOR_VIABILITY/LIBRARY_EMAX 等单药读数构造 additive-adjusted Q（用法冻结；若不可用则记录限制，不强行）。
4. **δ_min 与 MDE**：δ_min 由"最小有用条件偏移复验相关"定义（建议 Spearman δ_min=0.10，且在冻结前写明理由；不得用旧 CI 下界倒推）；MDE80 按实际聚类与样本量计算，必须先于效果报告；若 MDE80 > δ_min → `inconclusive`（停，不救）。
5. **批次/剂量**：A0 指出 screen 与批次完全混淆 → 只能主张"跨 screen 条件稳定性"（不是纯 test–retest）；剂量布局仅设计列可比（library 浓度点集未发布）→ 报告中显式限制；`LIBRARY_CONC` 只用最高浓度匹配。
6. **判定（先冻结）**：
   - `reproducible`：主统计量点估计 ≥δ_min 且 CI 下界>0 且优于打乱标签零分布；
   - `not_reproducible`：CI 含 0 或点估计≤0；
   - `inconclusive`：MDE>δ_min 或设计体检失败；
   - 分支：not_reproducible → 不做可迁移条件结构主张，接受普通加性解释（B/C 不启动）；reproducible 且普通层级模型可解释 → 给普通学习记功；有剩余结构 → 再冻结 B（反馈传递）。
7. **设计体检（先于 Q 读值）**：四元组/键/剂量一致性断言；端点存在性；聚合后 n 与聚类数；打乱零分布均值≈0；随机种子固定；A0 表 SHA 校验；任何失败 → `design_invalid`。

## 3. 计算与交付

- CPU；全量枚举 6.2M 四元组内存/时间可行性须在冻结前体检（可用分块/抽样；若全量不可行，冻结固定抽样方案与种子）。
- `research/2026-10-27-conditional-shift/`：`PROTOCOL_Q.md`（冻结版）、`q1.py`、`q1.json`、`q1_rows.csv`、`report_q1.md`、`record_q1.md`、`usage_q1.json`。
- 确定性：固定种子、JSON 键排序、无时间戳、输入/脚本 SHA；测试/验证不参与任何调参。

## 4. 边界

条件偏移不是机制；Q 复验只说明"存在可跨 screen 复现的条件结构"，不说明可迁移到新组合/新细胞；不晋升代码；阴性同样记录。
