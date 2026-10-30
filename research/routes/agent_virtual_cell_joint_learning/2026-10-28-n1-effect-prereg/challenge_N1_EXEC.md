# R203-N1 效果执行预注册独立挑战（task-141）：N1-EXEC

2026-10-28。角色：同一独立挑战者（非提案者、未参与 N1、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_N1_EXEC.md](PROBLEM_N1_EXEC.md)（SHA `9993F0BA…`）、[DESIGN_N1_EXEC.md](DESIGN_N1_EXEC.md)（`29F784E7…`）、[exec_plan.py](exec_plan.py)（`843DEC39…`）、[exec_plan.json](exec_plan.json)（`BECEE7F8…`）、[report_N1_EXEC.md](report_N1_EXEC.md)（`B4510841…`）、[record_N1_EXEC.md](record_N1_EXEC.md)（`4BD1B909…`）、N1 v0.4 链、C204 gates、R203-P1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_n1_exec_to_lead（仅批准 N1 效果执行：合成机制账、compute-only、0 wells；不批药理/真实决策/迁移/新颖性）。**

核验 PASS：
- **seeds 独立**：禁 `{20261030,20261061,20261062,20261063}`；执行 **20261070–20261119**（R=50；dataset seed=20261070+r）；方法 seeds **20262000+r*10+idx**（r0–49，idx0–6）；headroom **20261130–20261149**（20 reps）；与 gate seeds **overlap=[]**；两跑同 seeds 独立进程逐字节；执行时不得改 seed ✓。
- **方法/等预算**：M vs B1 full retrain/B2 static S-add/B3 EB/B4 GP/B5 random/B6 AL；T=6 fit4/hold2；每轮 1 feedback；同 query/特征/prior/初始数据/调参≤20/caps；B2 审计执行时最终 runner 再确认；只读导入冻结 generator（`AA5D454A…`）✓。
- **primary/多重性**：primary=`D_i=R_i(M)−R_i(B2)`、δ=.05；成功 ⇔ mean≤−δ ∧ 95%CI upper<0 ∧ **Holm p<.05**；family=6（M vs B1–B6，primary=B2）Holm α=.05；secondary 同 family；不换端点；headroom 预检（20 reps×300 units；headroom=U_max−U0(B2)；<δ→unreachable_gate；B2 近满→另立 budget-to-target，不静默换/降 δ）✓。
- **分析/单位**：n_units=300/R=50/deff2.2/n_eff136.36/SD .20→**MDE .04798268≤.05**/n_req278≤300；paired 15,000；cluster-robust SE 按 replicate G=50、t₄₉ 95% CI；每基线 mean/CI/Holm p；实际 MDE>δ→precision_insufficient（不算法失败、不事后加 n/降 δ）✓。
- **预算/schema/失败**：main 300×50×7；caps 1800s/2h/8GB/0 wells；C204 pilot .0455s/20.48s/.04GB 执行前复核；超→compute_budget_exceeded 不减；telemetry 分开、结果 JSON 无时间；schema top/per_method/summary；禁未预注册字段；失败类别完整（chain_mismatch/schema_mismatch/two_run_mismatch/leakage/compute_budget_exceeded/generator_misspecified/calibration_failed/nonidentifiable/unreachable_gate/precision_insufficient/no_increment/inconclusive）；失败只写类别不报方法差异 ✓。
- **执行前链核验**：v0.4 7 文件+C204 8 文件 SHA、V4 spec `A69B845D…`、V4 独立 gate 数值、G1/G2/G3/G7 全匹配；`pre_execution_chain.full_pass=true`、`mismatches={}` ✓。
- **边界/诚实**：机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不改旧判定；headroom 预检预注册、不会成为事后端点；`primary` 与 C204 的 n_eff/MDE 口径一致（MDE .04798 为单 replicate 保守下界，主分析 15,000 paired cluster-robust 只会更精确，报告两者）✓。

**结论：可提交 Lead 批准 N1 效果执行（仅合成机制账、compute-only、0 wells；不批药理/真实决策/迁移/新颖性）。**

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | seeds/样本独立 | **PASS** | exec 20261070–20261119；headroom 20261130–20261149；method 20262000+r*10+idx；forbidden gate seeds 20261030/61/62/63；overlap=[]；n_units=300；两跑同 seeds 独立进程；seed 不可改 ✓。 |
| ② | 方法/等预算/B2 | **PASS** | 7 方法；T6/feedback1/query6/同 prior/初始/特征/调参≤20/caps；B2 同信息同预算强基线；执行时最终 runner 再审计；只读 import generator AA5D454A ✓。 |
| ③ | primary/Holm/headroom | **PASS** | primary paired held-out regret δ=.05；成功三项 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family6 Holm α=.05；headroom 20×300 预检；<δ→unreachable_gate；B2 ceiling→budget-to-target；不换端点/降 δ ✓。 |
| ④ | 分析/单位/精度 | **PASS** | n_units300/R50/deff2.2/n_eff136.36/SD .20→MDE .04798≤.05；n_req278≤300；15,000 paired；cluster-robust SE G=50/t49；实际 MDE>δ→precision_insufficient；不事后加 n ✓。 |
| ⑤ | 预算/schema/失败 | **PASS** | main 300×50×7；caps 1800/7200/8GB/0 wells；C204 .0455/20.48/.04 执行前复核；telemetry 分离；schema 冻结；失败类别完整且只写类别 ✓。 |
| ⑥ | 执行前链 | **PASS** | v0.4 7 文件+C204 8 文件 SHA；V4 spec A69B845D；V4 独立 gate 503.04/64.42/[376.78,629.31]；G1 .0488/.05187；G2 1.000；G3 143/600/140/3；G7 .0455/20.48/.04；B2 audit；full_pass=true/mismatches={} ✓。 |
| ⑦ | 边界/统计诚实 | **PASS** | 机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不改旧判定；headroom 预检不做事后端点；MDE 口径一致且报告 cluster-robust 对照 ✓。 |
| ⑧ | 总判决 | **approve_n1_exec_to_lead** | 仅 N1 效果执行；不批外推。 |

## 2. 非阻塞实现备注（写入执行记录，不改变批准范围）

1. **C204 与 v0.4 pilot 数字不同**：C204 `.0455s/20.48s/.04GB`（G7 参考）vs v0.4 `.05622s/25.3s/.037GB`；两者都远低 caps，但执行前必须用**最终 effect runner** 跑 2-replicate pilot 复核并冻结 G7；G7 引用执行时实测，不混用两个 snapshot。
2. **headroom 预检**：20 reps×300 units 的 U0(B2)/headroom 要在执行前记录；若 headroom<δ→unreachable_gate；B2 近满分→另立 budget-to-target；不得把 headroom 预检结果当作事后效果端点或据此改 primary。
3. **cluster-robust/MDE 口径**：主分析用全部 15,000 paired units、cluster by replicate G=50、t₄₉ CI；保守 MDE .04798 是单 replicate n_units=300 的下界，报告两者；不得因 cluster-robust SE 与保守 MDE 不同而事后改分析单位或加 n。
4. **Holm/primary**：family=6（M vs B1–B6），primary=M vs B2；成功三项全部满足；Holm p 用同 family；secondary 方向不替代 primary；不得换端点/降 δ。
5. **两跑/schema**：run1/run2 同 seeds 独立进程，结果 JSON 无 telemetry、逐字节一致；schema 禁未预注册字段；失败只写类别不报方法差异；0 wells/compute-only；不晋升代码；N1 效果执行仍须 Lead 批准（本批）。

## 3. Lead N1 效果执行批准文本（建议）

> **批准范围**：批准 R203-N1 **效果执行**（合成机制账、compute-only、0 new wells）；不批准药理/真实决策/迁移/机制/新颖性；不批准代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：执行 seeds 20261070–20261119（R=50；dataset 20261070+r）、method seeds 20262000+r*10+idx、headroom 20261130–20261149（20 reps）；n_units=300；7 方法 M/B1–B6 等预算（T6/feedback1/query6/同 prior/初始/特征/调参≤20/caps）；B2 static S-add 同信息同预算强基线+执行时审计；只读 generator AA5D454A；primary paired held-out regret δ=.05；成功 mean≤−δ ∧ 95%CI upper<0 ∧ Holm p<.05（family6 Holm α=.05，primary M vs B2）；headroom 预检 20×300（<δ→unreachable_gate；B2 ceiling→budget-to-target）；分析 15,000 paired、cluster-robust SE G=50/t49、保守 MDE .04798/n_req278；caps 1800s/2h/8GB/0 wells；C204 pilot .0455/20.48/.04 执行前复核；两跑同 seeds 独立进程逐字节；schema/失败类别/telemetry 分离；执行前链 v0.4+C204 SHA/V4 spec/G1–G7 全部匹配。
>
> **禁止**：效果外推/药理/真实决策/迁移/机制/新颖性；A/B 资源；改旧门槛/判定；恢复停止实验；晋升代码；换 primary 端点/降 δ/事后加 n/改 cluster；用未预注册字段；Two-run mismatch 继续报结果；N1 结果不得升级为真实决策/药理证据。

## 4. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 N1-EXEC 预注册/exec_plan/v0.4/C204 链；只写本文件与 `tmp/`；未改 N1 产物。
- **总判决：approve_n1_exec_to_lead**。seeds 独立、方法/等预算与 B2 审计、primary/Holm/headroom、分析单位/cluster-robust/MDE、预算/schema/失败类别、执行前链核验均已写死且一致；仅批准 N1 合成机制账效果执行（compute-only、0 wells）；不批药理/真实决策/迁移/新颖性。

**一句话：N1-EXEC 预注册的 seeds（20261070–20261119；headroom 20261130–20261149；method 20262000 段；overlap=[]）、7 方法等预算+B2 审计、primary paired regret δ=.05 三项成功/Holm family6、15,000 paired cluster-robust G=50/t49、保守 MDE .04798/n_req278、caps/C204 pilot、两跑/schema/失败类别与 v0.4+C204 链核验（full_pass=true）均已一致——判 approve_n1_exec_to_lead（仅合成机制账、compute-only、0 wells；不批药理/真实决策/迁移/新颖性）。**
