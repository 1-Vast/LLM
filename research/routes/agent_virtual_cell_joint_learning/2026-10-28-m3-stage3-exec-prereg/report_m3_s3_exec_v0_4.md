# report_m3_s3_exec_v0_4 —— R204-M3-S3.3 修订预注册报告（evaluation seed/allocation 公式写死；不运行）

2026-10-28。对象：R204-M3 Stage3 合成执行预注册 v0.4。依据：M3-S3.2-C1 复核（revise，必改 1–3）、M3 v0.2 链、Lead Stage1/Stage2 决定、Stage1/C209、Stage2/C213、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216。
**状态：预注册修订草案；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.4 新文件；v0.1–v0.3 保留不改）

- 问题定义：[PROBLEM_M3_S3_EXEC_v0_4.md](PROBLEM_M3_S3_EXEC_v0_4.md)（`EAB4E85D…`）
- 执行设计：[DESIGN_M3_S3_EXEC_v0_4.md](DESIGN_M3_S3_EXEC_v0_4.md)（`5C6CFF4A…`）
- 规划/骨架：[exec_plan_m3_s3_v0_4.py](exec_plan_m3_s3_v0_4.py)（`3338F70D…`）→ [exec_plan_m3_s3_v0_4.json](exec_plan_m3_s3_v0_4.json)（`9FB57C5B…`）
- schema：[schema_m3_s3_exec_v0_4.json](schema_m3_s3_exec_v0_4.json)（`3DEFD258…`）
- 记录/用量：[record_m3_s3_exec_v0_4.md](record_m3_s3_exec_v0_4.md)、[usage_m3_s3_exec_v0_4.json](usage_m3_s3_exec_v0_4.json)

## 1. 必改落实

| # | 挑战问题 | v0.4 落实 |
|---|---|---|
| ① **evaluation seed 未写死** | **写死 evaluation seed = `20261701 + r`（20261701–20261710）**，与 feedback seed `20261601+r` 独立；**300 units 固定顺序 j=0..299**：h_j~p(h)（第一随机数）→a_j~shared-score w(·\|h_j)（同流第二随机数）；canonical `"h,a\n"`；evaluation utility 用 known-truth μ(h,a) 精确值（无噪声 Y 标签）；不用于拟合/选择；7 arms 复用；写入 sample_semantics/stage3/schema |
| ② **allocation 只有 token** | **写死 Q 公式** `Q(h,a)=p(h)·π_2(a\|h)^2·[Var(Y\|h,a)+(μ(h,a)−m_wrong(h,a))^2]/b(a\|h)`、`w=Q/Σ_legal Q`、`Var=μ(1−μ)`；p/μ/b/π_2/m_wrong/C_H=20/b_min=1e-6 冻结自 Stage2；采样顺序 h→a→Y；support b>0、b≥1e-6、Q finite；**引用 Stage2/C213 `m3_stage2.json` `36C4DF12…`、schema `0E46DEC0…`** 与 S_shared_score 规则；feedback SHA 可独立复算 |
| ③ **sample_semantics/schema 同步** | sample_semantics 加 `feedback_seed_rule/evaluation_seed_base/evaluation_seed_rule/evaluation_stream_rule/allocation_policy_rule`；stage3 加 `allocation_policy_spec/evaluation_stream_spec`；schema 加同字段；per-arm 三 SHA；不一致→`design_invalid: leakage`/stop；toy canonical 保持（feedback `0696F595…`/evaluation `01063FFF…`/policy `6A976C3C…`） |
| ④ 保持 | 35 文件链/Stage1/Stage2；seeds（env 20261601、feedback 20261601–10、evaluation 20261701–10、arms 20261611–80、headroom 20261681–90；overlap=[]/unique）；R=10/300/300/3,000；7 arms 纯 learner/固定 shared-score/无 optimal allocation；primary/family6/MDE .04798268/n_req278/headroom/cluster/6,282；G1–G6/13 失败/caps/schema/pilot 冻结/闭环/停止/边界 |

## 2. 链/Stage1/Stage2（已通过）

- **35 文件 SHA 全匹配**（chain_pass=true、mismatches=0）：M3 v0.2 8+Lead Stage1；Stage1/C209 8；Stage2 exec v0.2 8+Lead Stage2；Stage2/C213 9（`36C4DF12…`、60/60 per-arm、failure_category null）；Stage1/Stage2 状态 PASS。
- 不匹配→`design_invalid: chain_mismatch`；执行时重核。

## 3. 反馈/评价/分配（写死）

- Feedback：seed **20261601+r**；unit u=0..299 顺序 h~p、a~w(·\|h)、Y~Bernoulli(μ)；记录 `(h,a,Y)`；7 arms 同一流；任何 arm 不得改。
- Allocation：`Q(h,a)=p(h)·π_2(a\|h)^2·[Var+(μ−m_wrong)^2]/b(a\|h)`；`w=Q/Σ_legal Q`；`Var=μ(1−μ)`；p/μ/b/π_2/m_wrong/C_H=20/b_min=1e-6 冻结；support b>0、b≥1e-6；C_H 仅诊断；unsupported→support/positivity；引用 Stage2 C213 SHA。
- Evaluation：seed **20261701+r**；unit j=0..299 顺序 h~p、a~w(·\|h)；canonical `"h,a\n"`；用已知 μ(h,a) 精确评估；评价独立、target 不作标签；7 arms 复用。
- Toy canonical 保持：feedback `[(0,1,1),(1,2,0),(2,0,1),(0,2,0)]`→`0696F595…`；evaluation `[(0,1),(1,0),(2,1),(1,2)]`→`01063FFF…`；policy→`6A976C3C…`；重算一致。

## 4. Per-arm/端点/失败/预算（保持）

- per-arm 16 字段（n_feedback/n_eval/tuning/cost/regret/mean ΔR/CI95/Holm p/pass + feedback/evaluation/allocation policy SHA）；7 arms 两 SHA 一致否则 leakage/stop。
- primary=candidate vs A_standard_DR_TMLE；δ=.05；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm；MDE .04798268≤.05、n_req278；headroom 先检；6,282/1,573 仅 Fisher-z；不换端点。
- G1–G6；13 失败类别（含 chain_mismatch）；caps 1800 s/2 h/8 GB/0 wells；schema 先写；执行前最终实现 Stage3 pilot（2×7×300）实测冻结；Stage2 pilot 仅历史参考；闭环成本同账；JSON 无 telemetry。
- **单测（仅链/算术，不训练）全 PASS**：chain=35/35；Stage1/Stage2 PASS；failure=13；family=6；arms=7 纯 learner/无 optimal allocation；**evaluation seeds 20261701–10 与 feedback 独立/overlap=[]**；**allocation 公式/support/采样/schema 字段存在**；**Stage2 C213 SHA 匹配**；canonical 示例重算一致；seeds overlap=[]；sample 3,000/3,000；MDE≤δ/n_req278。

## 5. 边界

支撑研究/机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；**禁止把 learner 比较写成 allocation 比较或反之、把 allocation/feedback 优势算进 primary**；Stage3 执行须另立独立挑战+Lead 批准。

## 6. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC_v0_4.md` | `EAB4E85DD044E1A0EC5151EBBA1715C063F06F90378BFBCB196C5EB2B57BD27E` |
| `DESIGN_M3_S3_EXEC_v0_4.md` | `5C6CFF4A2C26CA1EA4E177E91A2CA4BFE04D8AD5FEDB768CF6F6EFC0D58C4240` |
| `exec_plan_m3_s3_v0_4.py` | `3338F70DC1C4AC0FC87173656C4BB7941D5ECC1F69BCD0102BEFBC0DEC282816` |
| `exec_plan_m3_s3_v0_4.json` | `9FB57C5B7E4AF73933AA4F40D918031FFBC6D96448E5A48D77CFDD118A9CBC10` |
| `schema_m3_s3_exec_v0_4.json` | `3DEFD25876480409297EC9995F44DC3290B0E4E524185C85E0C1DE69E4C4E6FB` |
| report/record/usage | 见 `usage_m3_s3_exec_v0_4.json` |

**确定性**：`exec_plan_m3_s3_v0_4.json` 与 `schema_m3_s3_exec_v0_4.json` 两跑逐字节一致；JSON 无 telemetry。

## 7. 建议

1. **建议轻量复核**：evaluation seed=20261701+r 与 feedback 20261601+r 独立、300 units 顺序/canonical 可复算；shared-score Q 公式/采样/support 与 Stage2 C213 SHA 对齐；sample_semantics/schema 字段完整；toy canonical 保持；其余 35 链/样本/7 arms/primary/family6/预算/失败/边界不变。
2. 复核通过 + Lead 批准后才可执行 **Stage3 合成学习比较**（支撑研究/机制账、compute-only、0 wells）；执行前重核 35 文件链、最终实现 pilot 实测冻结、per-arm 三 SHA 一致检查、两跑/schema/失败模板核验。
3. **不做**：训练/效果/真实数据/湿实验/代码晋升/旧判定修改/恢复停止实验；不把 learner 比较写成 allocation 比较或反之。
