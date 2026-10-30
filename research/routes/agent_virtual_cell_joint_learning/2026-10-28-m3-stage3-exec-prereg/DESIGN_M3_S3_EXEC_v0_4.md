# DESIGN_M3_S3_EXEC_v0_4 —— R204-M3-S3.3 Stage3 执行设计（evaluation seed/allocation 公式写死；不运行）

2026-10-28。依据：[PROBLEM_M3_S3_EXEC_v0_4.md](PROBLEM_M3_S3_EXEC_v0_4.md)、`exec_plan_m3_s3_v0_4.json`、`schema_m3_s3_exec_v0_4.json`、M3 v0.2 链、Lead Stage1/Stage2 决定、Stage1/C209、Stage2/C213。
**状态：预注册修订设计 v0.4；未运行 Stage3 训练/效果/真实数据；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 执行前核验/门顺序

1. **SHA 链**：35 文件（M3 v0.2 8+Lead Stage1+Stage1 8+Stage2 exec v0.2 8+Lead Stage2+Stage2 run 9）全部匹配（本地 chain_pass=true）；执行时重核；失败→`design_invalid: chain_mismatch`。
2. **Stage1/C209**：failed_checks=[]/all_checks_pass/check19_pass；**Stage2/C213**：status completed_allocation_diagnostics、per_arm=60、failure_category null、no_effect_results=true。
3. **seeds 核验**：env 20261601、feedback 20261601–10、evaluation **20261701–10**、arms 20261611–80、headroom 20261681–90；与禁用集交集 []；执行时重核。
4. **pilot**：执行前最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测冻结 canonical；Stage2 pilot 仅历史参考；超 caps→compute_budget_exceeded。
5. **schema/失败模板先写**：`schema_m3_s3_exec_v0_4.json` 运行前冻结。
6. **Stage3 通过后**：真实数据/湿实验不批；真实 Stage3 另立资源/预注册。

## 1. Feedback stream（写死）

- 每 replicate r=0..9：**feedback seed=20261601+r**；unit u=0..299 固定顺序：
  1. `h_u ~ p(h)`（第一随机数）；
  2. `a_u ~ w(·|h_u)`（同 seed 流第二随机数）；
  3. `Y_u ~ Bernoulli(μ(h_u,a_u))`（第三随机数）；
  记录 `(h_u,a_u,Y_u)`；canonical `"h,a,Y\n"`；**7 arms 复用同一流**，任何 arm 不得改。
- **Shared-score allocation policy（Stage2/C213 定义，写死）**：
  - `Q(h,a) = p(h) · π_2(a|h)^2 · [Var(Y|h,a) + (μ(h,a) − m_wrong(h,a))^2] / b(a|h)`；
  - `w(a|h) = Q(h,a) / Σ_{a'∈legal(h)} Q(h,a')`；
  - `Var(Y|h,a)=μ(h,a)(1−μ(h,a))`；p=[.3,.4,.3]、μ/b 矩阵、π_2、m_wrong=.5、C_H=20、b_min=1e-6 冻结自 Stage2；
  - **spatial support**：legal 动作要求 b(a|h)>0 且 b(a|h)≥b_min；Q finite/nonnegative；C_H=20 仅诊断 H clipping、不用于 allocation weights；unsupported→`design_invalid: support/positivity`；
  - 引用 Stage2/C213 `m3_stage2.json` SHA `36C4DF12…`、schema `0E46DEC0…`；S_shared_score 规则 `w∝p·π²(Var+(μ−m)²)/b`。
- 环境：H=3/A=3/Y binary；p/μ/b/π_2/m_wrong/C_H=20 冻结；合成不推广真实。

## 2. Evaluation stream（写死；独立）

- **evaluation seed=20261701+r**（r=0..9），与 feedback seed 独立；unit j=0..299 固定顺序：
  1. `h_j ~ p(h)`（第一随机数）；
  2. `a_j ~ w(·|h_j)`（同 seed 流第二随机数）；
  - canonical record `"h,a\n"`；evaluation utility 用 **known-truth μ(h,a) 精确值**（无噪声 Y 标签）；target 不作标签；
  - 评价不用于拟合/更新/选择；**7 arms 复用同一评价流**；任何 arm 不得改评价。
- 每 replicate 300 feedback+300 evaluation；R=10；总 3,000/3,000；per-arm 300/300。

## 3. per-arm 输出/三 SHA/leakage

- 16 字段：arm_id、replicate_id、update_rule、allocation_policy、n_feedback、n_eval、tuning_configs、cost_ledger、per_replicate_regret、mean_DeltaR、CI95、holm_p、pass、feedback_stream_sha、evaluation_stream_sha、allocation_policy_sha。
- canonical：feedback `"h,a,Y\n"`、evaluation `"h,a\n"`（整数、固定顺序、UTF-8、SHA256 uppercase）；policy token `shared_score_fixed_same_feedback_stream` SHA256。
- **每 replicate 7 arms 的 feedback/evaluation SHA 必须逐字节一致**；不一致→`design_invalid: leakage`/stop、不报学习比较；`unit_checks` 布尔不替代 SHA。
- toy canonical 保持：feedback `[(0,1,1),(1,2,0),(2,0,1),(0,2,0)]`→`0696F595…`；evaluation `[(0,1),(1,0),(2,1),(1,2)]`→`01063FFF…`；policy→`6A976C3C…`；本轮重算一致（不训练）。

## 4. 样本/arms/主端点/失败/预算（保持）

- seeds：feedback 20261601–10；evaluation 20261701–10；arms 20261611–80；headroom 20261681–90；env 20261601；overlap=[]、unique=true；两跑同 seeds/独立进程/逐字节/telemetry 单独。
- 7 arms（纯 learner/固定 shared-score/无 optimal allocation）：A_candidate_score_tilt、A_full_history_retrain、A_importance_weighting、A_DR_targeting、A_TMLE_targeting、A_value_aware、**A_standard_DR_TMLE**。
- primary=candidate vs A_standard_DR_TMLE；δ=.05；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm；MDE .04798268≤.05、n_req278；headroom 先检；6,282/1,573 仅 Fisher-z；不换端点。
- G1–G6；13 失败类别（含 chain_mismatch）；caps 1800 s/2 h/8 GB/0 wells；schema 先写；执行前最终实现 pilot 实测冻结；闭环成本同账；失败只写类别。
- 边界：只更新功能均值≠细胞动力学；无序贯→不称序贯 DR；支撑研究/机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 35 文件链/Stage1/Stage2；② seeds（含 eval 20261701–10）/两跑；③ 反馈/评价生成与 allocation 公式/support/采样写死；④ per-arm 16 字段/三 SHA/leakage；⑤ primary/family6/MDE/headroom/6,282；⑥ G1–G6/13 失败/caps/schema/pilot/闭环/停止/边界。Stage3 执行须另立独立挑战+Lead 批准。
