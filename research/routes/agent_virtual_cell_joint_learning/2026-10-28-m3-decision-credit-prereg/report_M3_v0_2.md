# report_M3_v0_2.md —— R204-M3.1 决策反馈信用分数（DR/TMLE 支撑）预注册报告（M3-C1 三必改；**不运行效果**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 `2026-10-28-deep-coupling-redesign/{report.md,BRIEF_R204.md}`、ERRATA C197/C199/C201/C207、R203 decision/power、M1 v0.2、M2 v0.2、N1 `report_n1_effect.md`。**状态：v0.2 修订完成；未运行效果比较、未拟合真实/响应数据、未声称增益；机制账 only、compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛。**

## 0. 判定（一屏）

- **M3 v0.2 预注册草案完成；M3-C1 的 3 项必改已落实；形式化/算术自洽检查全部 PASS（19 项 checks 全 true）。**
- **① 标准基线补全**：`optimal_experimental_design`、`decision_AL` 已入 `standard_baselines.baselines_required`、schema、Stage2/3 arms；M3 分配与最优设计/决策 AL 直接重叠→同预算显式比较；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤。
- **② 失败类别补全**：`design_invalid: nonidentifiable`（共线/分离/无有限解）与 `design_invalid: two_run_mismatch`（两跑不一致）已入 failure 全集/schema/模板；失败只写类别、不报效果。
- **③ Fisher-z 标注**：6,282.1038 / 1,572.7759 **仅 Fisher-z 连续规划参考**（非整数、非通用门、非 paired DR 公式）；schema 给 **round=6282/1573、ceil=6283/1573**、`not_a_gate=true`；**决策用 MDE80=.047982685、n_req_cluster=278、headroom、cluster**。
- 保留：DR/截断/ε root/共线/分配二阶项/π=b/两跑/pilot/caps；三阶段；data_unavailable（C203/C205）；支撑研究/机制账；N1 `no_increment` 不作 M3 证据。
- **未运行效果**；M3 Stage1 执行仍须另立执行预注册+独立挑战+Lead 批准。

## 1. 一步形式化（冻结）

- `h` 已知背景/历史；`Y∈[0,1]` 独立功能读数；`b(a|h)` 已知随机分配；`π_k(a|h)` 冻结候选策略；`mθ` 功能均值。
- `H_k=π_k/b`；`δ_k=E_b[H_k(Y−mθ)]`；`V_k=E_hΣπ_k mθ+δ_k`。
- **评价样本独立于 mθ 拟合与 π_k 选择**，否则 `leakage`；b>0 覆盖 π 支持，否则 `support/positivity`；mθ 可错仍有双稳健性（标准 DR，不称新）。
- 更新 `logit m_{θ,ε}=logit mθ+Σ_k ε_k H_k`；独立反馈拟合 ε；预定截断；共线/分离/无有限解→`design_invalid: nonidentifiable`；只更新功能均值≠细胞动力学兼容更新；无完整序贯历史/propensity/删失，不称序贯 DR。

## 2. 形式化算术结果（仅自洽检查；无效果）

| 检查 | 结果 |
|---|---|
| DR 恒等（m_true/m_wrong，两策略） | max abs gap **0.0 ≤1e-12**（PASS） |
| 零支持反例 | H 未定义、policy value 未识别；`identified=false`（PASS） |
| 截断偏差 | cap=20；max raw H=167；有界估计 bias **−0.026407185629**（检出；截断≠精确） |
| score-tilt | ε root **−0.562633036711**；score→0≤1e-10（PASS） |
| 共线 H | rank **1<2**→ε 非唯一→`nonidentifiable` 模板（PASS） |
| 分配二阶项 | π1 noise .6675/full .8125/bias² .145；π2 .24406/.28479/.04073；full≥noise（PASS） |
| π=b 退化 | H=1；加权残差等价（保留、撤主创新） |
| 规划 | MDE80 **.047982685≤.05**；n_req_cluster **278≤300**；**6,282.10/1,572.78 仅 Fisher-z（round 6282/1573；ceil 6283/1573；非 gate/非 paired DR）** |
| 标准基线/失败/Fisher-z 标注检查 | **optimal/decision_AL 入基线+Stage2/3 arms；nonidentifiable/two_run_mismatch 入失败全集；Fisher-z non-gate 标注 true**（全 PASS） |
| 形式化两跑 | `formalism_M3_v0_2.json` 逐字节一致 SHA **`299E5B03E916BFB0FA36C02FE8446EA6170FAD89E6DF4BC039A92B0E36DD7E39`** |
| pilot timing | 10 rep 平均 **0.000176 s/rep**、wall **0.00176 s**；caps 1800s/2h/8GB PASS；0 wells |

> 以上仅形式化/算术自洽；不比较方法、不报告效果/增益；截断/零支持/共线为有意构造诊断反例。

## 3. 标准基线/Stage2–3 arms（M3-C1 必改落实）

- **`baselines_required`（JSON/schema）**：full-history retrain、importance weighting、DR/TMLE targeting、value-aware model learning、hierarchical/GP、BATCHIE adaptation、**optimal_experimental_design**、**decision_AL**。
- **Stage2 arms**：shared-score allocation、random、GP/uncertainty、**decision_AL**、**optimal_experimental_design**、DR+MLE allocation。
- **Stage3 arms**：candidate score-tilt、full-history retrain、IW、DR targeting、TMLE targeting、**optimal_experimental_design**、**decision_AL**。
- **重叠/停止**：M3 分配与最优设计/决策 AL 直接重叠；同信息/反馈/调参≤20/caps/合法实验包显式比较；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤；不称分配新颖性。

## 4. 失败类别/停止/预算/数据

- **失败全集**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **Stage1 路由**：共线/分离/无有限唯一解→`nonidentifiable`；两跑不一致→`two_run_mismatch`；零支持/极端权重→`support/positivity`；截断/校准→`calibration`；失败只写类别、不报效果。
- **停止**：标准 DR/TMLE+最优分配等预算复制/超过→撤；评价样本复用选策略→leakage；超 caps→stop；CI 不能排除无实用收益→inconclusive；功能头校准不得升级为细胞规律。
- **预算**：合成 compute-only、0 wells；caps **1800 s/2 h/8 GB**；不运行效果/湿实验；真实数据 **data_unavailable（C203/C205）**，不得合成/RNA/预测替代独立功能决策。
- N1 `no_increment` 仅其 own primary，不作 M3 证据。

## 5. 三阶段（预注册；不运行）

1. **Stage1 已知真值诊断**：DR 恒等/双稳健、截断、零/低支持、错设、共线/分离、分配二阶项、两跑；只检查/诊断，不报效果；当前形式化算术已通过（非 Stage1 执行）。
2. **Stage2 固定更新器比较分配**：shared-score vs random/GP/decision_AL/optimal_experimental_design/DR+MLE；同反馈/成本/特征/调参；只测分配；复制/超过→no_increment；当前不运行。
3. **Stage3 固定反馈比较学习+闭环**：candidate vs full-history/IW/DR/TMLE + optimal_experimental_design/decision_AL；主端点独立功能决策效用/后悔 δ=.05；headroom/MDE/cluster；6,282 仅 Fisher-z；次端点校准/DR 分数/RNA；最后计成本；当前不运行、真实数据 data_unavailable。

## 6. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `formalism_M3_v0_2.py` | `3E709B8193AFA3814D821B46E9D541957B1864308D9DF98E2A60F118A25997B3` |
| `formalism_M3_v0_2.json` | `299E5B03E916BFB0FA36C02FE8446EA6170FAD89E6DF4BC039A92B0E36DD7E39` |
| `timing_M3_pilot_v0_2.json` | `BA261FA71AE957D38CA76BB4EB6A43B1E1FC230F5290088469425A63A3963C36` |
| `schema_M3_v0_2.json` | 见文件 |
| `PROBLEM_M3_v0_2.md` / `DESIGN_M3_v0_2.md` / `report_M3_v0_2.md` / `record_M3_v0_2.md` / `usage_M3_v0_2.json` | 见各文件/SHA 表 |

## 7. 建议（仅建议）

- 3 必改已落实；建议 **轻量复核**（基线表/失败类别/Fisher-z 标注/两跑）后由 Lead 决定是否批准 **M3 Stage1 合成实现**（支撑研究、仅机制账）；Stage1 执行仍须另立执行预注册+独立挑战+Lead 批准。
- 不运行效果；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛。
