# record_m2_stage2_prep.md —— R204-M2 Stage2/3 设计准备记录（不运行效果）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-149（R204-M2-STAGE2-PREP）· 日期 2026-10-28
只写 `research/2026-10-28-m2-stage2-prep/` 与 `tmp/`；**未改 M2 预注册/Stage1/N1/A-B-D 产物**；**未运行方法比较/未读真实响应/未报告效果**；当前数据 `data_unavailable`；机制账 only；0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 数据就绪门（D1–D7、当前 data_unavailable、获取/重导清单、引用 request spec、不伪造联系人） | ✅ PROBLEM §1：合同 7 项；当前 `data_unavailable`（映射/numeric/独立培养标签缺失；C203/C205；DATA1 partial；missing≠未做）；P0/P1/P2 清单引用 `data_request_spec.json`（`D9A36585…`）；不发起请求、不读数据、不伪造联系人 |
| ② Stage2 固定反馈比较（M2 vs full retrain/hier-GP/KoopCell-DisKO/TD-JEPA/PKPD；同信息预算调参；先程序后背景；新功能同标定；主端点 δ=.05/headroom/MDE/cluster CI；次端点） | ✅ PROBLEM §2/DESIGN §1：基线/协议/端点写死；固定反馈；先程序后背景；新功能同标定；有限任务重组非零样本迁移；δ=.05、headroom/MDE 先检、cluster CI、6,282 仅 Fisher-z；次端点预测/算子/RNA 仅 secondary |
| ③ Stage3 固定更新器比较取证（候选主动干预 vs random/GP/最优输入设计/BATCHIE；同成本/合法实验包；完整闭环；防选择性） | ✅ PROBLEM §3/DESIGN §2：selector/learner 分离；同成本包；闭环计培养物/板/对照/失败/重复/标定/计算/调参；候选集/轮次先注册、全 selector 同菜单、不得事后调 |
| ④ 基线实现规格/骨架（输入/信息集/超参/流程/等预算审计；骨架+单测+计时，不跑效果） | ✅ DESIGN §1.2 表 + stage2_plan.py 骨架 11 项单测全 PASS（有限性/形状/selector 合法/等 query/等 tuning）；计时 0.03082 s/rep；**无效果比较/无 regret/无方法差异** |
| ⑤ 失败类别/停止/预算 | ✅ PROBLEM §4：data_unavailable/unreachable_gate/precision_insufficient/no_increment/inconclusive/compute_budget_exceeded + design_invalid 类别；Stage2/3 wall≤1800 s/CPU≤2 h/内存≤8 GB；当前 compute-only/0 wells |
| ⑥ 边界 | ✅ 机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据 |
| ⑦ report/record/usage/timing + schema；标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~11:50 | 读 task-149 并 claim；读 M2 v0.2 链、C206 Stage1 报告/JSON、Lead Stage1 决定、DATA1 report/request spec、ERRATA、R203 链 |
| ~11:54 | 写 `stage2_plan.py`（链核验、数据门、Stage2/3 设计、种子/功效/预算、基线骨架/单测/计时、schema/失败树） |
| ~11:56 | 运行成功：chain_pass=true、Stage1 PASS、data_unavailable、11 项骨架单测 PASS、pilot 0.03082 s/rep、seed 交集 [] |
| ~11:58 | 两跑 `stage2_plan.json` 与 `stage23_schema.json` 逐字节一致；写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做设计/规划/骨架单测/计时**：stage2_plan.py 核验 15 文件 SHA、构造数据门合同与当前状态、冻结 Stage2/3 设计/基线规格/统计/预算/schema/失败树；骨架单测只在 dummy 数组/菜单上检查有限性/形状/合法性/等预算审计；**不拟合真实数据、不运行方法比较、不计算 regret/效果指标**。
2. **数据门**：当前 `data_unavailable`（AZ 映射/功能 numeric/独立培养标签未取得；C203/C205；DATA1 partial）；**未发起请求、未读真实响应**；获取清单引用 `data_request_spec.json`，不伪造联系人；门失败只写 `data_unavailable`，不以合成/RNA 替代。
3. **Stage1 核实**：C206 `failed_checks=[]`、`no_effect_results=true`、full K 75/75、same-U 3/3、线性闭合 5.47e-16/非闭合 3.7576893、随机化 PASS、pilot .00253 s、两跑逐字节；仅机制账。
4. **种子**：Stage2 20261200–20261239、Stage3 20262100–20262139；与 Stage1 脚本内 seed-like 数字（20261082/20261083）交集 []；执行时重核。
5. **确定性**：`stage2_plan.json`（`3D57AA6F…`）与 `stage23_schema.json`（`C1EAA4B3…`）两跑逐字节一致；JSON 无 telemetry；计时只在 timing 文件。
6. **无效果/无增益**：所有输出只有设计/门/骨架单测/计时；不含 regret/决策效用/方法比较/top-k。

## 3. 关键结果

- 链核验：15/15 SHA 匹配；Stage1 PASS。
- 数据门：D1–D7 未满足 → **data_unavailable**、Stage2 执行不允许。
- Stage2/3 设计冻结：基线清单/输入信息集/超参≤20/流程/等预算审计；固定反馈/固定更新器；先程序后背景；防选择性；主端点 δ=.05/headroom/MDE/cluster/6,282；失败/停止/预算/schema。
- 种子：Stage2/3 各 40 组；与 Stage1 seed-like 交集 []。
- 功效表：SD=.10/.15/.20/.30 → n_req cluster 71/157/278/623；SD=.20 → 278；headroom 目标 .10。
- 骨架单测 11/11 PASS；0.03082 s/rep；投影 Stage2 1.48 s/Stage3 2.96 s；caps 1800 s/2 h/8 GB。
- 预算：当前 compute-only/0 wells；Stage3 实验成本进闭环账、不执行。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2_STAGE2.md` | `362A1AED7486BD2ECEA686CEE095FD062FF397993EE12FCAF845996C081DBA10` |
| `DESIGN_M2_STAGE2.md` | `F4F90EDB583A3779C6A268EDC0EACB43FFF0A7A6A7EF34F03F6E82222767ED52` |
| `stage2_plan.py` | `E185AAAE40D710E9ED9297F3516BDF63075B1DA21D679DDD0349E2DF42B5E70A` |
| `stage2_plan.json` | `3D57AA6F7F6D4D6FD68C652D81C6023D73AE5298D6B72AA40BE0DF07DC7DB294` |
| `stage23_schema.json` | `C1EAA4B35DBCB81D6DEF227E227C2CA694128A63D8E262BB45656EE6864D86D8` |
| `timing_m2_stage2_prep.json` | telemetry（末次 `AEAA2E65…`） |
| report/record/usage | 见 `usage_m2_stage2_prep.json` |
| 只读链（未改） | M2 v0.2 五件 + Stage1 决定 + C206 八件 + DATA1 两件（见 stage2_plan.json） |

## 5. 缺口与下一步

- **Stage2 不能执行**（data_unavailable）；需按 DATA1 获取/重导清单取得映射/功能 numeric/协议并登记数据 SHA/交换性诊断。
- 可提交本设计准备做独立挑战；数据门通过 + 挑战 + Lead 批准后执行 Stage2；Stage3 另立预注册。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验。
