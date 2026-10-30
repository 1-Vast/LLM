# record_N1_EXEC.md —— R203-N1 效果执行预注册记录（不运行效果）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-140（R203-N1-EXEC-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-n1-effect-prereg/` 与 `tmp/`；**未改 N1 预注册/实现/A-B-D 产物**；**未运行效果比较/未报告方法差异**；机制账 only；0 wells/compute-only。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 独立执行 seeds（不复用 20261061/62/63；n_units=300/R=50；两跑独立进程） | ✅ dataset seeds **20261070–20261119**（r=0..49）；方法 seeds **20262000+r*10+idx**；headroom seeds **20261130–20261149**（20 reps）；与 gate seeds 重叠 `[]`、唯一 `true`；两跑同 seeds 独立进程、结果 JSON 逐字节一致检查 |
| ② M vs B1–B6 等预算 + B2 等价审计 | ✅ T=6/每轮 1 feedback/调参≤20/特征/prior/初始数据/seed 统一；B2 同信息同预算；执行时最终 runner 再确认 initial-data hash/menus/query/prior/tuning/seed |
| ③ primary=paired held-out regret D_i=R_i(M)−R_i(B2)、δ=.05；成功 mean≤−δ ∧ CI upper<0 ∧ Holm 显著；secondary Holm family | ✅ 写死；family=6（M vs B1–B6），Holm α=.05；primary=M vs B2；不换端点；headroom 预检（headroom<δ→unreachable_gate；近满分→另立 budget-to-target） |
| ④ 分析单位/配对/cluster/MDE | ✅ n_units=300、R=50、deff=2.2、n_eff=136.36、保守 MDE80=.04798≤.05、n_req278≤300；cluster-robust SE 按 replicate G=50；报告 mean/CI/Holm p |
| ⑤ 预算/资源/两跑/telemetry | ✅ 300×50×7；caps 1800 s/2 h/8 GB/0 wells；C204 pilot .0455 s/rep、20.48 s main、.04 GB；执行前 2-rep pilot 复核；两跑结果 JSON 无 telemetry；wall/CPU/内存只写 timing 文件 |
| ⑥ schema/失败类别 | ✅ per_method/replicate selection regret/U/chosen/oracle/成本账；禁列未预注册终点；失败只写 design_invalid/预注册类别、不报方法差异 |
| ⑦ 边界 | ✅ 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；执行须另立挑战+Lead 批准 |
| ⑧ 执行前必核 | ✅ exec_plan.py 核验 v0.4+C204+V4 spec+G1–G7：chain_pass=true/full_pass=true；不匹配→stop chain_mismatch |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~10:57 | 读 task-140 并 claim；读 DECISION_R203_N1_PREREG、C204 report/n1_gates.json/timing/schema、N1 v0.4 链、R203-P1/ERRATA |
| ~10:59 | 写 `exec_plan.py`（链核验、种子分配、精度/headroom、分析/多重性、预算/schema/失败树；不跑方法效果） |
| ~11:00 | 首跑链核验 1 处 mismatch（PROBLEM_N1_v0_4 expected 常量少一位）→ 修为实际 SHA，重跑 chain_pass=true/full_pass=true |
| ~11:02 | 写 PROBLEM/DESIGN v0.4；exec_plan 两跑 `exec_plan.json` 逐字节一致（`BECEE7F8…`） |
| ~11:06 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露

1. **只规划、不执行效果**：exec_plan.py 仅做 SHA 链核验、seed 分配（含首次 RNG draw 的确定性哈希）、MDE/headroom/budget 算术、分析/多重性/schema/失败树冻结；**不生成数据、不跑方法、不计算 regret/任何效果指标**。
2. **链核验**：15 个文件 SHA（v0.4 7 个 + C204 8 个）与冻结常量一致；V4_MODEL_SPEC `A69B845D…` 匹配；V4 gate 数值（503.04246827/64.42138097/[376.78,629.31]）、G1/G2/G3/G7 与 C204 `n1_gates.json`/`timing_n1_gates.json` 一致；初次核验发现 expected 常量手误（PROBLEM_N1_v0_4 SHA 少一位），已修正为实际值；**执行前必须重跑核验**。
3. **种子独立性**：execution seeds 20261070–20261119、headroom 20261130–20261149、method 20262000+ 段；与 gate seeds {20261030,20261061,20261062,20261063} 交集 **[]**；全部唯一；执行时不得改 seed。
4. **分析口径**：primary 用 paired held-out regret；cluster-robust SE 按 replicate；保守 MDE .04798 基于单 replicate n_units=300/deff2.2（冻结口径），实际 50 replicates 精度不差于该保守值；两套均报告。
5. **边界**：机制账 only；无真实/响应数据；无 A/B 资源；0 wells；未报告方法差异；执行须另立独立挑战+Lead 批准。
6. **确定性**：`exec_plan.json` 两跑逐字节一致；JSON 键排序/无时间戳/无 telemetry。

## 3. 关键冻结数字

- Seeds：exec **20261070–20261119**（R=50）；headroom **20261130–20261149**（20）；method **20262000+**；gate 禁用 20261030/61/62/63。
- n_units=300；R=50；methods=7；T=6（fit4/held-out2）；m=5。
- deff=2.2；n_eff=136.36；SD(D)=.20；**MDE80=0.04798268≤.05**；n_req(cluster)=**278≤300**。
- δ=.05；primary M vs B2；family=6 Holm；成功三项 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05。
- Budget：300×50×7；caps 1800 s/2 h/8 GB；0 wells；C204 pilot .0455 s/rep、20.48 s main、.04 GB；B2 audit PASS。
- Chain：v0.4+C204 全匹配；V4 spec `A69B845D…`；V4 gate seed 20261062；G1 .0488/.05187354；G2 1.000；G3 143/600/140/3；G7 .0455/20.48/.04。
- Schema：top/per_method/summary 字段冻结；禁列预测/预算/top-k/探索/药理等字段；失败只写类别。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_EXEC.md` | `9993F0BA259AD22CEDC63D816DB168449D0E8806E8B995903D941A6DF16D0B7B` |
| `DESIGN_N1_EXEC.md` | `29F784E7E71CEBEC3873097BFAAD1A080FCB26F49F4D6C78D2A14D16A538F5F6` |
| `exec_plan.py` | `843DEC399D88DF88FE733D2A286CC75E8655E73CD1A7A483B250048AB0346E27` |
| `exec_plan.json` | `BECEE7F8B64A0919CE435AAE614A911E73D01AA0C9BD6347DF1CFF1E1BFBBA39` |
| report/record/usage | 见 `usage_N1_EXEC.json` |
| C204 只读链（未改） | n1_gates.json `529C1D2E…`；run_n1_gates.py `D2AA831F…`；timing `5A52E42F…` 等（见 exec_plan.json） |

## 5. 缺口与下一步

- **未运行效果**；exec_plan 只有规划算术/种子/链核验。
- 执行前须：独立挑战 + Lead 批准 + 重跑链核验 + headroom 预检 + 最终 runner G7 pilot 复核；任何一步失败按预注册停止。
- 机制账 only：不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验。
