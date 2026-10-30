# Lead 接受：R204-M2 Stage2/3 设计（不执行；当前 data_unavailable；获取/重导优先）

2026-10-28。依据：R204-M2-STAGE2.1-C1（i003）判 **approve_stage2_design_v0_2_to_lead**；EDMD learner 基线、JSON 拆分、去重、样本量冻结规则、数据门/Stage1 机制账/固定反馈/Stage3 分离/预算/失败/边界均 PASS。

## 接受范围
- **仅接受 Stage2/3 设计**；**不执行**、不读真实数据/响应、不批效果/药理/真实决策/迁移/新颖性；当前 **data_unavailable**。
- 冻结 v0.2 链：PROBLEM_M2_STAGE2_v0_2 `2402CEED…`、DESIGN_M2_STAGE2_v0_2 `671BFD46…`、stage2_plan_v0_2.py `2CFD0C73…`、stage2_plan_v0_2.json `156E358F…`、stage23_schema_v0_2.json `BC22524E…`、timing `385FD6A9…`、report `7A63EC03…`、record `E467496D…`、usage `01A2B8A8…`。
- **数据门 D1–D7**：+SHA/字典/角色/交换性冻结前 Stage2 只写 `data_unavailable`；不得合成/RNA/预测替代；request spec P0/P1/P2 为获取/重导优先；不伪造联系人/不绕许可/不发起请求；`gate_pass=false`、`stage2_execution_allowed=false`。
- **Stage2**：7 对象（M2_candidate + `B_edmd_system_id` learner + B_full_history_retrain（去重后）+ B_hierarchical_gp + B_koopcell_disiko + B_td_jepa_successor + B_state_space_pkpd；1+6）；固定反馈/同信息/预算/调参/预训练；先程序后背景；新功能同标定；主端点 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z；**EDMD 同预算复制/超过→`rename_edmd`/`no_increment`、撤主算法**；样本量执行前冻结（n=300 仅 planning example）。
- **Stage3**：5 对象（S_M2_candidate/S_random/S_gp_acquisition/S_optimal_input_design/S_batchie）；同一 learner/updater、selector 与 learner 分离（不得把 acquisition 信息喂给 learner）；同成本/合法实验包；完整闭环；候选集/轮次先注册；**Stage2 PASS+数据+另立批准后启动**。
- **预算/失败/边界**：caps 1800s/2h/8GB/0 wells；机制账 only；Stage1 仅边界/可辨识结果、非效果证据；Stage2/3 执行须另立预注册+独立挑战+Lead 批准+合格数据；不晋升代码；不改旧判定；不恢复停止实验。
- 非阻塞备注：pilot 文档 .02880/1.38/2.76 vs timing .031795/1.53/3.05 → 执行前统一并冻结 canonical timing；`sample_size_policy` 读取路径为 `power.sample_size_policy`；EDMD learner 与 Stage3 selector 保持分离。

## 不批准
- Stage2/3 执行；真实数据/湿实验/药理/真实决策/迁移/新颖性；用合成/RNA 替代独立功能决策；代码晋升；改旧判定/门槛；恢复已停止实验；伪造联系人/绕过许可。
