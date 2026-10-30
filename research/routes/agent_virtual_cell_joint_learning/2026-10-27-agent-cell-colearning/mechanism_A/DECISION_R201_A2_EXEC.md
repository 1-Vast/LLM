# Lead 批准：R201-A.2 data-only P1 重跑（0 新 wells；不进入 P2/S2/H_A2）

2026-10-28。依据：A.2.1-C1（i003）判 **approve_a2_to_lead**；S2 ×0.5 修正、F_self_check 重写、legal 规则/校准表/预算/失败类别统一 PASS，SHA/算术一致。

## 批准范围
- **仅 A.2 data-only P1 重跑**：0 新 wells、不读新响应做效应、不做生物学/机制/迁移/决策收益/新颖性主张；**不批准 P2/S1/S2/H_A2，不重判 A.1**。
- 冻结：O'Neil batch1 complete-case/target30/完整 4×4/|U|=340,088；A.2 legal `RMS≤1.96·σ_obs_A2`（σ_obs_A2=0.0464595，阈值 0.0910607）、n_legal_A2≥17,004.4；`σ_pair²_A2=0.5×mean||P⊥(f_h1−f_h2)||²/(K−1)`（预期 0.00107924）；F_self_check 用 A={1,2}/{3,4}、B={1,3}/{2,4} 两套半拆 d_avg；D1–D7 先于 P1；F_pair/per-cell T_c/pooled/BH q=.05/F_crit=2.60（仅 D2+D3 通过时保留）；N_perm=500；primary null=N0（pooled χ²）；per-cell=N1 bootstrap；阳性三条件同 A.1。
- 预算：wall≤900s、CPU≤2h、内存≤8GB、≈2,500 模拟、两跑逐字节、JSON 无 telemetry；超→`design_invalid: compute_budget_exceeded`（不减 N_perm）。
- 失败映射：D1/D2/ratio/F_crit→`scale_mismatch`；D3→`noise_calibration`；D4/D5→`null_calibration`；D6→`compute_budget_exceeded`；D7→A.1 既有类别。
- 解释边界：阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`，**不写矛盾不存在**；pair 级仅描述性；non-blind/peeked；禁止用 A.1 结果改 null/σ/阈值、用 A.2 observed 选规则、把 positive 写机制/生物学。
- 实现备注：F_self_check 按 well 索引同组同 seed 记录 d；legal 的 σ_obs_A2 为行均值噪声 SD（σ_w_hat/2），勿混 A.1；N0/N1 按 A.2 n_legal_A2 生成；实现后做 pilot 预算测试；解释边界与 peer/non-blind 披露保持。
