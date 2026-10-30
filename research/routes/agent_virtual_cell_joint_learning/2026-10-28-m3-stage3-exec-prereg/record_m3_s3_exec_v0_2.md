# record_m3_s3_exec_v0_2.md —— R204-M3-S3.1 修订预注册记录（方案A；不运行）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-183（R204-M3-S3.1）· 日期 2026-10-28
只写 `research/2026-10-28-m3-stage3-exec-prereg/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/M3 预注册/Stage1/Stage2/M1/M2/N1/A-B-D**；**未运行 Stage3 训练/效果/真实数据**；支撑研究/机制账 only；compute-only、0 wells。

## 0. M3-S3-EXEC-C1 方案A落实

| # | 要求 | 状态 |
|---|---|---|
| ① 统一纯 learner 比较 | ✅ **7 arms 全部同 shared-score/固定反馈/同评价**；`A_standard_DR_TMLE_optimal_allocation` → **`A_standard_DR_TMLE`（固定 allocation 下的标准 DR/TMLE learner）**；删除 optimal allocation arm（`no_optimal_allocation_arm=true`）；primary 纯 learner；无 A/B 混写 |
| ② primary/secondary/Holm 写死 | ✅ primary=candidate vs A_standard_DR_TMLE；secondary=full-history/IW/DR/TMLE/value-aware 5 个；**family=6 Holm**；成功 mean ΔR≤−δ ∧ CI upper<0 ∧ Holm p<.05 |
| ③ 冻结 fixed feedback 实现 | ✅ 每 replicate 固定 seed/分配 policy 生成 300 条 (h,a,Y)；7 arms 复用同一反馈/同一 300 评价；评价独立、target 不作标签；**任何 arm 不得改变 feedback/分配**；结果要求 per-arm feedback/evaluation stream SHA 相同，否则 leakage/stop；无法保证则 stop（不改方案B） |
| ④ 保持 | ✅ 35 文件链/Stage1/Stage2；seeds env 20261601/reps 20261601–10/arms 20261611–80/headroom 20261681–90、overlap=[]；R=10/300 反馈+300 评价/总 3,000/3,000；MDE .04798268/n_req278/headroom/cluster/6,282 仅 Fisher-z；G1–G6/13 失败/caps/schema/pilot 冻结/闭环成本；停止/边界 |
| ⑤ 禁止 | ✅ 未把 learner 比较写成 allocation 比较或反之；无 optimal allocation arm/feedback 优势进 primary；未改旧判定/阈值/端点/容差；未晋升代码；未执行真实数据/湿实验 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~15:10 | 读 task-183 并 claim；读 M3-S3-EXEC-C1 挑战、v0.1 产物、M3 v0.2/Stage1/Stage2 链 |
| ~15:14 | 复制 v0.1→v0.2 脚本；Python patch：重命名标准 arm、7 arms 统一 allocation policy、primary/family 更新、fixed-feedback 字段、schema arm_fields、checks；两次修正 allocation policy 字符串/标准 arm 以达 all_pass=true |
| ~15:18 | 运行成功：chain=35/35、Stage1/Stage2 PASS、arms=7（含 A_standard_DR_TMLE、无 optimal allocation）、family=6、policy same、feedback stream same、seeds overlap=[]、all_pass=true；两跑 plan/schema 逐字节一致 |
| ~15:22 | 写 PROBLEM/DESIGN/report/record/usage v0.2；标 completed + send_message |

## 2. 实现与披露

1. **只做规划/算术/骨架单测**：35 文件链核验、seeds、固定反馈 sample 语义、7 arms（纯 learner）、primary/Holm/headroom/MDE、闭环成本、G1–G6/13 失败、预算/pilot 政策、schema、链/状态/样本/精度/手臂一致性算术单测；**不训练、不生成/比较方法结果、不计算 regret/效果**。
2. **方案A**：删除 optimal allocation arm/比较，标准 baseline 为固定 allocation 下的 standard DR/TMLE learner；7 arms 全部 shared-score 固定；primary 为纯 learner 比较；family/Holm 按 6；不存在 learner×allocation 复合比较。
3. **固定反馈**：同一 (h,a,Y) 生成 seed/分配 policy；所有 arms 复用同 300 反馈/300 评价；评价独立、target 不作标签；任何 arm 不得改变 feedback/分配；结果要求 per-arm feedback/eval stream SHA 相同，否则 leakage/stop；无法保证则 stop。
4. **链/状态**：35/35 SHA 匹配；Stage1 failed_checks=[]/all_checks_pass/check19_pass；Stage2 completed_allocation_diagnostics/60 per-arm/failure_category null。
5. **确定性**：`exec_plan_m3_s3_v0_2.json`（`7E51CBA5…`）与 `schema_m3_s3_exec_v0_2.json`（`F6AC87B9…`）两跑逐字节一致；JSON 无 telemetry。
6. **边界**：支撑研究/机制账；Stage3 不执行；未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 链：35/35 SHA、chain_pass=true；Stage1/C209 与 Stage2/C213 PASS。
- seeds：env 20261601；replicates 20261601–10；arms 20261611–80；headroom 20261681–90；overlap=[]；unique=true。
- 样本：R=10；n_units=300；feedback=300；eval=300；总 3,000/3,000；7 arms；每 arm 300/300/≤20/caps。
- arms：7（候选+5 学习基线+**A_standard_DR_TMLE**）；**无 optimal allocation arm**；所有 arm allocation_policy 相同；all_arms_same_feedback_stream=true。
- 端点：primary candidate vs A_standard_DR_TMLE；δ=.05；family=6 Holm；MDE .04798268、n_req278；6,282/1,573 仅 Fisher-z；headroom 先检。
- 13 失败类别（含 chain_mismatch）；caps 1800 s/2 h/8 GB/0 wells；schema 先写；pilot 最终实现实测冻结；闭环成本同账。
- 无训练/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC_v0_2.md` | `814AE8BEE0D2E9C8BC497E293180E205C8DAD44DF02691539E8197A447F35615` |
| `DESIGN_M3_S3_EXEC_v0_2.md` | `F7E525A6824DCA273E14275165D7B7CD320EABE342D768FC22EA18420496829D` |
| `exec_plan_m3_s3_v0_2.py` | `9E0449E4D3ABF4ADFD63361298F9CFA350814B004F98E2B8A026C748E14256D8` |
| `exec_plan_m3_s3_v0_2.json` | `7E51CBA589A0EFBCF6972763614C94F937EA55F1EDB22164E59EF3B6B2827D02` |
| `schema_m3_s3_exec_v0_2.json` | `F6AC87B97645E7230CE5F95B527CF461ED4A74EA241E2A6691F31943A1C3DBE7` |
| report/record/usage | 见 `usage_m3_s3_exec_v0_2.json` |
| v0.1 只读（未改） | PROBLEM `C7B91087…`、DESIGN `C45925D0…`、script `FF1A3FB4…`、JSON `671F2617…`、schema `B46D3249…` |

## 5. 缺口与下一步

- **Stage3 尚未执行**；本文件仅预注册修订，未训练/未读真实数据/无效果。
- 执行前：轻量复核 + Lead 批准 + 重核 35 文件链 + 最终实现 pilot 实测冻结 canonical + feedback/evaluation stream SHA 检查 + seed/两跑/schema/失败模板核验。
- 真实数据另立资源/预注册；data readiness open（C203/C205/C210/C214）；支撑研究/机制账；不晋升代码/不改旧判定/不恢复停止实验。
