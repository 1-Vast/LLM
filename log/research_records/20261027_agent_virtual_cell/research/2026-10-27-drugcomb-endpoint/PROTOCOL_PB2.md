# PROTOCOL_PB2 — R192 前置：**有注释宇宙**下的 MDE80、检定力与阶段 2 可重开性判定

**运行前冻结。** 本文件在 `pb2.py` 第一次运行前写成并固定；`pb2.py` 只按本文件执行，结果与判定不因看到数据调整。本协议是 P-B（[PROTOCOL_PB.md](PROTOCOL_PB.md)）冻结方法在**有注释分析宇宙**上的扩展。

- 角色：端点与测量体制审计员（独立于提案者）。本任务**只做零模型与检定力**：不拟合 identity/annotation 模型，不评估任何臂的效应（含 `通路−identity` 增益），不做机制/临床推断。
- 工作目录：`D:\MAESTRO`；只在 `research/2026-10-27-drugcomb-endpoint/` **新增** `PROTOCOL_PB2.md / pb2.py / pb2.json / report_pb2.md / record_pb2.md / usage_pb2.json`；**不修改 P-B 既有产物**（`PROTOCOL_PB.md / pb.py / pb.json / endpoint_audit.csv / report.md / record.md / usage.json`），不改其它目录、INDEX、SYNTHESIS、git。
- 上位背景：R191-PB 判定 `endpoint_not_usable`，原因**只是检定力**（r=0.20 全体宇宙 two-way MDE80=0.1149 > δ_min=0.03；饱和/聚合/构造可比性均通过）。本任务回答：**在"有注释宇宙"上是否存在预先可辩护的设计（r × 切分口径），使阶段 2 可被正当重开**。

## 1. 冻结输入

| key | 路径 | 用途 |
|---|---|---|
| `mapping_table` | `research/2026-10-27-drugcomb-annotation/mapping_table.csv` | P-A 冻结表；SHA256 `45EDE63521DC44FEFEC52D717765B4D2BA7D08EC3FDE4372811C4D516DE038D4`（`pb2.py` 重新计算并断言） |
| `v14_summary` | `research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv` | 只读 `block_id/drug_row/drug_col/cell_line_name` 与 `synergy_bliss`（主端点，P-B 冻结）+ `conc_*_unit`（结构核对）；SHA256 `E08E3D35…A2F` |
| `pb_protocol`/`pb_json`/`pb_py`/`endpoint_audit.csv` | 本目录 | **只读**方法参照与"未改动"核验；哈希记入 `pb2.json` |
| `pa_json`/`pa_report` | `research/2026-10-27-drugcomb-annotation/` | 只读交叉核对（88,118 / 2,682 / 3,739 / 1,418 / 4,088） |

**主策略（P-A 冻结，不改选）**：`source_library == "S1"`（KEGG 186 集）＋规则 A。本协议只用 `mapping_table.csv` 中 `source_library=="S1"` 的行：
- **已映射药集合** `M := { drug_normalized_name : pathway != "unmapped" }`；期望 **|M| = 1,418**（`drug_drop=="none"`）；若与 P-A 数字不符 → 以实测为准并在 `pb2.json` 记录差异，不作改选。
- 药物宇宙 `U` = v1.4 组合行归一药集合（P-B 结构预跑：**4,088**，归一 = NFKC→casefold→仅字母数字，与 R190-E1/P-A 一致）。

## 2. 分析单元与端点（沿用 P-B 冻结，不换端点）

- 单元 = （`cell_line_name` 归一名，无序归一药对），与 P-B 完全一致。
- **主端点 = `synergy_bliss`**，端点值 = 单元内**全部非缺失 block 的算术均值**（P-B §4 冻结规则）；本任务**不重新选择端点、不换指标**。
- **有注释宇宙** `A := {单元 : 两个药均 ∈ M}`；期望 **|A| = 88,118**（P-A G3 上下文）。作为断言与交叉核对，不作判据。
- 报告 `A` 的单元/药对/细胞数与端点缺失数。

## 3. 两种切分口径（冻结规则，均与 P-A/R190-E1 字面一致）

归一药名按字典序排序得 `names`，`N = len(names)`；对给定留出比例 `r`：
`k = max(1, round(r·N))`，`step = max(1, N // k)`，`H = set(names[0::step][:k])`。

- **PA 切分（主口径）**：`names = sorted(M)`，`N = |M|`（在**已映射药**上留出；期望 r=0.20 时 k=284）。
- **E1 切分（敏感性/阶段 2 兼容口径）**：`names = sorted(U)`，`N = 4,088`（在全体药上留出；r=0.20 时 k=818，step=4）。
- **both-unseen 有注释单元** = 单元两药均 ∈ M 且均 ∈ H（对 PA 切分，两药 ∈ H 已蕴含 ∈ M）。
- 期望交叉核对（P-A 报告）：r=0.20 时 PA **2,682**、E1 **3,739**；不符则在 `pb2.json` 记录并说明实现差异，不用其改判据。
- 同时报告每个设计的：**训练有注释单元**（两药均 ∈ M 且均 ∉ H）与**严格训练单元**（两药均 ∉ H 且均 ∈ M，即 same as above — 严格口径 = 两药都不在留出集；对 PA 切分两药 ∈ M 自动满足）。

## 4. 设计矩阵（冻结）

`r ∈ {0.20, 0.30, 0.40} × 切分 ∈ {PA, E1}` = **6 个设计**。对每个设计报告：
留出药数 `k`、both-unseen 有注释单元数 / 药对数 / 细胞数、训练有注释单元数、`ρ_pair_mean_replication`（见 §6）。

## 5. MDE80（与 P-B §11 完全相同的口径与算法）

- 统计量 = 全评估单元上 `Spearman(ẑ, y)`，`y` = 该设计的 both-unseen 有注释单元的主端点值。
- both-unseen 下 identity 臂预测恒为常数（两药 one-hot 全 0）⇒ `ρ(identity)=0` 约定；主对比 `Δρ` 的 MDE = 单臂 ρ 对 0 的 MDE。
- 零信息预测：每个药对 `z_p ~ N(0,1)` 广播到该对全部单元（预测只随药对变化）。
- **MDE80 = 2.801585218112968 × SE**（α=0.05 双侧、power=0.80；与 P-B / A0 / C160 同口径）。
- **两类聚类口径（都报）**：
  - **A. 药对聚类 bootstrap**：有放回重采样药对（带入全部单元；单元重复计数），每 replicate 重抽 `z_p`；`SE_A`、`MDE80_A`。
  - **B. 药/细胞双向聚类 bootstrap（预注册门槛用）**：每 replicate 独立重采样药对与细胞系，单元权重 `= mult_pair × mult_cell`（展开后 midrank 相关）；`SE_B`、`MDE80_B`。
- `B = 2,000`；种子预注册为 `SEED2 + 1000 + 100·round(r·100) + (0 for PA / 1 for E1)`，`SEED2 = 20261028`。
- iid 解析 `SE = 1/sqrt(n−1)` 仅作参考（忽略聚类，不用于判定）。

## 6. 检定力（经验拒绝率，冻结算法）

对每个设计、`δ ∈ {0.1183, 0.10, 0.05}`：
1. 计算 `ρ_pm = Spearman(pair_mean 广播到单元, y)`（药对均值对单元端点的"复制度"）。
2. 构造预测 `z = c·standardize(pair_mean) + sqrt(1−c²)·noise`，`c = min(1, δ/ρ_pm)`（使单元级 ρ̂ 的目标值 ≈ δ）。
3. 以 `ρ̂ > 1.959963984540054 × SE_B` 为拒绝（单侧，与 P-B 一致），`1,000` 次重复，报告经验拒绝率。
- 该模拟**只使用端点边际分布与药对/细胞结构**，不涉及任何 identity/annotation 特征或模型（白名单同 P-B §1）。

## 7. 决策规则（冻结）

**"复现目标效应"先冻结**：冻结结论的头条效应 `Δρ = +0.1183`，95% CI `[+0.0947, +0.1409]`（C130）。复现的目标效应 = 该冻结效应本身，因此可正当化的 `δ_min` 只能取**目标效应量级**，不得取 ≤0.05 的小效应（那等于要求本资源探测比冻结效应小一个数量级的效应，不可由"复现"目标辩护）。
- **Tier B（主判据）**：`δ_min = 0.1183`（冻结头条点估计）。
- **Tier A（保守敏感性）**：`δ_min = 0.0947`（冻结效应 95% CI 下界——设计至少要能看见原始结论悲观端的效应）。

**设计"可正当重开"当且仅当**（全部满足）：
1. `MDE80_B ≤ δ_min_tier`（主用 Tier B；Tier A 同时报告）；
2. 经验检定力 @ δ=0.1183 **≥ 0.80**；
3. 训练有注释单元 ≥ **5,000**（沿用 P-A G4 门槛；阶段 2 训练侧需要）。若某设计 both-unseen 满足 1–2 但训练侧不足 → 记 `training_insufficient`，不推荐。
**推荐设计** = 通过设计的集合中 `MDE80_B` 最小者（检定力最大），并报告其精确 `r`、切分口径、`δ_min`、MDE80、power、训练单元数。若 Tier B 无设计通过 → `not_reopenable`。

**若不可重开**：按 §8 外推"**最小所需有注释 both-unseen 单元数**"（对 Tier B 与 Tier A 两个目标各报一次），并明确写"有注释宇宙太小，阶段 2 不能在本资源上被正当重开"。

## 8. 外推规则（冻结）

- 关系假设：`SE(n) ≈ c·n^(−α)`；以 6 个有注释设计的 `(n_units, SE_B)` 与 `(n_pairs, SE_B)` 做 log-log OLS，报告拟合 `α`；主外推**固定 α = 1/2**（P-B 三个全体宇宙设计点已显示 `SE·sqrt(n)` 近似常数），用 `c = median(SE·sqrt(n))` 估计。
- 目标 `SE_target = δ_min_tier / 2.801585218112968`。
- **最小所需有注释 both-unseen 单元数** = max( 由 `n_units` 拟合直接解出的 `n`，由 `n_pairs` 拟合解出的 `n_pairs × 本资源 units/pairs 比` )，两个 tier 各报一次；并报相对当前最大设计单元数的倍数。
- 外推是近似，必须附三条 caveat：① α 固定/拟合的不确定性（只有 6 个设计点）；② 细胞数固定在 ~100–110、药对大小分布不随 n 等比缩放；③ 若达到该单元数需要把分析宇宙扩大到注释覆盖之外，则外推不再适用（此时应写"需要更大的注释覆盖（P-A 扩展）"而非"更大 r"）。

## 9. 确定性与产物

- `pb2.py` 离线、单进程、固定种子（§5）、`json` 键排序、**无时间戳**、浮点 `round(...,6)`；输入/脚本/协议 SHA256 全部写入 `pb2.json`；连续两次运行 `pb2.json` 逐字节相同。
- **不得修改 P-B 产物**：`pb2.py` 在运行前后对 P-B 7 个文件计算 SHA256 并断言一致（写入 `pb2.json → pb_artifacts_unchanged`）。
- 产物中不得出现 identity/annotation 模型拟合或效应估计；grep 审计写入 `record_pb2.md`。

## 10. 明确不做

不评估 identity/annotation 效果；不拟合任何模型；不换指标/换端点（主端点固定 `synergy_bliss`）；不改 P-A 映射/切分定义（只按字面实现并交叉核对）；不重开线 D/I003；不做机制/临床主张；不把"可重开"写成"复现已成立"。

## 11. 预期核对的数字（P-A / P-B 已发布，供断言，不作判据）

| 项 | 期望 |
|---|---|
| v1.4 组合块 / cell×pair 单元 | 466,033 / 380,418 |
| 归一药 U | 4,088 |
| 已映射药 \|M\|（S1-A） | 1,418 |
| 有注释宇宙 \|A\|（两药均映射单元） | 88,118 |
| both-unseen 有注释单元 r=0.20 PA / E1 | 2,682 / 3,739 |
| 全体宇宙 both-unseen r=0.20 | 16,078（P-B） |
| 冻结效应 / CI | +0.1183 / [+0.0947,+0.1409] |
| P-B r=0.20 全体 two-way MDE80 | 0.114851（`pb.json → mde.0.20.B_two_way_clustered.mde80`） |

---
*冻结时间：2026-10-27（协议 SHA256 见 `pb2.json → protocol.sha256`）。本文件在 `pb2.py` 首次运行前完成。*
