# report_m2_stage2_prep_v0_2 —— R204-M2.1 Stage2/3 设计修正报告（不运行效果）

2026-10-28。对象：R204-M2 Stage2/3 设计。依据：Stage2-PREP-C1 挑战（revise，5 必改）、M2 v0.2 链、C206 Stage1 PASS、DATA1（C205）、R203-P1 链。
**状态：设计修正 v0.2；Stage2/3 未执行；未读真实响应/功能数据；未运行方法比较/未报告效果；当前 `data_unavailable`；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells；v0.1 产物保留不改。**

## 0. 交付物（v0.2 新文件）

- 问题定义：[PROBLEM_M2_STAGE2_v0_2.md](PROBLEM_M2_STAGE2_v0_2.md)（`2402CEED…`）
- 执行设计：[DESIGN_M2_STAGE2_v0_2.md](DESIGN_M2_STAGE2_v0_2.md)（`671BFD46…`）
- 规划/骨架/单测/计时：[stage2_plan_v0_2.py](stage2_plan_v0_2.py)（`2CFD0C73…`）→ [stage2_plan_v0_2.json](stage2_plan_v0_2.json)（`156E358F…`）
- Stage2/3 schema：[stage23_schema_v0_2.json](stage23_schema_v0_2.json)（`BC22524E…`）
- 计时：[timing_m2_stage2_prep_v0_2.json](timing_m2_stage2_prep_v0_2.json)（telemetry；末次 `385FD6A9…`）
- 记录/用量：[record_m2_stage2_prep_v0_2.md](record_m2_stage2_prep_v0_2.md)、[usage_m2_stage2_prep_v0_2.json](usage_m2_stage2_prep_v0_2.json)

## 1. 5 必改落实

| # | 挑战问题 | v0.2 落实 |
|---|---|---|
| ① **Stage2 缺 EDMD learner 基线** | **新增 `B_edmd_system_id`**（Stage2 learner，不是 Stage3 selector）：受控弱 EDMD/系统辨识拟合动作条件算子；同特征/历史/φ/K_a 约定；同信息/预算/调参≤20/**固定反馈**；**Stage2 内可执行 `rename_edmd`/`no_increment` 判定**（同预算复制/超过 M2→撤主算法主张）；已写入 DESIGN §2.1 表与 JSON `stage2_baselines` |
| ② **JSON `baselines` 混装** | 拆为 **`stage2_baselines`（7 个对象）**：M2_candidate、**B_edmd_system_id**、B_full_history_retrain、B_hierarchical_gp、B_koopcell_disiko、B_td_jepa_successor、B_state_space_pkpd；与 **`stage3_selectors`（5 个对象）**：S_M2_candidate、S_random、S_gp_acquisition、S_optimal_input_design、S_batchie；每项含输入/信息/超参/流程/审计或选择规则/成本；**无混合数组**；`stage23_schema_v0_2.json` 同步 `stage2_baseline_fields`/`stage3_selector_fields` |
| ③ **full-history/full-retrain 重复** | **合并为 `B_full_history_retrain`**（每轮用全部已观测历史重估参数）；明示 former `B_full_retrain` duplicate merged、无第二 from-scratch 基线；独立比较=**1 candidate + 6 baselines**（EDMD、full-history、hier-GP、KoopCell/DisKO、TD-JEPA、PKPD） |
| ④ **n_units=300 仅 example** | `power.sample_size_policy = not_frozen_until_data_gate`；n_units=300 标为 **planning_example_only（非执行值）**；数据门+pilot/headroom 后**冻结** `n_units_per_background/R/n_eff/SD_D/MDE80/cluster_definition/analysis_unit` 并写入执行预注册；**禁止 example 执行**；n_req278/SD .20 表仅规划 |
| ⑤ 保留 | 数据门 D1–D7/`data_unavailable`/missing≠未做/request spec P0/P1/P2（不伪造联系人/不绕许可/不发起请求）；Stage1 仅机制账；固定反馈/等预算/先程序后背景/新功能同标定；Stage3 selector-learner 分离/合法实验包/闭环；seeds/功效/预算/失败/边界不变 |

## 2. 前置核验/数据门（不变）

- **链核验**：15/15 SHA、mismatches=0、chain_pass=true；C206 Stage1 PASS（failed_checks=[]、no_effect_results=true、full K 75/75、same-U 3/3、pilot .00253 s、两跑逐字节）；仅机制账。
- **数据门**：D1–D7 合同；当前 **`data_unavailable`**（AZ 映射/functional numeric/独立培养标签缺失；C203/C205；DATA1 partial；missing≠未做）；获取按 request spec P0/P1/P2，重导独立培养/板/批次；不伪造联系人/不绕许可/不发起请求；不得合成/RNA/预测替代。

## 3. Stage2/3 设计要点（不变 + v0.2 修正）

- **Stage2**：M2 vs **EDMD learner（新）** + full-history retrain（去重）+ hier-GP + KoopCell/DisKO + TD-JEPA + PKPD；固定反馈流、同信息/预算/调参≤20/预训练；先程序后背景；新功能同标定；主端点独立功能决策效用/后悔 δ=.05；headroom/MDE/cluster CI/6,282 仅 Fisher-z；次端点仅 secondary。
- **Stage3**：同一 learner/updater、selector/learner 分离；候选主动干预 vs random/GP/**optimal input design（selector）**/BATCHIE；同成本/合法实验包；完整闭环成本账；防选择性；仅 Stage2 PASS+数据+另立批准后启动。
- **样本量**：数据门后冻结实际 n/R/n_eff/SD/MDE/cluster；n_units=300 仅 example；不得执行时用 example。

## 4. 骨架/单测/计时（本轮仅此可执行）

- 骨架含 full-history ridge、hier-GP、KoopCell/DisKO 线性算子、TD-JEPA successor、PKPD、**EDMD 系统辨识**、selector 合法性；**12 项单测全 PASS**（含 EDMD 形状/有限性、等 query、等 tuning≤20）；**无效果比较/无 regret/无方法差异**。
- 计时：**0.02880 s/rep**；Stage2 投影 1.38 s、Stage3 2.76 s（caps 1800 s）。
- **JSON 结构**：`stage2_baselines` 7 对象、`stage3_selectors` 5 对象、无 `baselines` 键；`sample_size_policy` 存在；schema 同步；两跑逐字节。

## 5. 失败/停止/预算/边界（不变）

- 失败类别：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`、`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止：数据门失败→data_unavailable（当前）；EDMD/标准方法同预算复制→撤主算法；闭合/随机化/测量失败→stop；仅 RNA 收益→撤；成本超限→stop；CI 无法排除→inconclusive；跨任务→限当前任务。
- 预算 Stage2/3 wall≤1800 s/CPU≤2 h/内存≤8 GB；当前 compute-only、0 wells；Stage3 实验成本进闭环账、不执行。
- 边界：机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；执行须另立预注册+独立挑战+Lead 批准+合格数据。

## 6. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M2_STAGE2_v0_2.md` | `2402CEED91A1CFD8A4F28A05B70D83CB605EA73DC5FCE47545436679C3263305` |
| `DESIGN_M2_STAGE2_v0_2.md` | `671BFD465704A7172A120828EFF16C87CD95DF6DA1487EBC5E32898D68B7DF38` |
| `stage2_plan_v0_2.py` | `2CFD0C73BC5CE049CC78C7080B27B78D8070CF3C616067A1C57C35961B38D3EE` |
| `stage2_plan_v0_2.json` | `156E358F13C3F08D1745FC1208997DA7CD824DA50FA830A093E1FA021E59CC9C` |
| `stage23_schema_v0_2.json` | `BC22524E2D0718ABF9074E0E1E801759174E8636B148EE5385536A613629100E` |
| `timing_m2_stage2_prep_v0_2.json` | telemetry（末次 `385FD6A9…`） |
| report/record/usage | 见 `usage_m2_stage2_prep_v0_2.json` |

**确定性**：`stage2_plan_v0_2.json` 与 `stage23_schema_v0_2.json` 两跑逐字节一致；JSON 无 telemetry。

## 7. 建议

1. **建议再挑战（不 stop）**：重点检查 EDMD learner 基线（Stage2 可判 rename_edmd）、JSON `stage2_baselines`/`stage3_selectors` 拆分、去重、样本量冻结规则、数据门/固定反馈/Stage3/预算/边界不变。
2. 挑战通过后请 Lead **接受 Stage2/3 设计（不执行）**：当前 data_unavailable，获取/重导优先（request spec P0/P1/P2）；Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据。
3. **不做**：运行效果/读真实数据/合成替代/声称增益/药理/真实决策/迁移/机制/新颖性/代码晋升。
