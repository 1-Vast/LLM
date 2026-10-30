# R204-M2 Stage2.1 轻量复核（task-152）：v0.2 设计

2026-10-28。角色：同一独立挑战者（非提案者、未参与 Stage2/3、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M2_STAGE2_v0_2.md](PROBLEM_M2_STAGE2_v0_2.md)（SHA `2402CEED…`）、[DESIGN_M2_STAGE2_v0_2.md](DESIGN_M2_STAGE2_v0_2.md)（`671BFD46…`）、[stage2_plan_v0_2.py](stage2_plan_v0_2.py)（`2CFD0C73…`）、[stage2_plan_v0_2.json](stage2_plan_v0_2.json)（`156E358F…`）、[stage23_schema_v0_2.json](stage23_schema_v0_2.json)（`BC22524E…`）、[timing_m2_stage2_prep_v0_2.json](timing_m2_stage2_prep_v0_2.json)、report/record/usage v0.2、M2/Stage1/DATA1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_stage2_design_v0_2_to_lead（仅接受 Stage2/3 设计；不执行；当前 data_unavailable）。**

v0.2 已修掉 v0.1 的阻断：
- **`B_edmd_system_id` 是 Stage2 learner**（不是 Stage3 selector）：同特征/cohort/history/φ/K_a 约定、同信息/预算/调参≤20/固定反馈；JSON `stage2_judgment` 明确同预算复制/超过→`rename_edmd`/`no_increment`、撤主算法；有形状/有限性单测 ✓。
- **JSON 拆分**：`stage2_baselines`=**7 对象**（M2_candidate/B_edmd_system_id/B_full_history_retrain/B_hierarchical_gp/B_koopcell_disiko/B_td_jepa_successor/B_state_space_pkpd）；`stage3_selectors`=**5 对象**（S_M2_candidate/S_random/S_gp_acquisition/S_optimal_input_design/S_batchie）；无混合 `baselines` 键；schema 有 `stage2_baseline_fields`/`stage3_selector_fields` ✓。
- **去重**：`B_full_history_retrain` 单列；former `B_full_retrain` 已合并、无第二 from-scratch；独立比较=**1 candidate+6 baselines** ✓。
- **样本量**：`power.sample_size_policy.status=not_frozen_until_data_gate`；n_units=300 仅 planning example；数据门 D1–D7+合格数据 pilot/headroom 后冻结 n_units_per_background/R/n_eff/SD_D/MDE80/cluster/analysis_unit 并写执行预注册；禁止 example 执行 ✓。
- **保留项**：数据门 D1–D7/current **data_unavailable**（mapping/功能 numeric 缺，C203/C205；missing≠未做）/request spec P0/P1/P2（不伪造联系人/不绕许可/不发起请求/不读数据/不合成替代）；Stage1 仅机制账；固定反馈/同信息预算调参/先程序后背景/新功能同标定；Stage3 selector-learner 分离/合法实验包/完整闭环；seeds 20261200–39/20262100–39（与 Stage1 交集[]）；预算 caps 1800s/2h/8GB/0 wells；失败/边界不变 ✓。
- **链/骨架**：15/15 SHA、mismatches=0、chain_pass=true；Stage1 PASS；12 单测全 PASS；无效果比较/regret/方法差异；JSON 无 telemetry；两跑一致 ✓。

**非阻塞**：pilot 文档 `.02880 s/rep、Stage2 1.38 s/Stage3 2.76 s` 与 `timing_m2_stage2_prep_v0_2.json` 实际 `.031795 s/rep、Stage2 1.53 s、Stage3 3.05 s` 不一致（都远低 caps）；执行前统一即可，不阻止接受设计。

**结论：可提交 Lead 接受 Stage2/3 设计（不执行；data_unavailable；获取/重导优先）。**

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | EDMD learner | **PASS** | `B_edmd_system_id` 在 `stage2_baselines`，role=equivalent strong learner；flow=受控弱 EDMD/系统辨识拟合动作条件算子；同特征/cohort/history/φ/K_a；同信息/预算/调参≤20/固定反馈；`stage2_judgment` 明确 rename_edmd/no_increment；单测 edmd shape ✓。 |
| ② | JSON 结构 | **PASS** | `stage2_baselines` 7 对象、`stage3_selectors` 5 对象；无 `baselines` 混合键；每项字段完整；schema `stage2_baseline_fields`/`stage3_selector_fields`；两跑一致 ✓。 |
| ③ | 去重 | **PASS** | `B_full_history_retrain` 单一；former `B_full_retrain` 合并说明；无第二 from-scratch；1 candidate+6 baselines ✓。 |
| ④ | 样本量冻结 | **PASS** | `sample_size_policy.status=not_frozen_until_data_gate`；n_units=300 planning_example_only；required freeze fields 列全；n_req278/SD .20 仅规划；禁止 example 执行 ✓。 |
| ⑤ | 保留项 | **PASS** | 数据门/current data_unavailable/request spec；Stage1 机制账；固定反馈/等预算/先程序后背景/新功能同标定；Stage3 分离/合法包/闭环；seeds/预算/失败/边界 ✓。 |
| ⑥ | 链/骨架/计时 | **PASS（pilot 文档有非阻塞不一致）** | 15/15 chain、Stage1 PASS；12 单测；无效果；schema 禁列；JSON 无 telemetry；两跑一致 ✓。timing JSON 实际 .031795/1.53/3.05 vs 文档 .02880/1.38/2.76；都远低 caps，需统一（§2）。 |
| ⑦ | 边界 | **PASS** | 机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；执行须另立预注册+独立挑战+Lead 批准+合格数据 ✓。 |
| ⑧ | 总判决 | **approve_stage2_design_v0_2_to_lead** | 仅接受设计；不执行。 |

## 2. 非阻塞实现备注（写入执行记录；不改变批准范围）

1. **pilot 数字统一**：文档写 `.02880 s/rep、Stage2 1.38 s/Stage3 2.76 s`；timing JSON 实际 **.031795 s/rep、Stage2 1.53 s、Stage3 3.05 s**；都远低于 caps（1800 s/2 h/8 GB），执行前用最终代码重跑并冻结 canonical timing，文档/JSON/schema 引用同一 snapshot。
2. **`sample_size_policy` 路径**：实际嵌在 `power.sample_size_policy`，`stage2_plan_v0_2.json` 顶层无同名键；执行预注册需明确读取路径/字段，n_units=300 仅 planning example；数据门+pilot/headroom 后冻结实际 n/R/n_eff/SD/MDE/cluster/analysis_unit。
3. **EDMD learner 与 Stage3 selector 区分**：`B_edmd_system_id` 是 Stage2 learner（拟合动作条件算子）；`S_optimal_input_design` 是 Stage3 selector（最优输入设计，不训练 learner）；执行时不得把 selector 的 acquisition 信息喂给 learner，保持 selector-learner 分离。
4. **数据门/边界**：当前 `data_unavailable`，`gate_pass=false`、`stage2_execution_allowed=false`；D1–D7 通过+SHA/字典/角色/交换性冻结前不执行；request spec P0/P1/P2 为获取/重导优先；不伪造联系人/不绕许可/不发起请求/不读数据/不合成替代；Stage1 只机制账；两跑/schema/失败/边界不变。

## 3. Lead 接受 Stage2/3 设计文本（不执行）

> **批准范围**：接受 R204-M2 Stage2/3 的**设计**（不执行 Stage2/3、不读真实数据/响应、不批效果/药理/真实决策/迁移/新颖性；当前 `data_unavailable`）。
>
> **数据门**：D1–D7 全满足+数据 SHA/字典/角色/交换性冻结前，Stage2 只写 `data_unavailable`，不得合成/RNA/预测替代；request spec P0/P1/P2（mapping、功能 numeric、协议）为获取/重导优先；不伪造联系人/不绕许可。
>
> **Stage2 冻结**：`stage2_baselines`=M2_candidate + **B_edmd_system_id（learner）** + B_full_history_retrain（去重后）+ B_hierarchical_gp + B_koopcell_disiko + B_td_jepa_successor + B_state_space_pkpd（7 对象；1 candidate+6 baselines）；固定反馈/同信息/预算/调参/预训练；先程序后背景；新功能同标定；主端点独立功能决策效用/后悔 δ=.05、headroom<δ→unreachable_gate、MDE=2.801585·SD/√n_eff、cluster CI、6,282 仅 Fisher-z；次端点 secondary；EDMD 同预算复制/超过→rename_edmd/no_increment；样本量执行前冻结（n=300 仅 example）。
>
> **Stage3 冻结**：`stage3_selectors`=S_M2_candidate/S_random/S_gp_acquisition/S_optimal_input_design/S_batchie（5 对象）；同一 learner/updater、selector 与 learner 分离；同成本/合法实验包；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参；候选集/轮次先注册、先程序后背景、全 selector 同菜单、不得事后调；Stage2 PASS+数据+另立批准后启动。
>
> **预算/边界**：Stage2/3 wall≤1800s/CPU≤2h/8GB、0 wells；失败类别/停止/schema/两跑/telemetry 分离；机制账 only；Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据；当前不执行。

## 4. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 Stage2 v0.2 设计/JSON/schema/timing 与 M2/Stage1/DATA1 链；只写本文件与 `tmp/`；未改 Stage2 产物。
- **总判决：approve_stage2_design_v0_2_to_lead**。EDMD learner、7/5 对象拆分、去重、样本量冻结规则、数据门/Stage1 机制账/固定反馈/Stage3/种子/预算/失败/边界均核验通过；仅 pilot 文档与 timing JSON 有非阻塞数字不一致（都远低 caps），执行前统一。仅接受 Stage2/3 设计；不执行；当前 data_unavailable。

**一句话：v0.2 已补 `B_edmd_system_id` Stage2 learner（可判 rename_edmd/no_increment）、拆 `stage2_baselines`=7/`stage3_selectors`=5、合并 full-history/full-retrain 重复、把 n_units=300 降为 planning example 并写 sample_size_policy=not_frozen_until_data_gate；15/15 链、12 单测、两跑均通过——判 approve_stage2_design_v0_2_to_lead（仅接受设计，不执行；当前 data_unavailable；获取/重导优先）。**
