# R204-M1 S2d.1 轻量复核（task-202）：v0.2 60 cells

2026-10-28。角色：同一独立挑战者（非提案者、未参与 S2d、不训练 C-MDN/不运行候选规划/不读真实数据）。对象：[PROBLEM_M1_S2D_v0_2.md](PROBLEM_M1_S2D_v0_2.md)（SHA `25114A56…`）、[DESIGN_M1_S2D_v0_2.md](DESIGN_M1_S2D_v0_2.md)（`1676FD5E…`）、[headroom_design_m1_s2d_v0_2.py](headroom_design_m1_s2d_v0_2.py)（`CA56B472…`）、[headroom_design_m1_s2d_v0_2.json](headroom_design_m1_s2d_v0_2.json)（`B2095AEF…`）、[schema_m1_s2d_v0_2.json](schema_m1_s2d_v0_2.json)（`A9D0D197…`）、report/record/usage、S2c 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_v0_2_to_lead；也不是 stop）。**

v0.2 已修掉 v0.1 的 R16 缺口：
- **60 cells**：T1 **20262041–60**、T2 **20262061–80**、T3 **20262081–100**，每 target **R=20**；`execution_cell_seed_blocks` 写死；48 cells 作废；headroom R=20 不冒充执行 R ✓。
- **schema 可判字段**：`R_execution_per_target=20`、`n_targets=3`、`n_cells=60`、`cluster="replicate"`、`CI_method`；`multiple_testing.CI` 与实际 cells 一致；T2/T3 每 target Holm 也按 R=20、不豁免 ✓。
- **T2 4093**：`valid_eval_rows=4093`（3 极端解析下溢行剔除，nominal 4096）；T1/T3=4096；schema/JSON `valid_eval_rows_frozen`/note 记录、不按 4096 谎报 ✓。
- **保持项**：分离/旧状态（S2c 仅合成、C216/C217/H1b/C208 不变）；目标 θ' T1/T2/T3；headroom T1 .51107412 CI [.46843293,.55371531]、T2 .56758207 CI [.56039835,.57476580]、T3 .39007047 CI [.38530525,.39483569]；候选仅源训练/目标禁用训练调参；六比较/Holm family6/δ=.05/单侧下尾/raw-paired/T2T3 不合并/主成功仅 T1/等价审计；headroom seeds 20262011–30/data 20262031/eval 20262032；两跑/caps/schema/11 失败/停止/边界 ✓。

**但 T3 的 seed 块与旧 M2 Stage3 保留区间重叠：**
- T3 block = **20262081–20262100**；**M2 Stage3 reserved = 20262100–20262139**（此前 M1 Stage2 exec 的 forbidden 集明确列出）。因此 **20262100 同时属于 M1 S2d T3 和 M2 Stage3 保留区**。
- `execution_seeds.forbidden_old_seeds` **没有列 M2 Stage3 20262100–20262139**，`overlap_with_forbidden=[]` 因此是**不完整的**；任务 ① 要求“与旧集 disjoint”，当前不满足。
- 这是 seed 可复现/隔离的实质问题，必须重划 T3 块（或明确 M2 Stage3 不再使用该 seed），并补 forbidden 集。

**结论：先修 §2 的 1–2，再提交 Lead 批准 M1-S2d 执行（机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | cells 扩展 | **FAIL/PARTIAL** | T1 20262041–60/T2 20262061–80/T3 20262081–100，每 target R20/共60；blocks写死；48作废；headroom R20不冒充 ✓。**但 T3 末 seed 20262100 与 M2 Stage3 保留区 20262100–20262139 重叠**（§0）。 |
| ② | schema 可判字段 | **PASS** | `R_execution_per_target=20`、`n_targets=3`、`n_cells=60`、`cluster=replicate`、`CI_method`；`multiple_testing.CI` 一致；T2/T3 Holm R20不豁免；`execution_design` ✓。 |
| ③ | T2 4093 | **PASS** | valid_eval_rows T2=4093（3 extreme analytic-underflow rows dropped）；T1/T3=4096；schema/JSON frozen/note；不按4096谎报 ✓。 |
| ④ | 保持项 | **PASS** | 分离/旧状态；T1/T2/T3 θ'；headroom T1 .51107412 CI [.46843293,.55371531]、T2 .56758207 CI [.56039835,.57476580]、T3 .39007047 CI [.38530525,.39483569]；候选仅源训练/目标禁用；六比较/Holm6/δ=.05/单侧/raw-paired/T2T3不合并/主成功T1/等价审计；seeds/caps/schema/11失败/停止/边界 ✓。 |
| ⑤ | 边界 | **PASS** | 机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only ✓。 |
| ⑥ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **重划 T3 seed 块避开 M2 Stage3 20262100–20262139**：例如 T3 = **20262141–20262160**（20 seeds）或 **20262081–20262099 + 20262140**；保持每 target R=20、总 60；T1/T2 可不变。**不能使用 20262100**，除非明确记录 M2 Stage3 不再使用该 seed 并解除保留。
2. **补 `forbidden_old_seeds`**：加入 **M2 Stage3 20262100–20262139**（以及 M2 Stage2 20261200–39、M3 20261500–99 等旧保留区，若尚未列）；重算 `overlap_with_forbidden`，必须为空；`execution_cell_seed_blocks`/`execution_cell_seeds`/DESIGN/schema/report/record 同步。
3. **保持** 60 cells/R20、schema 五字段、T2 4093、headroom 值/CI、目标 θ'、候选仅源训练/目标禁用、六比较/Holm6/δ=.05/单侧/raw-paired/T2T3不合并/主成功T1/等价审计、seeds20262011–32、两跑/caps/schema/11失败/停止/边界；不训练/不执行候选。
4. **T3 新块**与 headroom20262011–30/data20262031/eval20262032/T1/T2 块、S2c/H1b/C216/C217/M2/M3/N1 全部 disjoint；`cell_blocks_disjoint=true` 要用完整 forbidden 集重算。
5. **禁止**：把 20262100 重叠写成 overlap=[]；用 60 cells 掩盖 M2 Stage3 冲突；改旧判定/容差；真实数据/湿实验；称药理/真实决策/迁移/机制/新颖性。

## 3. 修完后建议的 Lead M1-S2d 执行批准文本（机制账/compute-only/0 wells）

> **批准范围**：在必改 1–2 完成并复核后，批准 **M1-S2d 错配/背景漂移规划比较执行**（机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：S2c 不改；C216 0/16/projection、C217、H1b 密度-only、C208 撤不变；源 Pθ 同 H1b/S2c；T1 主 c'~N(0,1.0²) seed20262001、T2 M'~N(0,.2²) seed20262002、T3 X'~N(0,1.5²I)；X64/A4/r/π0/S4096；候选仅源训练、目标数据禁用训练/调参（目标只评价/adapted baseline 512/动作标定）；known-truth 目标解析；headroom T1 .51107412 CI[.46843293,.55371531]、T2 .56758207 CI[.56039835,.57476580]、T3 .39007047 CI[.38530525,.39483569]，均≥2δ=.10；headroom<.10→redesign/freeze before candidate 或 design_invalid: unreachable_gate，不得执行/降δ/换seed/环境；六比较（primary candidate vs P_empirical_mean_source；secondary target-adapted/max-entropy/cond-density-MC/random/softmax-expected）、D<0、δ=.05、Holm family6、one-sided lower、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、raw/paired 分存、CI 每 target R≥20、cluster=replicate、T2/T3 每 target 内 Holm 不合并、主成功仅 T1、不用 MDE 当功效；等价审计；**执行 60 cells（3 targets×20）且 T3 块避开 20262100–20262139**、seeds headroom20262011–30/data20262031/eval20262032/cells 重划后每 target≥20；两跑/caps 1800s/2h/8GB/0 wells/final pilot/schema/11失败/停止；不输出effect/真实数据。**T2 valid_eval_rows=4093 冻结，不按4096报。**
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把目标数据用于候选训练/调参；把48 cells写成R≥20；用20262100（M2 Stage3保留区）；把T2/T3次级当可豁免CI；改旧判定/容差；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不训练 C-MDN/不运行候选规划/不读真实数据**：只读 S2d v0.2 预注册/headroom JSON/schema/S2c 链；只写本文件与 `tmp/`；未改 prereg 产物。
- **总判决：revise**。60 cells/R20、schema 五字段、T2 4093、headroom 值/CI、六比较/Holm/δ/raw-paired/T2T3 分层、等价审计、caps/schema/11失败/停止/边界基本正确；但 **T3 块末 seed 20262100 与 M2 Stage3 保留区 20262100–20262139 重叠**，forbidden 集未列该区间、overlap=[] 不完整。修完 1–2 后可提交 Lead 批准 M1-S2d 执行（机制账/compute-only/0 wells）。

**一句话：v0.2 已把 S2d 扩到 T1 20262041–60/T2 20262061–80/T3 20262081–100（R20/target、60 cells），schema 五字段可判、T2 4093 冻结、headroom 值与六比较/边界保持；但 T3 末 seed 20262100 落在 M2 Stage3 保留区 20262100–20262139，forbidden 集未列且 overlap=[] 不完整——判 revise：重划 T3 块并补 M2 Stage3 forbidden/overlap，再提交 Lead 批准 M1-S2d 执行。**
