# PROTOCOL_Q（R193 分析 A：条件偏移可复验性）——v1 **FROZEN**（2026-10-27，任何 Q/效应读取之前）

> 依据：R193 BRIEF、A0（`matching_qualified`）＋ [ERRATA_A0.md](ERRATA_A0.md)、独立挑战 [challenge_A0.md](challenge_A0.md)（verdict revise；≤5 必改）。**本文件取代 PROTOCOL_Q_DRAFT**；冻结后不改，偏离写 AMENDMENT 并在报告中披露。**本轮仍未读 Q/效应**；A1 由独立 runner 执行。

## 0. 问题、假设与谱系声明

- **H193a（主）**：在匹配四元组上，测量组 A（Original）的条件偏移 `Q=(y[c,p]−y[c,q])−(y[c',p]−y[c',q])` 能预测组 B（Validation）的同一 Q（同一四元组、同一端点 `SYNERGY_DELTA_EMAX`）。
- **H193b（必做主解释）**：Q 的可复验部分不能由 **cell×单药 / 剂量设计** 解释（单药列存在且空值 0，必须使用；见 §5）。
- **谱系声明（写死）**：本分析**不是**旧"两个固定交互族选一个"的有限交互筛选（`eight_directions_20261026`），**不是** R5 反序路线的重启，**不**用 Q 结果反推交互族/算子选择，**不**启动 acquisition/Agent/B/C。Q 复验即使成立也只支持"跨 screen 条件稳定性"的描述性结论，不是机制/迁移/新算法（BATCHIE 类细胞嵌入×药物交互已是直接强先例）。
- 限制：只能主张**跨 screen 条件稳定性**（screen 与批次完全混淆）；剂量等价只到已发布设计列；结论限定在 matched 子集与该 Validation 子集。

## 1. 数据与主分层（冻结）

- 输入：Jaaks Original/Validation fitted 表（SHA 见 A0 report）；A0 `matched_conditions.csv`（9,154 键）与 R4 匹配四元组全表（6,223,367，可由 `a0.py` 重生成）；更正后口径见 ERRATA。
- 端点：主 `SYNERGY_DELTA_EMAX`；敏感性三个其它 Δ 端点（不择优）。
- 原始重复板聚合：每个 (cell,condition) 键在原/验证 screen 内按 **barcode 均值** 聚合（冻结）；barcode 分半用于可靠性/衰减（§4）。
- **主分层 = `controlled_anchor`**：四元组满足同 anchor_id、同 `ANCHOR_CONC`、同 `LIBRARY_CONC`，仅 library 不同（A0 92,039 个；A1 重算）。次级分层（预注册，不参与主判定）：R4 全量、same_anchor_any_conc、修正后 disjoint_pairs、条件对级、barcode 分半。

## 2. 主统计量（唯一主设计，冻结）

- **P1（主）细胞对级聚合 Q**：对每个细胞对 cp（c≠c'）与每个主分层四元组，分别计算 `Q_A`、`Q_B`；对每个 cp 取该 screen 内主分层四元组的 **median** 得 `Q_A^cp`、`Q_B^cp`（cp 的四元组数 < 5 → 该 cp 不进入主分析；计数报告）。
- **主统计量 = `Spearman(Q_A^cp, Q_B^cp)`**（cp 数记为 n_p）；CI：**按细胞聚类 bootstrap**（重采样 96 个共同细胞，重构 cp 集合，B=1,000，seed 20261027）；MDE80 同法（2.801585×SE）。
- 次统计量（预注册、只报告、不替换主判定）：(i) 条件对级聚合 Spearman；(ii) 四元组级 Spearman + 药对×细胞双向聚类（固定抽样 200k，seed 20261027）；(iii) `same_anchor_any_conc` / 修正 disjoint / R4 全量分层；(iv) 三个非主端点。
- 非有限/平局：Spearman 遇平局按秩平均；常数向量 → 该单元剔除并计数；删失/缺失为 0（fitted 表端点无空值，仍须运行时断言）。

## 3. δ_min、零分布、MDE 与完整规则功效（先于 Q 计算；q1.py 运行时断言）

- **δ_min（latent）= 0.10**：operational 理由=下游使用门槛：条件偏移可复验相关低于 0.10（解释方差 <1%）不足以支持任何"用少量反馈改选未测组合"的后续实验（B 阶段的最小前提）；0.30 以上才值得设计反馈算子。**不得用旧 CI 下界或显著性倒推**。
- **观测尺度门槛**：`δ_min_obs = δ_min_latent × sqrt(rel_A × rel_B)`（衰减；rel 由 §4 估）；主判定用 δ_min_obs。
- **主零分布**：screen 内**细胞标签置换**——固定 Validation 的 (cell,condition) 结构，把 96 个共同细胞标签随机置换（固定种子 20261027），重算 `Q_B^cp` 与主统计量，1,000 次；p/CI 结合 cell-cluster bootstrap。该零分布保持条件结构与 screen 特异性。
- **MDE80 与完整规则功效（必须先于 Q 复验计算；不过 → `inconclusive` 停，不救）**：
  1. 用 §4 的 `rel_A/rel_B` 与 n_p、聚类结构计算 `MDE80_obs`；要求 `MDE80_obs ≤ δ_min_obs`；
  2. 模拟完整判定规则（点≥δ_min_obs ∧ CI 下界>0 ∧ 优于置换零分布 95 分位）在 latent ρ∈{0.10, 0.30} 下的 joint power（生成衰减后的观测相关 + 置换零分布 / cell-cluster bootstrap 近似，2,000 次，固定种子）；要求 **Power(latent=0.30) ≥0.80**（latent 0.10 只报告）；
  3. 完整规则 type-I：在置换零数据上模拟拒绝率，要求 ≤0.10（目标 0.05，二项噪声内）。
- 以上数字写入 `q1.json` 的 `design_check`，`q1.py` 在主 Q 计算前断言；未过 → 输出 `inconclusive` 并停止。

## 4. 可靠性/衰减与选择偏差（先于主判定）

- **within-screen barcode 分半可靠性**：对每个 screen 内有 ≥2 barcode 的 (cell,condition) 键，按 barcode 排序奇偶分半求 Q（主分层内），在细胞对级聚合后相关 → Spearman-Brown 校正得 `rel_A`、`rel_B`；覆盖率（46 细胞/583 对）作为限制报告。
- **衰减校正**：报告 `ρ_disattenuated = ρ_obs / sqrt(rel_A×rel_B)`（仅次级解释，不作主判定）。
- **选择偏差**：Validation 是已知可能挑过的子集（R31：4.4% 键；F9 组织构成偏移）→ 预注册 (i) matched vs unmatched 的元数据比较（细胞/组织/anchor/library/剂量元组）；(ii) Original 内按 Validation 细胞/条件构成匹配的随机子集对照（固定种子），重算主统计量；(iii) 回归到均值诊断（Q_A 极端分位的 Q_B 回归斜率）。全部写入报告，不改主判定但限定结论范围。

## 5. H193b：单药调整（必做，主解释项）

- 单药列（A0 曾 DENY；A1 解禁并冻结用法）：`ANCHOR_VIABILITY` 与 `LIBRARY_EMAX/XMID/XMID_uM/AUC/fAUC/RMSE`（空值 0，A0/挑战已核验）。
- **冻结特征**：对每个四元组构造 `F = ΔSA(c,p,q) − ΔSA(c',p,q)`，其中 `ΔSA(c,p,q)` = 该细胞在条件 p 与 q 的 **LIBRARY 单药 EMAX 差**（最高 library 浓度；anchor 同浓度时 anchor 项为 0；anchor 浓度不同时用 ANCHOR_VIABILITY 差，作为次特征）。主特征只用 `LIBRARY_EMAX`；其余列作敏感性。
- **交叉拟合调整**：β_A = OLS(`Q_A ~ F_A`，无截距，Original 主分层)；β_B 同法 Validation；`Q_adj^A = Q_A − F_A β_B`、`Q_adj^B = Q_B − F_B β_A`（交叉应用，避免自减）；主调整统计量 = `Spearman(Q_adj^A, Q_adj^B)`（细胞对聚合同 §2），CI 同法。
- 判定解释：若主 H193a 通过但 H193b 调整后 CI 含 0 或点估计 <δ_min_obs → **`single_agent_explained_unresolved`**：不得声称条件结构超出单药/剂量稳定性；若调整后仍过 → 可写"扣除单药线性解释后仍成立（描述性）"。
- 缺失/不可用：任何列不可用 → 记录并**不替换主判定**；不得跳过 H193b（必做）。

## 6. 判定规则（冻结）

- **`reproducible`**：主统计量点估计 ≥ δ_min_obs ∧ cell-cluster CI 下界 >0 ∧ 高于置换零分布 95 分位；且完整规则功效与 type-I 设计检查通过。
- **`not_reproducible`**：CI 含 0 或点估计 ≤0，或未高于零分布。**不得写"无条件结构"**（construct/剂量/power/选择/批次未分离）。
- **`inconclusive`**：design_check 未过（MDE/功效/type-I/可靠性不足）→ 停，不救。
- **分支（冻结）**：not_reproducible → 不做可迁移条件结构主张，接受普通加性/静态先验解释，B/C 不启动；reproducible 且 H193b 调整后仍成立 → 才允许下一轮设计 B（反馈传递）；reproducible 但 H193b 解释 → 给普通单药/剂量稳定性记功，B 不启动。

## 7. 运行时/交付/边界

- `q1.py` 顺序：加载 → 断言输入/A0 表 SHA 与 ERRATA 口径 → 设计体检（§3/§4）→ 若通过 → 计算主/次统计量与 H193b → 输出。**设计体检未过禁止进入 Q 复验计算**。
- 交付（`research/2026-10-27-conditional-shift/`）：`q1.py`、`q1.json`、`q1_rows.csv`、`report_q1.md`、`record_q1.md`、`usage_q1.json`。确定性：固定种子、JSON 键排序、无时间戳、输入/脚本 SHA；测试/验证不参与任何调参。
- 边界：条件偏移≠机制；复验≠可迁移；不晋升代码；阴性同样完整记录。
