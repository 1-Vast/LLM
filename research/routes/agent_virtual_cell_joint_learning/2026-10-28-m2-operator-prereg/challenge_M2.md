# R204-M2-P1 独立挑战（task-145）：群体功能算子预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M2、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M2.md](PROBLEM_M2.md)（SHA `4AF84EE0…`）、[DESIGN_M2.md](DESIGN_M2.md)（`DAFDCBB3…`）、[formalism_M2.py](formalism_M2.py)（`54B227E9…`）、[formalism_M2.json](formalism_M2.json)（`107DB450…`）、[report_M2.md](report_M2.md)（`3D2EFE93…`）、[record_M2.md](record_M2.md)（`D12503D6…`）、R204 BRIEF/report、R203-P1 链、ERRATA。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_m2_stage1_to_lead，也不是 stop）。**

M2 的形式化方向、任务驱动闭环、EDMD/KoopCell/DisKO 边界、三阶段设计、主端点/headroom/MDE/6,282 边界、等预算基线/停止/数据边界**基本写清且可执行**；但 **Stage 1 测试床的可辨识算术与 φ 维数直接冲突**，是冻结前必须修的硬错误：
- PROBLEM/DESIGN/JSON `synthetic_testbed` 写 **φ 维 p=5**（d=4、A=3、cohorts=200、timepoints=3）；
- 但可辨识算术全部是 **p=4**：`full K` **48/48=3×4²**、`mixed` **40/48/nullity8**、`same U` 的 **U 向量长度4**、`same_U p=4`；JSON `identifiability` 明确 `p=4`。
- **若 p=5，full K 参数为 A·p²=3×25=75**（不是48）；mixed rank/nullity、U 向量、pure-group 数都要重算；**p=5 的测试床不能引用 p=4 的 48/48 作为“full K 可辨识”证据**。
- 这在 Stage 1 正是“已知真值/可辨识性”核心门；不修就批准，执行者要么按 p=5 实现却无法复现 48/48，要么按 p=4 实现但与冻结测试床 p=5 不符。

**结论：不能提交 Lead 批准 Stage 1 合成实现；修完 §2 的 1–2 后可提交。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 形式化 | **PASS** | X/φ；闭合声明 `E[φ(X_Δ)|X_0=x,a]=K_aφ(x)` 为待检验假设；固定 π 群体矩 `V_i=Σπ_i(a)K_aU_i`；**记录态分配正确式 `V_i=ΣK_aE[1{A=a}φ(X_0)|i]`**；禁止边际 π×均值捷径（JSON `assignment_estimator_bias.bias_norm=0.26508092`，非零）；动作标签完整；π=cohort 间分配、非单培养物细胞自由给药/非联用 ✓。 |
| ② | 任务驱动主动辨识 | **PASS** | 从 f_g 条件后继→选起始/给药/时点→真实新矩+闭合检验→K 乘积/已测功能重组、失败报不可复用作用/时程；函数选择/增补/有限样本误差标为开放问题；与传统输入设计差异边界写清 ✓。 |
| ③ | EDMD/KoopCell/DisKO 边界 | **PASS** | 固定 φ 线性闭合=受控弱 EDMD/系统辨识+最优输入设计**等价强基线**；KoopCell/DisKO/TD-JEPA/BATCHIE 已覆盖部分不称新；交叉点仅“破坏性群体测量下功能任务主动选干预辨识可复用作用”；同预算复制/超过→撤/`rename_edmd` ✓。 |
| ④ | 受控测试床/可辨识算术 | **FAIL（p=5 vs p=4）** | 测试床 p=**5**；但 `full K` **48/48=3×4²**、`mixed` **40/48/nullity8**、`same U` **U 长度4**、JSON `identifiability` 全部 **p=4**；p=5 时 full K 参数 **A·p²=75**，mixed rank/nullity/U/pure-group 数需重算。**48/48/40/48 不能作为 p=5 的可辨识证据**。另：同 U pure+mix rank3/3→K_aU 可辨识、gauge、非闭合 2.7e-15 vs3.7577、正交设计/随机化合同本身写清 ✓；但 p 冲突使 Stage1 核心门不可执行。 |
| ⑤ | 三阶段/防选择性 | **PASS** | Stage1 受控真值不报增益；Stage2 合格多时间功能数据、固定反馈、候选 vs full-history retrain/hierarchical-GP/KoopCell-DisKO/TD-JEPA/PKPD，同信息/预算/调参，先留出程序再背景，新功能同标定，只换已观测权重=有限任务重组；Stage3 固定更新器、候选主动干预 vs random/GP/最优输入设计/BATCHIE、完整闭环计成本；防选择性 ✓。 |
| ⑥ | 主端点/δ/headroom/MDE/6,282 | **PASS** | primary=独立功能决策效用/后悔（per endpoint）；δ=.05 normalized；headroom=U_max−U0 先检（<δ→unreachable_gate；近满→budget-to-target；不静默换）；配对/cluster（培养物/背景/任务）；MDE=2.801585·SD/√n_eff；**6,282 仅 Fisher-z 参考非通用门**；RNA/预测/算子误差仅 secondary；与 C197/C199 一致 ✓。 |
| ⑦ | 等预算基线/停止 | **PASS** | 受控弱 EDMD/工具变量系统辨识+最优输入设计（等价强基线）、KoopCell/DisKO、TD-JEPA、state-space/PKPD、层级 GP、full retrain；同信息/预算/调参；标准复制/超过→撤；闭合/随机化/测量合同失败→stop；仅 RNA 收益→撤；成本超限→stop；CI 无法排除→inconclusive；跨任务失败→限当前任务 ✓。 |
| ⑧ | 失败/预算/数据/边界 | **PASS** | 失败类别完整；Stage1 compute-only 0 wells、caps 600s/2h/8GB；Stage2/3 ≤1800s；真实数据需求列明（多时间功能/群体快照、π/动作标签、独立培养/板、正交功能、计数+RNA）；AZ 字典/数值未取得→data_unavailable；机制账 only、不称生物学/机制/迁移/真实决策/新颖性、不晋升代码、不改旧判定、不恢复停止实验；Stage1 执行须另立挑战+Lead 批准 ✓。 |
| ⑨ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5，Lead 批准 Stage 1 前）

1. **冻结一个 φ 维 p，并统一所有文件**：
   - 若采用 **p=5**（PROBLEM/DESIGN/JSON 的 testbed）：`full K` 参数 = A·p² = **75**；每动作≥5 pure 分配、`U_i` 张成 R^5；重算 full rank（应为 **75/75**，不是48/48）、mixed rank/nullity、`same U` U 向量长度5、pure-group 数；重写 `identifiability`/problem/design/JSON/code 的 48/48、40/48、nullity8。
   - 若采用 **p=4**（现 JSON 算术）：把 testbed `phi_dim_p` 改为4、`same U`/examples 统一，并在 PROBLEM/DESIGN 中明确 p=4；**不能 testbed p=5、算术 p=4 并存**。
2. **重算 p=5（或p=4）可辨识示例与代码**：`full K` rank 必须等于 A·p²；mixed 的 rank/nullity 用同一 p 重算；`same U pure+mix rank3/3` 保持；`unassigned action` 不可辨识；gauge `M K_a M^{-1}` 不变；nonclosure residual（2.7e-15/3.7577）与 p 无关，可保留。
3. 更新 **formalism_M2.py/JSON、PROBLEM_M2/DESIGN_M2、report/record**，并在 Stage1 产物 schema 写死 `p`/`A`/`full K rank`/`mixed rank`/`nullity`；重新核 SHA；Stage1 pilot 预算用最终代码重跑。
4. **保持**形式化/记录态估计/EDMD 边界/三阶段/主端点/6,282/等预算/停止/数据/边界不变；**不要用 p=4 的 48/48 冒充 p=5 full K**。
5. 若 Lead 坚持 p=5 而无法在 Stage1 前完成重算与代码更新 → **stop**，不得执行 Stage1。

## 3. 修完后建议的 Lead Stage 1 批准文本（仅合成机制账/compute-only/0 wells）

> **批准范围**：在必改 1–3 完成并复核后，批准 **M2 Stage 1 合成实现**（仅合成机制账、compute-only、0 new wells）；不批准 Stage 2/3 执行、不批准真实数据/效果/药理/真实决策/迁移/新颖性；不批准代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：X/φ（p 唯一定义）/闭合声明为待检验假设；固定 π 群体矩 `V_i=Σπ_i(a)K_aU_i`；记录态正确式 `V_i=ΣK_aE[1{A=a}φ(X0)|i]`，禁止边际捷径；π=cohort 间分配；动作标签完整；Stage1 测试床（d=4/A=3/p 唯一/cohorts200/T3/三例）；可辨识性 full K rank=A·p²（p=5则75/75，或p=4则48/48，必须与冻结 p 一致）、mixed rank/nullity、same U rank3/3、gauge、非闭合反例、正交设计/随机化合同；Stage1 不报增益；caps 600s/2h/8GB/0 wells；失败类别/两跑/schema/预算测试；Stage1 后 Stage2/3 须另立预注册+独立挑战+Lead 批准。
>
> **禁止**：真实数据/湿实验/药理/真实决策/迁移/新颖性；Stage2/3 执行；用 RNA/预测/算子误差替代独立功能决策；改 p/阈值/端点后救结果；用 p=4 算术冒充 p=5；晋升代码；不改旧判定；不恢复停止实验。

## 4. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 M2 预注册/formalism JSON/报告与 R204/R203/N1 链；只写本文件与 `tmp/`；未改 M2 产物。
- **总判决：revise**。M2 的形式化/任务驱动/EDMD 边界/三阶段/主端点/6,282/等预算/数据边界基本正确；但 **Stage1 测试床 p=5 与可辨识算术 p=4（48/48、40/48、U 长度4）直接冲突**；p=5 的 full K 应为 75 参数，不能引用 48/48。修完 p/算术/代码后再提交 Lead 批准 Stage1 合成实现。

**一句话：M2 方向/形式化/EDMD 边界/三阶段/主端点/6,282/等预算/停止/数据边界写清了；但 Stage1 测试床写 φ 维 p=5，而可辨识算术（full K 48/48=3×4²、mixed 40/48/nullity8、same U 长度4、JSON p=4）全是 p=4——p=5 的 full K 参数是 A·p²=75，48/48 不是 p=5 的证据。判 revise：先冻结 p 并重算 full/mixed/U/代码/JSON，或把 testbed 改成 p=4；修完再提交 Lead 批准 Stage1 合成实现（仅机制账/compute-only/0 wells，不批效果/真实决策/药理）。**
