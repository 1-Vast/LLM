# PROBLEM_M2_STAGE2_v0_2 —— R204-M2.1 Stage2/3 数据门与设计（EDMD 基线/JSON 拆分/去重/样本量冻结；不运行效果）

2026-10-28。对象：R204-M2 Stage2/3。依据：M2 v0.2 链、C206 Stage1 PASS、Lead `DECISION_R204_M2_STAGE1.md`、DATA1（C205/C203）、Stage2-PREP-C1 挑战（revise，5 必改）、ERRATA C197/C199/C201/C203/C205、R203-P1 链。
**状态：预注册设计草案 v0.2；Stage2/3 未执行；未读真实响应/功能数据；未运行方法比较/未报告效果；当前 `data_unavailable`；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells；v0.1 产物保留不改。**

## 0. Stage2-PREP-C1 必改落实（v0.1 → v0.2）

| # | 挑战问题 | v0.2 修正 |
|---|---|---|
| ① **Stage2 缺 EDMD/系统辨识 learner 强基线** | **新增 `B_edmd_system_id`（Stage2 learner 基线）**：受控弱 EDMD/系统辨识，输入/信息/超参≤20/流程/等预算审计与 M2 相同；**固定反馈**（最优输入设计是 Stage3 selector，不是本 learner）；**Stage2 内即可执行 `rename_edmd`/`no_increment` 判定**（同预算复制/超过→撤主算法主张） |
| ② **JSON `baselines` 混装 Stage2 基线对象与 Stage3 selector 字符串** | JSON 拆为 **`stage2_baselines`（7 个对象：M2_candidate、B_edmd_system_id、B_full_history_retrain、B_hierarchical_gp、B_koopcell_disiko、B_td_jepa_successor、B_state_space_pkpd）** 与 **`stage3_selectors`（5 个对象：S_M2_candidate、S_random、S_gp_acquisition、S_optimal_input_design、S_batchie）**；每项含输入/信息/超参/流程/审计或选择规则/成本；**无混合数组**；`stage23_schema_v0_2.json` 同步字段 |
| ③ **`B_full_history_retrain` 与 `B_full_retrain` 流程重复** | **合并为单一 `B_full_history_retrain`**：每轮用全部已观测历史重估参数（不再保留独立 `B_full_retrain`）；文档明示"former B_full_retrain duplicate merged; no second from-scratch baseline"；独立比较数=1 candidate + **6** 外部 baseline（EDMD、full-history、hier-GP、KoopCell/DisKO、TD-JEPA、PKPD） |
| ④ **n_units=300 仅示例** | 新增 **`sample_size_policy`**：`status=not_frozen_until_data_gate`；n_units=300 标为 **planning_example_only（非执行值）**；数据门 D1–D7 通过 + 合格数据 pilot/headroom 后**冻结** `n_units_per_background/R/n_eff/SD_D/MDE80/cluster_definition/analysis_unit` 并写入执行预注册；**禁止用 example 执行**；n_req278/SD .20 表仅规划 |
| ⑤ **保留项** | 数据门 D1–D7/`data_unavailable`/missing≠未做/request spec P0/P1/P2（不伪造联系人/不绕许可/不发起请求）；Stage1 仅机制账；固定反馈/同信息预算调参/先程序后背景/新功能同标定；Stage3 selector-learner 分离/合法实验包/完整闭环；seeds/功效/预算/失败/边界不变 |

## 1. 前置核验（已通过）

`stage2_plan_v0_2.py` 只读核验 15 文件 SHA：M2 v0.2 五件 + Lead Stage1 决定 + C206 Stage1 八件 + DATA1 report/request spec；**mismatches=0、chain_pass=true**；C206 Stage1 `failed_checks=[]`、`no_effect_results=true`、full K 75/75、same-U 3/3 → PASS。执行时重核，失败→`design_invalid: chain_mismatch`。

## 2. 数据就绪门（Stage2 前；当前未通过）

- **合同 D1–D7**：多时间功能/群体快照；同培养物/背景/批次可交换；剂量/时间/function readout；记录 π/动作标签；独立培养/板重复；正交功能；计数+RNA。
- **当前 `data_unavailable`**：AZ `BARCODE/cmatrix/CELL_ID → experiment/occasion/treatment date/passage/culture` 映射、7 系×6 实验×3 技术重复映射/对账、Fig 4E/F/5C/D/6C–E caspase/PARP/western numeric、协议-键映射、Figshare README/数据字典缺失（C203/C205；DATA1 partial；**missing ≠ 作者未做**）。**Stage2 执行不允许**；不得用合成/RNA/预测替代独立功能决策。
- **获取/重导清单**（引用 `data_request_spec.json` `D9A36585…`）：**P0 数据字典/映射；P1 功能 numeric；P2 协议映射**；重导独立培养/板/批次标签并与 301 exact-18/161 6×3 对账；门通过后登记数据 SHA/交换性诊断/角色冻结；不伪造联系人/不绕许可/不发起请求。

## 3. Stage2 设计（固定反馈比较学习；不执行）

- **候选 M2** vs **6 个 learner 基线**：**B_edmd_system_id（等价强基线）**、B_full_history_retrain（合并去重）、B_hierarchical_gp、B_koopcell_disiko、B_td_jepa_successor、B_state_space_pkpd。
- **B_edmd_system_id**：受控弱 EDMD/系统辨识，拟合动作条件算子；同特征/历史/φ/K_a 约定；同信息/预算/调参≤20/固定反馈；**Stage2 判定**：同预算复制/超过 M2 → `rename_edmd`/`no_increment`、撤主算法主张。
- 固定反馈流（所有方法同 queried actions/feedback）；先程序后背景；新功能同标定；只换已观测权重=有限任务重组；等预算审计（query/feedback/features/prior/initial/tuning/compute）。
- 主端点=独立功能决策效用/后悔、δ=.05；headroom=U_max−U0 先检（<δ→`unreachable_gate`；近满分→另立 budget-to-target）；配对 MDE=2.801585·SD/√n_eff；cluster CI 按培养物/背景/任务；**6,282 仅 Fisher-z**；次端点预测/算子/RNA 仅 secondary。

## 4. Stage3 设计（固定更新器比较取证；不执行）

- 同一 learner/updater，**selector 与 learner 分离**；**5 个 selector**：S_M2_candidate（候选主动干预选择）、S_random、S_gp_acquisition、S_optimal_input_design（受控弱 EDMD/系统辨识上的最优输入设计）、S_batchie。
- 同成本/合法实验包（cohorts/plates/doses/timepoints/controls/feedback rounds）；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参；候选集/轮次先注册、先程序后背景、全 selector 同菜单、不得事后调；仅 Stage2 PASS+数据合格+另立批准后启动。

## 5. 样本量冻结规则（关键）

- **n_units=300 仅为 planning arithmetic example**；`n_req278`/SD .20 表仅规划；**不得进入执行**。
- 数据门 D1–D7 通过 + 合格数据 pilot/headroom 预检后，**冻结**：`n_units_per_background`、`R_replicates`、`n_eff`、`SD_D_assumption`、`MDE80`、`cluster_definition`（培养物/背景/任务）、`analysis_unit`，写入 Stage2 执行预注册；未冻结前不得执行。
- 若 headroom<δ→`unreachable_gate`；MDE>δ→`precision_insufficient`；不得用 example/事后加 n 救结果。

## 6. 失败类别/停止/预算

- 失败类别：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`、`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止：数据门失败→`data_unavailable`（当前）；等预算复制/超过（含 EDMD）→撤主算法；闭合/随机化/测量失败→stop；仅 RNA/预测/算子误差收益→撤；成本超限→stop；CI 无法排除→`inconclusive`；跨任务失败→限当前任务；不换端点/降 δ。
- 预算：Stage2/3 wall≤1800 s/CPU≤2 h/内存≤8 GB；当前 compute-only、0 wells；Stage3 实验成本进闭环账、不执行。

## 7. 边界

机制账 only；Stage2/3 不执行；不读真实响应/功能数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；**Stage2/3 执行须另立预注册 + 独立挑战 + Lead 批准 + 合格数据**。
