# Lead 批准：R201-A P0/P1 最小实验（data-only、0 新 wells；开发性存在性）

2026-10-28。依据：A.1-C1（endpoint-auditor）判 **approve_p0p1_to_lead**；5 必改落实 PASS（例3/E3、P2 空集、P1 FPR/BH、H_A2 数值目标延后、P0/P1 细节）；附 3 条执行边界（行置换可交换性；pair 级仅描述；3.40×10⁸ F 需先预算预检）。

## 批准范围
- **仅 P0/P1**：P0=覆盖/过识别/噪声/泄漏等资格门；P1=联合矛盾存在性（`J≥δ_J=τ`）的**开发性存在性**检验。**P2/ΔW、S1 决策、S2/H_A2 不执行**（另立预注册+挑战+批准）。
- 冻结链：PROBLEM_A_v0_2 `61EC2FC9…B88AB18A`、DESIGN_A_v0_2 `486272B2…35459B3C`、qualify_A_v0_2.json `D6AE3506…B532B01E62`、report `75984409…`、record `75EC244F…`。
- 关键冻结量：y=mean(viability1–4)；半拆 {1,2}/{3,4} 标定 σ_obs、σ_pair²=σ_obs²/2；F_crit=2.60；|U|=340,088；N_perm=500（seed=20261029）；per-cell p + 30 细胞 BH q=0.05；P1 阳性三条件（BH 拒绝≥5 ∧ pooled F≥F_crit 比例≥置换零分布 Q95 ∧ G1–G5）；失败模板；**0 新 wells/plate/轮次**；wall≤900s、CPU≤2h、内存≤8GB；F 计算量 3.40×10⁸。
- **执行顺序**：P0 资格门（含 G5 六断言、两跑/schema、peek 打印）→ **预算预检**（3.40×10⁸ F；超限→`design_invalid: compute_budget_exceeded`，不得减 N_perm/换便宜分析）→ P1。
- **解释边界**：只写"本资源/本族/本设计下存在联合矛盾"的开发性存在性；阴性只写 `no_joint_contradiction`，**不写"矛盾不存在"**；pair 级计数仅描述性（H0 期望 ~1.7 万假阳，不得单独作证据）；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked（继承 ON3 披露）。
- 行置换零模型依赖 plan-cell 16 行可交换；若破坏可交换性→`design_invalid: null_calibration`，不得改阈值；技术半拆 FPR≤0.10、算子打乱检测≤0.10、族错设<5%→`design_invalid: family_misspecification`。
- 任何新测量/新 wells→停 P0/P1，另立协议。
