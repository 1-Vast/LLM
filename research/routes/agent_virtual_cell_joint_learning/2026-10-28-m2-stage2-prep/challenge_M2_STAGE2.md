# R204-M2 Stage2/3 设计独立挑战（task-150）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 Stage2/3、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M2_STAGE2.md](PROBLEM_M2_STAGE2.md)（SHA `362A1AED…`）、[DESIGN_M2_STAGE2.md](DESIGN_M2_STAGE2.md)（`F4F90EDB…`）、[stage2_plan.py](stage2_plan.py)（`E185AAAE…`）、[stage2_plan.json](stage2_plan.json)（`3D57AA6F…`）、[stage23_schema.json](stage23_schema.json)（`C1EAA4B3…`）、[report_m2_stage2_prep.md](report_m2_stage2_prep.md)（`FE75BCB5…`）、[record_m2_stage2_prep.md](record_m2_stage2_prep.md)（`D30EA50F…`）、M2 v0.2/Stage1 C206/DATA1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_stage2_design_to_lead；也不是 stop）。**

Stage1 链、数据就绪门、Stage2 固定反馈、Stage3 selector-learner 分离、种子/功效/预算/失败/边界大体写清；但 **Stage2 的核心等价强基线 EDMD/系统辨识在 DESIGN 基线表中缺失**（与 DESIGN §6 批准清单、PROBLEM §3/§7“EDMD 等价强基线”矛盾）；**JSON `baselines` 又把 Stage2 基线对象和 Stage3 selector 字符串混在一个数组**；**`B_full_history_retrain` 与 `B_full_retrain` 流程重复**。这三项影响“同预算强基线/防选择性”的冻结，需先修；另外 `n_units=300` 目前只是示例、Stage2/3 实际 n/R 未冻结，执行前必须冻结（可作为接受设计的条件，不阻止设计讨论）。

**结论：先修 §2 的 1–3，再提交 Lead 接受 Stage2/3 设计（不执行；data_unavailable）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 链核验/Stage1 状态 | **PASS** | 15/15 SHA、mismatches=0、chain_pass=true；Stage1 C206 `failed_checks=[]`、`no_effect_results=true`、full K 75/75、same-U 3/3、closure 5.47e-16/非闭合 3.7576893/partial 50/75、随机化 PASS、pilot .00253s、两跑一致；**仅机制账，不作效果证据** ✓。 |
| ② | 数据就绪门 D1–D7 | **PASS（当前未通过）** | D1–D7 合同写清（多时间功能/群体快照、可交换、剂量/时间/readout、π/动作、独立培养/板、正交功能、计数+RNA）；当前 `data_unavailable`（缺 mapping/功能 numeric，C203/C205；missing≠作者未做）；request spec P0/P1/P2；不伪造联系人/不绕许可/不发起请求；门通过后登记数据 SHA/交换性/角色；不得用合成/RNA 替代 ✓。 |
| ③ | Stage2 设计 | **FAIL（EDMD 强基线缺失/重复基线）** | 固定反馈流、先程序后背景、新功能同标定、只换已观测权重=有限重组、同信息/预算/调参、主端点/δ/headroom/MDE/cluster/6,282 写清 ✓；**但 DESIGN §1.2 基线表没有 EDMD/系统辨识等价强基线**（只有 full-history/hier-GP/KoopCell-DisKO/TD-JEPA/PKPD/full retrain），与 **DESIGN §6 批准清单“EDMD 等价强基线纳入”** 及 PROBLEM §3/§7 矛盾；**B_full_history_retrain 与 B_full_retrain 流程重复**（都是每轮全历史/从头重训）；同预算强基线/`rename_edmd` 撤主张条件无法在 Stage2 执行。 |
| ④ | Stage3 设计 | **PASS** | 同一 learner/updater、selector 与 learner 分离；候选主动干预 vs random/GP/最优输入设计（受控弱 EDMD/系统辨识）/BATCHIE；同成本/合法实验包（cohorts/plates/doses/timepoints/controls/rounds）；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参；候选集/轮次先注册、先程序后背景、全 selector 同菜单、不得事后调；仅 Stage2 PASS+数据+另立批准后启动 ✓。**但 Stage3 的 optimal input design 是 selector，不是 Stage2 learner 的 EDMD 基线**（见③）。 |
| ⑤ | 基线骨架/单测/计时 | **PASS（JSON 结构需修）** | 11 项单测 PASS、等 query 数/等 tuning≤20 审计；0.03082 s/rep；Stage2 1.48 s/Stage3 2.96 s、caps 1800 s；无效果比较/regret/方法差异；schema 冻结 per-method/禁列 ✓。**但 `stage2_plan.json → baselines` 数组把 6 个 Stage2 基线对象与 “candidate M2/random/GP/optimal input design/BATCHIE” 4 个 Stage3 selector 字符串混在一起**，不是可执行的 schema。 |
| ⑥ | 种子/功效/预算/失败 | **PASS（n/R 未冻结）** | Stage2 seeds 20261200–20261239、Stage3 20262100–20262139（40 sets；与 Stage1 seed-like 20261082/83 交集[]）；功效 deff2.2/δ.05：SD .10/.15/.20/.30→n_req 71/157/278/623；headroom .10；预算 Stage2/3 wall≤1800s/CPU≤2h/8GB、0 wells；失败类别/停止完整 ✓。**但 `power.stage2_units_plan` 只写 `n_units=300 (example planning)`，Stage2/3 实际 n_units/R 未冻结；n_req278 的 278 是 cluster 需求，若每背景 n=300 可以，但必须在数据门后 pilot/headroom 冻结并在执行预注册写死，不能以“示例”进入执行。** |
| ⑦ | 边界诚实 | **PASS** | 机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据；未把 Stage1 PASS 当效果证据 ✓。 |
| ⑧ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5，Lead 接受设计前）

1. **把 EDMD/系统辨识等价强基线加入 Stage2 学习比较**（同信息/同预算/同调参/同固定反馈）：在 DESIGN §1.2 表与 JSON `baselines` 中增加 `B_edmd_system_id`（受控弱 EDMD + 最优输入设计的学习器版本，不是 Stage3 的 selector）；明确 `rename_edmd`/`no_increment` 判定在 Stage2 就能执行。若决定 EDMD 只在 Stage3 selector，则必须在 PROBLEM/DESIGN 明确“Stage2 不检验 EDMD learner”，并调整主算法主张/批准清单，不能保留“EDMD 等价强基线纳入”的矛盾文字。
2. **修 JSON `baselines` 结构**：拆成 `stage2_baselines`（对象：id/inputs/hyperparams/flow/audit）与 `stage3_selectors`（对象：id/info/cost/rule），不要把 selector 字符串塞进 Stage2 基线数组；`stage23_schema.json` 同步字段；两跑逐字节。
3. **合并/区分重复基线**：`B_full_history_retrain`（all observed histories）与 `B_full_retrain`（from scratch each round）当前流程相同；二者合一，或明确写出可区分的训练/更新差异（例如是否保留历史/是否每轮重置参数），避免 6 个基线里实际只有 5 个独立比较。
4. **冻结 Stage2/3 的 n_units/R**：`n_units=300` 目前只是 example；在数据门通过后用合格数据 pilot/headroom 预检冻结实际 n_units、R、n_eff、MDE、cluster 口径，并写入执行预注册；n_req278/SD .20 的表只作规划；不得执行时用“example”数字。
5. **保留**数据门 D1–D7/current data_unavailable/request spec P0/P1/P2/不合成替代；Stage1 仅机制账；Stage2 固定反馈/先程序后背景/新功能同标定；Stage3 selector-learner 分离/合法实验包/完整闭环；seeds/功效/预算/失败/边界不变。

## 3. 修完后建议的 Lead 接受 Stage2/3 设计文本（不执行）

> **批准范围**：在必改 1–4 完成并复核后，**接受** R204-M2 Stage2/3 的**设计**（不执行 Stage2/3、不读真实数据、不批效果/药理/真实决策/迁移/新颖性；当前 `data_unavailable`）。
>
> **数据门**：D1–D7 全满足+数据 SHA/字典/角色/交换性冻结前，Stage2 只写 `data_unavailable`；不得用合成/RNA/预测替代；request spec P0/P1/P2（mapping、功能 numeric、协议）为获取/重导优先；不伪造联系人/不绕许可。
>
> **Stage2 冻结**：候选 M2 vs **EDMD/系统辨识等价强基线** + full-history retrain + hierarchical GP + KoopCell/DisKO + TD-JEPA + PKP D + 全重训（去重后）；固定反馈流/同信息/同预算/同调参/同预训练；先程序后背景；新功能同标定；主端点独立功能决策效用/后悔 δ=.05、headroom<δ→unreachable_gate、MDE=2.801585·SD/√n_eff、cluster CI、6,282 仅 Fisher-z；次端点仅 secondary；防选择性。
>
> **Stage3 冻结**：同一 learner/updater，selector 与 learner 分离；候选主动干预 vs random/GP/最优输入设计/BATCHIE；同成本/合法实验包；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参；候选集/轮次先注册；Stage2 PASS+数据+另立批准后启动。
>
> **预算/边界**：Stage2/3 wall≤1800s/CPU≤2h/8GB、0 wells；失败类别/停止/schema/两跑/telemetry 分离；机制账 only；Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据；当前不执行。

## 4. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 Stage2 prep 设计/JSON/schema/Stage1/DATA1 链；只写本文件与 `tmp/`；未改 Stage2 产物。
- **总判决：revise**。Stage1 链/数据门/固定反馈/selector-learner/种子/功效/预算/失败/边界基本正确；但 **Stage2 缺 EDMD/系统辨识等价强基线（与批准清单矛盾）、JSON baselines 混入 Stage3 selector 字符串、full-history/full-retrain 重复、n_units/R 仅示例未冻结**；修完 1–4 后可接受设计（不执行；data_unavailable）。

**一句话：Stage2/3 设计骨架、数据门 D1–D7、固定反馈/selector-learner 分离、seeds/功效/预算/失败/边界都写清了；但 Stage2 少了 EDMD/系统辨识等价强基线（DESIGN §6 自己要求纳入），JSON `baselines` 又把 Stage3 selector 字符串混进 Stage2 基线，`B_full_history_retrain`/`B_full_retrain` 重复，且 n_units=300 只是示例——判 revise：补 EDMD learner 基线、拆 JSON baseline/selector、去重、数据门后冻结 n/R，再提交 Lead 接受设计（不执行；当前 data_unavailable）。**
