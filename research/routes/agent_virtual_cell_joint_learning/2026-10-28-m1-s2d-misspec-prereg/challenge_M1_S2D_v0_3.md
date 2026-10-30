# R204-M1 S2d.2 轻量复核（task-204）：v0.3 T3 重划/forbidden 补全

2026-10-28。角色：同一独立挑战者（非提案者、未参与 S2d、不训练 C-MDN/不运行候选规划/不读真实数据）。对象：[PROBLEM_M1_S2D_v0_3.md](PROBLEM_M1_S2D_v0_3.md)（SHA `33EE4312…`）、[DESIGN_M1_S2D_v0_3.md](DESIGN_M1_S2D_v0_3.md)（`58E26FB0…`）、[headroom_design_m1_s2d_v0_3.py](headroom_design_m1_s2d_v0_3.py)（`34B92436…`）、[headroom_design_m1_s2d_v0_3.json](headroom_design_m1_s2d_v0_3.json)（`B4C99ADD…`）、[schema_m1_s2d_v0_3.json](schema_m1_s2d_v0_3.json)（`5C6D95D9…`）、report/record/usage、S2c 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_exec_v0_3_to_lead（仅批准 M1-S2d 错配/背景漂移规划比较执行：机制账、compute-only、0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**

v0.3 已修掉 v0.2 的 T3/M2 Stage3 seed 冲突：
- **T3 重划为 20262141–20262160（20）**；T1 **20262041–60**、T2 **20262061–80**；每 target R=20/共 60；**20262100 不再使用**；M2 Stage3 **20262100–39 未解除**；旧 T3 20262081–00 作废 ✓。
- **forbidden 补全 10 ranges**：M1 Stage1 20261112–13、M1 v0.2 20261201–03、M2 Stage2 20261200–39、M1 Stage2 exec 20261300–49、M3 Stage2 20261400–99、M3 20261500–99、M3 Stage3 20261600–90、H1b 20261800–49、S2c 20261900–59、M2 Stage3 20262100–39；**去重 count=533**；`overlap_with_forbidden=[]`、`cell_blocks_disjoint=true`；T1/T2/T3 cells 与 data/eval 均不与全集相交 ✓。
- **schema 五字段**：`R_execution_per_target=20`、`n_targets=3`、`n_cells=60`、`cluster="replicate"`、`CI_method`；`multiple_testing.CI` 与实际 cells 一致；T2/T3 每 target Holm R=20、不豁免 ✓。
- **T2 4093**：`valid_eval_rows=4093`（3 极端解析下溢行剔除，nominal 4096）；T1/T3=4096；schema/JSON `valid_eval_rows_frozen`/note 记录、不按 4096 谎报 ✓。
- **保持项**：headroom T1 **.51107412 CI [.46843293,.55371531]**、T2 **.56758207 CI [.56039835,.57476580]**、T3 **.39007047 CI [.38530525,.39483569]**；目标 θ'；候选仅源训练/目标禁用训练调参；六比较/Holm6/δ=.05/单侧下尾/raw-paired/T2T3 不合并/主成功仅 T1/等价审计；seeds headroom20262011–30/data20262031/eval20262032；两跑/caps 1800s/2h/8GB/0 wells/schema/11 失败/停止/边界 ✓。
- **边界**：机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only ✓。

**结论：可提交 Lead 批准 M1-S2d 执行（机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | T3 重划/冲突解除 | **PASS** | T3 20262141–60；T1 20262041–60/T2 20262061–80；R20/target/60；20262100 不再使用；M2 Stage3 20262100–39 未解除；旧 T3 作废 ✓。 |
| ② | forbidden 补全 | **PASS** | 10 ranges；去重 count=533；overlap=[]；cell_blocks_disjoint=true；T1/T2/T3/data/eval 与全集不相交 ✓。 |
| ③ | schema 五字段 | **PASS** | R20/n_targets3/n_cells60/cluster/CI_method；multiple_testing.CI 一致；T2/T3 Holm R20；execution_design ✓。 |
| ④ | T2 4093 | **PASS** | valid_eval_rows T2=4093（3 extreme analytic-underflow rows dropped）；T1/T3=4096；frozen/note；不按4096报 ✓。 |
| ⑤ | 保持项 | **PASS** | headroom T1 .51107412 CI [.46843293,.55371531]、T2 .56758207 CI [.56039835,.57476580]、T3 .39007047 CI [.38530525,.39483569]；目标 θ'；候选仅源训练/目标禁用；六比较/Holm6/δ=.05/单侧/raw-paired/T2T3不合并/主成功T1/等价审计；seeds/caps/schema/11失败/停止/边界 ✓。 |
| ⑥ | 边界 | **PASS** | 机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only ✓。 |
| ⑦ | 总判决 | **approve_exec_v0_3_to_lead** | 仅 S2d 执行；不批真实数据/效果。 |

**非阻塞实现备注**：
1. `forbidden_ranges` 10 项中 M1 v0.2 20261201–03 是 M2 Stage2 20261200–39 的子集；去重后 533 正确；执行器按范围并集判即可，不要重复计数。
2. T3 20262141–60 与 M2 Stage3 20262100–39 之间留出 20262101–40 未用；不冲突，但不要临时把 T3 移回 20262100。
3. T2 valid_eval_rows=4093 冻结；报告不得写 4096；执行前 final pilot 仍要实测 60 cells 的 wall/CPU/memory 并冻结 canonical。
4. 旧 C216/C217/H1b/C208/S2c 不变；不把 S2d 写成真实数据/药理/迁移/机制/新颖性。

## 2. Lead M1-S2d 执行批准文本（建议）

> **批准范围**：批准 **M1-S2d 错配/背景漂移规划比较执行**（机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：S2c 不改；C216 0/16/projection、C217、H1b 密度-only、C208 撤不变；源 Pθ 同 H1b/S2c；T1 主 c'~N(0,1.0²) seed20262001、T2 M'~N(0,.2²) seed20262002、T3 X'~N(0,1.5²I)；X64/A4/r/π0/S4096；候选仅源训练、目标数据禁用训练/调参（目标只评价/adapted baseline 512/动作标定）；known-truth 目标解析；headroom T1 .51107412 CI[.46843293,.55371531]、T2 .56758207 CI[.56039835,.57476580]、T3 .39007047 CI[.38530525,.39483569]，均≥2δ=.10；headroom<.10→redesign/freeze before candidate 或 design_invalid: unreachable_gate，不得执行/降δ/换seed/环境；六比较（primary candidate vs P_empirical_mean_source；secondary target-adapted/max-entropy/cond-density-MC/random/softmax-expected）、D<0、δ=.05、Holm family6、one-sided lower、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、raw/paired 分存、CI 每 target R≥20、cluster=replicate、T2/T3 每 target 内 Holm 不合并、主成功仅 T1、不用 MDE 当功效；等价审计；**60 cells（T1 20262041–60、T2 20262061–80、T3 20262141–60），20262100 不用，M2 Stage3 20262100–39 保留**；10 forbidden ranges/533 去重/overlap=[]；seeds headroom20262011–30/data20262031/eval20262032；两跑/caps 1800s/2h/8GB/0 wells/final pilot/schema/11失败/停止；不输出effect/真实数据。**T2 valid_eval_rows=4093 冻结，不按4096报。**
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把目标数据用于候选训练/调参；用 20262100（M2 Stage3 保留区）；把 T2/T3 次级当可豁免 CI；改旧判定/容差；晋升代码；恢复停止实验。

## 3. 声明

- **本轮不训练 C-MDN/不运行候选规划/不读真实数据**：只读 S2d v0.3 预注册/headroom JSON/schema/S2c 链；只写本文件与 `tmp/`；未改 prereg 产物。
- **总判决：approve_exec_v0_3_to_lead**。T3 20262141–60/20262100 不用、10 forbidden ranges/533/overlap=[]/disjoint、60 cells/R20、schema 五字段、T2 4093、headroom 值/CI、六比较/Holm/δ/等价/seeds/caps/11失败/边界均核验通过；仅 forbidden 子集去重、T3 区间、T2 4093、final pilot 为非阻塞执行备注。仅批准 S2d 执行（机制账/compute-only/0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性。

**一句话：v0.3 已把 T3 重划为 20262141–60（不再用 20262100）、补全 10 forbidden ranges/533 去重/overlap=[]/disjoint、保持 60 cells/R20/schema 五字段/T2 4093/headroom T1 .51107412/T2 .56758207/T3 .39007047 与六比较/边界——判 approve_exec_v0_3_to_lead（仅 M1-S2d 错配/漂移规划比较执行：机制账/compute-only/0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**
