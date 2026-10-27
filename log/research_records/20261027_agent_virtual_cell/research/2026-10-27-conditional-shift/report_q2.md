# R194-A2 报告：Q 的条件级结构可估性（方差分解 + 可靠性 + 设计检查）

2026-10-27。角色：独立设计/执行 runner。按已冻结的 [PROTOCOL_Q2.md](PROTOCOL_Q2.md)（v1 **FROZEN**，SHA256 `0F8D1946…286CE`）执行 R194-A2。**这是与 A1 不同的信息对象问题，不是 A1 的复活/换聚合**：A1 问"Q 能否跨 screen 复验"（cell-pair 级，判 `inconclusive`，C171）；A2 问"**Q 是否存在可估的 condition-pair 级结构，而非被 cell-pair 交互/测量噪声淹没**"（condition-pair × cell-pair 交叉随机效应）。A0 引用一律同时引用 [ERRATA_A0.md](ERRATA_A0.md) 与 [challenge_A0.md](challenge_A0.md)。

- 脚本：[q2.py](q2.py)；结果：[q2.json](q2.json)＋逐 condition-pair 表：[q2_rows.csv](q2_rows.csv)
- 输入（只读，SHA256 全部断言通过）：Jaaks Original/Validation fitted、A0 `matched_conditions.csv`/`a0.json`、PROTOCOL_A0、PROTOCOL_Q、q1.json、ERRATA、challenge、R194 BRIEF
- 确定性：固定种子、JSON 键排序、无时间戳；连续两次运行 `q2.json` **逐字节相同**（见 §11）；单次运行 **≈195 s**

## 0. 判定（一屏）

**设计检查 15/15 全部通过**（D1–D4），随后主估计按冻结规则判定：**`condition_structure_present`**（H194a 全部成立）；但 **H194b 判定为"可忽略份额"**——**σ²_cond 只占 Q 总方差的 1.43%**，Q 的绝大部分是 **condition-pair × cell-pair 交互（48.5%）+ 测量噪声（46.1%）**（cell-pair 主效应 3.94%）。

> 一句话：**条件级结构在统计上可估（显著 >0、p=0.001、条件级可靠性 0.868），但实质份额可忽略（1.4%）**；Q 主要被细胞特异的 condition×cell 交互与 barcode 测量噪声支配 → **后续反馈/迁移/Agent 研究不应以"条件级共享规律"为前提**（R194 BRIEF H194b 语义）。

| 项 | 值 | 说明 |
|---|---|---|
| 设计检查 | **15/15 PASS** | 结构/噪声/可辨识性/功效全部过 |
| 效应检定力（模拟） | power(s=0.4)=**1.00**，power(s=0.2)=1.00，type-I=**0.00** | 冻结的备择/零模型 |
| σ²_cond（主） | **0.000371**，95% CI **[0.000297, 0.000674]**，置换 p=**0.001** | 条件级方差分量 |
| σ²_cellpair | 0.001023（95% CI [0.001068, 0.002174]），置换 p=0.001 | cell-pair 主效应 |
| 交互 / 噪声 | σ²_int=**0.012582**（48.5%）/ σ²_noise=**0.011968**（46.1%） | Q 的主导来源 |
| 份额 | cond **1.43%** / cellpair 3.94% / interaction 48.5% / noise 46.1% | H194b：cond 可忽略 |
| 条件级 Q 可靠性 | **0.868**（median n_i=435；IQR 0.841–0.882；阈值 0.50） | H194a 通过 |
| Validation 探索性 | 条件级 Spearman **0.177**（CI [0.055,0.296]），σ²_cond^B=0.000186（0.98%） | 仅探索，不参与判定 |

**边界**：A2 不是 A1 的通过/不通过；不做跨 screen 复验；不启动 B/C/acquisition；不换端点/分层/δ；不按 Q 大小挑层。条件偏移 ≠ 机制。

## 1. 数据、单元与结构（冻结口径）

- 主分层 **controlled_anchor**（同 anchor、同 ANCHOR_CONC、同 LIBRARY_CONC，仅 library 不同）；端点 `SYNERGY_DELTA_EMAX`；barcode 均值聚合；条件为有向 (ANCHOR_ID→LIBRARY_ID, ANCHOR_CONC, LIBRARY_CONC)；condition-pair 按 library_id 升序定向。
- **观测单元 = (condition-pair, cell-pair) 唯一格**，**92,039** 个：**229 个 condition-pair × 1,501 个 cell-pair**（96 细胞、291 条件、9,154 匹配键、129 条件级有向药对；与 A0/ERRATA 一致）。
- 每 condition-pair 的 cell-pair 数：**78–595**（中位 **435**，均值 401.9）；每 cell-pair 的 condition-pair 数：6–134（中位 58）；格密度 0.268；二部图 3 个连通分量（condition-pair sizes 134/58/37）；`unique(i,j)=92,039/92,039`（无重复格）。
- 边界：缺失格=缺失（不插补、不按 Q 选层）；Q 双差使 cell/condition 加性主效应精确消去；不剔除极端 Q（影响由 bootstrap/置换报告）。

## 2. 设计检查 D1–D4（先于 H194a 判定）

- **D1 结构（7/7 PASS）**：N=92,039 ≥10,000；cell-pair 1,501 ≥200；condition-pair 229 ≥50；每 cond-pair ≥10 cp（实测 min 78）；每 cp ≥5 cond-pair（min 6）；unique cells ✓；连通分量 3 ≤5。
- **D2 噪声标定（4/4 PASS）**：barcode 分半标定四元组 **1,312**（≥300；占观测 1.43%）→ `σ²_single = 0.003351`（单 barcode 单药读数误差方差）；**分半稳定性**：按 cell-pair 奇偶 ratio **1.027**、按 condition-pair 奇偶 ratio **0.797**（均在冻结区间 [0.5,2]）；每观测平均噪声方差 **0.011968**。
- **D3 可辨识性（2/2 PASS）**：点估计有限；pilot 双向 bootstrap（B=200）SE 有限比例 100% ≥95%。
- **D4 功效/type-I（2/2 PASS）**：在观测格型上模拟（σ²_total=1，ρ_cellpair=0.4）：**power(s=0.4)=1.00 ≥0.80**、power(s=0.2)=1.00、**type-I(s=0)=0.00 ≤0.10**；备择分割敏感性 ρ_cellpair∈{0.2,0.6} 的 power 均 1.00。
- 噪声标定的限制（已披露）：只有 **1.43%** 的观测四键都有 ≥2 barcode；校准样本集中于 barcode-rich 的细胞（barcode 分布见 `q2.json → design_check.noise`），其**平稳性假设**是 D2 的检查项（两个分半比值均通过，但这是本设计最大测量体制不确定性）。

## 3. 主估计：方差分量与份额

模型（冻结）：`Q_ij = μ + a_i(condition-pair) + b_j(cell-pair) + c_ij(交互) + ε_ij(噪声)`；矩估计用同 condition-pair / 同 cell-pair 观测对的协方差（PROTOCOL_Q2 §2）；噪声由 barcode 分半标定；`σ²_int = max(0, σ²_resid − σ²_noise)`。

| 分量 | 估计 | 份额 | 对应 SD（ΔEMAX viability 分数尺度） |
|---|---|---|---|
| **σ²_cond（condition-pair）** | **0.000371** | **1.43%** | 0.019 |
| σ²_cellpair | 0.001023 | 3.94% | 0.032 |
| σ²_int（condition×cell 交互） | 0.012582 | **48.5%** | 0.112 |
| σ²_noise（barcode 测量噪声） | 0.011968 | **46.1%** | 0.109 |
| σ²_total | 0.025944 | — | 0.161 |

- 无负分量（σ²_cond、σ²_cellpair、σ²_int 原始值均为正；无需截断）。
- 读法：**Q 的变异几乎全部来自"同一 condition-pair 在不同 cell-pair 上的差异（交互）"与测量噪声**；条件级共享成分只有 1.4%（SD ≈ 1.9% viability 点）。
- **H194b**：`share_cond = 1.43% < 10%` → **"条件级份额可忽略，条件结构主要是细胞特异的"**；后续反馈/迁移/Agent 研究不应以"条件级共享规律"为前提。

## 4. 条件级 Q 与可靠性（公式冻结）

- 条件级 Q：`Q̄_i = mean over cell-pairs`（229 个 condition-pair，每个 78–595 cp）。
- 主可靠性：`rel_i = σ²_cond / (σ²_cond + (σ²_int + σ²_noise)/n_i)`；**headline（median n_i=435）= 0.868**（IQR 0.841–0.882），阈值 0.50 → **H194a 通过**。
- 敏感性（不替换主定义）：noise-only 口径 0.931；含 cell-pair 抽样口径 0.863。
- **重要读法（先冻结的语义）**：可靠性高是"n_i≈435 个 cp 平均后条件级均值稳定"的结果，**不等于**条件级成分占 Q 方差的比例大；后者是 1.43%（H194b）。两个数字回答不同问题，不可互替。

## 5. 推断：双向聚类 bootstrap 与置换零分布

- **双向 cluster bootstrap**（重采样 229 condition-pair × 1,501 cell-pair，B=1,000，seed 20261028）：σ²_cond 的 SE=9.6e-5，95% CI **[0.000297, 0.000674]**（下界 >0）；σ²_cellpair CI [0.001068, 0.002174]。
- **置换零分布（condition-pair 标签打乱，保持 cell-pair 结构，B=1,000，seed 20261029）**：null mean 0、sd 6e-6、**95 分位 1.0e-5**；观测 σ²_cond=3.71e-4 ≫ q95 → **p=0.001**（最小可分辨）。
- **置换零分布（cell-pair 标签打乱，B=1,000，seed 20261030）**：q95(σ²_cellpair)=2.3e-5，观测 1.02e-3 → p=0.001。
- **H194a 四项**：σ²_cond>0 ✓；CI 下界>0 ✓；高于置换 95 分位 ✓；rel(median n_i)≥0.50 ✓ → `condition_structure_present`。

## 6. 判定与措辞边界

- **判定：`condition_structure_present`**（按 PROTOCOL_Q2 §6 冻结规则）；同时 **H194b：份额可忽略（1.43%）**。
- 措辞边界（写死）：
  - "present" = **存在可估的、统计上非零的 condition-pair 方差分量**；**不等于**"条件级结构是 Q 的主要来源"（后者被 1.43% 否认），也**不是** A1 的通过/不通过，**不是**跨 screen 复验。
  - 后续反馈/迁移/Agent 研究**不应**以"条件级共享规律"为前提（BRIEF H194b）；若未来要主张条件级规律，需先有更大的独立资源与更强标定。
- 分支（BRIEF，写死）：present → 下一轮**只在更大独立资源上**做条件级跨 screen 复验的资格审计（**不是**用同一 96 细胞换聚合）；不启动 B/C/Agent；不晋升代码。

## 7. 探索性 Validation 交叉检查（不参与主判定）

- 用 Validation 的同 92,039 个匹配四元组计算条件级均值 `Q̄_i^B`，与 Original 的 `Q̄_i^A` 在 229 个 condition-pair 上相关：**Spearman = 0.177**（按 condition-pair bootstrap 95% CI **[0.055, 0.296]**）。
- Validation 的 σ²_cond^B = **0.000186**（share 0.98%），与 Original 同向、同量级（略小）。
- 措辞：**仅探索性样本外条件级一致性，不进入 H194a/H194b 判定，不构成跨 screen 复验**（跨 screen 复验是 A1 的问题，已判 inconclusive）。

## 8. 与 A1 的关系（明确声明）

- A1 判定 `inconclusive`（C171）**不变**：96 细胞 → n_eff≈189，MDE80_obs=0.2042 > δ_min_obs=0.0893；**A2 不是 A1 的复活**、不用同一 96 细胞换聚合、不做跨 screen 复验。
- A2 换的是**信息对象**：从"cell-pair 级跨 screen 相关"换成"condition-pair 级方差分量是否可估/多大"。两者结论可以并存：**条件级结构统计上可估但份额可忽略（1.4%）；Q 主要被 cell×condition 交互与噪声淹没**。这同时说明：即使 A1 的设计有足够 power，其"可复验的 Q"也很可能主要是 cell-pair 交互与噪声，而不是条件级共享规律。

## 9. 敏感性、不确定性与限制

1. **噪声标定覆盖薄**：只有 1,312 个四元组（1.43%）四键都有 ≥2 barcode；校准样本集中于 barcode-rich 细胞；分半稳定性通过（ratio 1.03 / 0.80）但**平稳性假设**是本设计最大测量体制不确定性。若 σ²_noise 被低估，σ²_int 会被高估；因 σ²_int 与 σ²_noise 各约 46–48%，该误差不改变"cond 份额小"的结论（σ²_cond 的估计不依赖噪声标定：矩估计只依赖 Q 值）。
2. **矩估计假设**：交叉随机效应、加性可分解、无 a×b 结构之外的效应；估计对极端 Q 与不平衡（n_i 78–595、m_j 6–134）稳健性由 bootstrap 覆盖（CI 不含 0 且远离 0）。
3. **交互/噪声分离**依赖 σ²_noise 外推（每观测 4 键的 1/b 权重）；已在 note 中写明。
4. **可靠性高的语义**：rel 高主要来自 n_i≈435 的平均效应，不代表条件级成分占比大（1.43%）；两个口径都已报告，不互相替换。
5. 二部图 3 个连通分量：分量内成熟、分量间只由 grand mean 连接（跨分量条件对共享更少 cell-pair），分量结构已报告；估计按全数据 pooled，未按分量分层（冻结口径）。
6. 未做（明确不做）：跨 screen 复验、δ/端点/分层改动、B/C/Agent、按 Q 大小挑层、用 Q 结果反推模型选择。

## 10. 实现选择（冻结前写入 PROTOCOL_Q2，非事后）

- condition-pair 定向：library_id 升序（Q 符号一致）；
- 矩估计：同层观测对协方差（`Σ_{j<j'}(Q−μ)(Q−μ)/Σ C(n,2)`，`½[(Σx)²−Σx²]` 实现）；
- 噪声：`σ²_single = Σdiff²/Σ[Σ_k(1/b_h1+1/b_h2)]`（四键都 ≥2 barcode 的四元组），每观测噪声 = `σ²_single·Σ_k 1/b_k`；
- 可靠性主定义：`σ²_cond/(σ²_cond+(σ²_int+σ²_noise)/n_i)`，headline 在 median n_i；
- 检验：双向 bootstrap CI + 置换 95 分位；power 模拟的备择分割 ρ_cellpair=0.4（敏感性 0.2/0.6）；
- 全部写在 [PROTOCOL_Q2.md](PROTOCOL_Q2.md)，跑前冻结；未改门槛/统计量/分层/判定。

## 11. 复现

```powershell
cd D:\MAESTRO
$env:PYTHONHASHSEED="0"
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-conditional-shift\q2.py
```

- 实测 **199–201 s**（含 800 次功效模拟 × 100 bootstrap）；最终两轮运行 `q2.json` 与 `q2_rows.csv` 逐字节相同（SHA256 见 [usage_q2.json](usage_q2.json)）。
- 输入/协议/脚本 SHA256 全在 `q2.json → inputs / protocol / script`；A0 引用同时包含 PROTOCOL_A0、ERRATA_A0、challenge_A0（`q2.json → a0_citation`）。

## 12. 边界

- 条件偏移 ≠ 机制；condition 级结构 ≠ 可迁移；本分析只描述"在 matched 子集、该端点、该标定精度上 condition 级方差是否可估/多大"。
- 不把 A2 写成 A1 通过；不启动反馈/Agent/元学习/RSI；不做机制/临床主张；阴性/不可估同样完整记录（本轮为 present-but-negligible）。
