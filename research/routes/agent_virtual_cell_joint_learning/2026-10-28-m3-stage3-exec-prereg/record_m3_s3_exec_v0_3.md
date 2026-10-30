# record_m3_s3_exec_v0_3.md —— R204-M3-S3.2 修订预注册记录（per-arm 流 SHA/输出字段；不运行）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-185（R204-M3-S3.2）· 日期 2026-10-28
只写 `research/2026-10-28-m3-stage3-exec-prereg/` 下 v0.3 文件与 `tmp/`；**未改 v0.1/v0.2 产物/M3 预注册/Stage1/Stage2/M1/M2/N1/A-B-D**；**未运行 Stage3 训练/效果/真实数据**；支撑研究/机制账 only；compute-only、0 wells。

## 0. 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① per-arm stream SHA 落 schema | ✅ `arm_fields`/per-arm 结果含 **feedback_stream_sha/evaluation_stream_sha/allocation_policy_sha**；canonical 写死（`"h,a,Y\n"`/`"h,a\n"`、UTF-8、固定顺序、SHA256 uppercase）；7 arms 两 SHA 必须一致，否则 `design_invalid: leakage`/stop；unit_checks 布尔保留但不替代 SHA |
| ② 固定反馈 seed/policy 写死 | ✅ 每 replicate seed 20261601+r 生成 300 反馈/300 评价；评价独立、target 不作标签；A_standard_DR_TMLE allocation 固定 shared-score（无 optimal allocation）；任何 arm 不得改 feedback/分配 |
| ③ 补 per-arm 输出字段 | ✅ 16 字段：arm_id、replicate_id、update_rule、allocation_policy、n_feedback、n_eval、tuning_configs、cost_ledger、per_replicate_regret、mean_DeltaR、CI95、holm_p、pass、feedback_stream_sha、evaluation_stream_sha、allocation_policy_sha；两跑 JSON 逐字节；无 telemetry |
| ④ 保持 | ✅ 35 文件链/Stage1/Stage2；seeds/两跑；R=10/300/300/3,000；7 纯 learner arms/固定 shared-score/无 optimal allocation；primary/family6/MDE/n_req278/headroom/cluster/6,282；G1–G6/13 失败/caps/schema/pilot 冻结/闭环/停止/边界 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~15:30 | 读 task-185 并 claim；读 M3-S3.1-C1 复核、v0.2 产物、M3 链 |
| ~15:34 | 复制 v0.2→v0.3 脚本；Python patch：paths、canonical 函数/示例、per-arm 16 字段、schema 三 SHA 字段/canonical spec、checks/all_pass、task/输出/schema_file、stop 措辞 |
| ~15:37 | 运行成功：chain=35/35、Stage1/Stage2 PASS、arms=7 纯 learner、family=6、per-arm 16 字段、三 SHA schema 字段、canonical 示例重算一致、seeds overlap=[]、all_pass=true；两跑 plan/schema 逐字节一致 |
| ~15:41 | 写 PROBLEM/DESIGN/report/record/usage v0.3；标 completed + send_message |

## 2. 实现与披露

1. **只做规划/算术/骨架单测**：35 文件链核验、seeds/固定反馈 sample 语义、7 arms、primary/Holm/headroom/MDE、闭环成本、G1–G6/13 失败、canonical SHA spec/示例、schema、算术单测；**不训练、不生成/比较方法结果、不计算 regret/效果**。
2. **per-arm 流 SHA**：schema/per-arm 结果含 feedback/evaluation/allocation policy SHA；canonical 写死；7 arms 两 SHA 必须一致；不一致→leakage/stop；布尔不替代 SHA。
3. **固定反馈**：seed/policy 写死；300 反馈/300 评价/replicate；评价独立、target 不作标签；A_standard_DR_TMLE allocation 固定 shared-score；任何 arm 不得改 feedback/分配。
4. **per-arm 16 字段**：含 n_feedback/n_eval/tuning/cost/regret/mean ΔR/CI95/Holm p/pass + 三 SHA。
5. **保持**：方案A/7 纯 learner arms/primary/family6/样本/预算/35 链/seeds/两跑/G/失败/闭环/停止/边界不变。
6. **确定性**：`exec_plan_m3_s3_v0_3.json`（`0A8D2DD2…`）与 `schema_m3_s3_exec_v0_3.json`（`D408D1DC…`）两跑逐字节一致；JSON 无 telemetry。
7. **边界**：支撑研究/机制账；Stage3 不执行；未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 链：35/35 SHA、chain_pass=true；Stage1/C209 与 Stage2/C213 PASS。
- seeds：env 20261601；reps 20261601–10；arms 20261611–80；headroom 20261681–90；overlap=[]；unique=true。
- 样本：R=10；300 反馈/300 评价/replicate；总 3,000/3,000；7 arms 纯 learner/固定 shared-score。
- per-arm 字段：**16**；schema 含 feedback_stream_sha/evaluation_stream_sha/allocation_policy_sha 要求 + canonical spec + leakage 失败。
- canonical 示例（不训练）：feedback `[(0,1,1),(1,2,0),(2,0,1),(0,2,0)]`→`0696F595…`；evaluation `[(0,1),(1,0),(2,1),(1,2)]`→`01063FFF…`；policy→`6A976C3C…`；重算一致。
- 端点：primary vs A_standard_DR_TMLE；δ=.05；family=6 Holm；MDE .04798268、n_req278；6,282/1,573 仅 Fisher-z；headroom 先检。
- 13 失败类别；caps 1800 s/2 h/8 GB/0 wells；schema 先写；pilot 最终实现实测冻结；闭环成本同账。
- 无训练/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC_v0_3.md` | `3D8B2E4BFB6D39598CA4DADAC9CE118442D076DE3BD319E38C2318187B2552B8` |
| `DESIGN_M3_S3_EXEC_v0_3.md` | `B98D4A302CFB5DFD7123B8FBAB87C57AAE34117397602F40FBA0106714BE8618` |
| `exec_plan_m3_s3_v0_3.py` | `FC40E25D9D840494C416D9A1346E232B5A24B571FD4FC80DF95838F5D0C040F6` |
| `exec_plan_m3_s3_v0_3.json` | `0A8D2DD252019AF98F325AF2E4505DA52A44A6F2EA42030E20DDFFC3C05B7499` |
| `schema_m3_s3_exec_v0_3.json` | `D408D1DC981B2B24FBACEE2AC28F81C0484ADFA0FB78FCA2AAE3BC956F36144F` |
| report/record/usage | 见 `usage_m3_s3_exec_v0_3.json` |
| v0.1/v0.2 只读（未改） | v0.2 PROBLEM `814AE8BE…`、DESIGN `F7E525A6…`、script `9E0449E4…`、JSON `7E51CBA5…`、schema `F6AC87B9…` |

## 5. 缺口与下一步

- **Stage3 尚未执行**；本文件仅预注册修订，未训练/未读真实数据/无效果。
- 执行前：轻量复核 + Lead 批准 + 重核 35 文件链 + 最终实现 pilot 实测冻结 + per-arm feedback/eval SHA 一致检查 + seed/两跑/schema/失败模板核验。
- 真实数据另立资源/预注册；data readiness open（C203/C205/C210/C214）；支撑研究/机制账；不晋升代码/不改旧判定/不恢复停止实验。
