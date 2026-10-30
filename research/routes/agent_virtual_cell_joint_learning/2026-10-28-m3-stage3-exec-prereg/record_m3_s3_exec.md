# record_m3_s3_exec.md —— R204-M3 Stage3 合成执行预注册记录（固定反馈学习比较；不运行）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-180（R204-M3-S3-EXEC-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-m3-stage3-exec-prereg/` 与 `tmp/`；**未改 M3 预注册/Stage1/Stage2/M1/M2/N1/A-B-D**；**未运行 Stage3 训练/效果/真实数据**；支撑研究/机制账 only；compute-only、0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 链核验 M3 v0.2+Stage1+Stage2 链+Lead 决定；不匹配→chain_mismatch | ✅ 只读核验 **35 文件 SHA 全匹配**（M3 v0.2 8+Lead Stage1、Stage1 8、Stage2 exec v0.2 8+Lead Stage2、Stage2 run 9）；mismatches=0、chain_pass=true；Stage1/C209 与 Stage2/C213 状态 PASS；不匹配→`design_invalid: chain_mismatch` |
| ② 独立 seeds（不复用 M3 Stage1/Stage2 20261401–70、M1 Stage2、M2、N1；两跑同 seeds 独立进程逐字节、telemetry 分开） | ✅ env **20261601**、replicates **20261601–10**、arms **20261611–80**、headroom **20261681–90**；与禁用集交集 **[]**、unique=true；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独 |
| ③ Stage3 固定反馈比较学习（同 (h,a,Y) 总量/评价样本；candidate vs full-history/IW/DR/TMLE/value-aware；分配配套 shared-score 固定；同信息/反馈/调参≤20/caps/合法包；标准 DR/TMLE+最优分配等预算复制/超过→no_increment/撤写死） | ✅ R=10、300 feedback/300 eval/replicate、总 3,000/3,000；7 arms（候选+5 学习基线+**combined standard DR/TMLE+最优分配**）；固定 shared-score 分配、不比较分配；等价判定写死；不称新颖性 |
| ④ 主端点/分析（独立功能决策效用/后悔 δ=.05、headroom/MDE/cluster；6,282/1,573 仅 Fisher-z；主/次+Holm；不换端点） | ✅ primary=candidate vs combined standard；δ=.05；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm；n_eff136.36/MDE .04798268/n_req278；headroom 先检；6,282/1,573 仅 Fisher-z；不换端点 |
| ⑤ 闭环成本（反馈/实验包/计算同账，超限 stop） | ✅ 每 arm 300 feedback/300 eval/≤20 configs/caps 1800 s/2 h/8 GB/0 wells；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限→compute_budget_exceeded/stop |
| ⑥ G1–G6/13 失败类别/caps/schema/pilot 最终实现实测冻结 | ✅ G1–G6 写死；13 类（含 chain_mismatch）；caps；schema `schema_m3_s3_exec.json` 先写；执行前最终实现 Stage3 pilot（2×7×300）实测冻结；Stage2 pilot 仅历史参考；JSON 无 telemetry |
| ⑦ 停止/边界 | ✅ 标准 DR/TMLE/最优设计等价→no_increment/撤；π=b/共线/分离/无支持/截断按类别；功能均值≠细胞动力学；无序贯→不称序贯 DR；机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open C203/C205/C210/C214 |
| ⑧ report/record/usage+schema；标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~15:10 | 读 task-180 并 claim；读 M3 v0.2/Stage1/Stage2 exec/run、Lead 决定、ERRATA、R203 |
| ~15:15 | 写 `exec_plan_m3_s3.py`（35 文件链核验、独立 seeds、固定反馈 sample/7 arms、主端点/Holm/headroom/MDE、闭环成本、G1–G6/13 类、schema、预算/pilot 政策、算术单测） |
| ~15:18 | 运行成功：chain=35/35、Stage1/Stage2 PASS、seeds overlap=[]、family=6/arms=7、sample 3,000/3,000、MDE .04798268、all_pass=true |
| ~15:21 | 两跑 plan/schema 逐字节一致；写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做规划/算术/骨架单测**：35 文件链核验、seeds/固定反馈 sample 语义、7 arms、primary/secondary/Holm/headroom/MDE、闭环成本、G1–G6/13 失败类别、预算/pilot 政策、schema、链/状态/样本/精度算术单测；**不训练、不生成/比较方法结果、不计算 regret/效果**。
2. **链核验**：35/35 SHA 匹配；Stage1 failed_checks=[]/all_checks_pass/check19_pass；Stage2 status completed_allocation_diagnostics/60 per-arm/failure_category null/no_effect_results=true。
3. **seeds**：env 20261601、replicates 20261601–10、arms 20261611–80、headroom 20261681–90；与 M3 Stage1/Stage2 20261401–70、M1 Stage2、M2、N1 禁用集 overlap=[]；执行时重核。
4. **Stage3 设计**：固定反馈（同 300 条 (h,a,Y)/replicate、同 300 评价 units）、分配配套 shared-score 固定（不比较分配）、7 arms 含 combined standard DR/TMLE+最优分配；primary/Holm/headroom/MDE/6,282 边界；闭环成本；13 类失败。
5. **预算**：caps 1800 s/2 h/8 GB/0 wells；执行前最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测冻结 canonical；Stage2 pilot .100688/.078125/.001249 仅历史参考；JSON 无 telemetry。
6. **边界**：支撑研究/机制账；Stage3 不执行；未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
7. **确定性**：plan/schema 两跑逐字节一致；JSON 无时间戳；无 telemetry。

## 3. 关键结果

- 链：35/35 SHA、chain_pass=true；Stage1/C209 PASS；Stage2/C213 PASS（60/60 per-arm、`36C4DF12…`）。
- seeds：env 20261601；replicates 20261601–10；arms 20261611–80；headroom 20261681–90；overlap=[]；unique=true。
- sample：R=10；n_units=300；feedback=300；eval=300；总评价 3,000、总反馈 3,000；7 arms；每 arm 300/300/≤20/caps。
- 端点：primary candidate vs combined standard DR/TMLE+最优分配；δ=.05；family=6 Holm；headroom 先检；MDE .04798268、n_req278；6,282/1,573 仅 Fisher-z。
- 失败类别 13；caps/0 wells；schema 先写；pilot 最终实现实测要求；无训练/无效果。
- 本轮仅预注册草案。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC.md` | `C7B910875BD6C40C32B68E2F43582469AB50B0811A9177129354E1ECC77E5846` |
| `DESIGN_M3_S3_EXEC.md` | `C45925D0612A20559841E3D092948F398FF1633EFDE8E167A7735A337A1B6B65` |
| `exec_plan_m3_s3.py` | `FF1A3FB4C5D334655EC817560F86E8441C6F37F3CEADD29E2451BB394004C8C4` |
| `exec_plan_m3_s3.json` | `671F261736FA9AA57470292A2C44376FDD349268B83D2E1C9FCCB7290CD90705` |
| `schema_m3_s3_exec.json` | `B46D32490DE788BCE8FD8B93C04BE5475D0AAF4C585750BA46C6236F306DC81E` |
| report/record/usage | 见 `usage_m3_s3_exec.json` |
| 只读链（未改） | M3 v0.2+Stage1+Stage2 exec/run 35 文件（见 exec_plan JSON） |

## 5. 缺口与下一步

- **Stage3 尚未执行**；本文件仅预注册草案，未训练/未读真实数据/无效果。
- 执行前：独立挑战 + Lead 批准 + 重核 35 文件链 + 最终实现 pilot 实测冻结 canonical + seed/两跑/schema/失败模板核验。
- 真实数据另立资源/预注册；data readiness open（C203/C205/C210/C214）；支撑研究/机制账；不晋升代码/不改旧判定/不恢复停止实验。
