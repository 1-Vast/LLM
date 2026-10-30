# report_m3_s3_exec_v0_2 —— R204-M3-S3.1 修订预注册报告（方案A：纯 learner 比较；不运行）

2026-10-28。对象：R204-M3 Stage3 合成执行预注册 v0.2。依据：M3-S3-EXEC-C1 挑战（revise/方案A）、M3 v0.2 链、Lead Stage1/Stage2 决定、Stage1/C209、Stage2/C213、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216。
**状态：预注册修订草案；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.2 新文件；v0.1 保留不改）

- 问题定义：[PROBLEM_M3_S3_EXEC_v0_2.md](PROBLEM_M3_S3_EXEC_v0_2.md)（`814AE8BE…`）
- 执行设计：[DESIGN_M3_S3_EXEC_v0_2.md](DESIGN_M3_S3_EXEC_v0_2.md)（`F7E525A6…`）
- 规划/骨架：[exec_plan_m3_s3_v0_2.py](exec_plan_m3_s3_v0_2.py)（`9E0449E4…`）→ [exec_plan_m3_s3_v0_2.json](exec_plan_m3_s3_v0_2.json)（`7E51CBA5…`）
- schema：[schema_m3_s3_exec_v0_2.json](schema_m3_s3_exec_v0_2.json)（`F6AC87B9…`）
- 记录/用量：[record_m3_s3_exec_v0_2.md](record_m3_s3_exec_v0_2.md)、[usage_m3_s3_exec_v0_2.json](usage_m3_s3_exec_v0_2.json)

## 1. 方案A落实（M3-S3-EXEC-C1 最致命矛盾）

| 项 | v0.1 矛盾 | v0.2 修正 |
|---|---|---|
| 固定反馈 vs optimal allocation | 写"所有 arms 相同反馈/不比较分配"，却把 `A_standard_DR_TMLE_optimal_allocation`（含最优分配）作 primary comparator；最优分配改变 queried feedback→反馈流不同、变 learner×allocation 复合比较 | **7 arms 全部同 shared-score/固定反馈/同评价**；标准 arm 改为 **`A_standard_DR_TMLE`（固定 allocation 下的标准 DR/TMLE learner）**；**删除 optimal allocation arm/比较**（`no_optimal_allocation_arm=true`）；**primary 为纯 learner 比较** |
| primary/secondary/Holm | 需一致 | **Primary=candidate vs A_standard_DR_TMLE**；secondary=full-history/IW/DR targeting/TMLE targeting/value-aware 5 个；**family=6 Holm**；成功=mean ΔR≤−δ ∧ CI upper<0 ∧ Holm p<.05 |
| fixed feedback 实现 | 需冻结 | 每 replicate 固定 seed/分配 policy 生成 **300 条 (h,a,Y)**；**7 arms 复用同一反馈流/同一 300 评价 units**；评价独立、target 不作标签；**任何 arm 不得改变 feedback/分配**；结果要求 per-arm `feedback_stream_sha`/`evaluation_stream_sha` 相同，否则 leakage/stop；无法保证则 stop（不改方案B） |

## 2. 链核验/Stage1/Stage2（已通过）

- **35 文件 SHA 全匹配**（chain_pass=true、mismatches=0）：M3 v0.2 8+Lead Stage1；Stage1/C209 8；Stage2 exec v0.2 8+Lead Stage2；Stage2/C213 9（`36C4DF12…`、60/60 per-arm、failure_category null）。
- Stage1 failed_checks=[]/all_checks_pass/check19_pass；Stage2 completed_allocation_diagnostics/60 per-arm。不匹配→`design_invalid: chain_mismatch`；执行时重核。

## 3. 独立 seeds / 样本 / arms

- seeds：env **20261601**；replicates **20261601–10**；arms **20261611–80**；headroom **20261681–90**；禁用 M3 Stage1/Stage2 20261401–70、M1 Stage2、M2、N1；overlap=[]、unique=true；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- 样本：R=10；每 replicate **300 共享反馈 (h,a,Y)** + **300 评价 units**；总反馈/评价 **3,000/3,000**；每 arm 300/300/replicate；调参≤20；caps 1800 s/2 h/8 GB/0 wells。
- 7 arms（全部固定 shared-score allocation，仅 learner 不同）：A_candidate_score_tilt（候选）、A_full_history_retrain、A_importance_weighting、A_DR_targeting、A_TMLE_targeting、A_value_aware、**A_standard_DR_TMLE**（标准 DR/TMLE learner，固定 allocation、无最优分配）。
- 标准 DR/TMLE learner（固定分配）等预算复制/超过→`no_increment`/撤写死；不称新颖性/增量。

## 4. 主端点/分析/闭环成本

- Primary=candidate vs A_standard_DR_TMLE；独立功能决策效用/后悔 normalized、δ=.05；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm；次端点预测/DR 分数/RNA 仅 secondary。
- n_units=300、deff=2.2、n_eff=136.36、MDE80=.04798268≤.05、n_req278≤300；cluster 按 replicate/背景/任务；headroom=U_max−U0 先检（<δ→unreachable_gate；近满分→另立 budget-to-target；不换端点）；6,282.1038/1,572.7759 仅 Fisher-z（非整数/非门/非 paired DR）。
- 闭环：每 arm 反馈 300/评价 300/≤20/caps；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限 stop。

## 5. G1–G6/失败/预算/schema/单测

- G1 支持→support/positivity；G2 截断→calibration；G3 投影/拟合→calibration/nonidentifiable；G4 无泄漏（含 feedback/eval SHA 同）→leakage；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded；**13 类失败类别**（含 chain_mismatch）。
- caps 1800 s/2 h/8 GB/0 wells；schema 先写；执行前最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测冻结；Stage2 pilot .100688/.078125/.001249 仅历史参考；JSON 无 telemetry。
- **单测（仅链核验/算术，不训练）全 PASS**：chain=35/35；Stage1/Stage2 PASS；failure=13；family=6；arms=7（含 A_standard_DR_TMLE、**无 optimal allocation arm**）；**所有 arm allocation_policy 相同**；**all_arms_same_feedback_stream=true**；seeds overlap=[]；sample 3,000/3,000；MDE .04798268≤.05、n_req278。

## 6. 边界

支撑研究/机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；Stage3 执行须另立独立挑战+Lead 批准；**禁止把 learner 比较写成 allocation 比较或反之、把 optimal allocation feedback 优势算进 primary**。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC_v0_2.md` | `814AE8BEE0D2E9C8BC497E293180E205C8DAD44DF02691539E8197A447F35615` |
| `DESIGN_M3_S3_EXEC_v0_2.md` | `F7E525A6824DCA273E14275165D7B7CD320EABE342D768FC22EA18420496829D` |
| `exec_plan_m3_s3_v0_2.py` | `9E0449E4D3ABF4ADFD63361298F9CFA350814B004F98E2B8A026C748E14256D8` |
| `exec_plan_m3_s3_v0_2.json` | `7E51CBA589A0EFBCF6972763614C94F937EA55F1EDB22164E59EF3B6B2827D02` |
| `schema_m3_s3_exec_v0_2.json` | `F6AC87B97645E7230CE5F95B527CF461ED4A74EA241E2A6691F31943A1C3DBE7` |
| report/record/usage | 见 `usage_m3_s3_exec_v0_2.json` |

**确定性**：`exec_plan_m3_s3_v0_2.json` 与 `schema_m3_s3_exec_v0_2.json` 两跑逐字节一致；JSON 无 telemetry。

## 8. 建议

1. **建议轻量复核**：方案A是否彻底（7 arms 纯 learner/固定 shared-score/同反馈/同评价；无 optimal allocation arm；primary 纯 learner 比较；family/Holm 6 正确；固定反馈实现可执行且失败可判）。
2. 复核通过 + Lead 批准后才可执行 **Stage3 合成学习比较**（支撑研究/机制账、compute-only、0 wells）；执行前重核 35 文件链、最终实现 pilot 实测冻结 canonical、feedback/evaluation stream SHA 相同检查、两跑/schema/失败模板核验。
3. **不做**：训练/效果/真实数据/湿实验/代码晋升/旧判定修改/恢复停止实验；不把 learner 比较写成 allocation 比较或反之。
