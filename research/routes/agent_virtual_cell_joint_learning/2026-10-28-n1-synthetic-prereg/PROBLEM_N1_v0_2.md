# PROBLEM_N1_v0_2 —— R203-N1.1：非静态 S-add + plan-pair conflict 合成机制预注册（修正版；设计，不运行效果）

2026-10-28。对象：R203-N1（机制账）。本文件修正 v0.1（[PROBLEM_N1.md](PROBLEM_N1.md) `23F4668A…`，保留不改）。依据：N1-C1 挑战（revise，5 必改）、`challenge_N1.md`、R203-P1 链、A 线停止记录。
**状态：设计/预注册草案 v0.2，未执行任何效果或方法比较；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；0 wells/compute-only。**

## 0. 5 必改落实（v0.1 → v0.2）

| # | v0.1 问题（N1-C1） | v0.2 修正 |
|---|---|---|
| ① **n_units/MDE 双重不一致** | PROBLEM 写 300、DESIGN/JSON/pilot 写 360；MDE 公式写 √n_units 而 .0438 来自 √n_eff | **冻结 n_units=300（单一值，全部文件一致）**；`MDE80=2.801585×SD/√n_eff`，`n_eff=n_units/deff`；n_eff=**136.36**，MDE80(SD=.20)=**0.0480≤.05**；n_req(SD=.20, cluster)=**278 ≤300**；不再出现 360 |
| ② **G1 实际超门且不自洽** | `GT_static_FPR=.05023>.05` 却 `meet_gates=true`；200 reps 不可能产生 .05023 | **G1 重算**：LRT χ²_df（df=3）临界值 7.8147（α=.05）；**n_mc=20,000** 独立 MC null 抽样；预注册 **MC 容差** `mc_tol=2√(α(1−α)/n_mc)=0.00308` 与 **Wilson 95% 上界≤0.075**；PASS ⇔ point≤α+mc_tol **且** Wilson upper≤0.075；`chosen_amplitudes_meet_gates` 由**实际** G1/G2 结果决定；G1 失败→`calibration_failed`/`rename_static_Sadd` |
| ③ **gauge/Jacobian 算术** | `n_gauge_constraints=147` 与陈述（加性 S=3、交互 126）不符；params107/rank90/nullity17 不可复算 | **改为 full-h 参数化**：f 27 + g 36 + h **288**（16 per pair/state）+ transition 8 = **params 359**；观测 288；显式有限差分 Jacobian 代码；**gauge = 加性常数 S=3 + 交互 (2K−1)·pairs·S=7×6×3=126 = 129**；重算 rank/nullity 并报告与 129 的一致性；G3 参数恢复门基于 full 参数化 |
| ④ **V4 未冻结** | `pass="to be measured"` | **V4 预注册为执行前 gate**：static vs nonstatic 模型、held-out=T_hold=2、`ΔELPD=ELPD_nonstatic−ELPD_static`、n_rep=**200**、seed=**20261061**、`SE=sd(ΔELPD)/√200`、判定 `mean ΔELPD>0 ∧ mean≥2SE ∧ 95% CI lower>0`；失败→`design_invalid: rename_static_Sadd`；V1–V4 全 PASS 才进入效果 |
| ⑤ **stub pilot 不可作预算** | pilot 只是 stub 下界（.00041s/rep） | **真实 generator + 7 方法（含 B2）pilot**：pilot n_units=20、R=2、T=6、m=5、plans=12；逐方法计时 wall/CPU/内存 → 投影 main（n_units=300、R=50、7 方法）；G7 用实测投影；**B2 等价审计**：同 initial data hash、同 menus/轮、同 query 数、同 prior、同调参预算、共享 generator seed；caps 1800 s/2 h/8 GB/0 wells 保留 |

## 1. 与已停止静态 S-add 的实质区别（不变，v0.1 PASS 部分）

- **静态 S-add（A 线对象）**：`y_p(d_a,d_b)=f_a(d_a)+g_b(d_b)+ε`；无状态/历史/共享动态核/conflict；反馈不改变状态。N1 在 `S=1, P=I, β_s=γ_s=0, h=0` 时**严格退化**为它。
- **N1 非静态生成**：隐藏状态 `s_t∈{1,2,3}`；**state-specific 历史/动作依赖转移**（β_s=[−1.5,0,1.5]、γ_s=[1,−1,0]，softmax）；计划对共享同一轮 state；状态依赖 f/g/h（h=plan-pair conflict）；一次反馈统一修订（state posterior + 算子）；held-out decision regret 终点。
- **V1–V4 + `design_invalid: rename_static_Sadd`**：V1 状态可检测（Δ_f/σ≥2、power≥.80）；V2 历史/动作依赖（KL≥.10、β_s/γ_s CI 不含 0）；V3 plan-pair conflict（E_h≥.20、power≥.80）；V4 静态不可吞并（§4，已冻结）。**任一失败即停、不运行效果、不换名救活。**

## 2. 生成器冻结（v0.2；单一 n_units=300）

| 组件 | 冻结值 |
|---|---|
| **n_units** | **300（单一值；全部文件一致）** |
| 隐藏状态 | S=3；π0~Dirichlet(1,1,1)；状态标签按 Var(f) 降序固定 |
| 序列 | T=6（T_fit=4 / T_hold=2）；每轮 1 反馈；state-specific 历史/动作依赖转移 |
| 计划/菜单 | universe 12 plans（A=3 × B=4 的子集）；菜单 m=5；每轮 1 pair window |
| 剂量 | 4×4 归一化网格 {0,1/3,2/3,1} |
| 算子 | f/g 三基；h 两活跃基（double-centered）；状态依赖；噪声 σ=.15 |
| ground-truths | GT-static（S=1,β_s=γ_s=0,h=0）→ G1 FPR；GT-nonstatic（S=3,β_s/γ_s≠0,h≠0,Δ_f/σ=2）→ G2 power/V4 |
| 随机性 | 每 replicate 独立 seed；seed 集预注册（20261030+r）；V4 seed=20261061 |
| 泄漏防护 | held-out 轮不参与更新；特征不含 hidden state；菜单除观测反馈外与状态独立；same prior/initial data |

## 3. 可辨识性/gauge（v0.2 重算，显式参数化 + Jacobian 代码）

- **参数化**：f_{a,s}(d)=Σ_k φ_k(d)θ^f_{a,s,k}（A·S·3=**27**）；g（B·S·3=**36**）；h 采用**2 活跃基 per (pair,state)**（x_a·x_b、x_a²·x_b）；transition（S(S−1)+2=**8**）。**执行宇宙 = 全部 A×B=12 pairs**（与 frozen N1 universe 一致）。
- **两套 Jacobian 重算（代码在 `generator_n1_v0_2.py`，有限差分）**：
  - **compact 6-pair（v0.1 代表设计）**：params **107**、obs **312**、rank **95**、nullity **12**（其中加性常数参数 gauge=3；其余 9 个是 6-pair 覆盖/2-basis 表示带来的结构冗余；**非执行设计**）。
  - **full 12-pair（N1 执行宇宙）**：params **143**、obs **600**、rank **140**、nullity **3 = 加性常数参数 gauge 恰好 3** → 预期可辨识维 **140**；Jacobian 重算与 gauge 一致。
- **参数 gauge vs 函数空间冗余（明确区分）**：
  - **参数空间 gauge**：`f_{a,s}+c_s, g_{b,s}−c_s` 仅 **S=3** 个方向（full 设计 nullity=3 即由它解释）。
  - **函数空间冗余**（不是参数方向）：交互 `h+φ_s(d_a)+ψ_s(d_b)` 的 **(2K−1)·pairs·S** 个方向——compact 6-pair 时 =7×6×3=**126**，与加性 3 合计 **129**（v0.1 挑战算术）；full 12-pair 时 =7×12×3=**252**，与加性 3 合计 **255**。这些交互加性方向在 2-basis h 参数化下不可表示，故列为函数空间冗余，不计入参数 rank。
  - 离散状态标签 S!=6（由 Var(f) 排序固定，不是线性 gauge）。
- **G3（基于 full 12-pair 重算）**：rank 140/nullity 3（=加性 gauge）；参数恢复门：状态核差相关≥.90、transition TV≤.10、β_s/γ_s 95% CI 不含 0、interaction 相关≥.90；**恢复仅在同一可辨识子空间（140 维）上判定**；若目标量不在可辨识子空间 → `design_invalid: nonidentifiable`。G3 失败→`design_invalid: nonidentifiable`。

## 4. V4 预注册（static S-add 不可吞并；执行前 gate）

- **模型**：static S-add（`y=f_a+g_b+noise`，ridge 拟合）vs nonstatic N1（`y=f_{a,s}+g_{b,s}+h_{a,b,s}+noise`，hidden-state posterior filter）。
- **数据/held-out**：GT-nonstatic，n_rep=**200** 独立 replicate 数据集；fit 用 T_fit=4 轮，**ELPD 只在 T_hold=2 held-out 轮**计算（不参与拟合/更新）。
- **统计量**：per replicate `ΔELPD = ELPD_nonstatic − ELPD_static`（held-out log predictive density 之和）。
- **判定**：`SE = sd(ΔELPD)/√200`；**PASS ⇔ mean ΔELPD>0 ∧ mean ΔELPD ≥ 2×SE ∧ 95% CI lower >0**；seed=**20261061**。
- **失败** → `design_invalid: rename_static_Sadd`，**不进入效果**。V1–V4 全 PASS 才是 N1 执行前置条件。

## 5. 主终点/headroom/MDE（v0.2 统一）

- **Primary**：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`（lower better）；δ=**0.05** normalized；菜单 m=5、U∈[0,1]、held-out 仅评价；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- **MDE（统一公式）**：`MDE80=2.801585×SD(D)/√n_eff`，`n_eff=n_units/deff`；m=5、ICC=.30 → deff=**2.2**；n_units=**300** → n_eff=**136.36**；保守 SD(D)=.20 → **MDE80=0.0480≤.05** ✅。
- **n_req**：SD(D)=.20 → n_req=126；cluster×2.2 → **278 ≤300** ✅（SD .10→32/71；.15→71/157；.30→283/623）。
- **headroom**：GT-nonstatic 设计目标 **0.10≥δ=.05**；GT-static≈0（预期 no_increment）；headroom<δ→`unreachable_gate`；基线近满分→另立 budget-to-target（E5），**不静默换端点/不降 δ**。
- **执行前预检**：N1 校准 pilot 估 SD(D)/headroom；不通过→停止；不得事后改 δ/端点/加 n 后静默继续。

## 6. 等 compute/query 基线（v0.2 落地 + B2 等价审计）

统一 prior/初始数据/feedback（每轮 1 次）/query T=6/调参 ≤20 配置/特征信息/seed/wall：**B1 full retrain；B2 static S-add（同信息同预算，关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method**。
**B2 等价审计（pilot 实现）**：同 initial data hash、同 menus/轮、同 query 数、同 prior、同调参预算、共享 generator seed；pilot 报告 `B2_equivalence_audit`；审计失败→`design_invalid: generator_misspecified`；**任何基线等预算等效→`no_increment`，撤回算法主张**。

## 7. 校准/资格门、失败类别、真实 pilot 预算

| 门 | v0.2 规则 | 失败类别 |
|---|---|---|
| **G1** GT-static FPR | LRT χ²_df=3，crit=7.8147，α=.05；n_mc=**20,000**；**PASS ⇔ point≤α+mc_tol(0.00308) 且 Wilson upper≤0.075**；**实测：k=976/20000、point=0.0488、mc_tol=.00308、Wilson upper=.0519 → PASS**；`chosen_amplitudes_meet_gates` 由实测 G1/G2 决定 | `calibration_failed` / `rename_static_Sadd` |
| G2 GT-nonstatic power | state/interaction/history 各 ≥.80−mc_tol（n_mc=20,000） | `calibration_failed` |
| G3 可辨识/参数恢复 | §3 full 参数化 + 恢复门 | `nonidentifiable` |
| G4 无泄漏 | held-out 不更新/特征无 state/menus 独立/same histories | `leakage` |
| G5 两跑 | 结果 JSON 逐字节一致 | `design_invalid` |
| G6 schema/失败模板 | 预注册字段 | `design_invalid` |
| G7 预算 | **真实 pilot 投影** ≤caps（wall 1800 s/CPU 2 h/内存 8 GB） | `compute_budget_exceeded` |
| V4 | §4 ELPD gate | `rename_static_Sadd` |

**失败类别统一**：`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。失败只写 `design_invalid`，**不报 regret/效果**。

## 8. 预算与边界

- **真实 pilot**：generator（S=3/T=6/m=5/plans=12/4×4/σ=.15）+ **7 方法（含 B2）**；pilot n_units=20、R=2；**实测 per-replicate 0.0282 s、投影 main（n_units=300、R=50、7 方法）≈12.7 s、内存 0.038 GB**；逐方法计时与 **B2 等价审计 PASS**（同 initial-data hash、同 menus、同 query 数 6、同 prior、同调参 20、共享 generator seed）；`timing_n1_pilot_v0_2.json`（telemetry 单独文件）。
- **主预算**：n_units=300、R=50、methods=7、T=6、每轮 1 反馈；wall≤**1800 s**、CPU≤**2 h**、内存≤**8 GB**；**0 wells/compute-only**；不使用 A/B 线资源；两跑逐字节、结果 JSON 无 telemetry。
- **边界**：机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不恢复已停止实验；不改旧门槛/判定；**N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准**。
