# PROBLEM_M3_S3_EXEC —— R204-M3 Stage3 合成执行预注册草案（固定反馈比较学习；不运行）

2026-10-28。对象：R204-M3（支撑研究：同一组决策反馈分数用于功能均值修订与实验分配）Stage3。依据：M3 v0.2 链、Lead `DECISION_R204_M3_STAGE1.md`（`9743CF2E…`）、M3 Stage1/C209、Stage2 exec/C213（Lead `DECISION_R204_M3_S2_EXEC.md`、结果 `36C4DF12…`）、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216、R203 decision/power。
**状态：执行预注册草案；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 定位

- Stage1/C209：一步 DR 合成诊断 PASS（DR 恒等、截断、共线、π=b、分配二阶项、19 checks PASS）；B2 等价、一步投影主算法主张已撤。
- Stage2/C213：合成分配诊断 PASS（60/60 records、60/60 pass；G1–G6；两跑 `36C4DF12…`；仅机制账、无效果证据；DR/TMLE+最优分配等价判定**留 Stage3**）。
- **Stage3 只做固定反馈下的学习比较 + 闭环成本**；**分配只作配套 shared-score 固定**（不比较分配，避免与 Stage2 混同）；合成结果不推广真实数据。
- **标准 DR/TMLE+最优分配等预算复制/超过 → `no_increment`/撤**（写死；若被复制/超过，不保留 M3 算法增量主张）。

## 1. 链核验（执行前；不匹配→stop）

`exec_plan_m3_s3.py` 本地只读核验 **35 文件 SHA 全部匹配（chain_pass=true、mismatches=0）**：
- M3 v0.2 八件 + Lead Stage1 决定 `9743CF2E…`（9）；
- Stage1/C209 八件（8）；
- Stage2 exec v0.2 八件 + Lead Stage2 决定 `A29CBF7B…`（9）；
- Stage2/C213 结果九件：`m3_stage2.json` `36C4DF12…`（60/60 per-arm、failure_category null）、per_arm.csv、diagnostics、schema、timing、report、record、usage、run script（9）。
- 另核 Stage1（failed_checks=[]/all_checks_pass/check19_pass）与 Stage2（status completed_allocation_diagnostics/60 per-arm/no_effect_results）。不匹配/状态不符→`design_invalid: chain_mismatch`、不报结果；执行时重核。

## 2. 独立执行 seeds（不复用已有）

| 用途 | seeds |
|---|---|
| 冻结环境 | **20261601** |
| replicate seeds（R=10） | **20261601–20261610** |
| arm seeds（a=0..6,r=0..9） | **20261611 + 10a + r** → **20261611–20261680** |
| headroom 预检 seeds | **20261681–20261690** |
| 两跑 | 同 seeds、独立进程、结果 JSON 逐字节、telemetry 单独 |

禁用：M3 Stage1 20261112/13、20261200；**M3 Stage2 20261401–20261470**；M1 Stage1 20261112/13；M1 v0.2 20261201–03；M1 Stage2 20261301–49；M2 Stage2 20261200–39；M2 Stage3 20262100–39；N1 20261030/61/62/63。本地 **overlap=[]、unique=true**；执行时不得改 seed。

## 3. Stage3 设置（固定反馈比较学习）

- **环境（复用 Stage2 冻结，写死）**：一步 DR H=3/A=3/Y∈[0,1] binary；p(h)=[.3,.4,.3]、μ/b/π_1/π_2/m_true/m_wrong、C_H=20 冻结；H=π/b、δ/V/score-tilt 公式冻结。
- **固定反馈**：R=**10** replicates；每 replicate **同一反馈流 300 条记录 (h,a,Y)** 与**同一评价样本 300 units**；所有 arms 看完全相同反馈/评价；**评价独立于拟合/更新/选择**；**每 arm 不选择分配**（shared-score 固定）。
- **样本语义**：每 replicate n_units=**300**、n_feedback=**300**、n_eval=**300**；总评价 units=**3,000**、总反馈=**3,000**；7 arms。
- **arms（7）**：A_candidate_score_tilt（候选，一步 score-tilt，固定 shared-score 分配）、A_full_history_retrain、A_importance_weighting、A_DR_targeting、A_TMLE_targeting、A_value_aware、**A_standard_DR_TMLE_optimal_allocation（标准 DR/TMLE+最优分配组合等预算基线）**。
- **同信息/反馈/调参≤20/caps/合法包**；**不比较分配**（分配固定 shared-score）；**不输出 top-k/方法比较效果替代端点**。
- **等价判定（写死）**：A_standard_DR_TMLE_optimal_allocation 等预算复制/超过候选 → `no_increment`/撤；不称 M3 增量/新颖性；本轮只登记规格与可复现性，不执行。

## 4. 主端点/次端点/多重性

- **Primary comparison**：A_candidate_score_tilt vs **A_standard_DR_TMLE_optimal_allocation**。
- **Primary endpoint**：独立功能决策效用/后悔（normalized）；δ=**0.05**。
- **成功判据**：`mean ΔR ≤ −δ` ∧ 95% CI upper < 0 ∧ **Holm 校正 p<.05**。
- **Holm family=6**：primary + 5 secondary（full-history、IW、DR targeting、TMLE targeting、value-aware）；α=.05。
- **次端点**：预测校准、DR 分数误差、RNA 误差（仅 secondary，不替代）。
- **不得换端点**：primary 固定；不得事后换成预测/top-k/预算端点制造收益；headroom 先检（<δ→`unreachable_gate`；近满分→另立 budget-to-target，不换端点）。
- **功效**：n_units=300、deff=2.2、n_eff=**136.36**、MDE80=**0.04798268≤.05**、n_req=**278≤300**；cluster 按独立 replicate/背景/任务；**6,282.1038/1,572.7759 仅 Fisher-z 参考**（非整数/非门/非 paired DR）。

## 5. 闭环成本

- 每 arm 成本账：反馈 **300 条/replicate**、评价 **300 units/replicate**、调参≤20、计算 caps 1800 s/2 h/8 GB；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限→`compute_budget_exceeded`/stop。
- 反馈/实验包/计算预算全部计入，不得隐去或事后减项。

## 6. G1–G6 / 失败类别 13

- G1 支持/程序→support/positivity；G2 截断（C_H=20，clipped≠exact，报 bias/bound）→calibration；G3 投影/拟合（score-tilt/DR/TMLE 诊断）→calibration/nonidentifiable；G4 无泄漏（评价独立、target 不作标签）→leakage；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded。
- **13 类**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- caps **1800 s/2 h/8 GB/0 wells**；schema 先写；**执行前最终实现 pilot（2 reps×7 arms×300 units）实测并冻结 canonical timing**；Stage2 pilot .100688/.078125/.001249 **仅历史参考、不得当执行 pilot**；JSON 无 telemetry；失败只写类别。

## 7. 停止/边界

- 标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤；π=b→H=1 退化；共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration；评价复用→leakage；两跑/链/预算→对应类别；不改旧判定/门槛；不放宽/改阈值/换端点。
- 只更新功能均值 ≠ 细胞动力学兼容更新；无完整序贯 history/propensity/删失→不称序贯 DR/TMLE。
- 支撑研究/机制账 only；**不执行真实数据/湿实验**；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；**Stage3 执行须另立独立挑战+Lead 批准**。
