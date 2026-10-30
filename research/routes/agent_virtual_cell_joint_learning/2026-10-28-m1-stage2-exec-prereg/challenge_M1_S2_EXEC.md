# R204-M1 Stage2 合成执行预注册独立挑战（task-169）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M1、不运行效果/训练/真实数据）。对象：[PROBLEM_M1_S2_EXEC.md](PROBLEM_M1_S2_EXEC.md)（SHA `F7ED4520…`）、[DESIGN_M1_S2_EXEC.md](DESIGN_M1_S2_EXEC.md)（`503618F4…`）、[exec_plan_m1_s2.py](exec_plan_m1_s2.py)（`CFF1C734…`）、[exec_plan_m1_s2.json](exec_plan_m1_s2.json)（`3DC88FEF…`）、[schema_m1_s2_exec.json](schema_m1_s2_exec.json)（`181A77E3…`）、report/record/usage、M1 Stage2 v0.2/Stage1 C208/Lead 接受决定。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_exec_to_lead（仅批准 M1 Stage2 合成诊断执行：机制账、compute-only、0 wells；不批 Stage3/真实数据/效果/药理/真实决策/迁移/新颖性）。**

核验 PASS：
- **链/Stage1**：12 文件 SHA 匹配（`chain_pass=true/mismatches={}`；M1 Stage2 v0.2 八件 + Lead 接受 `6EC860D2…` + Stage1 json `EF701C66…`/report `E3701DA8…`/决定 `EEA8CE76…`）；Stage1 `failed_gates=[]`、`no_effect_results=true`、B2 `rename_maxent`、一步投影撤 ✓。
- **seeds/两跑**：param/train/eval **20261301/02/03**；H1 16 cells **20261310–25**（d,N 固定顺序）；H2 ε **20261326–30**；H3 **20261331–32**；two-run reps **20261340–49**；禁用 C208/Stage1 20261112–13、M1 v0.2 20261201–03、M2 Stage2 20261200–39、M2 Stage3 20262100–39、M3 20261500–99；`overlap=[]/unique=true`；两跑同 seeds 独立进程、结果 JSON 逐字节、telemetry 单独；不得改 seed ✓。
- **执行范围**：唯一 Pθ（X64/A4/Y4 box[-2,2]^4；3 分量截断 GMM/对角协方差/条件异方差/无 Student-t；param/train/eval 20261301/02/03；train4096/eval2048）；reward r=w^Ty−λ||y||²、**r_max .375/r_min −5.2**；target Q GL64/dim、target 样本不作标签、Doob 不可执行；C-MDN（K=3 logits+mean4+diag log-scale4、hidden128/2 ReLU、NLL/Adam lr1e-3/wd1e-5/batch256/epochs200、采样4096/action、不称一步投影）；H1 d/N×256-bin TV×容差表（N 顺序写死；d8 [.12,.10,.08,.07]/d16 [.14,.11,.09,.08]/d32 [.16,.13,.11,.10]/d64 [.18,.15,.13,.12]；超→projection）；H2 Sinkhorn ε{.1,.25,.5,1,2}/maxiter2000/marginal1e-8/至少一 ε 收敛；H3 small-case d2/A2/Y2 oracle GL128/dim TV≤.05（256 eval x；非高维 oracle）；**不输出 decision utility/regret/top-k/方法比较** ✓。
- **G1–G6/B1–B5/失败**：G1 calibration/G2 support/G3 projection/G4 leakage/G5 two_run_mismatch/G6 compute_budget_exceeded；B1–B5 仅规格不执行比较；12 失败类别完整 ✓。
- **预算/schema**：caps 1800s/2h/8GB/0 wells；执行前最终实现重跑 pilot 并冻结 canonical timing（planning `.00115028 s/rep、.011503 s、mem .00668467 GB` 非执行实测）；schema 先写（H1/H2/H3/G1–G6/失败/forbidden）；结果 JSON 无 telemetry；失败只写类别；骨架单测全 PASS（形状/权重和/截断/边界/seed/Sinkhorn 23 iter/H1 容差表/H2 网格/H3 小例；无训练/无比较/无效果）✓。
- **停止/撤主张**：B2 等价/一步投影已撤不得写 M1 增量；H1 超容差/H2 不收敛/H3 TV>.05→projection；target 改 Pθ→calibration；不放宽容差/改阈值/换端点 ✓。
- **边界**：机制账 only；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M1 不与 M2/M3 混同；N1 不作 M1 Stage2 证据；data readiness open（C203/C205/C210）；Stage2 执行另立预注册+挑战+Lead；Stage3 另立 ✓。

**三个非阻塞执行备注**（不影响批准）：
1. **内存/训练 pilot**：`memory_planning_estimate_gb=.00668467` 只覆盖 planning 实例；`Q_g` GL64/dim（64^4≈1.68e7）与 H3 GL128/dim 实际占用更高（仍应<8GB），且 H1 要训练 16 个 C-MDN（N≤4096、d≤64、200 epochs）——执行前必须用最终实现实测 **训练+规划** 的 wall/CPU/内存；G6 不能只用 planning/单测数字。
2. **H3 仅 small-case**：TV≤.05 是 d2/A2/Y2 oracle 的规划诊断，不是高维 exact oracle；高维由 H1 判；报告不得把 H3 通过写成“高维近似准确”。
3. **H1 容差表 N 顺序**：JSON 已写 `tolerance_order=N=[512,1024,2048,4096]`，执行/报告必须保持这一顺序；不得按反序/转置。
4. **pilot 参考非实测**：planning .00115028 s/rep/.011503 s/.00668467 GB 只是 planning/单测；执行前 canonical telemetry 必须重跑最终实现并冻结，文档/JSON 引用同一 snapshot。

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 链/Stage1 | **PASS** | 12 文件 SHA 匹配；mismatches={}；Stage1 failed_gates=[]、no_effect=true、B2 rename_maxent、一步投影撤 ✓。 |
| ② | seeds/两跑 | **PASS** | param/train/eval 20261301/02/03；H1 20261310–25；H2 20261326–30；H3 20261331–32；two-run 20261340–49；禁用区间/overlap=[]/unique；两跑同 seeds 独立进程/telemetry ✓。 |
| ③ | 执行范围/诊断 | **PASS** | 唯一截断 GMM Pθ；r∈[−5.2,.375]；Q GL64/dim；C-MDN；H1 d/N+容差表 N 顺序；H2 ε/maxiter/tol；H3 small-case GL128/TV≤.05；不输出 effect ✓。 |
| ④ | G1–G6/B1–B5/失败 | **PASS** | G1–G6 规则/失败映射；B1–B5 仅规格；12 失败类别完整 ✓。 |
| ⑤ | 预算/schema | **PASS（非阻塞1）** | caps；schema 先写；pilot planning 参考；单测 PASS；结果 JSON 无 telemetry；但 planning 内存/训练未实测（§0-1）✓。 |
| ⑥ | 停止/撤主张 | **PASS** | 一步投影/B2 撤；H1/H2/H3 失败投影；target 改 Pθ calibration；不放宽/改阈值/换端点 ✓。 |
| ⑦ | 边界 | **PASS** | 机制账；Stage2/3 不执行；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M1 不与 M2/M3 混同；N1 不作证据；data readiness open ✓。 |
| ⑧ | 总判决 | **approve_exec_to_lead** | 仅 Stage2 合成诊断；不批 Stage3/真实数据/效果。 |

## 2. Lead M1 Stage2 合成诊断执行批准文本（建议）

> **批准范围**：批准 R204-M1 **Stage2 合成诊断执行**（仅机制账、compute-only、0 new wells）；不批 Stage3/真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：12 文件链（M1 Stage2 v0.2 八件+Lead 接受+Stage1 json/report/decision）；Stage1 failed_gates=[]/no_effect=true/B2 rename_maxent/一步投影撤；执行 seeds 20261301+（Pθ param/train/eval 20261301/02/03；H1 20261310–25 d/N 顺序；H2 20261326–30；H3 20261331–32；two-run 20261340–49；禁用 C208/Stage1/M1 v0.2/M2/M3 区间；overlap=[]/unique）；唯一 Pθ（X64/A4/Y4 box[-2,2]^4；3 分量截断 GMM/对角协方差/条件异方差/无 Student-t；train4096/eval2048）；r=w^Ty−λ||y||²∈[−5.2,.375]；target Q GL64/dim target 样本不作标签/Doob 不可执行；C-MDN 规格；G1/G2/G4/G5/G6；G3/H1/H2/H3（H1 容差表 N 顺序、H2 ε/marginal≤1e-8、H3 small-case TV≤.05，仅诊断）；B1–B5 仅规格；失败类别 12 项；caps 1800s/2h/8GB/0 wells；schema 先写；两跑/schema/无 telemetry；执行前最终实现 pilot 实测并冻结 canonical timing。
>
> **禁止**：Stage3/真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把一步投影/B2 等价写成 M1 增量；把 H1–H3 合成诊断当效果；H3 small-case 当高维 oracle；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验。

## 3. 声明

- **本轮不运行效果/训练/真实数据**：只读 M1 Stage2 exec prereg/JSON/schema/Stage1 链；只写本文件与 `tmp/`；未改 exec prereg 产物。
- **总判决：approve_exec_to_lead**。12 文件链/Stage1 状态、独立 seeds/两跑、唯一 Pθ/reward 有界、C-MDN/H1–H3、G1–G6/B1–B5/失败、caps/schema/停止/边界均核验通过；仅 planning 内存/训练未实测、H3 small-case、H1 N 顺序、pilot 非实测四个非阻塞执行备注。仅批准 Stage2 合成诊断执行（机制账/compute-only/0 wells）；不批 Stage3/真实数据/效果/药理/真实决策/迁移/新颖性。

**一句话：M1 Stage2 exec 预注册的 12 文件链、Stage1 撤一步投影/B2 rename、独立 seeds（20261301+，overlap=[]）、唯一截断 GMM Pθ、reward r∈[−5.2,.375]、C-MDN/H1 容差表 N 顺序/H2 Sinkhorn/H3 small-case、G1–G6/B1–B5/12 失败类别、caps/schema/两跑/停止/边界均已核验——判 approve_exec_to_lead（仅 M1 Stage2 合成诊断执行：机制账/compute-only/0 wells；不批 Stage3/真实数据/效果/药理/真实决策/迁移/新颖性）。**
