# R204-M3 Stage2.1 轻量复核（task-177）：v0.2 合成分配诊断执行

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/训练/真实数据）。对象：[PROBLEM_M3_S2_EXEC_v0_2.md](PROBLEM_M3_S2_EXEC_v0_2.md)（SHA `FE9180FA…`）、[DESIGN_M3_S2_EXEC_v0_2.md](DESIGN_M3_S2_EXEC_v0_2.md)（`2569079C…`）、[exec_plan_m3_s2_v0_2.py](exec_plan_m3_s2_v0_2.py)（`C85C1AEA…`）、[exec_plan_m3_s2_v0_2.json](exec_plan_m3_s2_v0_2.json)（`F16D1C04…`）、[schema_m3_s2_exec_v0_2.json](schema_m3_s2_exec_v0_2.json)（`987089F8…`）、report/record/usage v0.2、M3 v0.2/Stage1 C209/Lead 决定。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_exec_v0_2_to_lead（仅批准 M3 Stage2 合成分配诊断执行：支撑研究/机制账、compute-only、0 wells；不批 Stage3/真实数据/效果/药理/真实决策/迁移/新颖性）。**

v0.2 已修掉 v0.1 的两个阻断：
- **13 失败类别**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/**chain_mismatch**/unreachable_gate/precision_insufficient/no_increment/inconclusive；schema/失败模板/stop 同步；单测 count=13、chain_mismatch_present=true ✓。
- **per-arm 13 字段/判据**：`arm_id/replicate_id/allocation_weights/realized_allocation_frequency/H_summary/delta_summary/allocation_Q/variance_term/clipping/equal_budget_audit/two_run_sha/pass/failure_category`；每 arm 通过判据（simplex/support、H/δ 有限、Q 报告、等预算审计、two-run SHA、无禁输出）与失败映射写死；**无 decision utility/regret/top-k/学习效果比较**；DR/TMLE+最优分配等价判定留 Stage3 ✓。
- **sample 语义/预算**：R=10；data seed 20261401；replicate seeds 20261401–10；每 replicate initial/behavior 300 + 每 arm 300×6 → **2,100 units/replicate、总21,000、allocation/feedback 18,000**；arm a,r seed=20261411+10a+r（20261411–20261470）；每 arm n_alloc=300/feedback=300/tuning≤20/caps/合法包（H=3/A=3/Y binary）；执行前必须最终实现 pilot（2 reps×6 arms×300 alloc）实测冻结 canonical；Stage1 pilot 仅历史参考 ✓。
- **保留项**：17 文件链/Stage1（chain_pass=true、19 checks PASS）；独立 seeds/两跑 overlap=[]/unique；H=3/A=3/Y binary、p/μ/b/π/m/C_H=20；六 arms（含 decision_AL/optimal_experimental_design）；G1–G6；caps 1800s/2h/8GB/0 wells；schema 先写；无 telemetry；骨架算术（DR gap0/1.1e-16、clip bias −.026407185629、rank1、π=b H−1 0、ratios 1.21722846/1.16686763）✓。
- **边界**：支撑研究/机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作 M3 证据；data readiness open（C203/C205/C210）；不把分配诊断写成学习效果比较；标准 DR/TMLE+最优分配等预算复制/超过判定留 Stage3 ✓。

**非阻塞执行备注**：
1. **DR gap 表述**：task/旧报告写 1.1e-16，v0.2 单测 `dr_identity_gap_max=0.0`；两者等价（≤1e-12），报告统一写“0.0/≤1e-12”，不要同时出现两个精度值造成误读。
2. **pilot**：Stage1 pilot `.00016347/.001635/.007137` 仅历史参考；执行前 final-implementation pilot（2 reps×6 arms×300 alloc）必须实测并冻结 canonical；G6 不能引用 Stage1 数字。
3. **per-arm 输出**：`allocation_Q`/`variance_term`/`clipping`/`equal_budget_audit` 是诊断字段；报告不得把它们解释为 decision utility/regret/学习效果；DR/TMLE+最优分配等价判定留 Stage3。
4. **sample 语义**：initial/behavior 300 + 6×300/arm=2,100/replicate；R=10→21,000；allocation/feedback 18,000；arm seed 20261411+10a+r；确认执行器每 arm 独立 300 alloc/feedback，不共用评价。

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 13 失败类别 | **PASS** | 13 项含 chain_mismatch；schema/模板/stop 同步；单测 count=13/chain_mismatch_present=true ✓。 |
| ② | per-arm 字段/判据 | **PASS** | 13 字段；per-arm pass criteria + failure map；无 decision utility/regret/top-k/学习效果；等价判定留 Stage3 ✓。 |
| ③ | sample 语义/预算 | **PASS** | R=10/data 20261401/replicate 20261401–10；2,100/replicate→21,000 total/18,000 allocation；arm seed 20261411+10a+r；n_alloc=300/feedback=300/tuning≤20/caps/合法包；final pilot 要求冻结 ✓。 |
| ④ | 保留项 | **PASS** | 17 文件链/Stage1、独立 seeds/两跑、H3/A3/Y binary、p/μ/b/π/m/C_H20、六 arms、G1–G6、caps、schema、无 telemetry、骨架算术、规则/边界 ✓。 |
| ⑤ | 边界 | **PASS** | 支撑研究/机制账；Stage3/真实数据不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；分配诊断≠效果 ✓。 |
| ⑥ | 总判决 | **approve_exec_v0_2_to_lead** | 仅 Stage2 合成分配诊断；不批 Stage3/真实数据/效果。 |

## 2. Lead M3 Stage2 合成分配诊断执行批准文本（建议）

> **批准范围**：批准 R204-M3 **Stage2 合成分配诊断执行**（支撑研究/机制账、compute-only、0 wells）；不批 Stage3/真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：17 文件链/Stage1（chain_pass=true、19 checks PASS）；seeds（data 20261401、replicate 20261401–10、arm 20261411+10a+r、两跑同 seeds 独立进程/逐字节/telemetry 分离；禁用集交集[]/unique）；Stage2 环境 H=3/A=3/Y∈{0,1}、p/μ/b/π/m/C_H=20、六 arms（含 decision_AL/optimal_experimental_design）、同 learner/updater/预算；R=10、每 replicate initial/behavior 300+6×300、total 21,000/allocation 18,000、每 arm n_alloc=300/feedback=300/tuning≤20/caps/合法包；G1–G6；per-arm 13 字段/判据/失败映射；13 失败类别（含 chain_mismatch）；caps 1800s/2h/8GB/0 wells；schema 先写；final-implementation pilot（2 reps×6 arms×300 alloc）实测冻结 canonical；JSON 无 telemetry；π=b/截断/共线/分离/支持规则；不输出 decision utility/regret/top-k/学习效果比较。
>
> **禁止**：Stage3/真实数据/湿实验/效果/真实决策/迁移/机制/新颖性；把分配诊断写成学习效果比较；把 DR/TMLE+最优分配等预算复制/超过写成本轮结论（留 Stage3）；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验；引用 Stage1 pilot 作为执行 pilot。

## 3. 声明

- **本轮不运行效果/训练/真实数据**：只读 M3 Stage2 v0.2 exec prereg/JSON/schema/Stage1 链；只写本文件与 `tmp/`；未改 exec prereg 产物。
- **总判决：approve_exec_v0_2_to_lead**。13 类失败/chain_mismatch、per-arm 13 字段/判据、R=10 sample 语义（2,100/replicate、21,000 total、18,000 allocation）、17 文件链/Stage1、独立 seeds/两跑、六 arms、G1–G6、caps/schema/停止/边界均核验通过；仅 DR gap 表述、final pilot、per-arm 字段解释、sample 执行细节为非阻塞备注。仅批准 Stage2 合成分配诊断执行（支撑研究/机制账、compute-only/0 wells）；不批 Stage3/真实数据/效果/药理/真实决策/迁移/新颖性。

**一句话：v0.2 已补 13 失败类别（含 chain_mismatch）、per-arm 13 字段/判据/失败映射、R=10 sample 语义（2,100/replicate、21,000 total、18,000 allocation、arm seed 20261411+10a+r）并保留六 arms/G1–G6/caps/边界——判 approve_exec_v0_2_to_lead（仅 M3 Stage2 合成分配诊断执行：支撑研究/机制账、compute-only/0 wells；不批 Stage3/真实数据/效果/药理/真实决策/迁移/新颖性）。**
