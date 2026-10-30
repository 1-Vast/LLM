# PROTOCOL_DRAFT_v4 — R198-A1v4（per-tissue Breast/Colon；方案 A）

**状态：DRAFT，未冻结、未执行。** 本文件是 [protocol_draft_v3.md](protocol_draft_v3.md) 的修订版（v1–v3 保留不改），落实 R198-A1v3 复审 [challenge_A1_v3.md](challenge_A1_v3.md) 与 **Lead 已决方案 A**（[spec_v4.md](spec_v4.md) §0）。**本轮不运行效果/真实 relations_check；不读 S/U 响应；不声称新颖性。**

## P-1 不可变式

- 不声称新颖性；不越 C141/C154/C160/C167/C171/C172/C174/C175/C176/C177；不换端点/不换聚合；只排组合不排细胞。
- **主族 = per-tissue Breast/Colon**；**Pancreas 明确排除**（29 Original/28 matched 细胞；reference 24+S12=36>29 结构性不可行）并披露外部有效性损失；**删除"跨 tissue 平均/池化"**；**τ_t 从主模型删除**（仅在多 tissue 关系时启用，主族无）。
- `n_ctx_min=12`、`alpha_per_relation=0.01` 不放宽；S=24（Breast12/Colon12）。
- 任何不足 → `data_unavailable`/`design_invalid`/`insufficient_precision` 停，**不降 n_ctx、不放宽 α、不改覆盖分母、不加回 Pancreas**。

## P0a-metadata（metadata-only；先跑；≤10 min）

1. **分配（写死 84/24/17）**：reference 84 ⊆ matched 96；A=42（Breast17/Colon16/Pancreas9）、B=42（Breast16/Colon17/Pancreas9）；S=24（Breast12/Colon12/Pancreas0）；U=17（Breast6/Colon0/Pancreas11）；三向不交；Pancreas 参考细胞仅 nuisance/稳健性，不进主族。
2. **候选网格**：matched 96 的 229 条（Breast134/Colon37/Pancreas58，全单 tissue）；主族 = Breast/Colon **171**；Pancreas 58 结构排除。
3. **S 选择（metadata-only 覆盖最大化，写死）**：remaining 41 池（Breast18/Colon12/Pancreas11）中选 S=24（12/12），最大化"≥12 S 细胞满足 Cond_r 且两侧 library/两浓度元数据键齐全"的候选数；MILP（scipy.optimize.milp/HiGHS）主，确定性贪心兜底；tie-break 冻结 cell 顺序；记录 `s_milp_optimum`（或贪心数）与 SHA。
4. **non-vacuity gate**：主族网格非空；每条关系 tissue span=1；A/B 各≥12；S 覆盖≥12；Pancreas 不在主族；reference⊆matched96；三向不交；**post-precheck eligible ≥86**；否则 `data_unavailable`/`design_invalid` **跑前 stop**。
5. 输出 p0a_metadata.json + SHA；通过后才可跑 P0a relations_check。

## P0a relations_check（参考响应可读；≤30 min）

1. per-tissue 独立关系：细胞级受控对比 d_c；`d_c ~ μ_r + u_batch + ε`（**无 τ_t**）。
2. A 半选方向（bootstrap 稳定性≥0.90）、B 半验证/估区间；A↔B 交换；方向一致率≥0.90；n_ctx≥12；|μ_r|≥0.5σ_r；区间 **w_r≤2.0σ_r**（效用/δ_min 在 P0d）。
3. **覆盖 ≥86/171**；R_old∈[20,200]；primary 族≤10；每关系 α=0.01；primary BH q≤0.10；exploratory BH q≤0.10 仅报告；Breast/Colon 分别报告（不合并）。
4. 输出 relations.csv/relations_check.json/relation_splits.json + SHA。

## P0b constructive 体检（independent generator；依赖模型）

1. 独立生成器 M0（iid）/M1（依赖 ρ∈{0.2,0.4,0.6}、κ∈{1,3,10}）；只用参考方差/相关参数 + 合成长标签，**不注入参考违反结构**；两版独立脚本、与更新器解耦。
2. 注入类每类 ≥30 单元：(i) nuisance-only、(ii) 关系方向在 ≥12 contexts 系统性翻转、(setup) γ≠1/τ_b>0；(iii) 只 proxy、不注入不计判类。
3. 通过：recall≥0.80、precision≥0.80、置换零 type-I≤0.10；**退出率上限固定 0.15/0.10**（operational 分母=eligible S 单元；P95 仅诊断记录，不用于设 cap）；失败→`design_invalid`。iid/依赖矛盾→以依赖版为准并披露。

## P0c MDE/功效预检

1. ρ×κ 4×3 格，每格 ≥1,000 批；`n_eff=n_ctx/(1+(n_ctx−1)ρ̂)`。
2. 目标：**power=80%±0.05**；type-I：点≤0.05 且 **CP95 上界≤0.10**；**CP 精确规则**：0 事件→n≥29 已足（0/29=0.098），预注册取 n≥40（0/40=0.072）；≤1 事件→n≥47（1/47=0.097）；否则按 CP 公式报。
3. **MDE 标注写死**：MDE(80%,n=12)=**p1≈0.930743**；p1≥0.95 为保守设计目标（power=0.88164）。**S=24 按 tissue 12/12 → 每条主族关系最多 12 个 S context；n=14/19 行不可用**；若预期 p1<0.9307 → `insufficient_precision`（不放宽 α、不把 n=14/19 写进主计划）。
4. 任一格不达标 → `insufficient_precision`。

## P0d δ_min/成本/效用（Stage 1 前）

1. δ_min 必须由任务成本/效用定义；未定义 → `blocked_by_utility_definition`（不编造）。
2. 效用宽度检查 `w≤min(2.0σ_r, 0.10×utility_range)`（P0d；P0a 已用 2.0σ_r 先行）。
3. A5 成本接口（A5 修订通过前只 planning CU；未通过 Stage 2 不启动）；预算/墙钟写死。
4. P0d 不过 → 不进 Stage 1；Stage 0 关系表保留。

## P1–P6（保留 v3，更新 v4 差异）

- P1 任务对象：端点 `SYNERGY_DELTA_EMAX`；单位 (c,p,d)；φ 购板前可得、SHA 冻结；S 响应盲抽取（seed/键 SHA）；U 固定菜单（只排组合不排细胞）+ 成本/效用；U 读数隔离；ref/S/U 三元不交；batch 进 nuisance；跨 screen 仅敏感性；A0 matched 96 限制参考。
- P2 统计/判类：X_flip（n=12、α=0.01、MDE p1≈0.9307 + cluster 敏感性）；四解释 M_i/M_ii(J)/M_setup（M_setup 正式模型无 τ_t、共享预测似然）；惩罚拟合（k_E 写死：M_i=q+2、M_setup=q+4、M_ii=q+2+|J|；`score=−2loglik_heldout+k_E log(n_eff)`；δ_fit=2.5 主、2.0/5.0 敏感性；5-fold by cells）；J 候选族/代价（cost=|J| 主，tie-break Σw/σ；敏感性 |J|+0.1Σw/σ；J_max=min(5,ceil(0.10|R|))；60 s）；κ 主法=留出校准半 B 残差 κ_B（κ_N 污染诊断、κ_perm 敏感性）；σ 带一致；退出上限固定 0.15/0.10；Stage 1 只判 (i)/(ii)/(setup)，(iii) proxy；与 A4 协调。
- P3 更新器/对照：M1 PRU-CC 区间约束更新 + 冲突证书；对照 (a) 等式投影核、(b) 同区间无释放 constrained ridge、(c) soft-penalty/层级、(d) 尺寸匹配随机释放 + 全量重训/普通适配/层级 EB/GP；等价条件写死。M2 DPG：Stage 2 才启动；对照 VOI/decision-focused（2602.05340/GoBOED/EVSI/ENBS）；无合法区分测量 → 拒绝购买/宣称。
- P4 失败类别：`data_unavailable`/`design_invalid`/`insufficient_precision`/`blocked_by_utility_definition`/`model_misspecified`/`ambiguous_conflict`/`not_identifiable`/`explained_by_baseline`/`conflict_only_in_development`/`proxy_only`/`leakage`/`completed_null`/`pass_to_stage2`。
- P5 泄漏：φ/关系表/S 键/U 键/δ_min/预算 SHA 接触 y 前冻结；所有对照同信息同预算；置换/尺寸匹配/负对照；planned/observed 分离。
- P6 预算：P0a-metadata ≤10 min；P0a relations_check ≤30 min；P0b ≤20 min；P0c ≤15 min（每格 ≥1,000 批按 CPU 规划）；Stage 1 每臂 ≤45 min、总 ≤2 h；超预算缩任务/停。

## P7 冻结清单（缺一不可；未齐不得冻结）

1. P0a-metadata 输出（分配/171 网格/S MILP 选择/non-vacuity/eligible≥86）+ SHA。
2. P0a relations_check 输出（R_old/覆盖≥86/稳定性/区间/swap）+ SHA。
3. P0b 独立生成器两版结果（iid/依赖、ρ/κ、退出率诊断）。
4. P0c 结果（80%±0.05、CP 规则、n_eff、MDE 标注 p1≈0.9307、S=12 context 联动）。
5. P0d δ_min/成本/效用（或 blocked 状态）。
6. φ/端点/S/U/预算/种子 SHA；更新器对照表；统计/多重比较/裁决规则。
7. 独立挑战复核（本文件修订后须由同一挑战者复审）。

## P8 边界

- 只在 P0a–P0d 全过（P0d 允许 blocked 仅阻止 Stage 1）+ 独立挑战复审通过后才冻结执行 Stage 1；本轮不运行。
- 只写"该参考/反馈/菜单/预算/per-tissue Breast/Colon context 下的 operational 归因与更新比较结果"；不写机制/临床/迁移/决策收益/新颖性；不晋升代码。
- 主族 per-tissue Breast/Colon 分别报告；Pancreas 明确排除并披露外部有效性损失；不写"跨 tissue 平均/每个 tissue 成立"。
