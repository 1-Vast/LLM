# DESIGN_M2_STAGE2_v0_2 —— R204-M2.1 Stage2/3 执行设计（EDMD 基线/JSON 拆分/去重/样本量冻结；不运行效果）

2026-10-28。依据：[PROBLEM_M2_STAGE2_v0_2.md](PROBLEM_M2_STAGE2_v0_2.md)、`stage2_plan_v0_2.json`、`stage23_schema_v0_2.json`、`timing_m2_stage2_prep_v0_2.json`、M2 v0.2 链、C206 Stage1、DATA1（C205）、Stage2-PREP-C1 挑战。
**状态：预注册设计 v0.2；Stage2/3 未执行；当前 `data_unavailable`；未运行方法比较/未报告效果；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells。**

## 0. Stage2-PREP-C1 必改落实

| # | 修正 |
|---|---|
| ① EDMD learner 基线 | **新增 `B_edmd_system_id`**（Stage2 learner，不是 Stage3 selector）：受控弱 EDMD/系统辨识，拟合动作条件算子；同特征/历史/φ/K_a 约定；同信息/预算/调参≤20/固定反馈；**Stage2 即可判定 `rename_edmd`/`no_increment`**（同预算复制/超过→撤主算法主张） |
| ② JSON 拆分 | `stage2_baselines`=7 对象（M2_candidate + 6 comparators）；`stage3_selectors`=5 对象；每项含输入/信息/超参/流程/审计或选择规则/成本；无混合数组；schema 同步 |
| ③ 去重 | `B_full_history_retrain` 与 `B_full_retrain` 合并为 **`B_full_history_retrain`**（每轮全历史重估；无独立 from-scratch 第二基线）；独立比较=1 candidate + 6 baselines |
| ④ 样本量冻结 | n_units=300 仅 planning example；`sample_size_policy=not_frozen_until_data_gate`；数据门+pilot/headroom 后冻结 n/R/n_eff/SD/MDE/cluster/analysis_unit 写入执行预注册；禁止 example 执行 |
| ⑤ 保留 | 数据门/不得合成替代/request spec；Stage1 仅机制账；固定反馈/等预算/先程序后背景/新功能同标定；Stage3 selector-learner 分离/合法实验包/闭环；seeds/功效/预算/失败/边界不变 |

## 1. 前置核验/门顺序

1. **SHA 链**：M2 v0.2 五件 + Lead Stage1 决定 + C206 Stage1 八件 + DATA1 两件，15/15 匹配（本地已核验 chain_pass=true/mismatches=0）；执行时重核；失败→`design_invalid: chain_mismatch`。
2. **Stage1 状态**：C206 PASS（failed_checks=[]、no_effect_results=true、full K 75/75、same-U 3/3）；仅机制账。
3. **数据门 D1–D7**：当前 `data_unavailable`；门未过→只写 `data_unavailable`、不执行、不合成/RNA 替代。
4. **数据冻结**：合格数据 SHA/字典/角色/交换性诊断；冻结后生成执行预注册并冻结样本量（§3）。
5. **Stage2 通过后**：Stage3 另立预注册+挑战+Lead 批准；本设计不执行。

## 2. Stage2 固定反馈比较学习（不执行）

### 2.1 学习器基线（`stage2_baselines`，7 对象）

| id | 角色 | 输入/信息集 | 超参 | 流程 | 等预算审计 |
|---|---|---|---|---|---|
| **M2_candidate** | candidate | 小 φ 族；state/action 依赖 K_a；记录 π/动作 | ≤20 | f_g 后继→任务方向→新矩闭合→K 乘积/重组 | 同 query/feedback/features/prior/initial/tuning/compute |
| **B_edmd_system_id** | **等价强 learner** | 同特征/cohort/history；冻结 φ/K_a 约定 | ≤20 | 受控弱 EDMD/系统辨识拟合动作条件算子；固定反馈（最优输入设计属 Stage3 selector） | 同上；**Stage2 判定 rename_edmd/no_increment** |
| **B_full_history_retrain** | strong | 全部已观测历史/动作/readout | ≤20 | 每轮全历史重估参数（former B_full_retrain 合并，无第二 from-scratch 基线） | 同上 |
| **B_hierarchical_gp** | strong | 同特征 + culture/background 随机效应 | ≤20 | 分层 GP 后验更新 | 同上 |
| **B_koopcell_disiko** | strong | 同特征/cohort | ≤20 | KoopCell/DisKO 式未配对 cohort 算子适配 | 同上 |
| **B_td_jepa_successor** | strong | 同特征；转移构造 successor features | ≤20 | TD-JEPA/后继特征适配 | 同上 |
| **B_state_space_pkpd** | strong | 同剂量/时间/readout | ≤20 | 状态空间/PKPD 更新 | 同上 |

- **固定反馈流**：所有方法同一 queried actions/feedback；**先程序后背景**；新功能同标定；只换已观测权重=有限任务重组。
- **等预算审计**：同 query 数/feedback 数/特征信息/prior/初始数据/调参≤20/compute caps；审计未过不作比较。
- **防泄漏**：特征不含 state/truth；oracle 仅评估；数据角色/划分冻结。

### 2.2 端点/统计（写死）

- Primary=独立功能决策效用/后悔；δ=.05 normalized；headroom=U_max−U0 先检（<δ→`unreachable_gate`；近满分→另立 budget-to-target）；配对 MDE=2.801585·SD/√n_eff；cluster CI 按培养物/背景/任务；**6,282 仅 Fisher-z**；次端点预测校准/算子误差/RNA 仅 secondary。
- 失败/停止：EDMD 或其他标准方法同预算复制/超过→`rename_edmd`/`no_increment`、撤主算法；闭合/随机化/测量失败→stop；仅 RNA 收益→撤；成本超限→stop；CI 无法排除→inconclusive；跨任务→限当前任务。

## 3. 样本量冻结（执行前）

- n_units=300 只是 planning arithmetic example；n_req278/SD .20 表仅规划；**不得以 example 执行**。
- 数据门 D1–D7 通过 + 合格数据 pilot/headroom 后冻结：`n_units_per_background`、`R_replicates`、`n_eff`、`SD_D_assumption`、`MDE80`、`cluster_definition`、`analysis_unit`；写入 Stage2 执行预注册。
- `headroom<δ→unreachable_gate`；`MDE>δ→precision_insufficient`；禁止事后加 n/改 cluster/降 δ。

## 4. Stage3 固定更新器比较取证（不执行；`stage3_selectors` 5 对象）

| id | 角色 | 选择规则 | 信息 | 成本 |
|---|---|---|---|---|
| **S_M2_candidate** | candidate | 任务相关方向主动干预选择 | 记录历史/menus；固定 updater | 同合法实验包 |
| **S_random** | baseline | 均匀随机合法动作 | 同 menus | 同 |
| **S_gp_acquisition** | baseline | GP 后验不确定性采集 | 同 menus/posterior | 同 |
| **S_optimal_input_design** | equivalent strong selector | 受控弱 EDMD/系统辨识上的最优输入设计 | 同 menus；无目标泄漏 | 同 |
| **S_batchie** | baseline | BATCHIE 式后验+反馈批量选择 | 同 menus/posterior | 同 |

- 同一 learner/updater，selector 与 learner 分离；同成本/合法实验包：相同 cohorts/plates/doses/timepoints/controls/feedback rounds；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参；候选集/轮次先注册、全 selector 同菜单、不得事后调；Stage2 PASS+数据+另立批准后启动。

## 5. Baseline 骨架/单测/计时（本轮仅此可执行）

- 骨架含 full-history ridge、hier-GP、KoopCell/DisKO 线性算子、TD-JEPA successor、PKPD Euler、**EDMD 系统辨识**、selector 合法性；**12 项单测全 PASS**（含 EDMD 形状/有限性、等 query、等 tuning≤20）；**未运行效果比较/无 regret/无方法差异**。
- 计时：**0.02880 s/rep**；投影 Stage2 1.38 s、Stage3 2.76 s（caps 1800 s）；telemetry 只在 timing 文件。

## 6. 预算/schema/两跑/边界

- Stage2/3 wall≤1800 s、CPU≤2 h、内存≤8 GB；当前 compute-only、0 wells；Stage3 实验成本进闭环账、不执行。
- **`stage23_schema_v0_2.json`**：Stage2/3 字段 + `stage2_baseline_fields`（id/role/inputs_information/hyperparameters/flow/equal_budget_audit/stage2_judgment）+ `stage3_selector_fields`（id/role/selection_rule/information/cost）+ per-method 字段 + 禁列（药理/真实决策/迁移/机制/新颖性/探索端点/RNA 当 primary）；无效果结果。
- 两跑逐字节（plan/schema）；JSON 无 telemetry；失败只写类别。
- 边界：机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据。

## 7. 批准清单（Lead 接受设计前）

1. Stage2 learner 基线含 **B_edmd_system_id** 且 Stage2 可判 `rename_edmd`/`no_increment`；无重复 `B_full_retrain`。
2. JSON `stage2_baselines`（7 对象）与 `stage3_selectors`（5 对象）分离；schema 同步；无混合数组；两跑逐字节。
3. 样本量冻结规则：n_units=300 仅 example；数据门+pilot/headroom 后冻结实际 n/R/n_eff/SD/MDE/cluster 并写入执行预注册；禁止 example 执行。
4. 数据门/合成替代禁止/request spec/Stage1 机制账/固定反馈/Stage3 分离/闭环/seeds/预算/失败/边界不变。
