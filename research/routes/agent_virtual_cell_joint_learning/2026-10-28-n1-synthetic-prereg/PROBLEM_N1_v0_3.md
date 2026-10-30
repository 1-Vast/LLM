# PROBLEM_N1_v0_3 —— R203-N1.2：非静态 S-add 合成机制预注册（v0.3 修正；设计，不运行效果）

2026-10-28。对象：R203-N1（机制账）。本文件修正 v0.2（[PROBLEM_N1_v0_2.md](PROBLEM_N1_v0_2.md) `C66FD8F4…`，保留不改）。依据：N1.1-C1 复核（revise，5 必改）、[challenge_N1_v0_2.md](challenge_N1_v0_2.md)、R203-P1 链。
**状态：设计/预注册草案 v0.3；未运行任何效果比较/结论；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；0 wells/compute-only。**

## 0. 5 必改落实（v0.2 → v0.3，按 N1.1-C1）

| # | v0.2 残留问题 | v0.3 修正（实测/冻结） |
|---|---|---|
| ① **full-h 参数摘要两套维数** | PROBLEM §1/DESIGN §0 仍写 full params=359/obs=288/gauge129（v0.1 残留），与 §3/JSON 的 143/600/140/3 冲突 | **全文统一**：实际参数化 = f27+g36+h（2 活跃基 per (pair,state)；compact 36/full 72）+transition 8。**compact 6-pair：params 107/obs 312/rank 95/nullity 12**（参数 gauge 3+结构冗余 9）；**full 12-pair（执行宇宙）：params 143/obs 600/rank 140/nullity 3（参数 gauge=3）**；**函数空间冗余单列：compact 3+126=129 / full 3+252=255**；不再出现 359/288/gauge129 作为 full 摘要；G3 只依 full 143/600/140/3 |
| ② **pilot 文本 vs telemetry 不一致** | 文本 .0282/12.7/.038 与 timing JSON 实际不符 | **统一引用 canonical telemetry（`timing_n1_pilot_v0_2.json`，v0.3 冻结快照 `timing_n1_pilot_v0_3.json`）**：per-replicate **0.02603 s**、projected main **11.72 s**、memory **0.037 GB**；逐方法 s：**B1 .00109 / B2 .00133 / B3 .001 / B4 .01731 / B5 .00083 / B6 .00139 / M .00308**；G7/预算一律引用同一 snapshot；v0.2 的 .0282/12.7/.038 废弃 |
| ③ **G1 point 门放宽** | v0.2 允许 point≤α+mc_tol=.05308 | **收紧为 point≤.05 且 Wilson 95% upper≤.075**；实际 **point=.0488**（976/20000）**PASS**、Wilson=.05187；`mc_tol=.00308` **仅作 CI/敏感性说明**，不作为 point 放宽；G1 失败→`calibration_failed`/`rename_static_Sadd` |
| ④ **V4 未实际运行** | v0.2 仅规则，pass="to be measured" | **V4 已实际运行**（pre-effect calibration）：200 reps、seed=20261061、T_hold=2、static ridge vs **nonstatic filter（soft state responsibilities/weighted ridge）**；**mean ΔELPD=306.1577、SE=65.4612、95% CI=[177.856, 434.459] → PASS**（mean>0 ∧ mean≥2SE ∧ CI lower>0）；失败路径仍为 `design_invalid: rename_static_Sadd`、不进入效果 |
| ⑤ 其余冻结 | — | **n_units=300/MDE80=.04798/n_req278、G2 power、B1–B6 等预算、B2 等价审计、caps 1800 s/2 h/8 GB/0 wells、边界/两跑/schema/失败类别不变** |

## 1. 与已停止静态 S-add 的实质区别（不变）

- 静态 S-add（A 线对象）：`y=f_a(d_a)+g_b(d_b)+ε`；无状态/历史/共享动态核/conflict。N1 在 `S=1,P=I,β_s=γ_s=0,h=0` 时**严格退化**为它。
- N1 非静态生成：S=3 隐藏状态；state-specific 历史/动作依赖转移（β_s=[−1.5,0,1.5]、γ_s=[1,−1,0]）；计划对共享同一轮 state；状态依赖 f/g/h（plan-pair conflict）；一次反馈统一修订；held-out decision regret 终点。
- **V1–V4 + `design_invalid: rename_static_Sadd`**：V1 状态可检测（Δ_f/σ≥2、power≥.80）；V2 历史/动作依赖（KL≥.10、β_s/γ_s CI 不含 0）；V3 plan-pair conflict（E_h≥.20、power≥.80）；**V4 已实测 PASS**（§4）。任一失败即停。

## 2. 生成器冻结（v0.3）

| 组件 | 冻结值 |
|---|---|
| **n_units** | **300（单一值；全部文件一致，无 360）** |
| 隐藏状态 | S=3；π0~Dirichlet(1,1,1)；标签按 Var(f) 降序固定 |
| 序列 | T=6（fit 4 / held-out 2）；每轮 1 反馈；state-specific 转移 |
| 计划/菜单 | universe 12 plans（A=3×B=4）；菜单 m=5；每轮 1 pair window |
| 剂量/噪声 | 4×4 归一化剂量网格；σ=.15 |
| 算子 | f/g 三基；h 两活跃基（double-centered）；状态依赖 |
| ground-truths | GT-static（S=1,β=γ=0,h=0）→ G1；GT-nonstatic（S=3,β_s/γ_s≠0,h≠0,Δ_f/σ=2）→ G2/V4 |
| 泄漏防护 | held-out 不更新；特征无 hidden state；菜单独立；same prior/initial data |
| pilot telemetry | canonical v0.2 real-pilot snapshot（实现未变）：**per-rep .02603 s、main 11.72 s、memory .037 GB**；逐方法见 §7 |

## 3. 可辨识性/gauge（v0.3 统一，唯一一套维数）

- **参数化**：f 27 + g 36 + h（2 活跃基 per (pair,state)；compact 36、full 72）+ transition 8；显式有限差分 Jacobian 代码在 `generator_n1_v0_3.py`。
- **compact 6-pair（v0.1 代表设计，非执行）**：params **107**、obs **312**、rank **95**、nullity **12**（参数 gauge 3 + 结构冗余 9）。
- **full 12-pair（N1 执行宇宙）**：params **143**、obs **600**、rank **140**、nullity **3 = 参数 gauge 3** → 可辨识维 **140**。
- **gauge 区分**：参数空间加性 gauge = **S=3**（full nullity=3 解释）；函数空间交互加性冗余 = `(2K−1)·pairs·S`：compact **126**（+3=**129**）、full **252**（+3=**255**）；在 2-basis h 下不作为参数方向；离散状态标签 S! 由 Var 排序固定。
- **G3（只依 full 143/600/140/3）**：参数恢复门：状态核差相关≥.90、transition TV≤.10、β_s/γ_s 95% CI 不含 0、interaction 相关≥.90；只在可辨识子空间（140 维）判定；目标量不可辨识→`design_invalid: nonidentifiable`。

## 4. V4 实际运行（pre-effect gate；已 PASS）

- **模型**：static S-add ridge vs nonstatic state-dependent filter（soft state responsibilities + weighted ridge）；**held-out 仅 T_hold=2 轮**；GT-nonstatic **200 reps、seed=20261061**。
- **规则**：`ΔELPD=ELPD_nonstatic−ELPD_static`；`SE=sd/√200`；PASS ⇔ mean ΔELPD>0 ∧ mean≥2SE ∧ 95% CI lower>0。
- **实测**：**mean ΔELPD=306.1577**、**SE=65.4612**、**95% CI=[177.856, 434.459]**、**PASS**；分位 p5 −861.3 / p50 206.3 / p95 1502.7。
- **失败路径**：若 FAIL → `design_invalid: rename_static_Sadd`，不进入效果；本 v0.3 已 PASS，V1–V4 全 PASS 才可进入效果（执行仍须另立预注册+批准）。

## 5. 主终点/headroom/MDE（v0.3 统一）

- **Primary**：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`（lower better）；δ=**0.05** normalized；菜单 m=5、U∈[0,1]、held-out 仅评价；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- **MDE**：`MDE80=2.801585·SD(D)/√n_eff`，`n_eff=n_units/deff`；deff=2.2（m=5,ICC=.30）；n_units=**300** → n_eff=**136.36**；SD=.20 → **MDE80=0.04798≤.05**；n_req=**278≤300**。
- **headroom**：GT-nonstatic 设计目标 0.10≥δ；GT-static≈0；headroom<δ→`unreachable_gate`；近满分→另立 budget-to-target；**不静默换端点/不降 δ**。

## 6. 等 compute/query 基线 + B2 等价审计

统一 prior/初始数据/feedback（每轮 1 次）/query T=6/调参≤20/特征信息/seed/wall：**B1 full retrain；B2 static S-add（关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method**。
**B2 等价审计 PASS**（canonical pilot）：same initial-data hash、same menus/round、same query count=6、same prior、same tuning=20、shared generator seed；任何基线等预算等效→`no_increment`（撤算法主张）；审计失败→`generator_misspecified`。

## 7. 资格门/失败类别/预算（v0.3）

- **G1**：point=.0488≤.05、Wilson upper=.05187≤.075 → **PASS**（mc_tol=.00308 仅敏感性）；失败→`calibration_failed`/`rename_static_Sadd`。
- **G2**：state/interaction/history power=1.000/1.000/1.000 → PASS。
- **G3**：full 143/600/140/3 + 参数恢复门。
- **G4** 无泄漏；**G5** 两跑逐字节；**G6** schema；**G7** 预算（canonical pilot：per-rep .02603 s、main 11.72 s、memory .037 GB ≤caps 1800 s/2 h/8 GB）→ PASS。
- **V4**：实测 PASS（§4）。
- **失败类别统一**：`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`；失败只写 `design_invalid`、不报 regret/效果。
- **预算**：main n_units=300、R=50、methods=7、T=6；wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only；两跑/schema/无 telemetry（结果 JSON）。

## 8. 边界

机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不恢复停止实验；不改旧门槛/判定；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本文件不运行效果。
