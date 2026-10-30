# record_m2_stage2_prep_v0_2.md —— R204-M2.1 Stage2/3 设计修正记录（不运行效果）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-151（R204-M2-STAGE2.1）· 日期 2026-10-28
只写 `research/2026-10-28-m2-stage2-prep/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/M2 预注册/Stage1/N1/A-B-D**；**未运行方法比较/未读真实响应/未报告效果**；当前 `data_unavailable`；机制账 only；0 wells。

## 0. 5 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① 补 EDMD/系统辨识 learner 强基线 | ✅ 新增 **`B_edmd_system_id`**（Stage2 learner；受控弱 EDMD/系统辨识；同信息/预算/调参≤20/固定反馈；最优输入设计属 Stage3 selector）；**Stage2 可判 `rename_edmd`/`no_increment`**（同预算复制/超过→撤主算法主张）；DESIGN §2.1 表 + JSON `stage2_baselines` + 骨架/单测含 EDMD |
| ② 拆 JSON 结构 | ✅ `stage2_baselines`=7 对象（M2_candidate、B_edmd_system_id、B_full_history_retrain、B_hierarchical_gp、B_koopcell_disiko、B_td_jepa_successor、B_state_space_pkpd）；`stage3_selectors`=5 对象（S_M2_candidate、S_random、S_gp_acquisition、S_optimal_input_design、S_batchie）；无混合 `baselines` 键；schema 同步 `stage2_baseline_fields`/`stage3_selector_fields`；两跑逐字节 |
| ③ 合并/区分重复基线 | ✅ `B_full_history_retrain` 与 `B_full_retrain` 合并为单一 `B_full_history_retrain`（全历史重估；明示 former duplicate merged、无第二 from-scratch）；独立比较=1 candidate + 6 baselines |
| ④ 样本量冻结规则 | ✅ `sample_size_policy=not_frozen_until_data_gate`；n_units=300 标为 planning_example_only；数据门 pilot/headroom 后冻结 `n_units_per_background/R/n_eff/SD_D/MDE80/cluster_definition/analysis_unit` 并写入执行预注册；**禁止 example 执行**；n_req278/SD .20 表仅规划 |
| ⑤ 保留 | ✅ 数据门 D1–D7/`data_unavailable`/missing≠未做/request spec P0/P1/P2（不伪造联系人/不绕许可/不发起请求）；Stage1 仅机制账；固定反馈/等预算/先程序后背景/新功能同标定；Stage3 selector-learner 分离/合法实验包/闭环；seeds/功效/预算/失败/边界不变 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~11:55 | 读 task-151 并 claim；读 Stage2-PREP-C1 挑战、v0.1 产物、M2/Stage1/DATA1 链 |
| ~11:57 | 复制 v0.1→v0.2 脚本；Python patch：新增 EDMD 骨架/单测、Stage2 baseline 对象、Stage3 selector 对象、去重、JSON 拆分、sample_size_policy、schema 字段、v0.2 路径 |
| ~11:59 | 运行成功：7 stage2 baselines/5 selectors、无混合键、EDMD 单测 PASS、12 项单测全 PASS、pilot 0.02880 s/rep；两跑 plan/schema 逐字节一致 |
| ~12:03 | 写 PROBLEM/DESIGN/report/record/usage v0.2；标 completed + send_message |

## 2. 实现与披露

1. **只做设计/规划/骨架单测/计时**：核验 15 文件 SHA、数据门、Stage2/3 设计、样本量冻结规则、失败/预算/schema；骨架单测仅 dummy 数组/菜单的有限性/形状/合法性/等预算审计；**不拟合真实数据、不跑方法比较、不计算 regret/效果指标**。
2. **JSON 结构**：`stage2_baselines`/`stage3_selectors` 均为对象数组；无 `baselines` 混合键；每对象包含输入/信息/超参/流程/审计（Stage3 为选择规则/信息/成本）；schema 同步；两跑逐字节。
3. **EDMD**：明确为 Stage2 learner 基线（不是 Stage3 selector）；固定反馈下拟合动作条件算子；同预算复制/超过→撤主算法；Stage2 可执行判定。
4. **去重**：合并 full-history/full-retrain；避免名义 6 实际 5。
5. **样本量**：n_units=300 仅 planning example；数据门后冻结 n/R/n_eff/SD/MDE/cluster/analysis unit；禁止 example 执行。
6. **确定性**：`stage2_plan_v0_2.json`（`156E358F…`）与 `stage23_schema_v0_2.json`（`BC22524E…`）两跑逐字节一致；JSON 无 telemetry；计时只在 timing 文件。
7. **无效果/无增益**：输出仅设计/门/骨架单测/计时；不含 regret/方法比较/top-k。

## 3. 关键结果

- 链核验 15/15、Stage1 PASS；数据门 `data_unavailable`（D1–D7 未满足；获取/重导清单引用 request spec）。
- Stage2 baselines 7 对象（含 EDMD；full-history 去重）；Stage3 selectors 5 对象；JSON/schema 一致。
- 12 项骨架单测全 PASS（含 EDMD 形状/有限性、等 query、等 tuning≤20）；0.02880 s/rep；Stage2 投影 1.38 s/Stage3 2.76 s；caps 1800 s/2 h/8 GB。
- seeds Stage2 20261200–39、Stage3 20262100–39（与 Stage1 seed-like 交集 []）；SD=.20→n_req cluster 278（**仅规划**）；实际 n/R 数据门后冻结。
- 失败类别/停止/预算/边界不变。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2_STAGE2_v0_2.md` | `2402CEED91A1CFD8A4F28A05B70D83CB605EA73DC5FCE47545436679C3263305` |
| `DESIGN_M2_STAGE2_v0_2.md` | `671BFD465704A7172A120828EFF16C87CD95DF6DA1487EBC5E32898D68B7DF38` |
| `stage2_plan_v0_2.py` | `2CFD0C73BC5CE049CC78C7080B27B78D8070CF3C616067A1C57C35961B38D3EE` |
| `stage2_plan_v0_2.json` | `156E358F13C3F08D1745FC1208997DA7CD824DA50FA830A093E1FA021E59CC9C` |
| `stage23_schema_v0_2.json` | `BC22524E2D0718ABF9074E0E1E801759174E8636B148EE5385536A613629100E` |
| `timing_m2_stage2_prep_v0_2.json` | telemetry（末次 `385FD6A9…`） |
| report/record/usage | 见 `usage_m2_stage2_prep_v0_2.json` |
| v0.1 只读（未改） | PROBLEM `362A1AED…`、DESIGN `F4F90EDB…`、script `E185AAAE…`、JSON `3D57AA6F…`、schema `C1EAA4B3…` |

## 5. 缺口与下一步

- **Stage2/3 未执行**（data_unavailable；未读真实数据）；需先按 DATA1 request spec 获取/重导映射/功能 numeric/协议。
- 建议再挑战；通过后 Lead 接受 Stage2/3 设计（不执行）；执行须另立预注册+独立挑战+Lead 批准+合格数据；Stage3 另立预注册。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验。
