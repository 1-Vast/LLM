# R204-M3 S3b 修正合同 learner 比较预注册独立挑战（task-207）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 S3b、不训练/不拟合候选/不读真实数据）。对象：[PROBLEM_M3_S3B.md](PROBLEM_M3_S3B.md)（SHA `869690F9…`）、[DESIGN_M3_S3B.md](DESIGN_M3_S3B.md)（`79E1E109…`）、[headroom_design_m3_s3b.py](headroom_design_m3_s3b.py)（`68EF6698…`）、[headroom_design_m3_s3b.json](headroom_design_m3_s3b.json)（`77F113FF…`）、[schema_m3_s3b.json](schema_m3_s3b.json)（`29747B9C…`）、report/record/usage、C209/C213/C218/C220 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_to_lead；也不是 stop）。**

核验 PASS：
- **分离/纠正**：C218 Stage3 `no_increment` 冻结保留；C220 “合格 M3/TMLE 比较”解释不成立；S3b 新预注册、不是重跑旧 Stage3；旧判定/阈值/输出不变；C208 一步投影仍撤 ✓。
- **高 regret/headroom**：H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b Stage2；m_wrong=.5；C_H=20；b_min=1e-6；π2' 对角 .82/非对角 .09；Q/w/H=π2/w；**H_max=18.91777778<C_H=20，无 clipping**；设计期 headroom（R=20 seeds 20262201–20）P_empirical_mean **.14841667 CI [.10382916,.19300417]**、P_standard_DR_TMLE 同；均≥2δ=.10→executable、未重设；<.10 规则 ✓。
- **DR 恒等**：m=μ、H=π2/w 时 correction expectation=0；**gap 0.0<1e-10**；用实际 w 不用旧 b；无 clipping ✓。
- **learner 合同**：candidate 真实 logit-fluctuation ε：per-cell weighted Bernoulli NLL（offset logit(m_hat)、weights H=π2/w）、L-BFGS、score 残差<1e-6、收敛；m_ε=σ(logit m_hat+ε)；standard=same m analytic DR/TMLE no ε；禁止 0.5+0.5*score/sigmoid(2*score)/无 NLL 变换/缩放/λ/类名 ✓。
- **六比较/统计/等价**：family=6：primary candidate vs P_standard_DR_TMLE；secondary P_empirical_mean/P_importance_weighting/P_full_history_retrain/P_DR_targeting/P_value_aware；D<0、δ=.05、Holm family6、单侧下尾；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；raw/paired 分开；CI R=20/cluster t(df=19)；不用 planning MDE；等价审计（策略/单调/正仿射/解析覆盖→equivalence/合并/no_increment；候选≡standard→no_increment）✓。
- **执行/seeds/caps/schema/失败/停止**：env 20262200；headroom 20262201–20；feedback 20262221–40；eval 20262241–60；arms 20262261+20a+r（a=0..6,r=0..19）；forbidden overlap=[]/unique；两跑/telemetry；caps 1800s/2h/8GB/0 wells；final pilot；schema；13 失败；停止 ✓。
- **边界**：机制账 only；不执行真实数据/湿实验；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；public-only ✓。

**但 seed 计数与 block 不一致：**
- `execution_seeds.all_exec_seeds_count = 181`；按冻结 blocks：env 1 + headroom 20 + feedback 20 + eval 20 + **arm_seeds 140（7 arms×20）** = **201**。
- `arm_seeds` 实际是 20262261–20262400（140 个）；`arm_seed_rule a=0..6,r=0..19` 也是 7 arms×20。**181 对应“6 arms”口径**，与 7 arms/140 arm seeds 矛盾。
- 这是预注册 seed 账的实质不一致；执行前必须修正为 **201**（或按 blocks 程序化计算），schema/report/record 同步。

**结论：先修 §2 的 1–2，再提交 Lead 批准 M3-S3b 执行（机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 分离/纠正 | **PASS** | C218 Stage3 no_increment 冻结；C220 解释无效；S3b 新预注册；旧判定/阈值/输出不变；C208 撤 ✓。 |
| ② | 高 regret/headroom | **PASS** | H3/A3/Y binary；π2' .82/.09；H=π2/w；H_max 18.91778<C_H20 无 clipping；headroom P_empirical_mean **.14841667 CI [.10382916,.19300417]**、P_standard same；均≥.10；未重设；<.10 规则 ✓。 |
| ③ | DR 恒等 | **PASS** | m=μ、H=π2/w；correction expectation 0；gap 0.0<1e-10；实际 w；无 clipping ✓。 |
| ④ | learner 合同 | **PASS** | 真实 ε：weighted Bernoulli NLL/offset/L-BFGS/score<1e-6；m_ε；standard same m no ε；禁 0.5+0.5*score/sigmoid/无 NLL/缩放/λ/类名 ✓。 |
| ⑤ | 六比较/统计/等价 | **PASS** | primary candidate vs P_standard；5 secondary；D<0、δ=.05、Holm6、单侧、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；raw/paired；CI R20/cluster；等价审计 ✓。 |
| ⑥ | 执行/seeds/caps/schema/失败/停止 | **FAIL/PARTIAL** | env/headroom/feedback/eval/arms blocks；两跑/caps/schema/13 失败/停止 ✓。**`all_exec_seeds_count=181` 与 7 arms×20+61=201 矛盾**（§0）。 |
| ⑦ | 边界 | **PASS** | 机制账 only；不执行真实数据/湿实验；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；public-only ✓。 |
| ⑧ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **修正 `all_exec_seeds_count`**：按 blocks 计算 env 1 + headroom 20 + feedback 20 + eval 20 + arm 140 = **201**（7 arms×20）；不是 181。若实际只有 6 arms，则须删除一个 secondary/arm 并同步 comparison_family/Holm；**不能同时保留 7 arms/140 seeds 和 181 count**。
2. **在 schema/JSON 明确 `n_arms=7`、`n_arm_seeds=140`、`n_exec_seeds=201`**；`all_exec_seeds_count` 由 blocks 程序化生成；schema/report/record 同步；`unique=true/overlap=[]` 保持。
3. **保持**：分离/纠正、高 regret/headroom、H_max18.9178<C_H20/无 clipping、DR gap0<1e-10、learner 合同、六比较/Holm6/δ=.05/raw-paired/CI R20/等价审计、seeds 20262200–2400、两跑/caps/schema/13 失败/停止/边界；不训练/不拟合候选。
4. **执行前 final pilot**：最终实现 pilot 实测 wall/CPU/memory 冻结 canonical；caps 1800s/2h/8GB/0 wells；stage3 no_increment/旧判定不改。
5. **禁止**：把 181 写成正确 count；把 6 arms 的 count 配 7 arms 的 family；改旧 Stage3 判定/阈值；改 learner 合同（0.5+0.5*score/sigmoid/无 NLL/缩放/λ/类名）；真实数据/湿实验；称药理/真实决策/迁移/机制/新颖性。

## 3. 修完后建议的 Lead M3-S3b 执行批准文本（机制账/compute-only/0 wells）

> **批准范围**：在必改 1–2 完成并复核后，批准 **M3-S3b 候选 learner 比较执行**（机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：C218 Stage3 no_increment 保留；C220 解释无效；S3b 新预注册、不重跑旧 Stage3；C208 一步投影撤；高 regret H3/A3/Y binary、p=[.3,.4,.3]、μ/b Stage2、m_wrong=.5、C_H=20、b_min=1e-6、π2' .82/.09、Q/w/H=π2/w、**H_max18.91778<C_H20 无 clipping**；headroom P_empirical_mean/P_standard_DR_TMLE **.14841667 CI [.10382916,.19300417]**，均≥2δ=.10；headroom<.10→redesign/freeze 或 unreachable_gate，不执行/降δ/换seed/环境；DR gap0<1e-10；learner 合同（真实 ε weighted Bernoulli NLL/L-BFGS/score<1e-6；standard same m no ε；禁 0.5+0.5*score/sigmoid/无 NLL/缩放/λ/类名）；六比较 family6（primary candidate vs P_standard_DR_TMLE；secondary empirical/IW/full-history/DR-targeting/value-aware）、D<0、δ=.05、Holm6、单侧、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、raw/paired、CI R20/cluster；等价审计；seeds env20262200/headroom20262201–20/feedback20262221–40/eval20262241–60/arms20262261+20a+r（7 arms×20=140；**n_exec_seeds=201**）；两跑/caps/schema/13失败/停止；不输出effect/真实数据。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把 181 count 配 7 arms；把旧 Stage3 no_increment 改写；改 learner 合同/缩放/λ/类名；改旧判定/阈值；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不训练/不拟合候选/不读真实数据**：只读 S3b 预注册/headroom JSON/schema/C209/C213/C218/C220 链；只写本文件与 `tmp/`；未改 prereg 产物。
- **总判决：revise**。分离/纠正、高 regret/headroom、H_max18.9178<C_H20 无 clipping、DR gap0、learner 合同、六比较/Holm/δ/CI/等价/失败/停止/边界基本正确；但 **`all_exec_seeds_count=181` 与 7 arms×20+61=201 矛盾**。修完 1–2 后可提交 Lead 批准 M3-S3b 执行（机制账/compute-only/0 wells）。

**一句话：S3b 预注册的分离/纠正、高 regret 环境（H_max18.91778<C_H20 无 clipping）、headroom .14841667 CI[.10382916,.19300417]（≥.10）、DR gap0、真实 ε learner 合同、六比较/Holm6/δ=.05/raw-paired/CI R20/等价审计/13失败/停止/边界都核验通过；但 `all_exec_seeds_count=181` 与 7 arms×20+61=201 的 seed 账矛盾——判 revise：修正为 201（或删一个 arm 并同步 family），再提交 Lead 批准 M3-S3b 执行（机制账/compute-only/0 wells）。**
