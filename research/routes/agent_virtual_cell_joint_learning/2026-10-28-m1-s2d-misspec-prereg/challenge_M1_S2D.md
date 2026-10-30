# R204-M1 S2d 错配/背景漂移规划比较预注册独立挑战（task-200）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 S2d、不训练 C-MDN/不运行候选规划/不读真实数据）。对象：[PROBLEM_M1_S2D.md](PROBLEM_M1_S2D.md)（SHA `00394113…`）、[DESIGN_M1_S2D.md](DESIGN_M1_S2D.md)（`86F5B08F…`）、[headroom_design_m1_s2d.py](headroom_design_m1_s2d.py)（`552F746C…`）、[headroom_design_m1_s2d.json](headroom_design_m1_s2d.json)（`12A9B91B…`）、[schema_m1_s2d.json](schema_m1_s2d.json)（`20B13ADD…`）、report/record/usage、S2c/C223/H1b/C222 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_to_lead；也不是 stop）。**

核验 PASS：
- **分离**：S2c 仅合成 known-truth、不改；C216 0/16/projection、C217、H1b 密度-only、C208 一步投影撤全部不变 ✓。
- **源/目标环境**：源 Pθ 同 H1b/S2c；T1 主 c'~N(0,1.0²) seed 20262001、T2 M'~N(0,.2²) seed 20262002、T3 X'~N(0,1.5²I)（θ 同源）；X64/A4/r/π0/S4096；候选仅源训练、目标数据禁用训练/调参（目标只评价/adapted baseline 512/动作标定）；known-truth 用目标 Pθ' 解析 ✓。
- **headroom**：T1 **.51107412 CI [.46843293,.55371531]**、T2 **.56758207 CI [.56039835,.57476580]**、T3 **.39007047 CI [.38530525,.39483569]**；均≥2δ=.10→executable、未重设；redesign_rule<.10/不降δ/不换seed写死 ✓。
- **六比较/Holm**：主 T1：primary candidate vs P_empirical_mean_source；secondary target-adapted empirical mean（3584源+512目标/动作）、max-entropy、conditional-density-MC（共用 C-MDN D=0 不称独立）、random、softmax-expected；D<0、δ=.05、统一 Holm family6、单侧下尾；raw/paired 分存；CI R≥20/cluster；T2/T3 每 target 内 Holm、不合并/pool、主成功仅 T1；不用 MDE 当功效 ✓。
- **等价审计**：candidate 与 empirical-mean/max-entropy/conditional-density 等价/解析覆盖→equivalence、停止增量；不得用目标数据训练/调参制造差异 ✓。
- **执行/seeds/caps/schema/失败/停止**：headroom 20262011–30；data 20262031；target eval 20262032；cells 20262041–88；与旧集 disjoint；两跑同 seeds/独立进程/逐字节/telemetry；caps 1800s/2h/8GB/0 wells；final pilot；schema；11 失败；停止 ✓。
- **边界**：机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only ✓。

**但执行样本量与 CI 要求不一致：**
- 预注册写 **CI 按独立 replicate R≥20**、`cluster=replicate`；但 `execution_cell_seeds` 只有 **20262041–20262088（48 个）**，而 **3 个 target**（T1/T2/T3）→ **每个 target 至多 48/3=16 replicates**，**R=16 < 20**。
- 这不是“T2/T3 次级”可豁免的问题：`multiple_testing.CI` 明确 R≥20；T2/T3 也各做六比较/Holm，R=16 会低于预注册 CI 口径。**必须把 execution cells 至少扩到 3×20=60（或明确每 target R=20 的 seed 块）**，且与旧集 disjoint；否则 CI/Holm 的 replicate 数不可判。

**结论：先修 §2 的 1–2，再提交 Lead 批准 M1-S2d 执行（机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 分离/旧状态 | **PASS** | S2c 仅合成、不改；C216/C217/H1b/C208 不变 ✓。 |
| ② | 源/目标 θ' | **PASS** | 源 Pθ；T1 c'~N(0,1²) seed20262001、T2 M'~N(0,.2²) seed20262002、T3 X'~N(0,1.5²I)；X64/A4/r/π0/S4096；候选仅源训练/目标禁用训练调参；known-truth 解析 ✓。 |
| ③ | headroom | **PASS** | T1 .51107412 CI[.46843293,.55371531]、T2 .56758207 CI[.56039835,.57476580]、T3 .39007047 CI[.38530525,.39483569]；均≥.10；未重设；redesign_rule/不降δ/不换seed ✓。 |
| ④ | 六比较/Holm/CI | **FAIL/PARTIAL** | 主T1/六比较/Holm6/δ=.05/one-sided/raw-paired/T2T3分层不合并/主成功仅T1 ✓；**但 execution cells 48/3 targets=R16，低于 CI R≥20**（§0）。 |
| ⑤ | 等价审计 | **PASS** | candidate 与 empirical-mean/max-entropy/conditional-density 等价/解析覆盖→equivalence；不得目标数据训练/调参 ✓。 |
| ⑥ | 执行/seeds/caps/schema/失败/停止 | **FAIL/PARTIAL** | headroom20262011–30/data20262031/target eval20262032/cells20262041–88；两跑/caps/schema/11失败/停止 ✓；**cells 48 只够 16/target，不足 R≥20**（§0）。 |
| ⑦ | 边界 | **PASS** | 机制账；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；public-only ✓。 |
| ⑧ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **扩执行 cells 到每 target ≥20**：当前 48 cells/3 targets=R16。改为 **3×20=60 cells**（或每 target 独立 R≥20 的 seed 块），并确保与 S2c/H1b/C216/C217/旧集 disjoint；更新 `execution_cell_seeds`、DESIGN/schema/report/record。
2. **在 JSON/schema 明确 `R_execution=20/target`、`n_targets=3`、`n_cells=60`、`cluster=replicate`、`CI_method`**；`multiple_testing.CI` 与实际 cells 数一致；T2/T3 每 target 的 Holm 也按 R≥20。
3. **保持**目标 Pθ'（T1/T2/T3）、headroom 值/CI、候选仅源训练/目标禁用训练调参、六比较/Holm6/δ=.05/raw-paired/T2T3 不合并/主成功仅T1、等价审计、seeds/data/eval、两跑/caps/schema/11 失败/停止、边界；不训练/不执行候选。
4. **注意 T2 `valid_eval_rows_min=4093`**（T1/T3=4096）：执行前确认目标 eval 的有效行数/缺失处理已冻结；若 4093 是小数值/截断造成，schema 中记录，不按 4096 谎报。
5. **禁止**：把 48 cells 写成 R≥20；用 headroom R=20 冒充 execution R=20；把 T2/T3 次级当可豁免 CI；改旧判定/容差；真实数据/湿实验；称药理/真实决策/迁移/机制/新颖性。

## 3. 修完后建议的 Lead M1-S2d 执行批准文本（机制账/compute-only/0 wells）

> **批准范围**：在必改 1–2 完成并复核后，批准 **M1-S2d 错配/背景漂移规划比较执行**（机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：S2c 不改；C216 0/16/projection、C217、H1b 密度-only、C208 撤不变；源 Pθ 同 H1b/S2c；T1 主 c'~N(0,1.0²) seed20262001、T2 M'~N(0,.2²) seed20262002、T3 X'~N(0,1.5²I)；X64/A4/r/π0/S4096；候选仅源训练、目标数据禁用训练/调参（目标只评价/adapted baseline 512/动作标定）；known-truth 目标解析；headroom T1 .51107412 CI[.46843293,.55371531]、T2 .56758207 CI[.56039835,.57476580]、T3 .39007047 CI[.38530525,.39483569]，均≥2δ=.10；headroom<.10→redesign/freeze before candidate 或 design_invalid: unreachable_gate，不得执行/降δ/换seed/环境；六比较（primary candidate vs P_empirical_mean_source；secondary target-adapted/max-entropy/cond-density-MC/random/softmax-expected）、D<0、δ=.05、Holm family6、one-sided lower、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、raw/paired 分存、CI **每 target R≥20**、cluster=replicate、T2/T3 每 target 内 Holm 不合并、主成功仅T1、不用MDE当功效；等价审计；**执行 cells ≥60（3 targets×20）**、seeds headroom20262011–30/data20262031/target eval20262032/cells 扩到每 target≥20；两跑/caps 1800s/2h/8GB/0 wells/final pilot/schema/11失败/停止；不输出effect/真实数据。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把目标数据用于候选训练/调参；把 48 cells 写成 R≥20；把 headroom R=20 冒充 execution R=20；把 T2/T3 次级当可豁免 CI；改旧判定/容差；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不训练 C-MDN/不运行候选规划/不读真实数据**：只读 S2d 预注册/headroom JSON/schema/S2c 链；只写本文件与 `tmp/`；未改 prereg 产物。
- **总判决：revise**。分离、源/目标 Pθ'、headroom T1/T2/T3 均≥.10、六比较/Holm/δ/raw-paired/T2T3 分层、等价审计、seeds/caps/schema/11失败/停止/边界基本正确；但 **execution cells=48/3 targets=R16<CI R≥20**。修完 1–2 后可提交 Lead 批准 M1-S2d 执行（机制账/compute-only/0 wells）。

**一句话：S2d 预注册的分离、源/目标 Pθ'、headroom T1 .51107412/T2 .56758207/T3 .39007047（均≥.10）、六比较/Holm6/δ=.05/raw-paired/T2T3 不合并、等价审计、caps/schema/11失败/停止/边界都核验通过；但 execution cells 48/3 targets=R16，低于预注册 CI R≥20——判 revise：扩到 3×20=60 cells（或每 target R≥20 seed 块）并同步 schema/JSON，再提交 Lead 批准 M1-S2d 执行（机制账/compute-only/0 wells）。**
