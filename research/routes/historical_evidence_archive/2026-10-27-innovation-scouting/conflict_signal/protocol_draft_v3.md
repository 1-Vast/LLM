# PROTOCOL_DRAFT_v3 — R198-A1（跨 tissue 池化关系冲突信号）

**状态：DRAFT，未冻结、未执行。** 本文件是 [protocol_draft_v2.md](protocol_draft_v2.md) 的修订版（v2 保留不改），落实 R198-A1v2 复审 [challenge_A1_v2.md](challenge_A1_v2.md) 的 5 必改与 **Lead 已决事项**（[spec_v3.md](spec_v3.md) §0）。**本轮不运行效果/relations_check/体检/MDE 预检；不读 S/U 响应；不声称新颖性。**

## P-1 不可变式

- 不声称新颖性；不越 C141/C154/C160/C167/C171/C172/C174/C175/C176/C177 边界；不复活 R196/R197（已作废）；不换端点/不换聚合；只排组合不排细胞。
- **Context = 跨 tissue 池化（tissue 进 nuisance）**；主族 = pooled；Breast/Colon 限制版仅敏感性；per-tissue 仅 exploratory。
- `n_ctx_min=12`、`alpha_per_relation=0.01` 不放宽；S=24（24≥12）。
- 若池化后仍不可行 → `data_unavailable`/`design_invalid` 停，**不降 n_ctx、不放宽 α、不改 context 定义**。

## P0 流程清单（按序；短路）

### P0a-metadata（metadata-only；不读任何响应）
1. 细胞分配（写死；seed 20261027；分层按 tissue；三元不交）：
   - **reference 84 ⊆ matched 96**（A0 匹配细胞）；**A=42、B=42**；
   - **S=24**（来自剩余 41 = 12 matched 余 + 29 unmatched Original）；**U=17**；
   - A/B 在 tissue 上比例分层（matched 96：Breast33/Colon35/Pancreas28），记录分配 SHA；若 96 不足 84 或 S/U 不足 → `data_unavailable`；
   - **64/16 口径废弃**，统一 84/24/17。
2. **候选关系网格（写死）**：A0 matched 96 上 pooled 池化的同 anchor/同两浓度/同方向受控 library 对比；网格 = **229 条**；A42/B42 切分下 A/B 均 ≥12 的供给预计 ≈154（Breast 86/Colon 37/Pancreas 31）。
3. **S 侧 Cond_r 覆盖预检（新，metadata-only）**：每条候选关系必须存在 **≥12 个 S 细胞**在 Cond_r 内且两侧 library/两浓度元数据键齐全（不读 y）；不满足者不进关系构造；预检后候选 <115 → `data_unavailable`。
4. 输出：`p0a_metadata.json`（分配/网格数/预检数/SHA）；冻结后才可进入 P0a 关系构造。

### P0a relations_check（关系资格；参考 cell 响应可读，S/U 不可读）
1. 关系单位/模型：细胞级受控对比 `d_c`；`d_c ~ μ_r + u_tissue + v_batch + ε`；tissue/batch 进 nuisance（随机/固定效应按预注册算子）；主族 = pooled Cond_r。
2. A/B 半分离：A 选方向（bootstrap 稳定性 ≥0.90）、B 估区间与验证方向；A↔B 交换复核；方向一致率 ≥0.90。
3. 统计（写死）：每关系精确单侧符号检验 **α=0.01**；**primary 族 ≤10**（预注册排序）BH q≤0.10；exploratory BH q≤0.10 仅报告；`n_ctx≥12`；`|μ_r|≥0.5σ_r`。
4. **区间宽度验收仅 `w_r ≤ 2.0σ_r`（P0a）**；**效用范围/δ_min 在 P0d，P0a 不依赖 utility**。
5. **覆盖：通过关系 ≥ 115/229（写死）**；`R_old∈[20,200]`；`J_max`/释放/κ 估计不在 P0a（P0a 只输出关系表）。
6. 输出：`relations.csv`（关系、Cond_r=pooled、μ/区间/σ/n_ctx/stability/swap、primary/exploratory、SHA）、`relations_check.json`（gates/失败类别）、`relation_splits.json`（分配 SHA；默认不写细胞名）。
7. 失败类别：`data_unavailable`（供给/覆盖/细胞不足）、`design_invalid`（协议/实现冲突、budget 超限）。预算 ≤30 min；超时 → design_invalid。

### P0b constructive 体检（independent generator；依赖模型）
1. **独立生成器**（不得注入参考违反结构）：只用 (a) 参考估计的方差/相关参数（σ, τ_t, τ_b, ρ）与 (b) 合成类标签生成；
   - 版本 M0（iid：ρ=0,τ=0）与 M1（依赖：ρ∈{0.2,0.4,0.6}、κ∈{1,3,10}）；两版均由独立脚本实现、与更新器解耦。
2. 注入类 **每类 ≥30 单元**：`(i) nuisance-only`、`(ii) relation 方向在 ≥12 contexts 系统性翻转`、`(setup) γ≠1/τ_b>0`；（(iii) 只 proxy，不注入、不计判类）。
3. 通过：每类 recall≥0.80、precision≥0.80；置换零 type-I≤0.10（point；CP 规则见 P0c 同款）；退出率 ≤ P0a/P0b 派生上限（§P0b-4）。
4. **退出上限（operational 分母）**：分母 = eligible S 单元（P0a 关系表 ∩ S 中 Cond_r 可用的 cell×relation 单元数，P0a 输出冻结）；上限 = `max(0.15, P95_notid)`、`max(0.10, P95_ambig)`（P0b 依赖零 1,000 批分位）；若 P95 超硬天花板 → `design_invalid`。
5. 失败 → `design_invalid`；iid/依赖两版矛盾 → 以依赖版为准并披露。

### P0c MDE/功效预检
1. 依赖生成模型网格：ρ∈{0.0,0.2,0.4,0.6} × κ∈{1,3,10}；每格 **≥1,000 批**；`n_eff = n_ctx/(1+(n_ctx−1)ρ̂)` 写死。
2. 目标：δ_min 处 **power=80%±0.05**；type-I：point≤0.05 且 **CP 95% 上界≤0.10**（不足则预注册追加 sims 到 ≥40 或 47 全 0/≤1 的 CP 规则）；报告 MDE/CP。
3. 任一格不达标 → `insufficient_precision` 停（不换聚合/不放宽 α/不改 δ_min 后跑）。
4. **MDE 标注（写死）**：MDE(80%, n=12)=**p1≈0.9307**；p1≥0.95 为**保守设计目标**（power 0.8816）；n–p1 表见 [spec_v3.md](spec_v3.md) §3.1；若预期 p1<0.9307 按表增大 n，否则 insufficient_precision。

### P0d δ_min/成本/效用（Stage 1 前）
1. δ_min 必须由任务成本/效用定义（单位=U 的效用/损失）；未定义 → **`blocked_by_utility_definition`**（不得编造；不得用旧 CI 反推）。
2. 进行效用宽度检查 `w_r ≤ min(2.0σ_r, 0.10×utility_range)`（Stage 1 前；P0a 已用 2.0σ_r 先行）。
3. 预算/成本：A5 成本接口（A5 修订通过前只 planning CU；A5 未通过 → Stage 2 不启动）；Stage 1 预算与墙钟写死。
4. P0d 不过 → 不进入 Stage 1；Stage 0 关系表保留（报告 `blocked_by_utility_definition`）。

## P1 任务对象（Stage 1 冻结字段）

- 端点 `SYNERGY_DELTA_EMAX`（换端点=新轮）；单位 `(c,p,d)`；φ 购板前可得、SHA 冻结；S 响应盲抽取（seed/键 SHA 冻结）；U 固定菜单（只排组合、不排细胞）+ 成本/效用；U 读数隔离。
- 参考 S/U 三元不交；screen/batch 进 nuisance；跨 screen 只作敏感性；A0 matched 96 限制参考。

## P2 统计与判类（Stage 1；继承 spec_v3 §3）

- X_flip：n_ctx=12、α=0.01、p1 表/ MDE 标注写死；sign test 主统计量 + cluster bootstrap/置换敏感性；不一致 → `ambiguous_conflict`。
- 四解释 `M_i / M_ii(J) / M_setup`（(iii) proxy）：M_setup 正式概率模型（γ/τ_t/τ_b + 共享预测似然）；惩罚拟合法 `score(E)=−2·loglik_heldout+λ_k·k_E·log(n_eff)`（λ_k=1 主；δ_fit=2.0；5-fold by cells）；J 候选族生成/`J_max`/60 s；κ 三法估计与 σ 带一致性；`Δ_pred(U)`。
- 判类：top-2 score 差 ≤δ_fit 或对 U 预测不同 → `ambiguous_conflict`；禁止顺序默认/释放廉价=证据/事后 tie-break；退出上限按 P0b 派生分母。
- Stage 1 只判 (i)/(ii)/(setup)；**(iii) 仅 `proxy_only`**；与 A4 协调。
- 主指标：未查询菜单配对决策损失 Δℓ（等预算），按细胞/药对聚类 bootstrap；δ_min 冻结；MDE 按 P0c。

## P3 更新器与对照（继承 v2，写死）

- M1 PRU-CC 区间约束更新 + 冲突证书；λ 内层药物分组 CV；J 候选/规模/时间上限。
- 对照：等式保护投影核、同区间无释放 constrained ridge、soft-penalty/层级先验、尺寸匹配随机释放、全量重训、普通适配、层级EB、GP；等价性条件（等式/无激活才等投影核；区间激活=QP 不等价）写死。
- M2 DPG：Stage 2 才启动；对照含 VOI/decision-focused（2602.05340/GoBOED/EVSI/ENBS）；无合法区分测量 → 拒绝购买/宣称。

## P4 失败类别（写死）

`data_unavailable`（P0a 供给/覆盖/细胞/S 侧覆盖不足）、`design_invalid`（协议/实现冲突/budget/P0b 体检失败/退出上限超）、`insufficient_precision`（P0c 不达标/context<n 表）、`blocked_by_utility_definition`（P0d 未定义）、`model_misspecified`/`setup_error` 子标签、`ambiguous_conflict`、`not_identifiable`、`explained_by_baseline`、`conflict_only_in_development`、`proxy_only`、`leakage`、`completed_null`、`pass_to_stage2`。

## P5 泄漏/公平（写死）

ref/S/U 三元不交；S 响应盲抽取；φ/关系表/S 键/U 键/δ_min/预算 SHA 在接触 y 前冻结；U 隔离实现失败=leakage；关系构造不用 S/U；所有对照同信息同预算；必做置换/尺寸匹配/负对照；报告 planned/observed 分离；不换端点/分层/阈值/context。

## P6 预算/墙钟

P0a-metadata ≤10 min；P0a relations_check ≤30 min；P0b ≤20 min；P0c ≤15 min（每格 ≥1,000 批按 CPU 规划）；Stage 1 每臂 ≤45 min、总 ≤2 h；超预算缩任务/停，不扩时间。

## P7 冻结清单（缺一不可；未齐不得冻结）

1. P0a-metadata 结果与 SHA（分配/S 侧覆盖/网格 229/供给）。
2. P0a relations_check 结果（R_old/覆盖 ≥115/稳定性/区间/swap）与 SHA。
3. P0b 独立生成器两版结果（iid/依赖、ρ/κ 敏感性、退出上限派生）。
4. P0c 结果（80%±0.05、CP 规则、n_eff、MDE 标注 p1≈0.9307）。
5. P0d δ_min/成本/效用（或 blocked 状态）。
6. φ/端点/S/U/预算/种子 SHA；更新器对照表；统计/多重比较/裁决规则。
7. 独立挑战复核（本文件修订后须由 challenge_A1_v2 同一挑战者复审）。

## P8 边界

- 只在 P0a–P0d 全过（P0d 允许 blocked 仅阻止 Stage 1）+ 独立挑战复审通过后才冻结执行 Stage 1；本轮不运行。
- 只写"该参考/反馈/菜单/预算/跨 tissue 池化 context 下的 operational 归因与更新比较结果"；不写机制/临床/迁移/决策收益/新颖性；不晋升代码。
- 主族 = 跨 tissue 平均（tissue 进 nuisance）；Breast/Colon 只是敏感性；不写"每个 tissue 成立"。
