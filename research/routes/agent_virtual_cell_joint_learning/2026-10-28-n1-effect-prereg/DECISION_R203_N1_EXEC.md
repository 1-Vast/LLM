# Lead 批准：R203-N1 效果执行（仅合成机制账；compute-only；0 wells）

2026-10-28。依据：R203-N1-EXEC-C1（i003）判 **approve_n1_exec_to_lead**；seeds 独立、等预算/B2 审计、primary/Holm/headroom、cluster-robust/MDE、预算/schema/失败类别、链核验、边界与诚实性均 PASS。

## 批准范围
- **N1 效果执行一次**：合成机制账、compute-only、**0 wells**；严格按冻结执行预注册：PROBLEM_N1_EXEC `9993F0BA…`、DESIGN_N1_EXEC `29F784E7…`、exec_plan.py `843DEC39…`、exec_plan.json `BECEE7F8…`、report `B4510841…`、record `4BD1B909…`。
- 冻结执行 seeds：dataset **20261070–20261119**（R=50；dataset seed=20261070+r）、method seeds **20262000+r*10+idx**、headroom **20261130–20261149**（20 reps）、n_units=300；禁用 gate seeds {20261030,20261061,20261062,20261063}；执行时不得改 seed。
- 方法：M（N1）vs B1 full retrain、B2 static S-add（关键强基线）、B3 hierarchical/EB、B4 GP、B5 random plan-pair、B6 decision AL；T=6（fit4/hold2）、每轮 1 feedback、query 同、特征/prior/初始数据同、调参≤20、compute caps 同；只读导入冻结 generator `AA5D454A…`；B2 等价审计执行时最终 runner 再确认。
- **Primary**=paired held-out decision regret `D_i=R_i(M)−R_i(B2)`，δ=.05；成功 ⇔ mean ΔR≤−δ ∧ 95% CI upper<0 ∧ **Holm p<.05**；family=6（M vs B1–B6，primary=M vs B2）Holm α=.05；secondary 同 family；**不得换 primary/降 δ**。
- **headroom 预检**：20 reps×300 units，headroom=U_max−U0(B2)；<δ→`unreachable_gate`；B2 近满分→另立 budget-to-target；预检结果不得当效果端点或据此改 primary。
- 分析：paired 15,000 决策单元；cluster-robust SE 按 replicate（G=50）、t₄₉ 95% CI；报告每基线 mean/CI/Holm p；保守 MDE .04798268≤.05（n_units=300 单 replicate 下界）、n_req278≤300；实际 MDE>δ→`precision_insufficient`（不算法失败、不事后加 n/降 δ/改 cluster）。
- 预算/输出：main 300×50×7；caps **1800s/2h/8GB/0 wells**；执行前最终 runner 跑 2-rep pilot 复核并冻结 G7（C204 .0455s/20.48s/.04GB 与 v0.4 .05622s/25.3s/.037GB 不得混用）；两跑同 seeds 独立进程、结果 JSON 无 telemetry、逐字节一致（否则 `two_run_mismatch`）；schema top/per_method/summary，禁未预注册字段；失败只写类别、不报方法差异。
- 执行前链核验：v0.4 7 文件+C204 8 文件 SHA、V4 spec `A69B845D…`、V4 独立 gate seed20261062、G1/G2/G3/G7；任何不匹配→stop `design_invalid: chain_mismatch`。

## 不批准
- 药理/真实决策/迁移/机制/新颖性外推；代码晋升；改旧判定/门槛；恢复已停止实验；用 A/B 线资源；换 primary/降 δ/事后加 n/改 cluster；未预注册字段；two-run mismatch 后继续报结果。
