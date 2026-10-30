# report_d3_v0_2 —— R200-D3.1 修订/可行性报告（D3 停止裁定）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）· 任务：task-91（D3.1）。
**状态：DESIGN REVISION / STOP；未运行效果、未拟合预测、未比较 acquisition、未读原始响应值做统计。**

## 1. 结论

- **v0.1 单 anchor D3 判 `design_invalid: precision_insufficient`；D3 当前停止，不进入执行协议。**
- 正确 mean-Δ MDE：单 anchor 8 wells/unit，`SE=σ/√2`；batch1 target30 σ=0.1384458171 → **MDE80=0.1119678 > δ_min=0.10**；all-batches σ=0.1422665081 → **0.1150578**。
- **rank-level MDE（primary Spearman Δρ）**：保守独立误差 Fisher-z 口径，n_eff=6 → **2.2875**；pooled 30 → **0.7625**；均 >0.10。**null/bootstrap 只答排除 0，不答分辨 0.10。**
- **若要 rank MDE≤0.10**：需 **≈1,573 条独立细胞系**（O'Neil target30 只有 30），或假设模型误差相关 **≥0.9828（n=30）/ ≥0.9981（n=6）**；后者未认证，不能先验假设。技术 wells/反馈量不能替代独立细胞系 n。
- **候选表全部不满足原 H_D3**：mean-only 6 reps/member 可使 mean MDE=.0914，但 rank MDE 仍 2.2875/0.7625；full-grid/partner-average mean pass、rank fail；因此不选“最低成本”方案，也不换 primary。

## 2. v0.1 MDE 单位错误（已修）

| 项 | v0.1 错误 | v0.2 修正 |
|---|---|---|
| 单元 | 单 anchor 2 members ×4 reps=8 wells | 保留；Δ var=2σ²/4=σ²/2 |
| SE_unit | 误用 full-grid σ/√32=0.0251494 | **σ/√2=0.0978960**（σ=.1384458） |
| MDE80 (n_eff=6) | 0.0287644（错误 prior pass） | **0.1119678**（batch1 target）/0.1150578（all-batches） |
| 判定 | 误判 pass | **MDE>δ_min → design_invalid: precision_insufficient** |

ON2-EX 的 full-grid se_unit 不能套到单 anchor；v0.2 不再使用 0.02876 作为 D3 prior pass。

## 3. rank-level 功效

- **Primary**：H_D3 `Δρ=ρ(U_conflict)−ρ(C2)≥0.10`；per-fold Δρ 为主口径（pooled 需每折 z 标准化，n_eff=30 保守）。
- **保守 MDE_rank**：`2.801585×sqrt(2/(n_eff−3))`：n=6 → 2.2875；n=30 → 0.7625；均 >δ。
- **所需独立细胞系**：n≈**1,573**（独立误差）；O'Neil target30 只有 30；技术重复/反馈包不能增加独立细胞系 n。
- **所需误差相关**：n=30 ≥.9828；n=6 ≥.9981；未认证，不能先验假设。
- **null/bootstrap**：N1/N2 只回答“CI 是否排除 0”；不替代 rank MDE；rank gate 必须独立预注册。

## 4. 候选聚合/加 wells（全部失败）

| id | 方案 | mean MDE | mean | rank MDE | rank | plate-eq* |
|---|---|---|---|---|---|---|
| A | 单 anchor 4 reps（8 wells/unit） | 0.111968 | ❌ | 2.2875 | ❌ | 11.0 |
| B | 单 anchor 4 reps，pooled30 | 0.050074 | ✅ | 0.7625 | ❌ | 11.0 |
| C | partner-dose 平均（32 wells/unit） | 0.055984 | ✅ | 2.2875 | ❌ | 44.0 |
| D | full 4×4 grid（128 wells/unit） | 0.027992 | ✅ | 2.2875 | ❌ | 176.0 |
| E | 单 anchor 6 reps（12 wells/unit） | 0.091421 | ✅ | 2.2875 | ❌ | 16.5 |
| F | full grid，pooled30 | 0.012518 | ✅ | 0.7625 | ❌ | 176.0 |

*模拟采购预算（5 folds，含 10% failure；query=0），不是湿实验报价；目标 held-out 数据来自已有资源；增加 target reps 另计。**没有候选 overall pass；不挑最低成本方案。**

## 5. ON3 non-blind / inherited peek 披露

- D3 与 ON3 共用 O'Neil complete-case；ON3 实现方已见 `tmp/on3_exec_quick_debug.invalid.json`（`39868CE4…`）的 primary/results：Δρ mean **0.0277068**、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5、verdict design_invalid。
- 规范披露：`PEEK_DISCLOSURE_ON3.md` `B4CAD955…`；ON3 有效执行 **non-blind/peeked**。
- **D3 是 non-blind/inherited-peek**：设计写于 ON3 QUICK 之后；**未用** ON3 QUICK primary/results 选择 D3 方向/阈值/切分/反馈预算/对照/指标；但**不得称 blind/独立确认/预注册确认**。若未来重开，结论必须附 peek 披露。

## 6. 强基线 / primary 固定

- 删除结果依赖的 **“U_conflict − best ordinary control”**；固定 primary = **U_conflict vs C2 full-history retrain**；其余 secondary/描述性、预指定多重性。
- 补 BRIEF 强基线：**C7** fully-tuned tree/GBM（depth 2/3/5、leaf 20/50/100、lr .05/.1、iter 200/500，nested CV）；**C8** matrix completion/low-rank；**C9** direct response prediction（预注册 feature contract）；**C10** exact closure where applicable；C0–C6 保留。
- 所有 arm 同数据/特征/反馈/调参 trials/seed/compute cap；不得给 U_conflict 额外信息。

## 7. 反馈 pack / 成本 / 失败树

- **k=24 units/fold（120 total），1 轮，no acquisition**；每 support cell 1 unit；strata=cell line/partner/member-pair/anchor；seed=20261130；hash rank、去重、配额/fallback；10% reserve 同 stratum 替换（response-independent）；held-out cell 不进 pack。
- **8 wells/unit / 11.0 plate-eq = 模拟采购预算**（不是真实湿实验）；base 24×8=192 wells=2 plates/fold；10% failure→2.2/fold；query=0。
- **compute cap**：调参≤20 trials、inner CV 5、3 seeds、≤2 CPU-h/arm；N1/N2 各 1,000×5 folds×arms；超限→design_invalid: compute_budget_exceeded；不得换便宜分析。
- **唯一失败树**：`design_invalid: precision_insufficient`（mean/rank MDE>δ）→停止；`design_invalid: leakage/endpoint`→停止；`evaluation_cannot_distinguish`（CI 含0/不能分辨δ）；`no_increment`（门过、点<δ且CI排除0/等效）；`development_increment_present`（全过，仅开发性）；`no_generalization`（只反馈点改善）；`data_unavailable`（资源失败；当前不是）。

## 8. 建议

- **D3 当前停止**：不提交 Lead 批准执行协议；不把 v0.1 的 0.02876 当 prior pass。
- 若 Lead 要改变问题（如 **mean-Δ primary**、full-grid/partner-average），必须**新预注册 + 重新挑战**；不能把本修订包装成原 H_D3 的“修订后可行”。
- 若坚持 rank primary，需外部队列 ~1,573 独立细胞系或可认证的 ≥.9828 模型误差相关；本资源无法满足；当前不运行。
- 不称独立确认/迁移/决策收益/机制/新颖性；技术重复≠独立培养；O'Neil 仅开发性；batch3 全失/702 pair-cell/无双药参照/单 anchor 派生等限制不变。
