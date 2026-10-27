# R196 判定撤回与重跑要求（REVOCATION，2026-10-27）

依据：独立挑战 [challenge_R196.md](challenge_R196.md)（task-29，i003-challenger）判决 **revise（≤5 必改）**；Lead 核对 `r196.json` 数字后认可。**本文件立即生效：R196 现有 verdict `replicated_under_audit` 撤回，在 AMENDMENT-001 重跑并通过挑战前，不得解释、引用为"审计协议下 C130 仍可靠"。** 原始数字（`r196.json`）保留为已执行结果，不改写。

## 1. 撤回理由（挑战的核心）

1. **主推断单位与审计目标不匹配**：预注册主 CI/MDE 用**细胞聚类**（cell CI [0.1213,0.1667]、MDE80_cell=0.032 → 判定 replicated）；但 R196 的审计目标是"**未见药物**"——按 **drug-cluster**：CI **[0.0139,0.2233]**、**MDE80_drug=0.1527 > δ_min=0.05**；5 个外层折 per-fold 增益 [0.0820,0.2952,0.2682,0.0661,0.0118]，fold SD=0.128、**t-CI [−0.0144,0.3037] 含 0**。按协议 §9"inconclusive = MDE>δ_min"，在主单位（drug）上应为 **inconclusive/weakened**；现 verdict 是靠最窄聚类口径通过。`r196.json` 的 reliability_qualifier 已承认"MAGNITUDE is not pinned at delta_min under held-out-DRUG resampling (MDE80_drug>0.05)"但 verdict 未变。
2. **单一 5 折药物划分**：不能估计"换一批留出药物"的方差（C130 原用 40 个重叠划分，已批评不能当独立 CI；R196 至少需预注册 ≥10 个独立药物划分/划分级重采样作为主方差）。
3. **内层 λ 选择口径混用**：grouped 用"3 个内层折预测拼接后的 pooled Spearman"（跨折截距/尺度混合），row-level 对照用"折均 Spearman" → H196b 的 rowlevel−grouped 差不是干净的行级 vs 分组对比；λ 网格扩到 10000 后 row-level 5 折全选 10000/3000，"复现 C130 口径"越界（C130 ≤1000）。
4. **δ_min=0.05 与稳定带上界 0.20（=0.1183×1.69）无 operational 理由**；需与主单位（drug）的 MDE 门槛联动。
5. **措辞/披露**：当前 verdict 会越界（需固定句式：replicated 只能是"审计修正协议 + 固定划分/声明推断口径内增益为正"；weakened 不得写 C130 被推翻；不得写外部复现/独立确认/决策收益）；需披露预冻结 peek（annotation-only ≈0.149；主 arm/identity/row-level 未在原型运行）；需声明 C130 CI 不是参照区间。

## 2. 当前登记口径（不改原始数字）

- **R196 初步结果**（r196.json）：主增益 0.1447；cell CI [0.1213,0.1667]；pair CI [0.0898,0.1876]；twoway [0.0872,0.1958]；drug CI [0.0139,0.2233]；MDE80_drug=0.1527、MDE80_pair=0.0721、MDE80_twoway=0.0783、MDE80_cell=0.0320。
- **登记判定**：`inconclusive（审计目标单位=MDE80_drug>δ_min）` **且** `weakened（折间 t-CI 含 0，仅 5 折单划分）` 并列；**不是 replicated**。C130 的"审计级可靠性"仍未建立；也不得写"C130 被推翻"。
- R196 不得进入 SYNTHESIS 的"成立"类；C130 状态保持"冻结但未被外部/审计级确认"。

## 3. 重跑要求（AMENDMENT-001，必须全部满足才能重新判定）

1. **主推断单位**：held-out 药物/药物划分（drug-cluster 主 CI + MDE80≤δ_min 判据）；细胞水平结果只作次级描述。
2. **≥10 个独立药物划分**（或划分级重采样），预注册；fold dispersion 从描述性升级为正式 sensitivity；报告划分级均值/CI。
3. **统一内层 λ 指标**：grouped 与 row-level 都用"折均 Spearman"或都做折内标准化；row-level 加 C130 原网格（≤1000）桥接，重做 H196b（行级 vs 分组差）。
4. **δ_min/稳定带 operational 化**：与 drug 单位 MDE 联动；写死"最小有用增益"的理由（不得用旧 CI 倒推）。
5. **措辞模板与披露**：固定句式 + 预冻结 peek 披露 + C130 CI 非参照 + 可比性声明（数据/端点/特征同构但折数/λ 网格/内层口径不同）。

重跑产物：`AMENDMENT_R196.md`、`r196_v2.py/json/rows.csv`、`report_r196_v2.md`、`record_r196_v2.md`、`usage_r196_v2.json`；跑完需再经独立挑战（task-32）通过后才能解释。原始 `r196.json`/`r196.py` 保留。

## 4. 影响

- 撤回仅针对"R196 审计协议下 replicated"这一判定；不改变 C130 原始冻结结果、不改变 A1/A2/A3 的结论。
- 外部重审关于 C130"可能只学平均倾向/无细胞特征"的批评仍有效；R196 重跑是检验其可靠性的必要步骤。
