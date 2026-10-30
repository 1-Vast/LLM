# R204-M2.1 轻量复核（task-147）：v0.2 p=5 修正预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M2、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M2_v0_2.md](PROBLEM_M2_v0_2.md)（SHA `25BC2663…`）、[DESIGN_M2_v0_2.md](DESIGN_M2_v0_2.md)（`5891858E…`）、[formalism_M2_v0_2.py](formalism_M2_v0_2.py)（`DE3C29A9…`）、[formalism_M2_v0_2.json](formalism_M2_v0_2.json)（`A99D31B1…`）、[stage1_schema_v0_2.json](stage1_schema_v0_2.json)（`3CC31B62…`）、[timing_M2_pilot_v0_2.json](timing_M2_pilot_v0_2.json)（`14E24027…`）、report/record/usage v0.2、R204 BRIEF/report、R203-P1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_m2_stage1_to_lead（仅批准 M2 Stage 1 合成实现：机制账、compute-only、0 wells；不批 Stage2/3、真实数据/效果/药理/真实决策/迁移/新颖性）。**

v0.2 已修掉 v0.1 的 p=5 vs p=4 阻断：
- **p=5 唯一**：testbed/schema/code/JSON 统一 p=5；v0.1 的 48/48、40/48、nullity8、U 长度4、pure24 全部移除（只留历史修正说明）。
- **full K**：A·p²=**75**；**30 pure 组=10/动作**（每动作≥p=5）、U 张成 R⁵ → **rank 75/75**。
- **mixed**：20 组、U 变化 → **rank 75/nullity 0**（构造性满秩；条件依赖设计支撑，明确不声称任意混合/有限观测识别全部 K）。
- **same-U** pure+mix → **rank 3/3**（K_aU 可辨识）；**U 长度 5**；无支持动作不可辨识；gauge `K_a→M K_a M^{-1}` ✓。
- **保留项**：记录态正确式；禁止边际捷径（p=5 naive bias 范数 **.26428825≈.2643** 非零）；动作标签/π=cohort 间分配；非闭合 2.7e-15 vs **3.75768926**；正交设计示例；随机化/可交换性合同；形式化/EDMD 边界/三阶段/主端点 δ=.05/headroom/MDE/6,282 仅 Fisher-z/等预算/停止/数据/失败类别/边界未变 ✓。
- **schema/两跑**：`stage1_schema_v0_2.json` 写死 p=5/A=3/full 75/mixed 75/nullity0/param75/U5/pure30/sameU3/无支持/闭合/随机化/caps 600s/2h/8GB/0 wells/禁报增益；formalism JSON 与 schema 两跑逐字节一致；JSON 无 telemetry ✓。
- **pilot**：最终代码 .00228 s/rep、投影 .1/.3/1.1 s（但 timing JSON 实际 .00247/.06/.3/1.19；见非阻塞备注）；都远低于 caps ✓。

**结论：可提交 Lead 批准 M2 Stage 1 合成实现（仅机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | p=5 唯一 | **PASS** | testbed/schema/code/JSON p=5；v0.1 p4 数字仅在历史修正说明；无 p=4 残留；p=5/A=3/d=4/cohorts200/T3 一致 ✓。 |
| ② | p=5 可辨识算术 | **PASS** | full K 75/75（30 pure=10/action，U5）；mixed 20 组 rank75/nullity0（构造性、条件性）；same-U 3/3；U 长度5；无支持不可辨识；gauge；代码/JSON 可复算 ✓。 |
| ③ | 保留项 | **PASS** | 记录态正确式/禁边际捷径（bias .2643）；动作标签/π 语义；非闭合 2.7e-15/3.7577；正交设计/随机化合同；形式化/EDMD/三阶段/主端点/6,282/等预算/停止/数据/失败/边界不变 ✓。 |
| ④ | schema/两跑/pilot | **PASS（pilot 文档有非阻塞不一致）** | schema 写死全部维数/合同/caps/禁增益；formalism JSON 与 schema 两跑一致；JSON 无 telemetry ✓。pilot：docs .00228/.1/.3/1.1 vs timing JSON .00247/.06/.3/1.19；都远低 caps，但需统一（见 §2）。 |
| ⑤ | 边界 | **PASS** | 机制账 only；Stage1 仅受控真值/可辨识检查、不报增益；不称生物学/机制/迁移/真实决策/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage1 执行另立挑战+Lead 批准；Stage2/3 不批 ✓。 |
| ⑥ | 总判决 | **approve_m2_stage1_to_lead** | 仅 Stage1 合成实现；不批效果/Stage2/3/真实数据。 |

## 2. 非阻塞实现备注（写入执行记录；不改变批准范围）

1. **pilot 数字统一**：文档写 **.00228 s/rep、stage1 .1/stage2 .3/stage3 1.1 s**；`timing_M2_pilot_v0_2.json` 实际 **.00247 s/rep、stage1 .06/stage2 .3/stage3 1.19 s**。两者都远低 caps（Stage1 600s、Stage2/3 1800s），**不影响批准**；执行前用最终代码重跑一次并冻结 canonical timing，文档/JSON 引用同一 snapshot。
2. **示例维数说明**：`assignment_estimator_bias` 用 3 函数、`closure_nonclosure` 用 2/3 函数，是独立算术示例，**不是 p=4 残留**；需在表单/记录中标注“示例维数，testbed φ 维固定 p=5”，避免误读。
3. **mixed 75/nullity0 条件性**：该结果依赖构造性设计支撑（20 组、U 变化）；不得在 Stage1 报告中写成“任意混合/有限观测可识别全部 K”；只作为设计算术示例，主结论仍是 pure 30 组 full K 75/75。
4. **Stage1 只做机制检查**：不报效果/增益；失败类别/两跑/schema/预算测试/随机化合同先于结果；caps 600s/2h/8GB/0 wells；Stage2/3 与真实数据/药理须另立预注册+独立挑战+Lead 批准。

## 3. Lead Stage 1 合成实现批准文本（建议）

> **批准范围**：批准 R204-M2 **Stage 1 合成实现**（仅机制账、compute-only、0 new wells）；不批准 Stage2/3 执行、真实数据/效果/药理/真实决策/迁移/新颖性；不批准代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：X/φ（唯一 **p=5**）/闭合声明为待检验假设；固定 π 群体矩 `V_i=Σπ_i(a)K_aU_i`；记录态正确式 `V_i=ΣK_aE[1{A=a}φ(X0)|i]`，禁止边际捷径；π=cohort 间分配、动作标签完整；Stage1 testbed d=4/A=3/p=5/cohorts200/T3、三例；full K 参数 A·p²=**75**、30 pure 组（10/动作、每动作≥5、U 张成 R⁵）→ **rank75/75**；mixed 20 组 rank **75/nullity0**（构造性、条件性，不推广）；same-U **3/3**；U 长度5；无支持动作不可辨识；gauge `M K_a M^{-1}`；非闭合 2.7e-15/3.7577；正交设计/随机化合同；形式化/EDMD 等价边界/三阶段/主端点 δ=.05/headroom/MDE/6,282 仅 Fisher-z/等预算/停止/数据/失败类别/边界不变；Stage1 caps 600s/2h/8GB/0 wells；schema/两跑/失败模板/预算测试；Stage1 只报检查结论不报增益。
>
> **禁止**：Stage2/3 执行；真实数据/湿实验/药理/真实决策/迁移/新颖性；用 RNA/预测/算子误差替代独立功能决策；改 p/阈值/端点后救结果；用 mixed 条件性结果冒充任意混合识别全部 K；晋升代码；不改旧判定；不恢复停止实验。

## 4. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 M2 v0.2 预注册/formalism JSON/schema/timing 与 R204/R203 链；只写本文件与 `tmp/`；未改 M2 产物。
- **总判决：approve_m2_stage1_to_lead**。p=5 唯一、full K 75/75、mixed 75/nullity0 条件性、same-U 3/3、U5、pure30、无支持不可辨识、gauge、非闭合/正交/随机化保留、schema/两跑均核验通过；仅 pilot 文档 .00228/.1/.3/1.1 与 timing JSON .00247/.06/.3/1.19 有非阻塞不一致，执行前统一。仅批准 Stage1 合成实现（机制账/compute-only/0 wells）；不批 Stage2/3/真实数据/效果/药理。

**一句话：v0.2 已把 p=5 唯一冻结，full K 75/75（30 pure、U5）、mixed 20 组 rank75/nullity0（条件性）、same-U 3/3、无支持不可辨识、gauge、非闭合 2.7e-15/3.7577、schema/两跑全部对齐；仅 pilot 文档与 timing JSON 数字有非阻塞差异——判 approve_m2_stage1_to_lead（仅 Stage1 合成实现：机制账/compute-only/0 wells；不批 Stage2/3、真实数据/效果/药理/真实决策/迁移/新颖性）。**
