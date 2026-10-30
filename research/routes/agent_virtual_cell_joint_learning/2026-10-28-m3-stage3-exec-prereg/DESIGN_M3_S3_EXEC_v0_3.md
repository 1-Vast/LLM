# DESIGN_M3_S3_EXEC_v0_3 —— R204-M3-S3.2 Stage3 执行设计（per-arm stream SHA/输出字段；不运行）

2026-10-28。依据：[PROBLEM_M3_S3_EXEC_v0_3.md](PROBLEM_M3_S3_EXEC_v0_3.md)、`exec_plan_m3_s3_v0_3.json`、`schema_m3_s3_exec_v0_3.json`、M3 v0.2 链、Lead Stage1/Stage2 决定、Stage1/C209、Stage2/C213。
**状态：预注册修订设计 v0.3；未运行 Stage3 训练/效果/真实数据；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 执行前核验/门顺序

1. **SHA 链**：35 文件（M3 v0.2 8+Lead Stage1+Stage1 8+Stage2 exec v0.2 8+Lead Stage2+Stage2 run 9）全部匹配（本地 chain_pass=true）；执行时重核；失败→`design_invalid: chain_mismatch`。
2. **Stage1/C209**：failed_checks=[]/all_checks_pass/check19_pass；**Stage2/C213**：status completed_allocation_diagnostics、per_arm=60、failure_category null、no_effect_results=true。
3. **seeds**：env 20261601、replicate 20261601–10、arm 20261611–80、headroom 20261681–90；与禁用集交集 []；执行时重核。
4. **pilot**：执行前最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测 wall/CPU/memory 并冻结 canonical；Stage2 pilot 仅历史参考；超 caps→`compute_budget_exceeded`。
5. **schema/失败模板先写**：`schema_m3_s3_exec_v0_3.json` 运行前冻结。
6. **Stage3 通过后**：真实数据/湿实验不批；真实 Stage3 另立资源/预注册。

## 1. 固定反馈生成（写死）

- 每 replicate r=0..9：**反馈流 seed=20261601+r**、**评价流 seed=20261601+r 的独立子流/固定派生**；反馈 300 条 (h,a,Y) 由固定 shared-score allocation policy 生成；评价 300 units 独立生成；**7 arms 完全复用同一反馈流/同一评价流**；任何 arm 不得选择分配或改变流。
- `A_standard_DR_TMLE` 只用标准 DR/TMLE learner；allocation 固定 shared-score；**无 optimal allocation arm/比较**。
- 评价独立于拟合/更新/选择；target 不作标签；失败只写类别。
- 环境复用 Stage2 冻结（H=3/A=3/Y binary；p/μ/b/π/m/C_H=20）。

## 2. per-arm 输出（16 字段）与 stream SHA

`arm_fields`（schema，写死）：
`arm_id, replicate_id, update_rule, allocation_policy, n_feedback, n_eval, tuning_configs, cost_ledger, per_replicate_regret, mean_DeltaR, CI95, holm_p, pass, feedback_stream_sha, evaluation_stream_sha, allocation_policy_sha`。

**canonical 计算**：
- 反馈记录：`"h,a,Y\n"`（整数，固定生成顺序）；评价记录：`"h,a\n"`（整数，固定评价顺序）；UTF-8 字节按序拼接；**SHA256 uppercase**。
- `allocation_policy_sha = SHA256("shared_score_fixed_same_feedback_stream")`。
- **每 replicate 所有 7 arms 的 feedback/evaluation SHA 必须逐字节一致**；不一致→`design_invalid: leakage`/stop、不报学习比较。
- `unit_checks` 布尔保留但**不能替代** per-arm SHA；本轮用固定 toy 序列重算 canonical 两次一致（示例 feedback `[(0,1,1),(1,2,0),(2,0,1),(0,2,0)]`、evaluation `[(0,1),(1,0),(2,1),(1,2)]`），不训练。

## 3. 样本/arms/主端点（保持）

- R=10；每 replicate 300 反馈+300 评价；总 3,000/3,000；7 arms（全部纯 learner、固定 shared-score）：A_candidate_score_tilt、A_full_history_retrain、A_importance_weighting、A_DR_targeting、A_TMLE_targeting、A_value_aware、**A_standard_DR_TMLE**。
- Primary=candidate vs A_standard_DR_TMLE；δ=.05；成功 mean ΔR≤−δ ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm；次端点预测/DR 分数/RNA 仅 secondary。
- n_units=300、deff2.2、n_eff136.36、MDE80=.04798268≤.05、n_req278；headroom 先检；6,282/1,573 仅 Fisher-z；cluster 按 replicate/背景/任务；不换端点。

## 4. G1–G6 / 失败类别 / 预算

| 门 | 规则 | 失败类别 |
|---|---|---|
| G1 | 支持/程序 | support/positivity |
| G2 | 截断 C_H=20；clipped≠exact；报 bias/bound | calibration |
| G3 | 投影/拟合 | calibration/nonidentifiable |
| G4 | 无泄漏；**per-arm feedback/eval SHA 一致**；评价独立；target 不作标签 | leakage |
| G5 | 两跑结果 JSON 逐字节 | two_run_mismatch |
| G6 | schema 先写、caps 1800 s/2 h/8 GB/0 wells | compute_budget_exceeded |

**13 类**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/chain_mismatch/unreachable_gate/precision_insufficient/no_increment/inconclusive。闭环成本同账；失败只写类别。

## 5. 两跑/schema/单测/边界

- 两跑：独立进程、同 seeds；结果 JSON（无 telemetry）逐字节；`run_shas` 记录；不一致→two_run_mismatch。
- schema v0.3：`arm_fields` 16 项、`feedback_stream_sha_required/evaluation_stream_sha_required/allocation_policy_sha_required`、`canonical_stream_spec`、`per_arm_sha_mismatch_failure=design_invalid: leakage`、13 失败类别、forbidden fields（topk/gain/pharmacology/real decision/transfer/mechanism/novelty/real data/sequential DR/allocation comparison）。
- 单测（仅链/算术，不训练）：chain=35/35；Stage1/Stage2 PASS；failure=13；family=6；arms=7（含 A_standard_DR_TMLE、无 optimal allocation）；policy 一致；**schema 三 SHA 字段存在**；**canonical 示例重算一致**；seeds overlap=[]；sample 3,000/3,000；MDE≤δ、n_req278。
- 边界：只更新功能均值≠细胞动力学；无序贯→不称序贯 DR；支撑研究/机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 35 文件链/Stage1/Stage2；② seeds/两跑；③ 7 纯 learner arms + 固定 shared-score + 无 optimal allocation；④ **per-arm 16 字段 + stream SHA canonical/leakage 判定**；⑤ primary/family6/MDE/headroom/6,282；⑥ G1–G6/13 失败/caps/schema/pilot/闭环/停止/边界。Stage3 执行须另立独立挑战+Lead 批准。
