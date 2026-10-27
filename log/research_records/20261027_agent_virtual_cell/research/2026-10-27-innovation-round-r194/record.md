# R194 轮次记录：Q 条件级结构可估性——`condition_structure_present` 但份额可忽略（1.43%）

2026-10-27。角色：Lead（冻结/核验/综合）＋ 独立 runner（endpoint-auditor，task-16）＋ 独立挑战（i003-challenger，task-17，已排待 A2 协议后审）。本轮**未运行反馈/策略/Agent**，只做 Q 的方差分解与可估性。

## 0. 一句话结果

- **H194a 成立（统计上可估、非零）**：condition-pair 方差分量 **σ²_cond=0.000371（占总方差 1.43%，SD 0.019）**，双向 CI **[0.000297,0.000674]**，置换零分布 **p=0.001**；条件级 Q 可靠性（435 cp 中位平均）**0.868**（阈值 0.50）。
- **H194b 判"可忽略份额"**：Q 方差 = **condition×cell-pair 交互 48.5%** + **barcode 测量噪声 46.1%** + cell-pair 主效应 3.9% + condition 级 1.43%；**条件级共享规律只占约 1.4%**。
- **含义（BRIEF 分支）**：Q 主要是**细胞特异的 condition×cell 交互 + 测量噪声**；后续反馈/迁移/Agent 研究**不应以"条件级共享规律"为前提**；若做条件级跨 screen 复验，只允许在**更大独立资源 + 更好噪声标定**上做资格审计（不是同一 96 细胞换聚合）。A1 的 `inconclusive`（C171）不变；A2 不是 A1 通过；B/C/acquisition 不启动。

## 1. 执行与设计（PROTOCOL_Q2 v1 冻结）

- 输入：Jaaks Original/Validation fitted（身份/剂量/单药列 + `SYNERGY_DELTA_EMAX`；SHA 见 A0 report）、A0 `matched_conditions.csv`；A0/ERRATA/challenge/PROTOCOL_A0/PROTOCOL_Q/q1 产物哈希全部未变（只读）。
- 设计（先冻结 [PROTOCOL_Q2.md](../2026-10-27-conditional-shift/PROTOCOL_Q2.md)，`0F8D1946…`）：controlled_anchor 主分层；barcode 均值聚合；交叉随机效应 `Q=μ+a(condition-pair)+b(cell-pair)+e`；矩估计 + 双向 bootstrap（B=100）检验；噪声由 within-screen barcode 分半标定（四键均 ≥2 barcode 的 1,312 四元组，占 1.43%）；条件级可靠性 `σ²_cond/(σ²_cond+(σ²_int+σ²_noise)/n_i)`；备择 s=σ_cond/σ_total∈{0.2,0.4} 功效、type-I 先于判定；Validation 仅探索性样本外检查。
- 判定：`condition_structure_present` / `condition_structure_absent` / `inconclusive`；absent 只表示"不可估/可忽略"，不是普遍"不存在"。

## 2. 结果（`q2.json`）

| 项 | 值 |
|---|---|
| 结构 | **92,039** 观测 = **229 condition-pair × 1,501 cell-pair**（96 细胞/291 条件/9,154 键/129 有向药对；每 cond-pair 78–595 cp 中位 435；每 cp 6–134 cond-pair 中位 58；格密度 0.268；unique(i,j)=92,039/92,039；二部图 3 分量 134/58/37） |
| design-check | **15/15 全过**；噪声标定四元组 1,312（1.43%）；σ²_single=0.003351；分半稳定性 ratio 1.027/0.797 ∈[0.5,2]；可辨识性 pilot bootstrap SE 有限 100% |
| 功效/type-I | **power(s=0.4)=1.00、power(0.2)=1.00、type-I=0.00**（N_SIM=200、B=100；冻结检验=双向 bootstrap z>1.645） |
| 方差分量（Original） | **σ²_cond=0.000371（1.43%）**、σ²_cellpair=0.001023（3.94%）、**σ²_int=0.012582（48.5%）**、**σ²_noise=0.011968（46.1%）**、σ²_total=0.025944（SD 0.161） |
| 条件级可靠性 | 主公式 n_i 中位 435 → **0.868**（IQR 0.841–0.882；阈值 0.5 通过）；noise-only 0.931；含 cell-pair 抽样 0.863。**可靠性高是 435 cp 平均的结果，≠条件级成分占比大**（协议冻结此语义，必须并列引用） |
| 零分布 | condition-pair 标签打乱（B=1,000）：null mean 0/sd 6e-6/q95 1.0e-5 vs 观测 **3.71e-4 → p=0.001**；cell-pair 打乱 q95 2.3e-5 vs 观测 1.02e-3 → p=0.001 |
| Validation（探索，非判定） | 条件级 Spearman **0.177**（condition-pair bootstrap CI **[0.055,0.296]**，229 对）；σ²_cond^B share 0.98% → 同向同量级偏小 |

## 3. 解释与分支（冻结）

- **Q 的条件级共享成分只有约 1.4%**：即使统计上可估、条件级 Q 可靠性高（因平均 435 个细胞对），其方差占比可忽略；Q 主要是**每个细胞对特异的 condition×cell 交互（48.5%）与测量噪声（46.1%）**。
- 分支（BRIEF）：present 但可忽略 → 条件级共享规律不作为反馈/迁移/Agent 前提；**下一轮只允许在更大独立资源 + 更好噪声标定上做条件级跨 screen 复验的资格审计**；B/C/acquisition 不启动。
- 局限（runner 披露）：噪声标定仅覆盖 **1.43%** 观测（σ²_cond 主估计不依赖该标定；受影响的只是 int/noise 分割）；Validation 探索性检查不是跨 screen 复验；barcode 分半同日同 screen，非独立培养。

## 4. 核验与产物

- Lead 核对：A2 产物 SHA256 与报告一致（PROTOCOL_Q2 `0F8D1946…`、q2.py `083694DA…`、q2.json `94C5CD9B…`、q2_rows.csv `8494FA08…`）；runner 自报两轮 `q2.json`/`q2_rows.csv` 逐字节相同（首次复核发现 `power.runtime_seconds` 非确定已删除）。
- 产物（`research/2026-10-27-conditional-shift/`）：[PROTOCOL_Q2.md](../2026-10-27-conditional-shift/PROTOCOL_Q2.md)、[q2.py](../2026-10-27-conditional-shift/q2.py)、[q2.json](../2026-10-27-conditional-shift/q2.json)、[q2_rows.csv](../2026-10-27-conditional-shift/q2_rows.csv)、[report_q2.md](../2026-10-27-conditional-shift/report_q2.md)、[record_q2.md](../2026-10-27-conditional-shift/record_q2.md)、[usage_q2.json](../2026-10-27-conditional-shift/usage_q2.json)。
- 边界：条件级结构"可估但份额可忽略"是**测量级边界**，不是机制/临床结论；A1 inconclusive 不变；未晋升代码；总体目标未达成。


## 6. ERRATA（外部重审后，2026-10-27）

依据 `research/2026-10-27-cross-domain-directions/{report.md,late_results_audit.md}` 与 Lead 对 q2.py 的核对：

1. **1.43% 只是加性条件主效应份额，不是可迁移规律总量**：Q2 模型估计的是与 cell-pair 无关的条件主效应；共享秩 1 规律 `Q_ij=u_i v_j`（u=v=(1,−1)）加性主效应为 0 但完全共享可学。**不得**从 1.43% 推出「条件级共享规律可忽略/不应以共享规律为前提」。残差 `c_ij` 是否可由可复用背景×条件结构预测，A2 未检验（R197 处理）。
2. **Q2 加权矩代数混用一次/二次权重**（`q2.py` moment_estimator 用 `Tc−2μSc+μ²W2c` 而 Sc/Tc 为一次权重；正确需 `Σw²y`、`Σw²y²`）。确定性例 y=(1,3),w=(2,1)：正确 −8/9、代码 −37/18；w≡1 时相同 → 未加权点估计不变，但 bootstrap CI/SE 与由此派生的可靠性/功效需重算。
3. **依赖单位**：435 个细胞对不是 435 份独立信息（同条件对 Q 共享细胞/键；n=30 时 dyadic 对比方差与独立边近似差 ~10.33×）；0.868 可靠性未被认证；置换/功效模拟未覆盖完整规则。
4. int/noise 48.5%/46.1% 是误差模型下的分割，**不是生物学机制比例**；噪声标定仅覆盖 1.43% 观测；Validation 探索性 0.177 不能当外部复制成功。
5. 以上不改变 Q2 原始测量（σ²_cond、share 等）作为「已执行统计量」的登记，但**解释与推断须按 [ERRATA_Q2.md](../2026-10-27-conditional-shift/ERRATA_Q2.md) 收窄**；C174 为更正入口。R197 先重核、再用低秩/留出预测检验残差结构。
