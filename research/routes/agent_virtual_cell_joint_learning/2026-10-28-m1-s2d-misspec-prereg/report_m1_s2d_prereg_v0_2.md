# report_m1_s2d_prereg_v0_2 —— R204-M1-S2D.1 修订预注册报告（每 target R≥20/共 60 cells；不运行候选）

2026-10-28。对象：R204-M1-S2d 错配/背景漂移规划价值预注册 v0.2。依据：M1-S2D-C1 挑战（revise，执行 cells 不足）；S2c/C223、H1b/C222、C216/C217、C208、C220/C221、M1 Stage2 v0.2。
**状态：预注册修订草案；仅设计期 headroom（冻结源/目标真值）；未训练 C-MDN/未运行候选规划/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不修改 S2c；执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.2 新文件；v0.1 保留不改）

- 问题定义：[PROBLEM_M1_S2D_v0_2.md](PROBLEM_M1_S2D_v0_2.md)（`25114A56…`）
- 执行设计：[DESIGN_M1_S2D_v0_2.md](DESIGN_M1_S2D_v0_2.md)（`1676FD5E…`）
- headroom 设计：[headroom_design_m1_s2d_v0_2.py](headroom_design_m1_s2d_v0_2.py)（`CA56B472…`）→ [headroom_design_m1_s2d_v0_2.json](headroom_design_m1_s2d_v0_2.json)（`B2095AEF…`）
- schema：[schema_m1_s2d_v0_2.json](schema_m1_s2d_v0_2.json)（`A9D0D197…`）
- 记录/用量：[record_m1_s2d_prereg_v0_2.md](record_m1_s2d_prereg_v0_2.md)、[usage_m1_s2d_prereg_v0_2.json](usage_m1_s2d_prereg_v0_2.json)

## 1. 必改落实

| # | 挑战问题 | v0.2 落实 |
|---|---|---|
| ① **cells 48÷3=16 <20** | 每 target R≥20 但仅 48 cells | **每 target 独立 R=20 seed 块、共 60**：**T1 20262041–20262060、T2 20262061–20262080、T3 20262081–20262100**；`execution_cell_seed_blocks` 写死；48 作废；与旧集 disjoint（overlap=[]） |
| ② **schema/JSON 可判字段** | — | 新增 **`R_execution_per_target=20`、`n_targets=3`、`n_cells=60`、`cluster="replicate"`、`CI_method="95% t interval across independent replicates (df=R-1); cluster=replicate"`**；`multiple_testing.CI` 与实际 60 cells 一致；**T2/T3 每 target Holm 也按 R=20**，不得次级豁免 |
| ③ **T2 有效行数** | 仅 valid_eval_rows_min=4093 | 冻结记录：**T2 target eval 有效=4093**（3 个极端解析下溢行剔除；nominal 4096）；T1/T3=4096；schema/JSON + note，**不按 4096 谎报** |
| ④ 保持 | — | 目标/headroom 值/仅源训练/六比较/δ/Holm/raw-paired/T2T3 不合并/主成功仅 T1/seeds 20262011–30/data 20262031/eval 20262032/两跑/caps/schema/11 失败/停止/边界；**不训练/不执行候选** |

## 2. 执行 cells（关键修正）

| target | 执行 cell seeds | R |
|---|---|---|
| T1_scale_drift | **20262041–20262060** | 20 |
| T2_slope_drift | **20262061–20262080** | 20 |
| T3_background_drift | **20262081–20262100** | 20 |
| **合计** | — | **60** |

- headroom R=20（20262011–30）仅设计期，**不冒充执行 R**；执行每 target 独立 R=20；cluster=replicate；95% t（df=19）。
- schema/JSON 字段与实际一致；T2/T3 每 target Holm（family=6，R=20）；不合并/pool；主成功仅 T1。

## 3. headroom（保留；先于候选）

- baseline=P_empirical_mean_source（N_train=4096 源样本/动作、动作级经验均值、忽略 x）；目标独立 eval X=4096；R=20；真值目标解析。
- **T1 .51107412 CI [.46843293,.55371531]**；**T2 .56758207 CI [.56039835,.57476580]**；**T3 .39007047 CI [.38530525,.39483569]**；均≥2δ=.10 → **executable**；未重设环境；headroom 设计期实测（候选未见前），不得用候选结果反选。
- **T2 有效行数 4093 冻结**；T1/T3 4096；按实际记录，不谎报。

## 4. 六比较/Holm/分析（保持）

- 主 target T1：primary candidate（源训练）vs P_empirical_mean_source；secondary P_empirical_mean_target_adapted（3584 源+512 目标/动作同预算）、P_max_entropy、P_conditional_density_MC（共用 C-MDN、D=0 不称独立）、P_random、P_softmax_expected_reward。
- D=regret_cand−regret_base<0；δ=.05；Holm family=6、单侧下尾；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；每 target R=20、cluster=replicate、95% t；不用规划 MDE 当功效。
- 等价审计：candidate 与 empirical-mean/max-entropy/conditional-density 等价→equivalence/no increment；不得目标训练/调参制造差异。

## 5. 执行/预算/失败/停止

- seeds：headroom 20262011–30；data 20262031/eval 20262032；cells 三块（60）；overlap=[]；两跑逐字节；caps 1800 s/2 h/8 GB/0 wells；pilot 实测冻结；schema/11 失败/停止；本任务不训练/不运行候选。
- 停止：headroom<.10（任一 target）→重设/冻结或 unreachable_gate；等价→no increment；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 边界：机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 6. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2D_v0_2.md` | `25114A56B5745A1A517E4AECF415EDD013A6C9F128CBA523E2238F6BCFE69D98` |
| `DESIGN_M1_S2D_v0_2.md` | `1676FD5E6087A775424EB34B0A8E919F8996D829F2869081C9D0D5722D8A623D` |
| `headroom_design_m1_s2d_v0_2.py` | `CA56B472585A2FFB63BEFAC56D0FEB331FB4A7F9D3CD6BC119B0428E2F10E44F` |
| `headroom_design_m1_s2d_v0_2.json` | `B2095AEFE23CA531B35794316A84A210C6263129D4E75D5644FA942B12C8F091` |
| `schema_m1_s2d_v0_2.json` | `A9D0D197BF406F04CB4F721F84CD5D718C19C8166FDF9D57DB55BA69357E6D43` |
| report/record/usage | 见 `usage_m1_s2d_prereg_v0_2.json` |

**确定性**：`headroom_design_m1_s2d_v0_2.json` 两跑逐字节一致；JSON 无 telemetry；headroom wall≈5.5–5.8 s 仅 usage/报告。

## 7. 建议

1. **建议轻量复核**：重点每 target R=20/共 60 cells 与 seed 块（20262041–20262100）、schema/JSON `R_execution_per_target/n_targets/n_cells/cluster/CI_method`、`multiple_testing.CI` 与实际 cells 一致、T2/T3 每 target Holm R=20、T2 有效行数 4093 冻结且不谎报、其余 headroom/六比较/δ/seeds/caps/失败/边界保持。
2. 复核通过 + Lead 批准后才可执行 **M1-S2d 候选规划比较**（执行时才训练/规划；本任务不运行）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练 C-MDN/运行候选/效果/代码晋升/旧判定修改；不把 S2c 正结果写成真实数据/药理/真实决策/迁移/机制/新颖性。
