# DESIGN_N1 —— R203-N1 执行设计（非静态 S-add + plan-pair conflict；机制账；预注册，不运行）

2026-10-28。依据：[PROBLEM_N1.md](PROBLEM_N1.md)（`23F4668A…`）、`generator_n1.json`（`8C676321…`）、`timing_n1_pilot.json`、R203-P1（`2026-10-28-decision-power-scope/`）、`DECISION_R203_P1_SCOPE.md`。
**状态：预注册草案（未执行）。N1 效果执行须先独立挑战 + Lead 批准；本文件不含任何效果结论。**

## 0. 范围与原则

- **机制账 only**：合成 ground-truth/噪声/可辨识/检测 power/FPR/参数恢复/合成决策 regret；不称药理、真实决策、迁移、机制、新颖性。
- **不是 A 线静态 S-add 检验的改名重做**：生成过程含隐藏状态转移/历史动作依赖/计划对共享动态核/plan-pair conflict；终点是 held-out decision regret，不是"矛盾存在性"检测。
- 0 wells、纯 compute；不用 A/B 线资源；不改旧判定/门槛；不晋升代码；不恢复已停止实验。
- 任何 generator/calibration 失败 → 停止，不报结果、不改 generator 救活。

## 1. 冻结对象（与 PROBLEM_N1 一致）

| 项 | 冻结值 |
|---|---|
| 隐藏状态 | S=3；π0~Dirichlet(1,1,1)；状态标签按 Var(f) 降序固定 |
| 序列 | T=6（fit 4 / held-out 2）；每轮 1 次反馈；transition state-specific 历史/动作依赖（β_s=[−1.5,0,1.5]、γ_s=[1,−1,0]） |
| 计划/菜单 | universe 12 plans（3 A drugs ×4 B drugs 的子集）；菜单 m=5；pair window 每轮 1 |
| 剂量 | 4×4 归一化网格 {0,1/3,2/3,1} |
| 算子 | f,g 三基函数；h 两活跃基（double-centered）；状态依赖；噪声 σ=.15 |
| ground-truths | **GT-static**（S=1,β=γ=0,h=0；静态 S-add 退化）用于 FPR 校准；**GT-nonstatic**（S=3,β/γ≠0,h≠0；Δ_f/σ=2）用于 power 校准 |
| 决策/效用 | 菜单 M_t（m=5），`U=(ȳ_control−ȳ_p)/(ȳ_control−ȳ_floor)∈[0,1]`；held-out regret `R_i=mean r_t`，`r_t=max U−U(â)` |
| 主终点 | paired `D_i=R_i(M)−R_i(B)`（lower better）；δ=**0.05** normalized；n_units=**360**、replicates R=**50**、methods=7 |
| 预算 | 合成 pilot 10 replicate；wall≤**1800 s**、CPU≤**2 h**、内存≤**8 GB**、0 wells |

## 2. 立项/执行前强制预检（先于任何效果）

### 2.1 rename_static_Sadd 检验（V1–V4；失败即 `design_invalid: rename_static_Sadd`，停止）

| # | 判据 | 阈值 | 本轮设计算术状态 |
|---|---|---|---|
| V1 状态可检测 | `min_{s≠s'}||f_{a,s}−f_{a,s'}||/σ ≥2.0` 且 LRT power≥.80 | 2.0 / .80 | 设计值 2.0；calibration power≈1.00（n_rep=200） |
| V2 历史/动作依赖 | `KL(P(·\|r,action flags)‖P(·)) ≥0.10` 且 β_s/γ_s 95% CI 不含 0 | 0.10 | 设计值 KL=**0.617** |
| V3 plan-pair conflict | `E_h=mean||h||²/σ² ≥0.20` 且 interaction power≥.80 | 0.20/.80 | 设计值 0.20；power≈1.00 |
| V4 静态不可吞并 | GT-nonstatic 下 static S-add 的 held-out ELPD 低 ≥2×SE | ΔELPD≥2SE | **N1 校准阶段实测**（先于效果） |

### 2.2 headroom + MDE preflight（先于效果；见 generator_n1.json）

- **MDE**：`MDE80=2.801585×SD(D)/√(n_eff)`；`n_eff=n_units/[1+(m−1)ICC]`；设计 m=5、ICC=.30 → deff=**2.2**；n_units=360 → n_eff≈163.6；保守 SD(D)=.20 → **MDE80≈.0438 ≤δ=.05** ✅。
- **n_req**：SD(D)=.20 → n_req=126；cluster×2.2 → **278 ≤360** ✅（SD .10→71；.15→157；.30→623）。
- **headroom**：`U_max−U0`；GT-nonstatic 设计目标 headroom≈**0.10 ≥δ=.05** ✅；GT-static headroom≈0（预期无增量）。
- **预检执行**：N1 校准阶段用 GT-nonstatic 的预注册 pilot 估 `SD(D)`、`headroom`；若 headroom<δ → `unreachable_gate`；若 SD 使 MDE>δ → `precision_insufficient`；**不降 δ、不加 n 后静默继续、不换端点**。基线近满分 → 另立 budget-to-target（E5）问题并新预注册。

## 3. 方法/基线（等 compute/query）

**统一规则**：同一 prior、同一初始数据（round-1 pair window）、同一 feedback 预算（每轮 1 次）、同一 query 数（T=6 轮）、同一调参预算（每方法 ≤20 配置、嵌套 CV 于同一数据）、同一特征信息（所有方法看到相同 histories；hidden state 不进入特征）、同一 wall/CPU cap；同 seed 集合。

| id | 方法/基线 | 更新/信息 | 备注 |
|---|---|---|---|
| M | **N1 method**：状态后验 + 一次反馈联合修订（f,g,h 状态依赖） | 每轮 1 次反馈，联合更新 state posterior + 算子 | 主方法 |
| B1 | full retrain（静态 S-add 全历史） | 每轮全历史重拟合；无状态 | 同预算 |
| B2 | **static S-add（同信息同预算）** | 仅静态 f+g；无状态/历史 | **关键强基线**；等效→撤算法主张 |
| B3 | hierarchical/EB | 随机效应部分池化 | 同更新次数 |
| B4 | GP | (a,b,d_a,d_b) GP 回归 | 同 query/调参预算 |
| B5 | random plan-pair | 随机选 pair 观测（无冲突定向） | 同预算 |
| B6 | decision AL | 基于不确定性的主动学习选 plan | 同预算 |

## 4. 终点/分析（预注册）

- **Primary**：`D_i=R_i(M)−R_i(B2)`（paired，per unit；lower better）；分析：cluster-robust paired mean（按 replicate/unit cluster），95% CI；**成功** ⇔ `mean ΔR ≤ −δ` 且 95% CI upper < 0；**no_increment** ⇔ CI 含 0 或 |ΔR|<δ；**inconclusive** ⇔ CI 不能分辨；不得事后改 δ/端点。
- **Secondary**（预指定 Holm）：mis-selection rate（paired risk difference）、state/history/interaction detection power/FPR、参数恢复（kernel 相关/transition TV/interaction 相关）、budget-to-target（E5，仅另立问题）。
- 描述性：按 state/轮次/菜单大小分层（不用于主判定）。

## 5. 校准/资格门（先于效果；失败只写 `design_invalid`，不报结果）

| 门 | 内容 | 阈值 | 失败类别 |
|---|---|---|---|
| G1 | GT-static 检测 FPR（误报非静态） | ≤α=.05 | `calibration_failed` / `rename_static_Sadd` |
| G2 | GT-nonstatic 检测 power（状态/历史/interaction；n_rep=200） | ≥.80 各项 | `calibration_failed` |
| G3 | 可辨识/参数恢复（状态核相关≥.90、transition TV≤.10、β/γ CI 不含 0、interaction 相关≥.90、gauge-fixed Jacobian 满秩） | 见 §PROBLEM §3 | `nonidentifiable` |
| G4 | 无泄漏（held-out 不更新、特征无 hidden state、菜单独立、same histories） | 审计 | `leakage` |
| G5 | 两跑逐字节一致（结果 JSON） | 是 | `design_invalid` |
| G6 | schema/失败模板 | 是 | `design_invalid` |
| G7 | 预算（pilot 投影 ≤caps） | wall≤1800 s/CPU≤2 h/内存≤8 GB | `compute_budget_exceeded` |
| V4 | static S-add 不可吞并（ELPD≥2SE） | 见 §2.1 | `rename_static_Sadd` |

**任一失败：停止，写 failure_category，不报 regret/其它效果数字。**

## 6. 失败类别/停止（统一）

`design_invalid: rename_static_Sadd`（V1–V4 任一）、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`（headroom<δ）、`precision_insufficient`（MDE>δ/n 不足）、`no_increment`（門通过但等效/CI 排除 δ）、`inconclusive`（CI 不能分辨）。**任何强基线（尤其 B2）等预算等效 → 撤回算法增量主张（`no_increment`），不称新颖性/决策收益。**

## 7. 预算与运行

- **pilot**：`timing_n1_pilot.json`（10 replicate stub：0.0005 s/rep、投影 main≈0.95 s、cap 1800 s）——**stub 仅为下界**；N1 执行前须用真实实现重跑 pilot 并冻结新的 wall 投影。
- **主预算**：n_units=360、R=50、methods=7、T=6、每轮 1 反馈；wall≤1800 s、CPU≤2 h、内存≤8 GB；**0 wells / compute-only**；不使用 A/B 线资源。
- 两跑逐字节一致（结果 JSON 无 telemetry；timing/telemetry 写单独文件）；schema 见 `generator_n1.json → endpoints/budget/failure_categories`。
- **任何效果执行须另立预注册 + 独立挑战 + Lead 批准**；本文件不运行。

## 8. 批准清单（建议 Lead/挑战者核对）

1. 与静态 S-add 的实质区别（状态转移/历史依赖/共享动态核/plan-pair conflict）与 V1–V4 rename_static_Sadd 判据（含 `design_invalid: rename_static_Sadd`）。
2. generator 冻结（S=3/T=6/m=5/plans=12/σ=.15/h 两基/β_s,γ_s/GT-static vs GT-nonstatic）与可辨识/gauge/参数恢复门。
3. 主终点定义（U/regret/归一化/菜单/held-out）、δ=.05、headroom+MDE preflight（n=360/deff=2.2/MDE .0438）与"不静默换端点"。
4. 等 compute/query 基线（B1–B6）及 B2 static S-add 关键强基线；统一 prior/初始数据/query/调参/feature。
5. 校准/资格门 G1–G7、失败类别/停止、两跑/schema/预算 caps。
6. 机制账边界（不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复已停止实验；不改旧判定）。
