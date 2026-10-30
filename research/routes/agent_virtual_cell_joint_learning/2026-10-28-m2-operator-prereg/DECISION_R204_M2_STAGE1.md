# Lead 批准：R204-M2 Stage 1 合成实现（仅机制账；compute-only；0 wells）

2026-10-28。依据：R204-M2.1-C1（i003）判 **approve_m2_stage1_to_lead**；p=5 唯一、full K rank 75/75、mixed 75/0 条件性、same-U 3/3、gauge、非闭合反例、schema/两跑/pilot、边界均 PASS。

## 批准范围（仅 Stage 1 合成实现/受控真值检查）
- **仅 Stage 1**：实现并运行**受控真值测试床**（可辨识性/非闭合/随机化合同检查），**不报效果/增益**；不批 Stage2/3 执行、真实数据/湿实验/药理/真实决策/迁移/新颖性。
- 冻结 v0.2 链：PROBLEM_M2_v0_2 `25BC2663…`、DESIGN_M2_v0_2 `5891858E…`、formalism_M2_v0_2.py `DE3C29A9…`、formalism_M2_v0_2.json `A99D31B1…`、stage1_schema_v0_2.json `3CC31B62…`、timing `14E24027…`、report `204270F2…`、record `CE446E7F…`。
- 冻结：X/φ（**唯一 p=5**）/闭合声明/固定 π 群体矩/记录态正确式/禁止边际捷径/π=cohort 间分配/动作标签；Stage1 testbed d=4/A=3/p=5/cohorts200/T3、三例（线性闭合 positive、非线性非闭合 negative、部分支持不可识别 negative）；full K A·p²=**75**、30 pure 组（10/动作、每动作≥5、U 张成 R⁵）→ rank **75/75**；mixed 20 组 rank **75/nullity 0**（**构造性、条件性，不推广**）；same-U **3/3**；U 长度 5；无支持动作不可辨识；gauge `K_a→M K_a M^{-1}`；非闭合 **2.7e-15 vs 3.7577**；正交设计/随机化合同；形式化/EDMD 等价边界/三阶段/主端点 δ=.05/headroom/MDE/6,282 仅 Fisher-z/等预算/停止/数据/失败类别/边界不变。
- 预算：caps **600s/2h/8GB/0 wells**；两跑逐字节；schema/失败模板/预算测试先于结果；只报检查结论不报增益。
- 非阻塞实现备注：① 执行前用最终代码重跑 pilot 并冻结 canonical timing（文档/JSON 引用同一 snapshot；.00228 vs .00247 不混用）；② bias/nonclosure 示例维数须标注"独立算术示例，testbed φ 维固定 p=5"；③ mixed 75/0 仅设计算术示例，主结论仍是 pure 30 组 full K 75/75；④ Stage1 失败只写对应 design_invalid，不改 p/阈值/端点救结果。

## 不批准
- Stage2/3 执行；真实数据/湿实验/药理/真实决策/迁移/新颖性；代码晋升；改旧判定/门槛；恢复已停止实验；用 RNA/预测/算子误差替代独立功能决策；用 mixed 条件性冒充任意混合识别全部 K；用 p=4 的 48/48 冒充 p=5。
