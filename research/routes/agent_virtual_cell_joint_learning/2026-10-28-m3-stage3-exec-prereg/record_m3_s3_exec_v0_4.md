# record_m3_s3_exec_v0_4.md —— R204-M3-S3.3 修订预注册记录（evaluation seed/allocation 公式；不运行）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-187（R204-M3-S3.3）· 日期 2026-10-28
只写 `research/2026-10-28-m3-stage3-exec-prereg/` 下 v0.4 文件与 `tmp/`；**未改 v0.1–v0.3 产物/M3 预注册/Stage1/Stage2/M1/M2/N1/A-B-D**；**未运行 Stage3 训练/效果/真实数据**；支撑研究/机制账 only；compute-only、0 wells。

## 0. 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① evaluation seed/派生写死 | ✅ **evaluation seed=20261701+r（20261701–20261710）**，与 feedback seed 20261601+r 独立；300 units 固定顺序 j=0..299：h~p（第一随机数）→a~w(·\|h)（同流第二随机数）；canonical `"h,a\n"`；evaluation utility 用 known-truth μ(h,a) 精确值；不用于拟合/选择；7 arms 复用；写入 sample_semantics/stage3/schema |
| ② shared-score allocation 写死 | ✅ Q 公式 `Q(h,a)=p(h)·π_2(a\|h)^2·[Var+(μ−m_wrong)^2]/b(a\|h)`；w=Q/Σ_legal Q；Var=μ(1−μ)；p/μ/b/π_2/m_wrong/C_H=20/b_min=1e-6 冻结自 Stage2；采样顺序 h→a→Y；support b>0、b≥1e-6、Q finite；C_H 仅诊断；引用 **Stage2/C213 `m3_stage2.json` `36C4DF12…`、schema `0E46DEC0…`** 与 S_shared_score 规则；feedback SHA 可独立复算 |
| ③ sample_semantics/schema 同步 | ✅ 加 feedback_seed_rule/evaluation_seed_base/evaluation_seed_rule/evaluation_stream_rule/allocation_policy_rule/allocation_policy_spec/evaluation_stream_spec；per-arm 三 SHA；不一致→`design_invalid: leakage`/stop；toy canonical 保持（feedback `0696F595…`/evaluation `01063FFF…`/policy `6A976C3C…`） |
| ④ 保持 | ✅ 35 文件链/Stage1/Stage2；seeds（含 eval 20261701–10；overlap=[]/unique）；R=10/300/300/3,000；7 纯 learner arms/固定 shared-score/无 optimal allocation；primary/family6/MDE/n_req278/headroom/cluster/6,282；G1–G6/13 失败/caps/schema/pilot 冻结/闭环/停止/边界 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~15:45 | 读 task-187 并 claim；读 M3-S3.2-C1 复核、v0.3 产物、Stage2 C213 链 |
| ~15:49 | 复制 v0.3→v0.4 脚本；Python patch：eval seed 20261701+r/规则、allocation Q 公式/sampling/support、sample_semantics/stage3/schema 字段、checks/all_pass、task/输出/schema_file |
| ~15:52 | 运行成功：chain=35/35、Stage1/Stage2 PASS、eval seeds 独立/overlap=[]、allocation 公式/schema 字段、Stage2 C213 SHA 匹配、toy canonical 保持、all_pass=true；两跑 plan/schema 逐字节一致 |
| ~15:56 | 写 PROBLEM/DESIGN/report/record/usage v0.4；标 completed + send_message |

## 2. 实现与披露

1. **只做规划/算术/骨架单测**：35 文件链核验、seeds（含 eval）、固定反馈/评价 sample 语义、shared-score allocation 公式、7 纯 learner arms、primary/Holm/headroom/MDE、闭环成本、G1–G6/13 失败、canonical/toy、schema、算术单测；**不训练、不采样方法、不执行分配/学习比较、不计算 regret/效果**。
2. **evaluation seed**：20261701+r 独立于 feedback 20261601+r；300 units 固定顺序/canonical；evaluation 用 known-truth μ 精确值、不用于拟合/选择；7 arms 复用；sample_semantics/stage3/schema 写死。
3. **allocation**：Q 公式/归一化/采样顺序/support/truncation 写死；引用 Stage2 C213 SHA；feedback SHA 可独立复算；不称 optimal allocation。
4. **per-arm/leakage**：16 字段 + 三 SHA；7 arms 两 SHA 一致否则 leakage/stop；toy canonical 保持并重算一致。
5. **确定性**：`exec_plan_m3_s3_v0_4.json`（`9FB57C5B…`）与 `schema_m3_s3_exec_v0_4.json`（`3DEFD258…`）两跑逐字节一致；JSON 无 telemetry。
6. **边界**：支撑研究/机制账；Stage3 不执行；未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 链：35/35 SHA、chain_pass=true；Stage1/C209 与 Stage2/C213 PASS。
- seeds：env 20261601；feedback 20261601–10；**evaluation 20261701–10**；arms 20261611–80；headroom 20261681–90；overlap=[]、unique=true。
- 样本：R=10；300 反馈/300 评价/replicate；总 3,000/3,000；7 纯 learner arms/固定 shared-score。
- allocation：Q 公式/采样/support 写死；Stage2 C213 `36C4DF12…`/schema `0E46DEC0…` 引用；Q finite/support 检查。
- evaluation：seed 20261701+r；300 units 顺序；canonical `"h,a\n"`；known-truth μ 精确评估；独立/不拟合。
- per-arm 16 字段/三 SHA/leakage；toy canonical 保持（`0696F595…`/`01063FFF…`/`6A976C3C…`）。
- 13 失败类别；caps 1800 s/2 h/8 GB/0 wells；schema 先写；pilot 最终实现实测冻结；闭环成本同账。
- 无训练/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC_v0_4.md` | `EAB4E85DD044E1A0EC5151EBBA1715C063F06F90378BFBCB196C5EB2B57BD27E` |
| `DESIGN_M3_S3_EXEC_v0_4.md` | `5C6CFF4A2C26CA1EA4E177E91A2CA4BFE04D8AD5FEDB768CF6F6EFC0D58C4240` |
| `exec_plan_m3_s3_v0_4.py` | `3338F70DC1C4AC0FC87173656C4BB7941D5ECC1F69BCD0102BEFBC0DEC282816` |
| `exec_plan_m3_s3_v0_4.json` | `9FB57C5B7E4AF73933AA4F40D918031FFBC6D96448E5A48D77CFDD118A9CBC10` |
| `schema_m3_s3_exec_v0_4.json` | `3DEFD25876480409297EC9995F44DC3290B0E4E524185C85E0C1DE69E4C4E6FB` |
| report/record/usage | 见 `usage_m3_s3_exec_v0_4.json` |
| v0.1–v0.3 只读（未改） | v0.3 PROBLEM `3D8B2E4B…`、DESIGN `B98D4A30…`、script `FC40E25D…`、JSON `0A8D2DD2…`、schema `D408D1DC…` |

## 5. 缺口与下一步

- **Stage3 尚未执行**；本文件仅预注册修订，未训练/未读真实数据/无效果。
- 执行前：轻量复核 + Lead 批准 + 重核 35 文件链 + 最终实现 pilot 实测冻结 + per-arm 三 SHA 一致检查 + seed/两跑/schema/失败模板核验。
- 真实数据另立资源/预注册；data readiness open（C203/C205/C210/C214）；支撑研究/机制账；不晋升代码/不改旧判定/不恢复停止实验。
