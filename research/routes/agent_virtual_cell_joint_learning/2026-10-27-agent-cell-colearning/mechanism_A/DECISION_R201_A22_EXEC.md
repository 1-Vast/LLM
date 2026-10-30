# Lead 批准：R201-A.2.2 data-only P1 重跑（异方差稳健 σ；0 新 wells；不进 P2/S2/H_A2）

2026-10-28。依据：A.2.2-C1（i003）判 **approve_a22_to_lead**；SHA/算术一致；R4 fuller-profile resampling 唯一 eligible（coverage .875/FPR .0439/worst .121/context-p95 .076/power .183）；D2/D3 重设计、零模型/预算/失败类别/边界 PASS。

## 批准范围
- **仅 A.2.2 data-only P1 重跑**：0 新 wells、不读新响应做效应、不做生物学/机制/迁移/决策收益/新颖性主张；**不批准 P2/S2/H_A2；A.1 `p0p1_negative` 与 A.2 `design_invalid: scale_mismatch` 不重判**。
- 冻结：数据/target30/完整 4×4/|U|=340,088；A.2 legal（σ_obs_A2≈0.0910607、n_legal_A2≥17,004.4）；**R4 per-context σ²_R4(c)**=`mean_{a<b}||P⊥(f_a−f_b)||²/(K−1)`（full-profile plan-pair 差；每 context ≥2 plans；排除 pair≤5% 否则 coverage）；F_pair 共享 context σ²_R4；D1–D7 先于 P1；D2=per-context F_self 中位 coverage∈[.5,2]≥.85 + 全局中位∈[.5,1.5] + overall F_self FPR≤.10；D3=overall FPR≤.10 + worst-context FPR≤.25 + context-FPR p95≤.20；F_crit=2.60 仅 D2+D3 PASS 保留；N_perm=500 seed=20261029；通孔 BH q=.05；阳性三条件同 A.1；primary null=N0-strat（分层 χ²₃/3）、per-cell=N1-R4 bootstrap；≈2,500 模拟；wall≤900s/CPU≤2h/8GB；两跑逐字节、JSON 无 telemetry；失败类别统一。
- 解释边界：阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`，**不写矛盾不存在**；pair 级仅描述性；non-blind/peeked；禁止用 A.1/A.2 observed 改规则/阈值、减 N_perm、把阳性写生物学/机制/迁移/决策收益。
- 非阻塞实现备注：① D2 的 F_self/coverage 精确公式写死（`F_self(p,q)=[||P⊥(f_p−f_q)||²/(K−1)]/σ²_R4(c)`；per-context coverage=F_self∈[.5,2] 比例；全局中位；context-FPR p95）；② R4 σ mean 含被检验 pair（resubstitution/finite-sample 校准，不称"独立尺度"；建议 leave-one-pair-out 敏感性，不作主判定）；③ 披露措辞：候选选择/校准只用合成，C194 仅用于问题诊断与预设阈值，不用于 A.2 P1 observed 选择；实现后做 pilot 预算测试；R4 前置排除>5% 只写 `design_invalid: coverage`，不进 F 推断。
