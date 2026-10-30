# R203-N1.1（v0.2）报告：N1 预注册 5 必改修正（设计/算术/真实 pilot 计时；不运行效果）

2026-10-28。对象：R203-N1（机制账）。依据：N1-C1 挑战（revise，5 必改）、`challenge_N1.md`、R203-P1 链、A 线停止记录。
**只做设计/算术/真实 pilot 计时：未运行效果、未做方法比较、未读 O'Neil 响应、未用 A/B 线资源；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；0 wells/compute-only。**
- 修正问题定义：[PROBLEM_N1_v0_2.md](PROBLEM_N1_v0_2.md)（`C66FD8F4…`）
- 修正执行设计：[DESIGN_N1_v0_2.md](DESIGN_N1_v0_2.md)（`1B179AB9…`）
- 生成器/算术：[generator_n1_v0_2.py](generator_n1_v0_2.py)（`F1EFD8D8…`）→ [generator_n1_v0_2.json](generator_n1_v0_2.json)（`045DEE05…`）
- 真实 pilot 计时：[timing_n1_pilot_v0_2.json](timing_n1_pilot_v0_2.json)（telemetry；末次 `7F57BB1D…`）
- 记录/用量：[record_N1_design_v0_2.md](record_N1_design_v0_2.md)、[usage_N1_design_v0_2.json](usage_N1_design_v0_2.json)
- **v0.1 产物未改**（PROBLEM_N1/DESIGN_N1/generator_n1 等 SHA 保持）。

## 0. 5 必改落实（v0.1 → v0.2）

| # | N1-C1 致命点 | v0.2 落实（实测） |
|---|---|---|
| ① **n_units/MDE 双重不一致** | PROBLEM 300 vs DESIGN/JSON/pilot 360；MDE 写 √n_units 而 .0438 来自 √n_eff | **n_units=300 单一冻结（全部文件一致，无 360）**；`MDE80=2.801585·SD/√n_eff`，`n_eff=n_units/deff=136.36`；SD=.20 → **MDE80=0.04798≤.05**；n_req(SD=.20,cluster)=**278≤300** ✅ |
| ② **G1 超门且不自洽** | `.05023>.05` 却 `meet_gates=true`；200 reps 不可能产生 .05023 | **G1 重算 + 预注册 MC 规则**：χ²_3 crit=7.8147、α=.05、n_mc=**20,000**、**mc_tol=0.00308**、Wilson 95% 上界≤0.075；**实测 k=976/20000、point=0.0488、Wilson upper=0.0519 → PASS**；G2 powers=1.000/1.000/1.000（≥.80−mc_tol）；**`chosen_amplitudes_meet_gates` 由实测 G1/G2 决定**；G1 失败路径→`calibration_failed`/`rename_static_Sadd` |
| ③ **gauge/Jacobian 算术** | 147 vs 陈述 3+126=129；params107/rank90/nullity17 不可复算 | 显式参数化+有限差分 Jacobian（代码见脚本）：**compact 6-pair（v0.1 代表）params 107/obs 312/rank 95/nullity 12**（3 加性参数 gauge + 9 结构冗余，非执行设计）；**full 12-pair（执行宇宙）params 143/obs 600/rank 140/nullity 3 = 加性参数 gauge** → 可辨识维 140；**函数空间冗余：加性 3 + 交互 126=129（compact 6-pair）/252+3=255（full 12-pair）**；参数 gauge 与函数空间冗余明确分开 |
| ④ **V4 未冻结** | `pass="to be measured"` | **V4 冻结为执行前 gate**：static S-add vs nonstatic（state-dependent）模型；fit T_fit=4、**ELPD 仅 T_hold=2 held-out**；GT-nonstatic **n_rep=200**、seed=**20261061**；`ΔELPD=ELPD_nonstatic−ELPD_static`、`SE=sd/√200`；**判定 mean ΔELPD>0 ∧ mean≥2SE ∧ 95% CI lower>0**；失败→`design_invalid: rename_static_Sadd`；V1–V4 全 PASS 才进入效果 |
| ⑤ **stub pilot 不可作预算** | pilot 只是 stub 下界 | **真实 generator + 7 方法（含 B2）pilot**（n_units=20、R=2、T=6、m=5、plans=12）：**实测 per-replicate 0.0282 s、投影 main（300 units×50 reps×7 methods）≈12.7 s、内存 0.038 GB**；逐方法计时：B1 .0005 / B2 .00201 / B3 .0015 / B4 .01914 / B5 .00025 / B6 .0015 / M .00327 s；**B2 等价审计 PASS**（same initial-data hash、same menus/round、same query count=6、same prior、same tuning=20、shared generator seed）；caps 1800 s/2 h/8 GB/0 wells 保留；G7 用实测投影 |

## 1. 与已停止静态 S-add 的实质区别（v0.1 PASS，保留）

- 静态 S-add（A 线对象）在 `S=1,P=I,β_s=γ_s=0,h=0` 时是 N1 的**严格退化**；N1 生成含 S=3 隐藏状态、state-specific 历史/动作依赖转移（β_s=[−1.5,0,1.5]、γ_s=[1,−1,0]）、计划对共享动态核、状态依赖 f/g/h（plan-pair conflict）、一次反馈统一修订、**held-out decision regret** 终点。
- V1–V4 + `design_invalid: rename_static_Sadd`：V1 状态可检测（Δ_f/σ≥2、power≥.80）；V2 历史/动作依赖（KL≥.10、β_s/γ_s CI 不含 0）；V3 plan-pair conflict（E_h≥.20、power≥.80）；V4 见上。**任一失败即停、不运行效果、不换名救活。**

## 2. 可辨识性/gauge 重算（v0.2 关键修正）

- **参数化**：f 27 + g 36 + h（2 活跃基 per (pair,state)；compact 6-pair=36、full 12-pair=72）+ transition 8。
- **compact 6-pair（v0.1 代表设计）**：params **107**、obs **312**、rank **95**、nullity **12**（3 加性参数 gauge + 9 由 6-pair 覆盖/2-basis 结构造成的参数冗余；**非执行设计**）。
- **full 12-pair（N1 执行宇宙）**：params **143**、obs **600**、rank **140**、nullity **3 = 加性常数参数 gauge 恰好** → 可辨识维 **140**；重算与 gauge 一致 ✅。
- **gauge 区分**：参数空间加性 gauge=S=3（`f+c_s,g−c_s`）；函数空间交互加性冗余=(2K−1)·pairs·S = compact **126** / full **252**（与加性合计 **129 / 255**），在 2-basis h 下不作为参数方向；离散状态标签 S! 由 Var 排序固定。**G3 基于 full 12-pair 重算**；参数恢复只在可辨识子空间（140 维）判定；目标量不可辨识→`design_invalid: nonidentifiable`。

## 3. 主终点/headroom/MDE（v0.2 统一）

- **Primary**：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`（lower better）；δ=**0.05** normalized；菜单 m=5、U∈[0,1]、held-out 仅评价；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- **MDE 统一公式**：`MDE80=2.801585·SD(D)/√n_eff`，`n_eff=n_units/deff`；deff=2.2（m=5,ICC=.30）；n_units=**300** → n_eff=**136.36**；SD=.20 → **MDE80=0.04798≤.05** ✅；n_req=**278≤300** ✅（SD .10→71；.15→157；.30→623>300→precision_insufficient）。
- **headroom**：GT-nonstatic 设计目标 0.10≥δ；GT-static≈0；headroom<δ→`unreachable_gate`；近满分→另立 budget-to-target（E5）；**不静默换端点/不降 δ**。

## 4. 等 compute/query 基线 + B2 等价审计

统一 prior/初始数据/feedback（每轮 1 次）/query T=6/调参≤20/特征信息/seed/wall：**B1 full retrain；B2 static S-add（关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method**。
**B2 等价审计（真实 pilot 实现）**：same initial-data hash、same menus/round、same query count=6、same prior、same tuning=20、shared generator seed → **PASS**；任何基线等预算等效→`no_increment`（撤算法主张）；审计失败→`generator_misspecified`。

## 5. 资格门/失败类别/预算（v0.2）

- **G1** 实测 PASS（point .0488、Wilson upper .0519、mc_tol .00308）；**G2** powers 1.000/1.000/1.000 PASS；**G3** full 12-pair rank140/nullity3 + 参数恢复门；**G4** 无泄漏；**G5** 两跑逐字节；**G6** schema；**G7** 真实 pilot 投影（≈12.7 s ≤1800 s）；**V4** 冻结规则。
- **失败类别统一**：`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`；失败只写 `design_invalid`、不报 regret/效果。
- **预算**：真实 pilot（generator+7 方法含 B2）per-rep 0.0282 s、投影 main≈12.7 s、内存 0.038 GB；主预算 n_units=300、R=50、7 方法；caps wall≤1800 s、CPU≤2 h、内存≤8 GB；**0 wells/compute-only**；两跑/telemetry 分开。

## 6. 边界

机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不恢复停止实验；不改旧门槛/判定；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本任务不运行效果。

## 7. 产物/确定性/SHA

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_v0_2.md` | `C66FD8F43BBD54F26C60DBDC35A94285E3B882B7ABC7ACE8D052B270259D81D6` |
| `DESIGN_N1_v0_2.md` | `1B179AB9AE44143C54C6FBC80A54F538DED43D594F855DCDD7EF516FED69BEE3` |
| `generator_n1_v0_2.py` | `F1EFD8D8C749AAB5EB36A5E5A99B2F9BF76091F3B3988B0BD39843AF7CE1864A` |
| `generator_n1_v0_2.json` | `045DEE0575C7AC2DCCCDCDEE40FD018156D6F983FE54C2EC7B757C754CA9CFBE` |
| `timing_n1_pilot_v0_2.json` | telemetry（多次运行可变；末次 `7F57BB1D…`） |
| report/record/usage | 见 `usage_N1_design_v0_2.json` |

**确定性**：`generator_n1_v0_2.json` 两跑逐字节一致（`045DEE05…`）；结果 JSON 不含 pilot 实测时间（仅 pass + 指向 timing 文件）；JSON 键排序/无时间戳/allow_nan=False。

## 8. 建议

1. **提交 v0.2 修正预注册做独立复核/再挑战**；重点：① 单一 n_units=300/MDE .04798/n_req278；② G1 MC 容差规则与实测 .0488/Wilson .0519；③ 参数化/gauge（参数 gauge 3 vs 函数空间 129/255；full 12-pair rank140/nullity3）；④ V4 ELPD 规则；⑤ 真实 pilot 12.7 s/0.038 GB 与 B2 等价审计。
2. 复核通过后请 Lead 批准 **N1 执行预注册**（仅合成机制账；不批效果外推/药理）；N1 效果执行另立预注册 + 独立挑战 + Lead 批准。
3. **不做**：效果比较/结论、代码晋升、旧判定修改、合成升级为药理。
