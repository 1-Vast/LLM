# DESIGN_M3_S3_EXEC —— R204-M3 Stage3 执行设计（固定反馈比较学习 + 闭环成本；不运行）

2026-10-28。依据：[PROBLEM_M3_S3_EXEC.md](PROBLEM_M3_S3_EXEC.md)、`exec_plan_m3_s3.json`、`schema_m3_s3_exec.json`、M3 v0.2 链、Lead Stage1/Stage2 决定、M3 Stage1/C209、Stage2/C213。
**状态：预注册设计草案；未运行 Stage3 训练/效果/真实数据；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 执行前核验/门顺序

1. **SHA 链**：35 文件（M3 v0.2 8+Lead Stage1+Stage1 8+Stage2 exec v0.2 8+Lead Stage2 决定+Stage2 run 9）全部匹配（本地 chain_pass=true、mismatches=0）；执行时重核；失败→`design_invalid: chain_mismatch`。
2. **Stage1/C209**：failed_checks=[]、all_checks_pass=true、check19_pass=true。
3. **Stage2/C213**：status=completed_allocation_diagnostics、per_arm=60、failure_category null、no_effect_results=true；仅机制账。
4. **seeds 独立核验**：env 20261601、replicate 20261601–10、arm 20261611–80、headroom 20261681–90；与 M3 Stage1/Stage2 20261401–70、M1 Stage2、M2、N1 禁用集交集 []；执行时重核、不改 seed。
5. **pilot 冻结**：执行前跑最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测 wall/CPU/memory，冻结 canonical timing；**不得引用 Stage2 pilot**（.100688/.078125/.001249 仅历史参考）；超 caps→`compute_budget_exceeded`。
6. **schema/失败模板先写**：`schema_m3_s3_exec.json` 运行前冻结。
7. **Stage3 通过后**：本预注册仅 Stage3 合成学习比较；真实数据/湿实验不批；真实 Stage3 另立资源/预注册。

## 1. 样本/固定反馈语义（冻结）

| 项 | 值 |
|---|---|
| R replicates | **10** |
| n_units（评价单位）/replicate | **300** |
| n_feedback（共享反馈记录）/replicate | **300** |
| n_eval（共享评价样本）/replicate | **300** |
| arms | **7** |
| 总评价 units | **3,000** |
| 总反馈 records | **3,000** |
| 每 arm 反馈/评价 | 300/300/replicate |
| 调参预算 | ≤20 configs |
| caps | 1800 s/2 h/8 GB/0 wells |
| 两跑 | 同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独 |

- **固定反馈**：每 replicate 生成同一反馈流（h,a,Y 300 条）与同一评价样本（300 units）；**所有 arms 看相同反馈/评价**；**评价独立于拟合/更新/选择**；**每 arm 不选择分配**（shared-score 固定）。
- **闭环成本**：每 arm 反馈 300/replicate、评价 300/replicate、调参≤20、caps；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限 stop。
- 环境复用 Stage2 冻结：H=3/A=3/Y binary；p/μ/b/π_1/π_2/m_true/m_wrong/C_H=20；公式冻结；合成结果不推广真实。

## 2. Stage3 arms（7；固定反馈；仅学习比较）

| id | 角色 | 更新规则 |
|---|---|---|
| A_candidate_score_tilt | candidate | 一步 score-tilt（H/δ）更新；固定 shared-score 分配 |
| A_full_history_retrain | baseline | 全历史重训 |
| A_importance_weighting | baseline | 重要性加权更新 |
| A_DR_targeting | baseline | DR targeting |
| A_TMLE_targeting | baseline | TMLE targeting |
| A_value_aware | baseline | value-aware model learning |
| A_standard_DR_TMLE_optimal_allocation | **combined standard equal-budget baseline** | 标准 DR/TMLE learner+最优分配 pipeline |

- 同信息/反馈/调参≤20/caps/合法包；**不比较分配**（避免与 Stage2 混同）；标准 DR/TMLE+最优分配**等预算复制/超过→`no_increment`/撤**写死；不称 M3 增量/新颖性。

## 3. 端点/分析（预注册）

- Primary comparison=candidate vs `A_standard_DR_TMLE_optimal_allocation`；primary endpoint=独立功能决策效用/后悔（normalized，δ=.05）。
- 成功：mean ΔR≤−δ ∧ 95% CI upper<0 ∧ **Holm p<.05**；Holm family=**6**（primary+5 secondary：full-history/IW/DR/TMLE/value-aware）。
- 分析：paired unit-level ΔR，cluster-robust SE 按 replicate；保守精度 n_units=300、deff=**2.2**、n_eff=**136.36**、MDE80=**0.04798268≤.05**、n_req=**278≤300**；实际 R=10 replicates 报告 cluster-robust SE。
- headroom=U_max−U0 先检（独立 headroom seeds 20261681–90；<δ→`unreachable_gate`；近满分→另立 budget-to-target，不换端点）。
- 次端点=预测校准/DR 分数误差/RNA 误差（仅 secondary）；**6,282.1038/1,572.7759 仅 Fisher-z 参考**（非整数/非门/非 paired DR）；**不得换端点制造收益**。

## 4. G1–G6 / 失败类别 13

| 门 | 规则 | 失败类别 |
|---|---|---|
| G1 | 支持/程序（b>0、b≥b_min、动作支持、随机化） | support/positivity |
| G2 | 截断 C_H=20；clipped≠exact；报 bias/bound | calibration |
| G3 | 投影/拟合（score-tilt/DR/TMLE 诊断） | calibration/nonidentifiable |
| G4 | 无泄漏（评价独立、target 不作标签） | leakage |
| G5 | 两跑结果 JSON 逐字节 | two_run_mismatch |
| G6 | schema 先写、caps 1800 s/2 h/8 GB/0 wells | compute_budget_exceeded |

**13 类失败类别**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 5. 两跑/预算/schema/单测

- **两跑**：run1/run2 独立进程、同 seeds；结果 JSON（无 telemetry）逐字节；`run_shas` 记录；不一致→`two_run_mismatch`。
- **预算**：caps 1800 s/2 h/8 GB/0 wells；执行前最终实现 pilot（2×7×300）实测冻结 canonical；Stage2 pilot 仅历史参考；main=10×7×300 反馈/评价；projected wall 由 pilot 验证≤caps。
- **schema**：top keys 含 chunk/endpoints/headroom_mde/closed_loop_cost/failure_categories；per-arm 字段（n_feedback/n_eval/tuning/cost_ledger/per-replicate regret/mean ΔR/CI95/holm p/pass）；forbidden fields（topk/gain/pharmacology/real decision/transfer/mechanism/novelty/real data/sequential DR/allocation comparison）；JSON 无 telemetry。
- **单测（仅算术/链核验，不训练）**：chain=35/35；Stage1/Stage2 PASS；failure=13（含 chain_mismatch）；family=6；arms=7（含 combined standard）；seeds overlap=[]；sample total 3,000/3,000；MDE .04798268≤.05、n_req278；**无训练/无效果**。

## 6. 停止/边界/批准清单

- 停止：标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤；π=b→H=1；共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration；评价复用→leakage；两跑/链/预算→对应类别；不改旧判定/门槛；不放宽/改阈值/换端点。
- 边界：只更新功能均值≠细胞动力学；无序贯→不称序贯 DR；支撑研究/机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 35 文件链+Stage1/C209+Stage2/C213；② seeds 20261601+ 独立/两跑；③ R=10/300 feedback/300 eval/7 arms 固定反馈语义；④ primary/secondary/Holm/headroom/MDE/6,282 边界；⑤ 闭环成本/预算/schema/pilot 实测冻结；⑥ G1–G6/13 失败类别/stop；⑦ 边界。Stage3 执行须另立独立挑战+Lead 批准。
