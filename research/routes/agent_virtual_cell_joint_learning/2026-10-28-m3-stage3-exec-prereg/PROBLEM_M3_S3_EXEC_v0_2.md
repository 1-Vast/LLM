# PROBLEM_M3_S3_EXEC_v0_2 —— R204-M3-S3.1 Stage3 合成执行预注册（方案A：纯 learner 比较；不运行）

2026-10-28。对象：R204-M3 Stage3 合成执行预注册（固定反馈比较学习 + 闭环成本）。本文件修正 v0.1（[PROBLEM_M3_S3_EXEC.md](PROBLEM_M3_S3_EXEC.md)，保留不改），落实 M3-S3-EXEC-C1 关键矛盾**方案A**：**7 arms 全部同 shared-score/固定反馈/同评价；`A_standard_DR_TMLE_optimal_allocation` → `A_standard_DR_TMLE`（固定 allocation 下的标准 DR/TMLE learner）；primary 为纯 learner 比较；不得 learner/allocation 混写。** 依据：M3 v0.2 链、Lead Stage1/Stage2 决定、M3 Stage1/C209、Stage2/C213（`36C4DF12…`）、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216、R203 decision/power。
**状态：预注册修订草案 v0.2；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。Stage3 执行须另立独立挑战+Lead 批准。**

## 0. M3-S3-EXEC-C1 必改落实（方案A）

| # | 矛盾 | v0.2 修正 |
|---|---|---|
| ① **固定反馈 vs optimal allocation 矛盾** | v0.1 写"所有 arms 相同反馈/不比较分配"，却把 `A_standard_DR_TMLE_optimal_allocation`（含**最优分配**）作 primary comparator；最优分配会改变 queried feedback/分配→反馈流不再相同，Stage3 变 learner×allocation 复合比较 | **方案A**：**7 arms 全部使用完全相同 shared-score/固定反馈/同评价**；标准 arm 改为 **`A_standard_DR_TMLE`**（固定 allocation 下的标准 DR/TMLE learner）；**删除 optimal allocation 作为 arm/比较**（`no_optimal_allocation_arm=true`）；**primary 为纯 learner 比较**；不再任何"allocation 比较/复合比较"表述 |
| ② **primary/secondary/Holm 写死** | 需与方案A一致 | **Primary=candidate vs A_standard_DR_TMLE**；secondary=full-history/IW/DR targeting/TMLE targeting/value-aware 共 5 个；**family=6 Holm**；成功=`mean ΔR≤−δ` ∧ 95% CI upper<0 ∧ **Holm p<.05**；不得换 primary/secondary |
| ③ **冻结 fixed feedback 实现** | 需保证所有 arm 同一 (h,a,Y) 流 | **每条 (h,a,Y) 生成 seed/分配 policy 固定**（冻结环境+shared-score 分配）；所有 arms **复用同一 300 条反馈/300 评价 units**；评价独立、target 不作标签；**任何 arm 不得通过分配改变 feedback 流**；**无法保证则 stop（不改方案B）**；单测 `all_arms_same_feedback_stream=true`、`all_arms_same_allocation_policy=true` |
| ④ 保持 | — | 35 文件链/Stage1/Stage2；独立 seeds（env 20261601、reps 20261601–10、arms 20261611–80、headroom 20261681–90；overlap=[]）；R=10/每 replicate 300 共享反馈+300 评价/总 3,000/3,000；MDE .04798268/n_req278/headroom/cluster/6,282 仅 Fisher-z；G1–G6/13 失败/caps 1800 s/2 h/8 GB/0 wells/schema 先写/pilot 实测冻结/闭环成本；停止/边界 |

## 1. 链核验（执行前；不匹配→stop）

`exec_plan_m3_s3_v0_2.py` 只读核验 **35 文件 SHA 全匹配（chain_pass=true、mismatches=0）**：M3 v0.2 八件+Lead Stage1 决定（9）；Stage1/C209 八件（8）；Stage2 exec v0.2 八件+Lead Stage2 决定（9）；Stage2/C213 九件（9）。另核 Stage1（failed_checks=[]/all_checks_pass/check19_pass）与 Stage2（completed_allocation_diagnostics/60 per-arm/failure_category null/no_effect_results）。不匹配/状态不符→`design_invalid: chain_mismatch`；执行时重核。

## 2. 独立执行 seeds（overlap=[]、unique=true）

env **20261601**；replicates **20261601–20261610**；arms **20261611+10a+r（20261611–20261680）**；headroom **20261681–20261690**；禁用 M3 Stage1 20261112/13、20261200；M3 Stage2 20261401–20261470；M1 Stage1 20261112/13；M1 v0.2 20261201–03；M1 Stage2 20261301–49；M2 Stage2 20261200–39；M2 Stage3 20262100–39；N1 20261030/61/62/63。两跑同 seeds、独立进程、结果 JSON 逐字节、telemetry 单独；不得改 seed。

## 3. Stage3 设置（纯 learner 比较；固定反馈/固定分配）

- **环境**：一步 DR H=3/A=3/Y∈[0,1] binary；p(h)=[.3,.4,.3]、μ/b/π_1/π_2/m_true/m_wrong、C_H=20 冻结；H=π/b、δ/V/score-tilt 公式冻结；合成不推广真实。
- **固定反馈实现（冻结）**：R=**10**；每 replicate **同一 (h,a,Y) 生成 seed/分配 policy** 产生 **300 条共享反馈**；所有 arms 复用**同一反馈流**与**同一 300 评价 units**；评价独立于拟合/更新/选择；target 不作标签；**任何 arm 不得改变 feedback 流**；每 arm 只改更新器/learner，不改分配。
- **样本**：每 replicate n_units=300、n_feedback=300、n_eval=300；总评价 units=**3,000**、总反馈 records=**3,000**；7 arms。
- **7 arms（全部固定 shared-score allocation）**：
  1. **A_candidate_score_tilt**（候选，一步 score-tilt 更新）
  2. A_full_history_retrain
  3. A_importance_weighting
  4. A_DR_targeting
  5. A_TMLE_targeting
  6. A_value_aware
  7. **A_standard_DR_TMLE**（固定 allocation 下的标准 DR/TMLE learner；等预算基线）
- **同信息/同反馈/调参≤20/caps/合法包；不比较分配**；**不输出 top-k/方法比较效果替代端点**；标准 DR/TMLE learner（固定分配）等预算复制/超过→`no_increment`/撤；不称新颖性/增量。
- 标准 DR/TMLE learner 只更新 learner，**不含 optimal allocation**；不存在通过最优分配改变 feedback 的 arm。

## 4. 主端点/次端点/多重性

- **Primary comparison**：A_candidate_score_tilt vs **A_standard_DR_TMLE**（纯 learner）。
- **Primary endpoint**：独立功能决策效用/后悔（normalized）；δ=**0.05**。
- **成功**：`mean ΔR ≤ −δ` ∧ 95% CI upper<0 ∧ **Holm p<.05**。
- **Holm family=6**：primary + 5 secondary（full-history、IW、DR targeting、TMLE targeting、value-aware）；α=.05。
- **次端点**：预测校准、DR 分数误差、RNA 误差（仅 secondary，不替代）。
- **不得换端点**：primary 固定；不得事后换预测/top-k/预算端点；headroom=U_max−U0 先检（<δ→`unreachable_gate`；近满分→另立 budget-to-target，不换端点）。
- **功效**：n_units=300、deff=2.2、n_eff=136.36、MDE80=**0.04798268≤.05**、n_req=**278≤300**；cluster 按独立 replicate/背景/任务；**6,282.1038/1,572.7759 仅 Fisher-z 参考**（非整数/非门/非 paired DR）。

## 5. 闭环成本/G1–G6/失败/预算

- **闭环**：每 arm 反馈 300/replicate、评价 300/replicate、调参≤20、caps 1800 s/2 h/8 GB/0 wells；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限→`compute_budget_exceeded`/stop。
- **G1** 支持/程序→support/positivity；**G2** 截断（C_H=20；clipped≠exact；报 bias/bound）→calibration；**G3** 投影/拟合→calibration/nonidentifiable；**G4** 无泄漏→leakage；**G5** 两跑→two_run_mismatch；**G6** schema/预算→compute_budget_exceeded。
- **13 类失败类别（含 chain_mismatch）**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- caps 1800 s/2 h/8 GB/0 wells；schema 先写；**执行前最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测并冻结 canonical**；Stage2 pilot 仅历史参考；JSON 无 telemetry；失败只写类别。

## 6. 停止/边界

- 标准 DR/TMLE learner（固定分配）等预算复制/超过→`no_increment`/撤；π=b→H=1 退化；共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration；评价复用→leakage；两跑/链/预算→对应类别；不改旧判定/门槛；不放宽/改阈值/换端点。
- **禁止**把 learner 比较写成 allocation 比较或反之；禁止把 optimal allocation feedback 优势算进 primary；不存在 optimal allocation arm。
- 只更新功能均值≠细胞动力学；无序贯 history/propensity/删失→不称序贯 DR；支撑研究/机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；Stage3 执行须另立独立挑战+Lead 批准。
