# R204-M3 Stage3 合成执行预注册独立挑战（task-182）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/训练/真实数据）。对象：[PROBLEM_M3_S3_EXEC.md](PROBLEM_M3_S3_EXEC.md)（SHA `C7B91087…`）、[DESIGN_M3_S3_EXEC.md](DESIGN_M3_S3_EXEC.md)（`C45925D0…`）、[exec_plan_m3_s3.py](exec_plan_m3_s3.py)（`FF1A3FB4…`）、[exec_plan_m3_s3.json](exec_plan_m3_s3.json)（`671F2617…`）、[schema_m3_s3_exec.json](schema_m3_s3_exec.json)（`B46D3249…`）、report/record/usage、M3 Stage1/Stage2/Lead 决定。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_to_lead；也不是 stop）。**

核验 PASS：
- **链/Stage1/Stage2**：35 文件 SHA、Stage1 failed_checks=[]/all_checks_pass/check19、Stage2 60 per-arm/failure null、no_effect=true ✓。
- **seeds/两跑**：env 20261601、reps 20261601–10、arms 20261611+10a+r、headroom 20261681–90；禁用集/overlap=[]/unique；两跑同 seeds 独立进程/逐字节/telemetry 分开 ✓。
- **Stage3 样本**：R=10；每 replicate 300 共享反馈 (h,a,Y)+300 评价 units；总评价 3,000/反馈 3,000；7 arms 同 feedback/eval；调参≤20/caps/合法包 ✓。
- **主端点/分析**：primary=candidate vs combined standard；δ=.05；成功 mean ΔR≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；family=6；n_units300/deff2.2/n_eff136.36/MDE .04798268≤.05/n_req278；cluster；headroom；6,282/1,573 仅 Fisher-z；次端点 secondary ✓。
- **闭环/G/失败**：每 arm 300 feedback/300 eval/replicate、调参≤20、caps 1800s/2h/8GB/0 wells；7 arms 同预算；G1–G6；13 失败类别；schema/pilot/两跑；骨架单测 PASS ✓。
- **边界**：支撑研究/机制账；只更新功能均值≠细胞动力学；无序贯→不称序贯 DR；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open ✓。

**但冻结设计有一个直接矛盾：**
- DESIGN §1.2/§2 同时写 **“固定反馈：所有 arms 看相同反馈/评价；每 arm 不选择分配（shared-score 固定）；不比较分配”**，又写 **`A_standard_DR_TMLE_optimal_allocation` = 标准 DR/TMLE learner+**最优分配** pipeline**，并把它作为 **primary combined standard**。
- **“最优分配”必然改变 queried feedback/分配**；若它真的使用最优分配，则 7 arms 的反馈流不再相同，**Stage3 变成 learner×allocation 复合比较**，不能声称“固定反馈、不比较分配”。若它不使用最优分配（只固定 shared-score），则 baseline 名不副实，**combined standard 的“optimal allocation”没有实际含义**。
- 这是 Stage3 主比较的核心；当前无法判定 candidate vs combined standard 到底比较的是 learner 还是 allocation。

**结论：先修 §2 的 1–2，再提交 Lead 批准 M3 Stage3 合成学习比较执行（支撑研究/机制账、compute-only、0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 链/Stage1/Stage2 | **PASS** | 35 文件 SHA、Stage1 failed_checks=[]/all_checks_pass/check19、Stage2 60 per-arm/failure null、no_effect=true ✓。 |
| ② | seeds/两跑 | **PASS** | env 20261601/reps 20261601–10/arms 20261611+10a+r/headroom 20261681–90；禁用集/overlap=[]/unique；两跑同 seeds 独立进程/逐字节/telemetry ✓。 |
| ③ | 样本/固定反馈 | **FAIL（与 combined standard 矛盾）** | R=10/300 feedback+300 eval/replicate/总3,000/3,000/7 arms ✓；**但 `A_standard_DR_TMLE_optimal_allocation` 含“最优分配”与“固定反馈/不比较分配”冲突**（§0）。 |
| ④ | 主端点/分析 | **PASS** | candidate vs combined standard；δ=.05；mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family6；MDE .04798/n_req278；cluster/headroom；6,282 仅 Fisher-z；次端点 secondary ✓。 |
| ⑤ | 闭环/G/失败 | **PASS** | 300 feedback/300 eval/replicate、调参≤20、caps 1800s/2h/8GB/0 wells；7 arms 同预算；闭环账；G1–G6；13 失败类别；schema/pilot/两跑；单测 PASS ✓。 |
| ⑥ | 停止/边界 | **PASS** | 标准 DR/TMLE/最优设计等预算复制/超过→no_increment/撤；π=b/共线/分离/支持/截断/评价复用/两跑/链/预算类别；不改旧判定；不放宽/改阈值/换端点；支撑研究/机制账；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；M3 不与 M1/M2 混同；N1 不作证据；data readiness open ✓。 |
| ⑦ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **解决“固定反馈/不比较分配”与“combined standard 含最优分配”的矛盾**：
   - **方案 A（推荐，保持 fixed feedback）**：所有 7 arms 使用**完全相同**的 shared-score/固定反馈与评价样本；把 `A_standard_DR_TMLE_optimal_allocation` 改为 **`A_standard_DR_TMLE`（固定 shared-score 下的标准 DR/TMLE learner）**，删去“optimal allocation”或明确其 allocation 固定为 shared-score；这样 primary 是 learner 比较，不混 allocation。
   - **方案 B（保留 optimal allocation）**：则 stage3 不是 fixed feedback；必须允许各 arm 使用不同 feedback/allocation，明确这是 **learner+allocation 复合比较**，并新增 allocation 控制/单独 Stage2 设计；同时 primary 不能声称“不比较分配”。**不能 A/B 同时写。**
2. **明确 primary/secondary/Holm 映射**：7 arms 中 candidate 与 combined standard 为 primary；full-history/IW/DR/TMLE/value-aware 为 5 secondary；family=6；若方案 B 改变比较集，重算 family/Holm/成功判据。
3. **冻结 fixed feedback 的“同一 queried actions/feedback”实现**：每条 (h,a,Y) 的生成 seed/分配 policy 固定；所有 arms 复用同一 300 条反馈/300 评价 unit；评价独立；target 不作标签；不得让任何 arm 通过“最优分配”改变 feedback 流；若无法保证，改方案 B。
4. **保持** 35 链/Stage1/Stage2、独立 seeds/两跑、R=10/300/300/3,000、MDE .04798/n_req278/headroom/cluster/6,282、G1–G6/13 失败/caps/schema/pilot 实测冻结/闭环成本/停止/边界；不执行真实数据/效果。
5. **禁止**：把 learner 比较写成 allocation 比较或反之；把 optimal allocation 的 feedback 优势算进 primary；改旧判定/阈值；放宽容差/换端点；晋升代码；真实数据/湿实验；称药理/真实决策/迁移/机制/新颖性。

## 3. 修完后建议的 Lead M3 Stage3 合成学习比较执行批准文本（支撑研究/机制账、compute-only、0 wells）

> **批准范围**：在必改 1–2 完成并复核后，批准 **M3 Stage3 合成学习比较执行**（支撑研究/机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：35 文件链/Stage1/C209/Stage2/C213；seeds（env 20261601、reps 20261601–10、arms 20261611+10a+r、headroom 20261681–90；禁用集/overlap=[]/unique；两跑同 seeds 独立进程/逐字节/telemetry 分离）；R=10、每 replicate 300 共享反馈+300 评价、总3,000/3,000、7 arms 同 feedback/eval、**fixed shared-score；combined standard 必须固定 allocation（方案A）或明确复合比较（方案B）**；调参≤20/caps/合法包；primary candidate vs combined standard、δ=.05、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、family6；MDE .04798268/n_req278/cluster/headroom/6,282 仅 Fisher-z；G1–G6/13 失败/caps 1800s/2h/8GB/0 wells；schema 先写；final-implementation Stage3 pilot（2 reps×7 arms×300 units）实测冻结 canonical；JSON 无 telemetry；闭环成本同账；停止/边界；不执行真实数据/效果。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把 learner 比较写成 allocation 比较或反之；把 optimal allocation feedback 优势算进 primary；改旧判定/阈值/端点；放宽容差；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不运行效果/训练/真实数据**：只读 M3 Stage3 exec prereg/JSON/schema/Stage1/Stage2 链；只写本文件与 `tmp/`；未改 exec prereg 产物。
- **总判决：revise**。35 链/Stage1/Stage2、seeds/两跑、R=10/300/300/3,000、7 arms、primary/Holm/MDE/6,282、G1–G6/13/caps/schema/pilot/闭环/边界基本正确；但 **“固定反馈/不比较分配”与 `A_standard_DR_TMLE_optimal_allocation` 的“最优分配”直接矛盾**，无法判定 Stage3 比较 learner 还是 allocation。修完 1–2 后可提交 Lead 批准 M3 Stage3 合成学习比较执行（支撑研究/机制账、compute-only、0 wells）。

**一句话：M3 Stage3 exec 的 35 链/Stage1/Stage2、seeds、R=10/300 feedback+300 eval/3,000、7 arms、primary/Holm/MDE/6,282、G1–G6/13/caps/schema/pilot/闭环/边界都核验通过；但 `A_standard_DR_TMLE_optimal_allocation` 的“最优分配”与“固定反馈、不比较分配”矛盾——判 revise：要么改为固定 allocation 的 standard DR/TMLE（方案A），要么明确 learner+allocation 复合比较并重算 family/Holm（方案B），再提交 Lead 批准 M3 Stage3 合成学习比较执行。**
