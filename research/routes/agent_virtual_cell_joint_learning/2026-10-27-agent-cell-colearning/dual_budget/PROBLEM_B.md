# PROBLEM_B —— 计算与真实实验双预算决策：形式化问题（R201-B，设计轮，不执行）

2026-10-27/28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：R201 `BRIEF.md`、`agent-cell-colearning/report.md` 方向2（D2）、`d1_information/DECISION_D1_STOP.md`、`d3_feedback/report_d3_v0_2.md`、`acquisition_stage3/cost_model.md`、`core-module-design/oneil_dev/exec_calibration/report_calib.md`、`core-module-design/oneil_dev/report_on3_exec.md`、`PEEK_DISCLOSURE_ON3.md`、C187/C190 记录。**本文件只做形式化/设计；不运行效果、不拟合预测模型、不读响应值。**

## 0. 问题陈述（一句话）

给定候选药物计划集合、当前（可能欠认证的）共同反事实模型、计算预算与真实实验预算，Agent 必须判断当前决策分歧**来自计算/估计不足（可用更多计算解决）还是生物证据不足（必须买实验）**，并在两类预算间分配；决策目标是**未测计划的独立决策收益（top-k/选择/后悔）**，不是预测提分。

## 1. 决策状态（形式化符号）

- **候选计划集** P：可执行的药物/剂量/成员组合计划（含未测计划 P_unseen）；每个计划有披露的共享结构特征（成员、剂量、角色、partner），不把未测计划的响应值当作已知。
- **决策菜单** M：本轮需要排序/选择的计划子集（如 top-k 选择、二选一、预算内组选）；菜单构造规则必须纯元数据、预注册，不得按结果/headroom 选菜单（A5-C1 教训）。
- **当前模型** M_t：声明族内的共同反事实/约束模型（可含相容集、近似证书、后验或集合表示）；包含当前求解精度/认证状态。
- **计算预算** B_C：以**实测 CPU-second** 计（可含并行但需折算；无 GPU）；每个求解、认证、重拟合、约束生成、构图、缓存重认证都计费。
- **实验预算** B_E：以**wells/plates/keys/rounds** 与 **规划成本单位 CU** 计（A5 成本模型；CU 是规划尺度，不是货币）；必须计入对照、重复、失败板、setup 与轮次。
- **动作空间** A = A_compute ∪ A_experiment：
  - A_compute：提高求解精度/迭代、增加分离/对偶证书、重新求解受影响方向、增加近似阶数、重认证缓存；
  - A_experiment：选择计划/细胞/剂量/时间进行真实测量（含 plate 打包、对照、重复、QC 失败预留）。
- **策略** π：在每轮观察 (M_t, remaining B_C, B_E) 后选择继续计算、买实验（买什么）、或停止。

## 2. "计算不足 vs 证据不足"的可操作判据

记 `d` 为当前决策方向（如 `c_q − c_p`，计划比较），`h_in/h_out` 为内外近似/证书界，`Δ_decision` 为预注册的决策裕度（decision margin；由 δ_min 与效用尺度换算，冻结前定义）。

1. **计算不足（compute-limited）判据（可执行、结果前）**
   - 在固定数据上，把计算预算从 B_C 提高到 B_C'（同一实现、同一 seed 族、只变精度/迭代/证书），重新认证；
   - 若 top-k 决策集或最优选择改变，或认证缺口 `g_C(d) = (h_out(d) − h_in(d)) / Δ_decision > 1`，则分类 `compute_limited`；
   - 此时**不应购买实验**（计算歧义未解决，买数据不能认证决策）；优先追加计算，直到 `g_C ≤ 1` 或计算预算耗尽。
2. **证据不足（evidence-limited）判据**
   - 计算已收敛（`g_C ≤ 1`）后，若相容集内仍存在改变决策的世界（`P(decision flip under M_t) > 0`），且存在可买实验使
     `MDE_decision(B_E) ≤ δ_min ≤ headroom`、`power ≥ 0.80`，且实验的期望决策价值 > 其成本 → 分类 `evidence_limited`；
   - 实验选择规则：在计划差/分层上选择**每 CU 期望决策歧义下降最大**的实验包（不是最大预测方差、不是最大参数方差）；
   - 若 `MDE_decision(B_E) > δ_min` 或 `headroom ≤ 0` 或没有合法实验能区分 → **不可购买/未决**，不得把计算歧义误当生物不确定性。
3. **计算充分的停止判据**
   - `g_C ≤ 1` 且相容集内所有世界给出同一决策（对声明菜单）→ `compute_sufficient`；停止，不买实验。
4. **不可识别边界**
   - 若计算/实验都无法在预算内达到 `MDE ≤ δ_min` → `evaluation_cannot_distinguish`（不是结构不存在，也不是策略失败）；记录所需测量/计算规模。

> 判据的关键纪律：**先认证计算缺口，再谈买实验**；数值缺口足够小后才评估真实实验的决策信息价值（与 CL1 的 "certification gap vs data ambiguity" 一致，但不声称新的最优调度）。

## 3. 双预算策略（何时算/何时测/买什么）

**Baseline policy π_dual（预注册草案，非运行）**：

1. 初始化 M_t，记录 `B_C/B_E` 与成本账本；
2. **计算阶段**：用当前证书/近似算决策集；把计算预算依次投入最影响决策的求解/认证（按 `g_C(d)` 排序）；每笔计算计费；重复直到 `g_C ≤ 1` 或 B_C 剩不足最小计算单元；
3. **决策分类**：
   - 若 `compute_limited` 且 B_C 未尽 → 继续 2；
   - 若 `compute_sufficient` → 停止（输出当前决策/证书）；
   - 若 `evidence_limited` → 进入实验选择；
4. **实验选择**：在预注册实验菜单中，选最大化「期望决策收益/规划 CU」的计划包；同时满足 `MDE_decision(B_E) ≤ δ_min`、`power ≥ 0.80`、同信息/同成本/同 cell 集合；买实验并更新 M_t（真实反馈统一修订共同约束；不允许只改已测点）；
5. **循环**：新证据回填后重算 `g_C`，重认证；每轮计费；最多 R_max 轮；
6. **停止/失败**：触发 §2/§5 的任一停止条件；不得看结果换指标/切分/预算/目标。

**何时算**：决策集对求解精度敏感、证书 gap 大、重认证可减少决策翻转且成本低于实验；
**何时测**：compute 收敛后仍存在可区分的相容世界，且实验有足够 power、成本在 B_E 内；
**买什么**：计划差/分层上的最小决策区分集（预注册候选动作），不是按预测方差/参数方差；实验包必须能映射到共同修订。

## 4. 与普通决策 AL / BOED / COPEx 的关系（不得声称新颖性）

- 普通决策主动学习（decision-focused AL）、BOED/EVSI/ENBS、动态约束实验设计（COPEx）、GP/贝叶斯优化等**已覆盖**"用决策价值选实验、非短视设计、约束生成、计算决策"的一般概念（R201 BRIEF/`report.md` §2；CoMap/LAWM/MDA/COPEx 已覆盖一般联合/任务摘要/动态约束）。
- 本设计**不主张**新的 AL/BOED 算法、不主张预测分歧采样、不主张"首次双预算"；与上述方法的差别仅限定为：**具体共享对象**（跨计划共同反事实/约束算子 + 其计算认证状态）与**具体更新运算**（计算证书收紧 + 真实实验统一修订共同对象，再改变下一次计划选择），以及把两类预算的**可审计成本账**写入决策状态。
- 这些差别是否构成新意，必须由同信息/同预算的同任务比较决定；若普通方法在等预算下等效，则**撤一般算法新意**（见 §6 停止条件）。

## 5. 决策规则/预注册要素（草案，待 DESIGN_B 冻结）

- **主假设 H_B**：在**同等总成本**（同 (B_C,B_E) 或同总 CU + 同实测计算秒；含对照/重复/失败板/轮次）下，`π_dual` 在留出未测计划上的决策收益（top-k/选择/后悔）高于最佳单一预算策略（compute-only / experiment-only），且**不是**由预测提分替代（预测指标只作辅助/阴性对照）。
- **比较器**：固定计算+随机实验；固定实验+更多计算；全历史重训；普通决策 AL；GP/BOED；通用求解器；随机预算分配（零模型）；oracle 上界仅描述。
- **主终点**：留出未测计划的 top-k 决策收益（或预注册归一化后悔；二选一在 DESIGN_B 冻结）；次：迁移（不作为主推断）、预测指标（辅助）。
- **MDE/δ_min**：δ_min 与效用尺度必须预注册；MDE 按决策指标与独立聚类单位计算；`MDE_decision(B) ≤ δ_min ≤ headroom` 才能买/判；否则 `evaluation_cannot_distinguish` 或 `blocked_by_utility_definition`。
- **零模型**：随机决策、随机预算分配、shuffle 计划效用/分配标签、compute-only 同预算、experiment-only 同预算、solver-seed shuffle。
- **失败类别**：`data_unavailable`、`design_invalid`（precision/leakage/cost/utility）、`evaluation_cannot_distinguish`、`no_increment`、`no_decision_benefit`、`cost_sensitive`、`protocol_deviation`。
- **停止条件**：同信息全局求解/共享后验/约束生成/普通 AL/BOED 等效完成同任务 → 撤新意；只改善预测不改善决策 → `no_decision_benefit` 停决策创新；只在当前背景成立 → 停迁移；MDE>δ → 未决并记录所需测量；数据/预算不可得 → `data_unavailable`。

## 6. 不重复的已否定路线（写死）

- **D1（R200）stop**：`precision_insufficient`（T2 MDE 0.0941>δ 0.05；不采用乐观独立规划）。
- **D3（R200）design_invalid**：单 anchor MDE 0.112>0.10；rank MDE 2.29（n_eff=6）/0.76（pooled30）；技术重复/加 wells 不增加独立细胞 n。
- **A1（R199）data_unavailable**：relations_check R=2<20、coverage=1.17%<86%；冻结资格门未过。
- **C187**：药对级主动学习无优势（Δ=−0.0040 [−0.0127,+0.0054]，MDE 0.0142；估计饱和）；本设计不得把"再做普通 pair-level AL"当新问题。
- 因此 B 的问题必须是**双预算决策**（计算与实验的分配 + 决策收益），不得退化为"再买更多数据"或"预测提分"。

## 7. 继承的 peek/非盲边界

- 本设计写于 ON3 v1.2 与 QUICK 之后，属于 **non-blind/inherited-peek** 上下文；**未使用** ON3 响应/QUICK primary 结果选择本设计的方向/阈值/切分/预算/比较器（QUICK 仅用于门规格诊断，已 quarantine）。
- 若未来执行使用 O'Neil/ON3 数据，必须携带 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…` 披露，**不得称盲验/独立确认/预注册确认**；结论只能写开发性描述（non-blind/peeked）。
- 技术重复≠独立培养；batch3 全失、702 个 15 行 pair-cell、无双药参照等限制不变；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**。
