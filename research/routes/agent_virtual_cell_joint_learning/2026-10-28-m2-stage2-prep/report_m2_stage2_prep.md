# report_m2_stage2_prep —— R204-M2 Stage2/3 设计准备报告（不运行效果）

2026-10-28。对象：R204-M2 Stage2/3。依据：M2 v0.2 链、C206 Stage1 PASS、Lead Stage1 决定、DATA1（C205）、ERRATA C197/C199/C201/C203/C205、R203-P1 链。
**状态：设计准备；Stage2/3 未执行；未读真实响应/功能数据；未运行方法比较/未报告效果；当前数据 `data_unavailable`；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells。**

## 0. 交付物

- 问题定义：[PROBLEM_M2_STAGE2.md](PROBLEM_M2_STAGE2.md)（`362A1AED…`）
- 执行设计：[DESIGN_M2_STAGE2.md](DESIGN_M2_STAGE2.md)（`F4F90EDB…`）
- 规划/骨架/单测/计时：[stage2_plan.py](stage2_plan.py)（`E185AAAE…`）→ [stage2_plan.json](stage2_plan.json)（`3D57AA6F…`）
- Stage2/3 schema：[stage23_schema.json](stage23_schema.json)（`C1EAA4B3…`）
- 计时：[timing_m2_stage2_prep.json](timing_m2_stage2_prep.json)（telemetry；末次 `AEAA2E65…`）
- 记录/用量：[record_m2_stage2_prep.md](record_m2_stage2_prep.md)、[usage_m2_stage2_prep.json](usage_m2_stage2_prep.json)

## 1. 链核验/Stage1 状态（已通过）

`stage2_plan.py` 只读核验 **15 文件 SHA 全部匹配**（mismatches=0、chain_pass=true）：M2 v0.2 五件 + Lead Stage1 决定 + C206 Stage1 八件 + DATA1 report/request-spec。**C206 Stage1 PASS 已核实**：`failed_checks=[]`、`no_effect_results=true`、full K **75/75**、same-U **3/3**、线性闭合 5.47e-16/非闭合 3.7576893/partial 50/75、随机化合同 PASS、pilot .00253 s、两跑逐字节；**仅机制账、无效果/增益**。

## 2. 数据就绪门（Stage2 前置；当前未通过）

- **合同 D1–D7**（PROBLEM §1）：多时间功能/群体快照；同培养物/背景/批次可交换；剂量/时间/function readout；记录 π/动作标签；独立培养/板重复；正交功能；计数+RNA。
- **当前状态：`data_unavailable`**。缺：AZ `BARCODE/cmatrix/CELL_ID → experiment/occasion/treatment date/passage/culture` 映射；7 系×6 实验×3 技术重复映射/对账；Fig 4E/F、5C/D、6C–E 的 caspase/PARP/western numeric；协议-键映射；Figshare README/数据字典（C203/C205；DATA1 `partial`；missing ≠ 作者未做）。
- **获取/重导清单**（引用 `data_request_spec.json` `D9A36585…`，不伪造联系人/不绕许可）：P0 数据字典/映射；P1 功能 numeric；P2 协议映射；重导独立培养/板/批次标签并与 301 exact-18/161 6×3 对账；门通过后登记数据 SHA/交换性诊断/角色冻结。
- **不得**用合成数据/RNA 提分/预测/算子误差替代独立功能决策；Stage2 执行不允许。

## 3. Stage2 设计（固定反馈比较学习；不执行）

- **候选** M2 vs **full-history retrain、hierarchical GP、KoopCell/DisKO 适配、TD-JEPA/后继特征适配、state-space/PKPD、full retrain**；同信息/同预算/同调参/同预训练；**固定反馈流**（所有方法同 queried actions/feedback）；先留出程序再背景；新功能同标定；只换已观测权重=有限任务重组非零样本迁移。
- 每基线输入/信息集/超参≤20/训练-更新流程/等预算审计已写死（DESIGN §1.2）；EDMD 等价强基线纳入；防泄漏（特征不含 state/truth、oracle 仅评估）。
- 主端点=独立功能决策效用/后悔、δ=.05；headroom=U_max−U0 先检（<δ→unreachable_gate；近满分→另立 budget-to-target）；配对 MDE=2.801585·SD/√n_eff；cluster 按培养物/背景/任务；**6,282 仅 Fisher-z**；次端点预测/算子/RNA 仅 secondary。

## 4. Stage3 设计（固定更新器比较取证；不执行）

- 同一 learner/updater，**selector 与 learner 分离**；候选 M2 主动干预选择 vs **random、GP、最优输入设计（受控弱 EDMD/系统辨识）、BATCHIE 适配**。
- 相同合法实验包（cohorts/plates/doses/timepoints/controls/feedback rounds）；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参；候选集/轮次先注册、先程序后背景、全 selector 同菜单/成本、不得事后调 selector。
- 仅 Stage2 PASS + 数据合格 + 另立预注册/独立挑战/Lead 批准后启动。

## 5. 种子/功效/预算/骨架单测

- **种子**：Stage2 `20261200..20261239`（40 组）；Stage3 `20262100..20262139`（40 组）；与 Stage1 脚本内 seed-like 数字交集 **[]**；执行时重核；不得改 seed。
- **规划表**（ICC=.30、m=5、deff=2.2、δ=.05）：SD(D)=.10/.15/.20/.30 → n_req cluster **71/157/278/623**；SD=.20 → **n_req 278**、MDE≈.0499；headroom 目标 .10；6,282 仅 Fisher-z 参考。
- **预算**：Stage2/3 wall≤1800 s、CPU≤2 h、内存≤8 GB；当前 data-only/compute-only、0 wells；Stage3 实验成本进闭环账、不执行。
- **基线骨架/单测/计时**：11 项单测全 PASS（有限性/形状、selector 合法、等 query/等 tuning 审计）；**0.03082 s/rep**；Stage2 投影 1.48 s、Stage3 投影 2.96 s（远低于 caps）；**无效果比较/无 regret/无方法差异**。
- **schema**：`stage23_schema.json` 冻结 Stage2/3/per-method 字段与禁列（药理/真实决策/迁移/机制/新颖性/探索端点/RNA 当 primary）；两跑逐字节；失败只写类别；结果 JSON 无 telemetry。

## 6. 失败/停止/边界

- 失败类别：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`、`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止：数据门失败→`data_unavailable`（当前）；等预算复制/超过→撤主算法；闭合/随机化/测量失败→stop；仅 RNA/预测/算子误差收益→撤；成本超限→stop；CI 无法排除→inconclusive；跨任务失败→限当前任务；不换端点/降 δ。
- 边界：机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；**Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据**。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2_STAGE2.md` | `362A1AED7486BD2ECEA686CEE095FD062FF397993EE12FCAF845996C081DBA10` |
| `DESIGN_M2_STAGE2.md` | `F4F90EDB583A3779C6A268EDC0EACB43FFF0A7A6A7EF34F03F6E82222767ED52` |
| `stage2_plan.py` | `E185AAAE40D710E9ED9297F3516BDF63075B1DA21D679DDD0349E2DF42B5E70A` |
| `stage2_plan.json` | `3D57AA6F7F6D4D6FD68C652D81C6023D73AE5298D6B72AA40BE0DF07DC7DB294` |
| `stage23_schema.json` | `C1EAA4B35DBCB81D6DEF227E227C2CA694128A63D8E262BB45656EE6864D86D8` |
| `timing_m2_stage2_prep.json` | telemetry（末次 `AEAA2E65…`） |
| report/record/usage | 见 `usage_m2_stage2_prep.json` |

**确定性**：`stage2_plan.json` 与 `stage23_schema.json` 两跑逐字节一致；JSON 无 telemetry；计时仅在 timing 文件。

## 8. 建议

1. **Stage2 不能执行**（data_unavailable）；先按 DATA1 request spec 获取映射/功能 numeric/协议，重导独立培养标签；不得以合成/RNA 替代。
2. 可提交本 Stage2/3 设计准备做独立挑战（重点：数据门 D1–D7、固定反馈/固定更新器、基线规格/等预算审计、主端点/headroom/MDE/6,282、防选择性、失败类别/预算/schema）。
3. 数据门通过 + 挑战 + Lead 批准后再执行 Stage2；Stage3 另立预注册；不批效果/药理/真实决策/迁移/新颖性/代码晋升。
