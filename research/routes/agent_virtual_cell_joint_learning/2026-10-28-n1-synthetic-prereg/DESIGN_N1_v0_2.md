# DESIGN_N1_v0_2 —— R203-N1.1 执行设计（非静态 S-add + plan-pair conflict；修正版预注册，不运行效果）

2026-10-28。修正 v0.1（[DESIGN_N1.md](DESIGN_N1.md) `8FAAC491…`，保留不改）。依据：N1-C1 挑战（5 必改）、[PROBLEM_N1_v0_2.md](PROBLEM_N1_v0_2.md)、`generator_n1_v0_2.json`、R203-P1 链。
**状态：预注册草案 v0.2（未执行效果）。N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本文件不含效果结论。**

## 0. 修正摘要

| 必改 | v0.2 落实 |
|---|---|
| ① n_units/MDE | **n_units=300 冻结**（全部文件唯一值）；`MDE80=2.801585·SD/√n_eff`，`n_eff=n_units/deff=136.36`；SD=.20→**MDE80=0.0480≤.05**；n_req(cluster)=**278≤300**；不再用 360 |
| ② G1 FPR | LRT χ²_df=3、crit=7.8147、α=.05；**n_mc=20,000**；**PASS ⇔ point≤α+mc_tol（.00308）且 Wilson upper≤.075**；实际 G1 结果由脚本计算，`chosen_amplitudes_meet_gates` 由**实际** G1/G2 决定；失败→`calibration_failed`/`rename_static_Sadd` |
| ③ gauge/Jacobian | **full-h 参数化**：params=**359**、obs=**288**；显式有限差分 Jacobian；**gauge=加性 S=3 + 交互 126=129**；rank/nullity 由脚本重算并与 gauge 一致性核对；G3 基于 full 参数化 |
| ④ V4 | 预注册执行前 gate：static vs nonstatic ELPD（held-out T_hold=2、n_rep=200、seed=20261061、SE=sd/√200、判定 mean ΔELPD≥2SE 且 CI lower>0）；失败→`rename_static_Sadd` |
| ⑤ real pilot | **真实 generator + 7 方法（含 B2）** pilot（n_units=20、R=2、T=6）测 wall/CPU/内存并投影 main；**B2 等价审计**（same initial data hash/menus/query count/prior/tuning/seed）；G7 用实测投影；caps 1800 s/2 h/8 GB/0 wells |

## 1. 冻结对象（v0.2）

- **n_units=300**；S=3、π0~Dirichlet、T=6（fit 4 / held-out 2）、m=5、plans=12（A=3×B=4）、4×4 剂量、σ=.15、f/g 三基、h 两活跃基（double-centered）、state-specific β_s/γ_s 转移。
- **GT-static**（S=1,β_s=γ_s=0,h=0）→ G1 FPR 校准；**GT-nonstatic**（S=3,β_s/γ_s≠0,h≠0,Δ_f/σ=2）→ G2 power、V4、效果。
- 主终点：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`，δ=.05 normalized；U∈[0,1]（control/floor 归一化）；菜单 m=5；held-out 轮不更新；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- 预算：n_units=300、R=50、methods=7、T=6；wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only。

## 2. 立项前预检（先于效果）

1. **headroom**：GT-nonstatic 设计目标 0.10 ≥δ=.05；GT-static≈0；执行前 calibration pilot 估 headroom/SD(D)。
2. **MDE**：`MDE80=2.801585·SD(D)/√n_eff`；n_eff=136.36；SD=.20→**0.0480≤.05**；n_req(cluster)=278≤300；SD=.30→623>300（则 precision_insufficient）。
3. **预检不通过**：headroom<δ→`unreachable_gate`；MDE>δ 或 n_req>300→`precision_insufficient`；不降 δ、不静默加 n、不换端点（近满分另立 budget-to-target E5）。

## 3. 可辨识性/gauge（v0.2 执行前 gate）

- **参数化**：f 27 + g 36 + h（2 活跃基 per (pair,state)；full 12-pair 时 72）+ transition 8。
- **重算（显式有限差分 Jacobian，代码在 `generator_n1_v0_2.py`）**：
  - compact 6-pair（v0.1 代表设计）：params **107**、obs **312**、rank **95**、nullity **12**（含加性参数 gauge=3；其余 9 为 6-pair/2-basis 结构冗余，非执行设计）。
  - **full 12-pair（执行宇宙）**：params **143**、obs **600**、rank **140**、nullity **3 = 加性参数 gauge** → 可辨识维 **140**；与 gauge 一致。
- **gauge 区分**：参数空间加性 gauge = **S=3**（full nullity=3 解释）；函数空间交互加性冗余 = **(2K−1)·pairs·S**（compact 6-pair=126，加性 3 合计 **129**；full 12-pair=252，合计 255），不作为参数方向；离散状态标签 S! 由 Var 排序固定。
- **G3**：基于 full 12-pair 重算（rank140/nullity3）；恢复门：状态核差相关≥.90、transition TV≤.10、β_s/γ_s 95% CI 不含 0、interaction 相关≥.90；恢复只在可辨识子空间（140 维）判定；目标量不可辨识→`design_invalid: nonidentifiable`。

## 4. V4（执行前 gate；冻结规则）

- static S-add（ridge）vs nonstatic（state-dependent filter）；GT-nonstatic n_rep=**200** 独立数据集；fit T_fit=4 轮，**ELPD 仅 T_hold=2 held-out 轮**。
- per replicate `ΔELPD=ELPD_nonstatic−ELPD_static`；`SE=sd/√200`；seed=**20261061**。
- **PASS ⇔ mean ΔELPD>0 ∧ mean≥2SE ∧ 95% CI lower>0**；失败→`design_invalid: rename_static_Sadd`；**V1–V4 全 PASS 才进入效果**。

## 5. 方法/基线（等 compute/query；B2 等价审计）

- 统一：同 prior、同 initial data、feedback/round=1、query T=6、调参≤20 配置、同特征信息、同 seed/wall。
- **B1 full retrain；B2 static S-add（关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method**。
- **B2 等价审计**（pilot 与 N1 执行均记录）：same initial-data hash、same menus/round、same query count、same prior、same tuning budget、shared generator seed；失败→`design_invalid: generator_misspecified`；任何基线等预算等效→`no_increment`（撤算法主张）。

## 6. 校准/资格门 G1–G7 + V4（先于效果；失败只写 design_invalid）

| 门 | 规则 | 失败类别 |
|---|---|---|
| G1 | GT-static FPR：χ²_3 crit=7.8147，n_mc=20,000，point≤α+mc_tol(.00308) 且 Wilson upper≤.075；**实际值**决定 PASS | `calibration_failed`/`rename_static_Sadd` |
| G2 | GT-nonstatic power（state/interaction/history）≥.80−mc_tol | `calibration_failed` |
| G3 | §3 可辨识/参数恢复 | `nonidentifiable` |
| G4 | 无泄漏（held-out/特征/menus/same histories） | `leakage` |
| G5 | 两跑逐字节 | `design_invalid` |
| G6 | schema/失败模板 | `design_invalid` |
| G7 | **真实 pilot 投影** ≤caps | `compute_budget_exceeded` |
| V4 | §4 ELPD gate | `rename_static_Sadd` |

## 7. 失败类别/停止（统一）

`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。任一失败：停止，不报 regret/效果。

## 8. 真实 pilot/预算/运行

- **pilot**：真实 generator + 7 方法（含 B2），n_units=20、R=2、T=6；**实测 per-replicate 0.0282 s、投影 main（300 units×50 reps）≈12.7 s、内存 0.038 GB**；逐方法计时见 timing JSON；**B2 等价审计 PASS**（same initial-data hash/menus/query counts/prior/tuning/seed）；`timing_n1_pilot_v0_2.json`。
- **主预算**：n_units=300、R=50、methods=7、T=6、每轮 1 反馈；caps wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only；不使用 A/B 资源；两跑逐字节；结果 JSON 无 telemetry。
- **两跑/schema**：同 seed 两跑结果 JSON 逐字节一致；schema 字段与失败模板预注册；telemetry 单独文件。
- **任何 N1 效果执行**：须另立执行预注册 + 独立挑战 + Lead 批准；本文件不运行。

## 9. 批准清单

1. v0.2 5 必改落实（n_units=300/MDE .0480；G1 MC 规则与实际值；full 参数化 gauge 129；V4 规则；真实 pilot+B2 审计）。
2. 生成器/两套 GT/V1–V4/`rename_static_Sadd`；可辨识与参数恢复门。
3. 主终点/U/regret/菜单/held-out/δ=.05；headroom+MDE preflight（n_req 278≤300）；不静默换端点。
4. B1–B6 等预算 + B2 等价审计；G1–G7/V4；失败类别/停止；真实 pilot 预算 caps。
5. 机制账边界：不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复停止实验；不改旧判定；0 wells。
