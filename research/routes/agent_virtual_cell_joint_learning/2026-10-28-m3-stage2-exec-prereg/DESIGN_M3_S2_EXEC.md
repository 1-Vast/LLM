# DESIGN_M3_S2_EXEC —— R204-M3 Stage2 合成执行设计（固定更新器分配比较；不运行）

2026-10-28。依据：[PROBLEM_M3_S2_EXEC.md](PROBLEM_M3_S2_EXEC.md)、`exec_plan_m3_s2.json`、`schema_m3_s2_exec.json`、M3 v0.2 链、Lead Stage1 决定、M3 Stage1/C209。
**状态：执行预注册设计；未运行 Stage2 训练/效果/真实数据；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage2 执行须另立独立挑战+Lead 批准。**

## 0. 执行前核验/门顺序

1. **SHA 链**：17 文件（M3 v0.2 八件 + Lead 决定 + Stage1 八件）全部匹配（本地已核验 chain_pass=true、mismatches=0）；执行时重核；失败→`design_invalid: chain_mismatch`。
2. **Stage1 状态**：C209 `failed_checks=[]`、`all_checks_pass=true`、`check19_pass=true`、`no_effect_results=true`；19 checks + S1 全 PASS；仅支撑/机制账。
3. **seeds 独立核验**：20261401+ 与 M3 Stage1/M1 Stage2/M2/N1 等禁用集交集为空；执行时重核，不得改 seed。
4. **pilot 冻结**：执行前最终实现实测 pilot 并冻结 canonical timing（单独 telemetry）；文档/JSON 同一 snapshot；超 caps→`compute_budget_exceeded`。
5. **schema/失败模板先写**：`schema_m3_s2_exec.json` 运行前冻结。
6. **Stage2 通过后**：本预注册仅 Stage2 分配诊断；Stage3/真实数据/湿实验不批；Stage3 另立预注册+独立挑战+Lead 批准。

## 1. Stage2 环境（冻结；仅合成）

- H=3 contexts、A=3、Y∈[0,1] 二值；p(h)=[.3,.4,.3]；μ 与 b 矩阵冻结（PROBLEM §3.1）；π_1 确定性置换、π_2 混合策略；m_true=μ、m_wrong=.5；C_H=20。
- `H_k=π_k/b`；δ/ V/ score-tilt/ allocation-Q 公式冻结；评价样本独立；target 样本不作标签；分配不得复用评价。
- 已知诊断用例：正支持、零支持（b=0 & π mass=1→未识别）、截断（clipped≠exact，报告 bias/bound）、共线（rank<2→nonidentifiable）、分离（root 在 −inf→nonidentifiable）、π=b（H=1 退化，保留等价/不称新意）。
- 合成/严格已知真值；**不外推真实数据**；data readiness open（C203/C205/C210）。

## 2. 六 arms（仅分配比较；同 learner/updater）

| id | 角色 | 规则 |
|---|---|---|
| S_shared_score | candidate | shared-score Q_k(b) 分配 |
| S_random | baseline | 随机合法分配 |
| S_gp_uncertainty | baseline | GP/不确定性分配 |
| S_decision_AL | **显式等预算强基线** | decision active learning |
| S_optimal_experimental_design | **显式等预算强基线** | optimal experimental design |
| S_DR_MLE_allocation | standard baseline | DR+MLE 最优分配 |

- **共同合同**：同 data/information/physical feedback/features/knowledge/tuning≤20/caps 1800 s/2 h/8 GB/0 wells/合法实验包；同更新器，只改分配。
- **不输出** decision utility/regret/top-k/学习效果比较；**不执行方法优劣结论**；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤的判定**留 Stage3**；本轮仅登记规格与可复现性。

## 3. G1–G6（执行时逐项）

| 门 | 规则 | 失败类别 |
|---|---|---|
| G1 支持/程序 | b>0 on π support、b≥b_min、动作支持、随机化记录 | support/positivity |
| G2 截断 | C_H=20 预设；clipped 估计≠精确 value；报 bias/bound | calibration |
| G3 分配二阶项 | full Q≥noise Q；错设 bias² 非零/未知；不按 noise-only 分配 | calibration |
| G4 无泄漏 | 评价独立于 mθ fit/策略选择；target 不作标签；不复用评价选 b | leakage |
| G5 两跑 | 结果 JSON 逐字节；telemetry 单独 | two_run_mismatch |
| G6 schema/预算 | schema 先写；caps 1800 s/2 h/8 GB/0 wells | compute_budget_exceeded |

## 4. 停止/分类

- π=b→H=1 退化：保留等价、撤/不称深世界模型创新。
- 共线/分离/无有限唯一解→`design_invalid: nonidentifiable`；零支持/极端权重→`support/positivity`；截断/错设→`calibration`；评价复用→`leakage`；两跑/链/预算→对应类别。
- **任何失败不改旧判定/门槛**；不执行时放宽容差/改阈值/换端点救结果。
- 只更新功能均值 **≠** 细胞动力学兼容更新；无完整序贯 history/propensity/删失→**不称序贯 DR/TMLE**。

## 5. 两跑/预算/schema/骨架单测

- **两跑**：run1/run2 独立进程、同 seeds；结果 JSON（无 telemetry）逐字节一致；`run_shas` 记录；不一致→`two_run_mismatch`。
- **预算**：caps 1800 s/2 h/8 GB/0 wells；执行前最终实现 pilot 实测并冻结 canonical；Stage1 pilot 参考 **.00016347 s/rep、projected .001635 s、wall .007137 s**（非执行实测）。
- **schema**：`schema_m3_s2_exec.json` 先写；top/arm/checks/forbidden fields 冻结；JSON 无 telemetry；失败只写类别。
- **骨架单测（本轮仅算术，不训练/不比较）**：DR identity gap **0.0/≤1e-12**；clipping detected（bias −0.026407185629，max raw H=167，1 clipped）；collinear rank **1**；π=b H−1 diff **0.0**；allocation ratios **[1.21722846, 1.16686763]**（full≥noise）；arm list 6（含 decision_AL/optimal design）；seeds overlap=[]；**无训练/无效果比较**。

## 6. 边界/批准清单

- 支撑研究/机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作 M3 证据；data readiness open（C203/C205/C210）。
- **批准清单**：① 17 文件链核验+Stage1 状态；② 独立 seeds/两跑/telemetry 分离；③ 环境/六 arms/同预算合同冻结；④ G1–G6/失败/停止/截断/共线/分离/π=b 规则；⑤ caps/pilot 冻结/schema；⑥ 边界。
- Stage2 执行须另立独立挑战 + Lead 批准；Stage3 另立预注册。
