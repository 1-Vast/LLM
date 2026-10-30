# Lead 批准：R204-M3 Stage 1 合成实现（支撑研究；仅机制账；compute-only；0 wells）

2026-10-28。依据：R204-M3.1-C1（i003）判 **approve_m3_stage1_v0_2_to_lead**；标准基线/Stage2-3 arms、失败类别、Fisher-z 标注、保留项/自检/两跑/pilot、边界均 PASS。

## 批准范围（仅 Stage1 合成诊断）
- **仅 M3 Stage1**：实现冻结一步 DR 形式化与 Step1 合成已知真值诊断（DR 正确性/截断/低支持/错设/共线/分配二阶项/π=b 退化等 19 checks + S1-a–e 类检查）；**不报效果/增益/方法比较**；不批 Stage2/3、真实数据/湿实验/药理/真实决策/迁移/新颖性。
- 冻结 v0.2 链：PROBLEM_M3_v0_2 `15DFE82C…`、DESIGN_M3_v0_2 `033D67CB…`、formalism_M3_v0_2.py `3E709B81…`、formalism_M3_v0_2.json `299E5B03…`、schema_M3_v0_2.json `E2E641BC…`、timing `BA261FA7…`、report `039B1A98…`、record `47042AD6…`。
- 冻结：一步 DR `H_k=π_k/b`、`δ_k=E[H_k(Y−mθ)]`、`V_k=E_hΣπ_k mθ+δ_k`；**评价样本独立于拟合/策略选择**；更新 `logit m_{θ,ε}=logit mθ+Σε_kH_k`；概率/权重截断 C；共线/分离/无支持→`nonidentifiable`；**只更新功能均值≠细胞动力学兼容更新**；无完整序贯历史/propensity/删失不称序贯 DR；分配二阶项 `Σπ_k²[Var+(E−mθ)²]/b`、错设不能只按 Var；π=b→H=1。
- **标准基线**：含 optimal_experimental_design 与 decision_AL（同信息/反馈/调参≤20/caps/合法实验包）；Stage2 6 arms、Stage3 7 arms；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤。
- **失败类别**：含 `design_invalid: nonidentifiable`、`design_invalid: two_run_mismatch`（按 schema 顶层 failure_categories/failure_template 路由）；失败只写类别不报效果。
- **Fisher-z 标注**：6,282.1038/1,572.7759 仅 Fisher-z 连续规划参考（non_integer/not_a_gate/not_paired_DR/not universal）；决策用 MDE .047982685/n_req278/headroom/cluster。
- 自检算术：DR gap 0；clip bias −.026407185629；ε root −.562633036711；rank1；ratios 1.217/1.167；19 checks PASS；两跑逐字节；canonical pilot 执行前用最终实现重跑冻结。
- caps 1800s/2h/8GB/0 wells；两跑逐字节、JSON 无 telemetry；schema/失败模板先写；失败只 design_invalid。
- 非阻塞备注：`failure_categories` 读取路径为 `three_stage_plan.failure_categories` 与 schema 顶层并用；pilot 重跑冻结 canonical；目标样本不作标签、评价样本独立、propensity/支持/截断冻结。

## 不批准
- Stage2/3 真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；把标准 DR/TMLE+最优分配等价写成 M3 增量；把功能头校准升级为细胞规律；改公式/阈值/端点救结果；代码晋升；改旧判定/门槛；恢复已停止实验。
