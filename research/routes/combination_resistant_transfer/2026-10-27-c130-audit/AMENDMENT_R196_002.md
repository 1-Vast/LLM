# AMENDMENT_R196_002.md —— PREGISTERED AMENDMENT-002（v2 verdict 规则补充；不重跑主统计）

2026-10-27，R196 v2。**在 v2 最终 verdict 落盘之前冻结。** 依据：Lead 转达的 i003 挑战预审结论（`challenge_R196_v2.md` §5 预留结果审）与 Lead 的两次状态检查指令。
**本修正案不改变任何数据/划分/内层 λ/网格/δ_min/主单位/主估计量，不重跑主统计**；只补两件必须在最终 verdict 前写死的事，并更正披露与小项口径。`AMENDMENT_R196.md`（001）保持冻结不改；两者冲突时以 **002** 为准（仅限 verdict 规则与 E9 后果）。

## 0. 与 001 的关系

- 001 的规则不变：主推断单位 = held-out 药物（10 个独立药物划分 × 5 折 = 50 折级增益的均值）；主 CI = drug-cluster bootstrap；主 MDE80 = 2.802 × SD(drug bootstrap)；δ_min = 0.05；`replicated_under_audit` 需主 CI 下界>0、点估计 ≥δ_min、主 MDE80 ≤δ_min、设计体检全过。
- 002 追加：**(A) partition 级 95% CI 下界>0 成为 `replicated_under_audit` 的合取条件**（对应挑战"二选一"的选项 a）；**(B) E9（单命令 ≤15 min wall-clock）不通过 ⇒ verdict 必须 `inconclusive`**，不得事后改记为 deviation 放行。
- 若 001 与 002 同时不满足，verdict 取最保守（`inconclusive`），并逐条记录子类型。

## A. partition 级进入判定（写死；选项 a）

**为什么**：50 个折级增益来自 **10 个划分**，每个划分使用**同一批 65 个药物**（划分之间共享药物总体；划分内 5 折的 held 药物互不相交，但划分之间高度相关）。`drug-cluster bootstrap` 在**固定划分**上重抽药物，只覆盖"同一划分方案下的药物抽样"；它**不覆盖**"换一批药物划分"的方差。因此只靠 drug CI 可能"drug CI 正、但 partition 均值 t-CI 含 0"而误判 replicated。

**冻结统计量**：
- 对每个划分 p，`G_p = mean_{f=1..5} gain_{p,f}`（5 折均值；identity 按 001 §4 显式 ρ=0）。
- **partition 级 95% CI**：`mean(G_p) ± t(0.975, df=9)·SD(G_p)/√10`（t=2.262，df=9；**同时报告 10 个 G_p 的 min/max 与 leave-one-partition-out 均值**）。该区间与 001 §4 的"划分级分布/CI"完全一致，只是升级为判定条件。
- **合取规则（写死）**：`replicated_under_audit` **必须同时满足**：
  1. drug-cluster 95% CI 下界 **> 0**（001 主单位）；
  2. **partition 级 95% CI 下界 > 0**（本修正案新增）；
  3. 点估计 ≥ δ_min；
  4. 主 MDE80（drug 单位）≤ δ_min；
  5. 设计体检 E1–E9 全通过（其中 E9 见 §B）。
   否则按 001 §5 映射到 `weakened`/`inconclusive`。若 **partition 均值符号不一致**（存在 G_p < 0 或 min(G_p)<0）或 partition CI 含 0 → **最多 `weakened`**；若主 MDE80 > δ_min 或设计体检失败（含 E9）→ `inconclusive`。

**"50 折非独立"的写死口径**：50 折由 10 个划分 × 5 折构成；**折级 t-CI（df=49）不得作为独立样本 CI**，只作 formal sensitivity（001 §4/§6 已定）。主方差由**两阶段构造**承担：阶段一 = 划分内 5 折均值（`G_p`）；阶段二 = 10 个划分的分布（partition CI）；药物单位另有 drug-cluster bootstrap（固定划分内的药物抽样）。**不做 nested bootstrap**（未预注册、也不重跑）；该限制写入报告与记录。两阶段估计量 = `mean_p G_p`（与 001 的 50 折等权均值在每划分 5 折时数值相同），方差口径取 partition CI。

## B. E9 预算后果（写死）

- 001 §6 E9 冻结："单命令 ≤15 min（900 s）"；E9 是设计体检的一部分。
- **规则（写死）**：**若 v2 主运行 wall-clock > 900 s，则 E9 不通过 ⇒ verdict 必须 `inconclusive`**；**不得**把超时改记为"运行时 deviation"而放行判定，也不得据超时后的结果升级为 replicated。
- **测量口径**：`r196_v2.py` 单进程从启动到 `r196_v2.json` 写盘的 wall-clock（脚本自报 `DONE wall`）；CPU 时间以运行环境可得值为准（不可得记 null）。分步缓存路径与各自 SHA 记录在 `record_r196_v2.md`（`tmp/r196_v2_stage_*.json`）。
- 已知事实（写死登记）：v2 的 CPU/wall 已显著超过 900 s → **E9 不通过**。因此即使 A 的合取条件全部满足，`replicated_under_audit` 也不可得；v2 verdict 至多 `inconclusive`（若 A 失败则 `weakened`，但 E9 失败优先 `inconclusive`）。

## C. 披露更正与新增小项（写死）

1. **peek 更正（重要）**：v2 **不是盲验、不是独立复现**。在 AMENDMENT-001 冻结前，v1 已跑出并已撤回的结果（`r196.json`：annotation 0.1447、rowlevel_c130 0.1441、cell CI [0.1213,0.1667]、pair/twoway CI、**drug CI [0.0139,0.2233] 与 MDE80_drug=0.1527**、5 折 per-fold 与 fold SD 0.128）。**v2 是在已知 v1 全部结果基础上的审计重分析**；v2 的规则/阈值/网格/划分种子来自挑战与撤回文本、不来自 v2 结果，但"任何响应读取前冻结"之类的表述对 v2 一律不成立，必须在报告与记录中显式写明。
2. **E7 与 §5 判定门的关系**：E7 只用 **`shuffle_seed0` 在完整 10 划分设计上的 drug-cluster bootstrap SD**（B=1,000，`SEED_BOOT_DRUG+21`）构造 `MDE80_design`，与 001 §4 的主 MDE80（treatment，cellular/drug bootstrap B=2,000）是**不同统计量**；E7 是**打分前**的功效门（不是对处理臂的检验），001 §5 的 `inconclusive` 条件"主 MDE80 > δ_min"指**处理臂主 MDE80**；两者任一失败均触发 `inconclusive`（记录子类型区分 `mde_design_gt_delta_min` 与 `primary_mde80_gt_delta_min`）。
3. **identity 不拟合的 50 折论证**：both-unseen 测试行中每个药物名都在留出集，其身份 one-hot 列在训练行全为 0 → 训练均值 μ=0、标准差置 1 → 该列在测试行取值 1 时 Z=1，但对应 ridge 系数恒为 0（该列 Gram 行/列全 0、b 分量 0、仅对角 λ → w=0）；其余（已见药物）列在测试行为 0 → Z=−μ/σ 为**行间常数**。故预测 = `ȳ + 常数` → 行间常数 → Spearman 未定义 → 按 001 §4 显式约定 ρ=0.0。v2 在 **partition 0 的 5 折**上实际拟合验证 5/5 常数值（脚本断言，见 `r196_v2.json` design_checks/E8 前后的 identity 检查与 log），该构造对每个划分/折的代码路径相同，故对全部 50 折沿用。
4. **`rowlevel_c130_grid` 的 C130 桥接限定**：v2 的 row-level 内层 CV 使用**折内 scaler**（每折内层训练集重拟合），而 C130 原实现是**折前 scaler**（外层训练集整体标准化后再切内层行），且 C130 用 40 个重叠随机划分、λ≤1000；因此 `rowlevel_c130_grid` 只是"**同一 R196 外层设计 + C130 网格**的桥接诊断"，**不是 C130 复现**；H196b 的结论限定在"本协议 + 扩展网格（或 C130 网格）"内。v1 的 `rowlevel_c130`（折前 scaler）结果仅作历史对照，不进入 v2 判定。
5. **Kendall 换算为近似**：δ_min 的 operational 表述用 `τ ≈ (2/π)·arcsin(ρ)`（bivariate normal 近似），ρ=0.05 → τ≈0.0318 → 排序概率提高 ≈1.59 pp 是**近似值**，不是精确换算；δ_min 仍是 0.05（写死），该换算只用于说明"最小可靠秩信息量"的含义，不用于判定计算。
6. **主统计量口径再确认**：`Δ = mean_{p,f} gain_{p,f}`（50 折等权；每划分 5 折 → 与 `mean_p G_p` 数值相同）；`gain_{p,f}=ρ(annotation)_{p,f}−ρ(identity)_{p,f}`，`ρ(identity)=0` 显式约定；不因 002 改动。

## D. v2 verdict 的机械规则（写死，按顺序）

1. 若 **E9 失败**（wall > 900 s）或任一设计体检失败（E1/E2/E6/E7 等）或主 MDE80 > δ_min → **`inconclusive`**（记录子类型）。
2. 否则若 (drug CI 下界>0) ∧ (partition CI 下界>0) ∧ (点估计 ≥δ_min) ∧ (主 MDE80 ≤δ_min) → **`replicated_under_audit`**。
3. 否则 **`weakened`**（子类型：`ci_includes_zero` / `partition_ci_includes_zero` / `below_minimum_effect`；若 partition 均值符号不一致另记 `partition_sign_inconsistent`）。
4. 措辞模板沿用 001 §7；**不得**写成 C130 复现/独立确认/决策收益/机制；`weakened`/`inconclusive` 不得写"C130 被推翻/注释无用"。

## E. 产物

- 本文件（先于最终 verdict 冻结）；v2 产物同 001 §8，另加 `report_r196_v2.md`/`record_r196_v2.md`/`usage_r196_v2.json` 记录 **wall/CPU、E9 判定、partition 结果、分步缓存路径与 SHA**。
- 所有 v2 结果在 task-32 独立挑战通过前不得解释。

## F. 明确不做

不改数据/端点/注释/特征/划分/折数/内层口径/λ 网格/δ_min/主单位/主估计量；不重跑主统计；不事后放宽 E9 或 partition 合取；不把超时或 peek 写成 pass。
