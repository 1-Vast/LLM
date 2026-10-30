# record_q2 —— R194-A2 执行过程记录（时间线 / 冻结 / 发现 / 偏离 / 边界）

2026-10-27。角色：独立设计/执行 runner。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / numpy 2.4.6 / pandas 2.3.3 / scipy）。判定与数字以 [q2.json](q2.json) / [report_q2.md](report_q2.md) 为准。

## 1. 范围与纪律

- 只写 `research/2026-10-27-conditional-shift/` 下**新增** `PROTOCOL_Q2.md / q2.py / q2.json / q2_rows.csv / report_q2.md / record_q2.md / usage_q2.json` 与 `tmp/`；**未改** A0 产物、ERRATA、PROTOCOL_Q、PROTOCOL_A0、challenge、q1 产物、其它目录、INDEX、SYNTHESIS、git。
- 严格按 `PROTOCOL_Q2.md`（v1 FROZEN，SHA256 `0F8D1946…286CE`）执行：先设计检查 D1–D4，全部通过后才做 H194a/H194b 主估计；未改门槛/统计量/分层/判定。
- **A2 不是 A1 复活**：不做跨 screen Q 复验、不用同一 96 细胞换聚合、不启动 B/C/acquisition、不换端点/分层/δ、不按 Q 大小挑层、不用 Q 结果反推模型选择。

## 2. 协议冻结前的数据接触（disclosure）

冻结（17:0x 前写完 `PROTOCOL_Q2.md`）之前只做了**结构/合成数据**探针，**没有读任何真实 Q 值/效果**：

1. `tmp/a2_probe.py`：只读身份/设计/barcode 列，建立 matched keys、condition-pair×cell-pair 格型、barcode 覆盖计数。结果：92,039 观测 / 229 condition-pair / 1,501 cell-pair；n_i 78–595（中位 435）；m_j 6–134（中位 58）；unique 格 92,039/92,039；二部图 3 分量；Original barcode 分半可用四元组 1,312（1.43%）。这些直接写成协议 §1 的结构事实。
2. `tmp/a2_estimator_probe.py`：**纯合成数据**（iid/备拟方差）验证矩估计无偏性与 bootstrap-z 的量级；未用真实 Q。
- 协议冻结后才运行 `q2.py`，其中设计检查阶段使用真实 y 的部分严格限于协议允许项：barcode 分半噪声标定（§2）与设计检查 D1–D4；主估计在 D 全过后才执行（`q2.json → design_check.design_check_passed=true` 在前，`main_analysis.computed=true` 在后）。

## 3. 时间线与运行

| 步骤 | 内容 | 结果 |
|---|---|---|
| 读 BRIEF / A0 / ERRATA / challenge / PROTOCOL_Q / q1 | 确认 A1 边界、A2 问题、必引 ERRATA | — |
| `tmp/a2_probe.py` | 结构/barcode 探针（不读 Q 值） | 92,039 / 229 / 1,501；barcode 覆盖 1,312 |
| `tmp/a2_estimator_probe.py` | 合成数据估计量验证 | 无偏（s=0.2/0.4 回收 0.039/0.158 vs 0.04/0.16）；bootstrap-z power≈1 |
| 写 `PROTOCOL_Q2.md`（冻结） | 模型/估计量/噪声/可靠性/检验/门槛/判定全写死 | SHA256 `0F8D1946…286CE` |
| `q2.py` 首次运行 | 完整执行 | **199–201 s**：D1–D4 全过；判定 `condition_structure_present`；share_cond=1.43% |
| 确定性复核 | 连续两次运行比较 SHA256 | `q2.json`/`q2_rows.csv` 逐字节相同（见 §8） |

## 4. 设计检查（15/15 PASS）

- D1 结构：N=92,039；cell-pair 1,501；condition-pair 229；每 cond-pair ≥78 cp；每 cp ≥6 cond-pair；unique cells；连通分量 3。
- D2 噪声：标定四元组 **1,312**（1.43%）；σ²_single=**0.003351**；分半稳定性 ratio **1.027**（cell-pair 奇偶）/ **0.797**（condition-pair 奇偶），均在 [0.5,2]；每观测平均噪声方差 0.011968。
- D3 可辨识性：点估计有限；pilot（B=200）SE 有限比例 100%。
- D4 功效/type-I：**power(s=0.4)=1.00**、power(s=0.2)=1.00、**type-I=0.00**；备择分割 ρ_cellpair∈{0.2,0.6} power 均 1.00。冻结的检验 = 双向 bootstrap z>1.645（B=100），N_SIM=200。

## 5. 主估计与判定

| 分量 | 估计 | 份额 |
|---|---|---|
| σ²_cond | **0.000371**（CI [0.000297,0.000674]，置换 p=0.001，SE=9.6e-5） | **1.43%** |
| σ²_cellpair | 0.001023（CI [0.001068,0.002174]，置换 p=0.001） | 3.94% |
| σ²_int（交互） | 0.012582 | 48.5% |
| σ²_noise | 0.011968 | 46.1% |
| σ²_total | 0.025944 | — |

- 条件级可靠性（主公式，median n_i=435）：**0.868**（IQR 0.841–0.882）；阈值 0.50 通过。noise-only 0.931；含 cell-pair 抽样 0.863。
- **H194a 四项全过** → **`condition_structure_present`**。
- **H194b：share_cond=1.43% < 10% → "条件级份额可忽略，条件结构主要是细胞特异的"**；后续反馈/迁移/Agent 不应以"条件级共享规律"为前提（BRIEF）。
- 置换零分布：condition-pair 标签打乱 null mean 0 / q95 1.0e-5；cell-pair 标签打乱 q95=2.3e-5；观测均远高于 q95（p=0.001 最小可分辨）。
- Validation 探索性：条件级 Spearman **0.177**（CI [0.055,0.296]）；σ²_cond^B=0.000186（0.98%）；**不参与判定**，非跨 screen 复验。

## 6. 发现（给 Lead 的实质读法）

1. **条件级方差分量可估但极小**：Q 总方差 ≈ 0.0259（SD 0.161 viability 分数），其中条件级 SD 仅 0.019（≈1.9% viability 点，份额 1.43%）；**cell×condition 交互（48.5%）+ barcode 测量噪声（46.1%）** 才是主导。**"可估"≠"重要"**。
2. **高可靠性是 n_i≈435 平均的结果**，不是条件成分占比大：rel=0.868 与 share=1.43% 同时成立，必须并列引用（协议已冻结语义）。
3. 噪声与交互各约 46–48% → Q 的相当部分是不可约的测量噪声（单 barcode 单药读数 SD≈5.8% viability）。这对任何以 Q 为端点的后续设计都是硬约束。
4. Validation 条件级一致性方向为正但小（ρ=0.177，CI 不含 0），与"条件级成分 1.4%"一致：**不能把它读成跨 screen 复验**。
5. 分支（BRIEF）：present → 下一轮只在**更大独立资源**上做条件级跨 screen 复验的资格审计；**但 H194b 的可忽略份额意味着：不应把"条件级共享规律"当作反馈/迁移/Agent 的前提**；若要做，先要解决噪声标定与 cell 数限制（不是同一数据的换聚合）。

## 7. 实现选择（冻结前写入协议 §2–§8，非事后）

- condition-pair 定向：library_id 升序；缺失格=缺失不插补；极端 Q 不剔除。
- 矩估计：同层观测对协方差（`½[(Σx)²−Σx²]`，无偏分母 `ΣC(n,2)`）；σ²_resid=σ²_total−σ²_cond−σ²_cellpair；σ²_int=max(0, σ²_resid−σ²_noise)。
- 噪声：只用四键均 ≥2 barcode 的四元组；`σ²_single=Σdiff²/Σ[Σ_k(1/b_h1+1/b_h2)]`；每观测噪声=`σ²_single·Σ_k 1/b_k`。
- 可靠性主公式：`σ²_cond/(σ²_cond+(σ²_int+σ²_noise)/n_i)`；headline 在 median n_i；阈值 0.50 先冻结。
- 检验：双向 cluster bootstrap（B=1000，seed 20261028）+ 置换零分布（condition 标签 seed 20261029、cell 标签 seed 20261030，各 B=1000）+ D4 功效模拟（N_SIM=200，B_POWER=100，seed 20261031，备择分割 ρ_cellpair=0.4）。
- 判定：present 需 σ²_cond>0 ∧ CI 下界>0 ∧ >置换 q95 ∧ rel≥0.50；absent 的措辞 = "不可估/可忽略"边界，不是"不存在"。
- 以上与冻结协议逐字一致；**无事后门槛/统计量修改**。

## 8. 产物与确定性（SHA256 见 [usage_q2.json](usage_q2.json)）

| 文件 | 说明 |
|---|---|
| `PROTOCOL_Q2.md` | 运行前冻结（`0F8D1946…286CE`） |
| `q2.py` | 确定性执行（`083694DA…A24769`）；无时间戳、键排序、固定种子 |
| `q2.json` | 输入/协议/脚本 SHA、结构、D1–D4、主估计、判定、边界 |
| `q2_rows.csv` | 229 个 condition-pair 一行：n_cp、Q̄_i、Q sd、rel_i、Validation 条件级均值（探索） |
| `report_q2.md` / `record_q2.md` / `usage_q2.json` | 报告 / 本记录 / 运行时账 |
| `tmp/a2_probe.py`、`tmp/a2_estimator_probe.py`、日志 | 冻结前结构/合成探针（不读真实 Q 效果） |

- 单次运行 **199–201 s**（≤45 min 预算）。**确定性修复（披露）**：首次确定性复核发现 `design_check.power.runtime_seconds` 字段非确定（两次 175.9 vs 181.4 s）→ 已删除该字段（运行时记账移到 `usage_q2.json`），最终两轮 `q2.json`/`q2_rows.csv` 逐字节相同；复算逻辑与数字未因该字段改动。
- A0 引用已同时包含 PROTOCOL_A0 + ERRATA_A0 + challenge_A0（`q2.json → a0_citation`）。

## 9. 局限与后续

- **噪声标定覆盖薄**（1,312 四元组 = 1.43% 观测，barcode-rich 细胞集中）：这是最大测量体制不确定性；分半稳定性通过但不能完全排除平稳性偏差。σ²_cond 的估计**不依赖**噪声标定（只依赖 Q 值矩），故"cond 份额小"的结论不受此影响；受影响的只有 σ²_int 与 σ²_noise 的分割（约 48% vs 46%，误差不改变主结论）。
- 矩估计假设加性交叉随机效应；不平衡与极端值影响由 bootstrap 覆盖（σ²_cond CI 远离 0）。
- 条件级可靠性高 ≠ 条件成分占比大（1.43%），两者必须并列引用。
- 后续若重开：需更大独立资源 + 更好的噪声标定（更多 barcode 重复）+ 更强的 cell 数；**不是**同一 96 细胞换聚合。B/C/Agent 不启动。
- 条件偏移 ≠ 机制；condition 级结构 ≠ 可迁移；结论限定 matched 子集与该端点/标定精度。
