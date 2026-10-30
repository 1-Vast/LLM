# R203-N1 报告：非静态 S-add + plan-pair conflict 合成机制预注册（设计，不运行效果）

2026-10-28。角色：独立设计/审计员（未参与 R197/R200/203 模型开发）。任务 task-130（R203-N1，机制账）。
**只做设计/算术/合成 pilot 计时：未运行效果、未做方法比较、未读 O'Neil 响应、未用 A/B 线资源；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛。**
- 问题定义：[PROBLEM_N1.md](PROBLEM_N1.md)（`23F4668A…`）
- 执行设计：[DESIGN_N1.md](DESIGN_N1.md)（`8FAAC491…`）
- 生成器/校准算术：[generator_n1.py](generator_n1.py)（`F509708E…`）→ [generator_n1.json](generator_n1.json)（`21BA30AA…`）
- 计时：[timing_n1_pilot.json](timing_n1_pilot.json)
- 记录/用量：[record_N1_design.md](record_N1_design.md)、[usage_N1_design.json](usage_N1_design.json)
- 依据：R203-P1（`2026-10-28-decision-power-scope/`）、`DECISION_R203_P1_SCOPE.md`、A 线 C192–C195 停止记录；**未改 A/B/D 线与 R203-P1 产物**。

## 0. 一句话

在**已知 ground-truth 的合成非静态 S-add + plan-pair conflict** 环境中，验证"一次反馈的统一修订（状态后验 + 状态依赖 f,g,h）"能否在 held-out **decision regret** 上优于**等 compute/query** 基线；**primary δ=.05 normalized**；本任务仅预注册，不运行效果。

## 1. 与已停止静态 S-add 的实质区别（不是改名）

- **静态 S-add（A 线对象，退化特例）**：`y_p(d_a,d_b)=f_a(d_a)+g_b(d_b)+ε`；无状态、无历史、无 plan-pair 共享动态核、无 conflict、反馈不改变状态。N1 生成过程在 `S=1, P=I, β=γ=0, h=0` 时**严格退化**为它。
- **N1 非静态过程**：隐藏状态 `s_t∈{1,2,3}`；**state-specific 历史/动作依赖转移**（β_s=[−1.5,0,1.5]、γ_s=[1,−1,0]；softmax）；计划对共享同一轮 hidden state；**状态依赖算子** `f_{a,s},g_{b,s},h_{a,b,s}`（h=plan-pair conflict）；**一次反馈统一修订**；held-out 轮只评价。
- **rename_static_Sadd 可检验判据（V1–V4）**：V1 状态可检测（`Δ_f/σ≥2` 且 LRT power≥.80）；V2 历史/动作依赖（`KL≥0.10` 且 β_s/γ_s CI 不含 0）；V3 plan-pair conflict（`E_h≥0.20` 且 interaction power≥.80）；V4 静态不可吞并（GT-nonstatic 下 static S-add 的 held-out ELPD 低≥2SE，N1 校准期实测）。**任一失败 → `design_invalid: rename_static_Sadd`，停止、不运行效果、不换名字救活。**
- 本轮设计算术：V1 设计值 2.0（power≈1.00）；V2 KL=**0.617**（power≈1.00）；V3 E_h=.20（power≈1.00）；V4 待 N1 校准实测。

## 2. 冻结生成器（摘要；完整见 PROBLEM_N1 §2 / generator_n1.json）

S=3、π0~Dirichlet(1,1,1)、T=6（fit 4/held-out 2）、每轮 1 反馈、菜单 m=5、plan universe=12（3 A×4 B 子集）、4×4 归一化剂量网格、σ=.15、f/g 三基函数、h 两活跃基（double-centered）、state-specific β_s/γ_s 转移；GT-static（S=1,β=γ=0,h=0）与 GT-nonstatic（S=3,Δ_f/σ=2,h≠0）两套 ground-truth 供校准；随机 seed 集预注册。

## 3. 可辨识性/gauge（设计算术）

- **gauge/对称性**：状态标签置换（按 Var(f) 降序固定）；加性常数 `f+c_s, g−c_s`（固定 mean_d f=0）；interaction 加性方向（h 双中心化）。
- 代表设计 Jacobian：参数 107、观测 288、**rank=90、nullity=17**；加性 gauge 投影后 rank 仍 90（nullity 17）→ 报告**可辨识子空间 90 维 + gauge 方向**；完整设计（更多 A/B/pairs）可在 N1 执行前校准期确认满秩/参数恢复。**参数恢复门**：状态核相关≥.90、transition TV≤.10、β/γ CI 不含 0、interaction 相关≥.90；失败→`design_invalid: nonidentifiable`。

## 4. 校准 power/FPR（设计算术，非效果）

- GT-static：检测器 FPR=**0.0502**（≤α=.05 gate，n_rep=200；临界值 7.79，df=3）。
- GT-nonstatic：state detection power≈**1.000**（noncentrality 1.536e5）、interaction power≈**1.000**（7.68e3）、history power≈**1.000**（1.48e3）→ 在 n_rep=200 下设计振幅满足 power≥.80；chosen amplitudes meet gates = true。
- 说明：这些是生成器/检测器设计算术，**不**构成算法效果或药理结论。

## 5. 主终点/headroom/MDE preflight

- **Primary**：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`（lower better），δ=**0.05** normalized；U 定义为菜单内归一化效用 ∈[0,1]；菜单 m=5、held-out 2 轮；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- **headroom**：GT-nonstatic 设计目标 **0.10 ≥δ=.05**；GT-static≈0（预期无增量）；headroom<δ → `unreachable_gate`，不降 δ，基线近满分另立 budget-to-target（E5）。
- **MDE**：m=5、ICC=.30 → deff=2.2；n_units=**360** → n_eff≈163.6；保守 SD(D)=.20 → **MDE80≈.0438 ≤.05** ✅；n_req(SD=.20)=126×2.2=**278 ≤360** ✅（SD .10/.15/.30 表见 generator_n1.json）。
- **不静默换端点**：预检不过 → 停止/另立新问题。

## 6. 等 compute/query 基线（预注册）

统一 prior、初始数据（round-1 pair window）、feedback/query=T=6/每轮 1 次、调参 ≤20 配置、特征信息相同、wall/CPU cap 相同：
**B1 full retrain；B2 static S-add（同信息同预算，关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method。** 任何基线（尤其 B2）等预算等效 → 撤回算法增量主张（`no_increment`）。

## 7. 校准/资格门、失败类别、预算

- **G1** GT-static FPR≤.05；**G2** GT-nonstatic power≥.80；**G3** 可辨识/参数恢复；**G4** 无泄漏；**G5** 两跑逐字节；**G6** schema；**G7** 预算；**V4** static 不可吞并。任一失败只写 `design_invalid`，不报结果。
- **失败类别**：`rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **预算**：合成 pilot 10 replicate（stub 0.0005 s/rep、投影 main≈0.95 s，**仅为下界**；N1 执行前用真实实现重跑 pilot 并冻结投影）；主预算 n_units=360、R=50、methods=7、wall≤**1800 s**、CPU≤**2 h**、内存≤**8 GB**、**0 wells/compute-only**、不用 A/B 线资源。
- **两本账**：机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复已停止实验；不改旧判定/门槛。

## 8. 产物/确定性/SHA

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1.md` | `23F4668A71F8B0201C38B9134E23D9AB4034CFDBA8FF81EE3093D68B1D55545B` |
| `DESIGN_N1.md` | `8FAAC49189BC8870488F3944E2131E4664FCD3B18D1162C62E95FB8BCBA039CE` |
| `generator_n1.py` | `F509708EE4922D65B04178CA7CD824963537A73D5119E182063DCF90BA9F2E44` |
| `generator_n1.json` | `21BA30AAFCC3D0E047BDFAAD8A2DEA778E616C32EEF11BAC44239E34D8378559` |
| `timing_n1_pilot.json` | 计时文件（telemetry；多次运行可变；末次 `7BA4E299…`） |
| report/record/usage | 见 `usage_N1_design.json` |

**确定性**：`generator_n1.json` 两跑逐字节一致（`21BA30AA…`；wall 0.2 s）；JSON 键排序/无时间戳/allow_nan=False；计时 telemetry 单独文件（可变，不进结果 JSON）。

## 9. 建议

1. **提交 N1 预注册（PROBLEM_N1 + DESIGN_N1 + generator_n1）做独立挑战**；重点：与静态 S-add 的实质区别与 V1–V4/`rename_static_Sadd`、可辨识/gauge 与参数恢复门、headroom/MDE preflight 与"不静默换端点"、等预算基线清单（B2 强基线）、校准门 G1–G7、失败类别/停止、预算 caps、两本账边界。
2. 挑战通过后另立 **N1 执行预注册 + Lead 批准**（本任务不运行效果）；执行前用真实实现重跑 pilot timing 并冻结预算。
3. **不做**：N1/N2 效果执行、A.2.3、代码晋升、旧判定修改、合成升级为药理。
