# PROBLEM_M3_S3_EXEC_v0_4 —— R204-M3-S3.3 Stage3 合成执行预注册（evaluation seed/allocation 公式写死；不运行）

2026-10-28。对象：R204-M3 Stage3 合成执行预注册（固定反馈纯 learner 比较 + 闭环成本）。本文件修正 v0.1–v0.3（保留不改），落实 M3-S3.2-C1 必改 1–3：**evaluation stream seed/派生写死**、**shared-score feedback allocation 公式/采样/support 写死**、**sample_semantics/schema 同步**。方案A（7 arms 纯 learner/固定 shared-score/同反馈同评价；无 optimal allocation arm）保持不变。依据：M3 v0.2 链、Lead Stage1/Stage2 决定、Stage1/C209、Stage2/C213（`m3_stage2.json` `36C4DF12…`）、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216。
**状态：预注册修订草案 v0.4；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。Stage3 执行须另立独立挑战+Lead 批准。**

## 0. M3-S3.2-C1 必改落实

| # | 挑战问题 | v0.4 修正 |
|---|---|---|
| ① **evaluation stream 只写"独立子流/固定派生"** | **写死 evaluation seed：`20261701 + r`（r=0..9，即 20261701–20261710）**；与 feedback seed `20261601+r` 独立；**300 units 固定顺序 j=0..299**：h_j~p(h)（第一随机数）；a_j~shared-score w(·\|h_j)（同 seed 流第二随机数）；canonical record `"h,a\n"`；evaluation utility 用 known-truth μ(h,a) 精确值（不用噪声 Y 标签）；评价不用于拟合/更新/选择；**7 arms 复用同一评价流** |
| ② **shared-score allocation 只有 token 名** | **写死 Q 公式**：`Q(h,a)=p(h)·π_2(a\|h)^2·[Var(Y\|h,a)+(μ(h,a)−m_wrong(h,a))^2]/b(a\|h)`；`w(a\|h)=Q/Σ_legal Q`；`Var=μ(1−μ)`；p/μ/b/π_2/m_wrong/C_H=20/b_min=1e-6 冻结自 Stage2；采样顺序 h→a→Y；support b>0、b≥b_min、Q finite；引用 **Stage2/C213 `m3_stage2.json` SHA `36C4DF12…`、schema `0E46DEC0…`**、S_shared_score 规则；7 arms 同一 policy、feedback SHA 可独立复算 |
| ③ **sample_semantics/schema 同步** | `sample_semantics` 加 `evaluation_seed_base/evaluation_seed_rule/evaluation_stream_rule/feedback_seed_rule/allocation_policy_rule`；`stage3` 加 `allocation_policy_spec/evaluation_stream_spec`；schema 加同字段；per-arm 三 SHA（feedback/evaluation/allocation policy）；**不一致→`design_invalid: leakage`/stop**；toy canonical 保持（feedback `0696F595…`、evaluation `01063FFF…`、policy `6A976C3C…`） |
| ④ 保持 | 35 文件链/Stage1/Stage2；seeds（env 20261601、reps 20261601–10、arms 20261611–80、headroom 20261681–90、eval 20261701–10；overlap=[]/unique）；R=10/300/300/总 3,000/3,000；7 arms 纯 learner/固定 shared-score/无 optimal allocation；primary candidate vs A_standard_DR_TMLE、family=6 Holm、δ=.05、MDE .04798268/n_req278/headroom/cluster/6,282 仅 Fisher-z；G1–G6/13 失败/caps 1800 s/2 h/8 GB/0 wells/schema 先写/pilot 实测冻结/闭环成本/停止/边界 |

## 1. 链核验（执行前；不匹配→stop）

`exec_plan_m3_s3_v0_4.py` 只读核验 **35 文件 SHA 全匹配（chain_pass=true、mismatches=0）**：M3 v0.2 8+Lead Stage1；Stage1/C209 8；Stage2 exec v0.2 8+Lead Stage2；Stage2/C213 9（`m3_stage2.json` `36C4DF12…`，60/60 per-arm、failure_category null、no_effect_results=true）。不匹配/状态不符→`design_invalid: chain_mismatch`；执行时重核。

## 2. 独立 seeds（写死）

| 用途 | seeds |
|---|---|
| 环境 | **20261601** |
| feedback | **20261601–20261610**（replicate r） |
| evaluation（独立） | **20261701–20261710**（evaluation r = 20261701+r） |
| arms | **20261611–20261680**（20261611+10a+r） |
| headroom | **20261681–20261690** |
| 两跑 | 同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独 |

禁用 M3 Stage1 20261112/13、20261200；M3 Stage2 20261401–20261470；M1 Stage1/Stage2、M2、N1 禁用集；本地 overlap=[]、unique=true；执行时不得改 seed。

## 3. 固定反馈/评价生成（写死）

- **Feedback**：每 replicate seed **20261601+r**；按 **shared-score allocation** 公式与采样顺序生成 **300 条 (h,a,Y)**；7 arms 完全复用；任何 arm 不得改 feedback/分配。
- **Allocation 公式（冻结）**：`Q(h,a)=p(h)·π_2(a|h)^2·[Var(Y|h,a)+(μ(h,a)−m_wrong(h,a))^2]/b(a|h)`；`w(a|h)=Q(h,a)/Σ_{a'∈legal(h)}Q(h,a')`；`Var=μ(1−μ)`；p/μ/b/π_2/m_wrong/C_H=20/b_min=1e-6 取自 Stage2（引用 `m3_stage2.json` `36C4DF12…`、`schema_m3_stage2_run.json` `0E46DEC0…`）；support=b>0 且 b≥1e-6、Q finite；C_H=20 仅诊断 H clipping、不用于 allocation weights；unsupported→support/positivity。
- **采样顺序**：unit u=0..299 固定顺序：h_u~p(h)（第一随机数）→a_u~w(·|h_u)（同流第二随机数）→Y_u~Bernoulli(μ(h_u,a_u))（第三随机数）；记录 `(h_u,a_u,Y_u)`；7 arms 同一流。
- **Evaluation**：seed **20261701+r**；unit j=0..299 固定顺序：h_j~p(h)（第一随机数）→a_j~shared-score w(·|h_j)（同流第二随机数）；canonical record `"h,a\n"`；evaluation utility 用 known-truth μ(h,a) 精确值（无噪声 Y 标签）；评价不用于拟合/更新/选择；7 arms 复用同一评价流；target 不作标签。
- 环境复用 Stage2 冻结：H=3/A=3/Y binary；p/μ/b/π/m/C_H=20。

## 4. per-arm 输出/端点/失败/预算（保持）

- per-arm **16 字段**：arm_id、replicate_id、update_rule、allocation_policy、n_feedback、n_eval、tuning_configs、cost_ledger、per_replicate_regret、mean_DeltaR、CI95、holm_p、pass、**feedback_stream_sha、evaluation_stream_sha、allocation_policy_sha**；7 arms 两 SHA 必须逐字节一致，否则 `design_invalid: leakage`/stop；toy canonical 保持。
- Primary=candidate vs A_standard_DR_TMLE；δ=.05；成功 mean ΔR≤−δ ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm；MDE .04798268≤.05、n_req278；headroom 先检；6,282/1,573 仅 Fisher-z；不换端点；不把 allocation/feedback 优势算进 primary。
- G1–G6；13 失败类别（含 chain_mismatch）；caps 1800 s/2 h/8 GB/0 wells；schema 先写；执行前最终实现 Stage3 pilot 实测冻结；Stage2 pilot 仅历史参考；JSON 无 telemetry；闭环成本同账。

## 5. 停止/边界

- 标准 DR/TMLE learner（固定分配）等预算复制/超过→`no_increment`/撤；π=b→H=1；共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration；评价复用/**per-arm SHA 不一致**→leakage；两跑/链/预算→对应类别；不改旧判定/门槛；不放宽/改阈值/换端点。
- **禁止**把 learner 比较写成 allocation 比较或反之；把 allocation/feedback 优势算进 primary；改旧判定/阈值；放宽容差/换端点；晋升代码；真实数据/湿实验。
- 只更新功能均值≠细胞动力学；无序贯→不称序贯 DR；支撑研究/机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；Stage3 执行须另立独立挑战+Lead 批准。
