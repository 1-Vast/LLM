# report_m3_stage1 —— R204-M3 Stage 1 合成诊断报告（支撑研究；不报效果）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者（endpoint-auditor）。
**状态：Stage 1 合成诊断完成；支撑研究、仅机制账、compute-only、0 wells；不报效果/增益/方法比较；Stage2/3 未执行；不称药理/真实决策/迁移/机制/新颖性。**

依据：Lead `DECISION_R204_M3_STAGE1.md`；冻结 v0.2 链 `PROBLEM_M3_v0_2` `15DFE82C…`、`DESIGN_M3_v0_2` `033D67CB…`、`formalism_M3_v0_2.py` `3E709B81…`、`formalism_M3_v0_2.json` `299E5B03…`、`schema_M3_v0_2` `E2E641BC…`、timing `BA261FA7…`。

## 1. 链核验

v0.2 PROBLEM/DESIGN/formalism.py/json/schema/timing **全部实算 match**；`chain_ok=True`；无 `design_invalid: chain_mismatch`。只读引用 v0.2 一步 DR 算术；未改 M3 预注册/M1/M2/N1/A-B-D/旧门槛/旧判定/代码。

## 2. 一步 DR / S1 诊断

- **DR 恒等**：`max_abs_gap=0.0`（policy value 精确；真/错 m 均 0 gap）；标准 DR/双重稳健，**不称 M3 创新**。
- **支持/positivity**：零支持动作 `b=0`、π mass=1 → `identified=False`；`design_invalid: positivity/support`；目标样本/评价样本独立。
- **截断偏差**：cap=20；max raw H=167；1 个 clipped；**bias = −0.026407185629**；detected true；**不把 clipped 当精确 policy value**。
- **score tilt**：ε root **−0.562633036711**；score(root)≈**0**；`logit m_{θ,ε}=logit mθ+ΣεH`。
- **共线/分离**：collinear rank **1**（expected 1，nonunique）；separation `finite_root_guaranteed=False` → `design_invalid: nonidentifiable` 风险。
- **分配二阶项**：full/noise ratios **1.21722846 / 1.16686763**；full≥noise；错设时 bias-square 不可忽略；只按 noise 分配不足。
- **π=b 退化**：`max_abs_H_minus_1=0.0`；一步线性 score 退化为 weighted residual；标准 DR/TMLE 等预算可复制。
- **规划**：n_units=300、deff=2.2、n_eff=**136.363636**、MDE80=**0.047982685**≤δ=.05、n_req_cluster=**278**≤300；headroom 示例 .10≥.05（须真实预检）。
- **Fisher-z 标注**：6,282.1038/1,572.7759 **仅连续 Fisher-z 参考**；非整数、非门、非 paired DR；决策用 MDE/n_req/headroom/cluster。

## 3. 19 checks（全 PASS）

`dr_identity_pass`, `support_counterexample_detected`, `clipping_bias_detected`, `score_tilt_root_pass`, `collinearity_nonunique_detected`, `allocation_full_ge_noise`, `planning_MDE_le_delta`, `n_req_le_n_units`, `baseline_degeneracy_H_equals_1`, `baselines_include_optimal_experimental_design`, `baselines_include_decision_AL`, `stage2_includes_optimal_experimental_design`, `stage2_includes_decision_AL`, `stage3_includes_optimal_experimental_design`, `stage3_includes_decision_AL`, `failure_nonidentifiable_present`, `failure_two_run_mismatch_present`, `fisher_z_labeled_non_gate`, `fisher_z_integer_round_ceil_defined` → **19/19 PASS**。

**S1 类诊断**：S1-a DR identity、S1-b clipping、S1-c score root、S1-d identifiability（rank1 + zero support）、S1-e allocation ratios、S1-f π=b、S1-g planning、S1-h Fisher-z only、S1-i baseline arms → **全 PASS**。

## 4. 基线/arms 规格（仅登记，不执行）

- **baselines_required（8）**：full-history retrain、importance weighting、DR/TMLE targeting、value-aware model learning、hierarchical/GP、BATCHIE adaptation、**optimal_experimental_design**、**decision_AL**。
- **Stage2（6 arms）**：shared-score allocation、random allocation、GP/uncertainty allocation、**decision_AL**、**optimal_experimental_design**、DR+MLE allocation。
- **Stage3（7 arms）**：candidate one-step score-tilt、full-history retrain、importance weighting、DR targeting、TMLE targeting、**optimal_experimental_design**、**decision_AL**。
- **同预算审计**：same features/knowledge/feedback/tuning≤20/caps/legal experiment package；标准 DR/TMLE+最优分配 equal-budget copy/exceed→`no_increment`/撤；**未执行比较**。

## 5. 失败类别/门

schema/结果/three_stage_plan 统一含：
`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
本轮 `failure_category=null`、`failed_checks=[]`、19 checks + S1 全 PASS；失败只写类别，不报效果。

## 6. 两跑/预算/timing

- 两独立进程：`m3_stage1.json` 逐字节 **`60845EFA66215F31FE18A8159943DC1F90EA38B86FB9C19203F3AF98D84F052D`**；checks/diagnostics/schema 亦一致；timing 单独。
- pilot：**1.6347e-04 s/rep**；projected **0.001635 s**；full Stage1 wall **0.007137 s**；caps **1800 s/2 h/8 GB**；0 wells；实际远低。
- schema/失败模板先写；JSON 无 telemetry；未输出 decision utility/regret/方法比较/top-k。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `m3_stage1.json`（两跑一致） | `60845EFA66215F31FE18A8159943DC1F90EA38B86FB9C19203F3AF98D84F052D` |
| `m3_stage1_checks.csv` | `2E6E3C8FFA91083386B14A96BC5B8415D95D58F43F327F01E5501F8433FFDFBE` |
| `m3_stage1_diagnostics.json` | `D0816802A6A9E9F95A51E14A41A4F1811BDE650D07E27891B40E9276A4C4DFD8` |
| `schema_m3_stage1.json` | `B0DC56A84797CF5E08B6139A2164F3264B9A8FCAFA793BCED206D620A489D1BC` |
| `timing_m3_stage1.json` | 见文件；result SHA `60845EFA…` |
| `run_m3_stage1.py` / report / record / usage | 见 usage |

## 8. Stage2 建议/边界

- **Stage1 合成诊断通过**；仅支撑/机制账，**不构成效果/药理/真实决策/迁移/新颖性证据**。
- **Stage2/3 不执行**；真实功能数据当前 **data_unavailable（C203/C205）**；Stage2 仅可另立设计/预注册，需独立挑战+Lead 批准；不得用合成/RNA 替代独立功能决策。
- 标准 DR/TMLE+最优分配等预算复制/超过→撤 M3 算法主张；π=b 退化/共线/分离/零支持/截断均按失败类别报告；只更新功能均值≠细胞动力学。
- 未改 M3 预注册/M1/M2/N1/A-B-D/旧门槛/旧判定/代码；不晋升代码；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养；N1 no_increment 不作 M3 证据。
