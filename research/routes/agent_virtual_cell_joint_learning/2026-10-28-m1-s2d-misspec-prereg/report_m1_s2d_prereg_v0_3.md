# report_m1_s2d_prereg_v0_3 —— R204-M1-S2D.2 修订预注册报告（T3 避开 M2 Stage3；forbidden 补全；不运行候选）

2026-10-28。对象：R204-M1-S2d 错配/背景漂移规划价值预注册 v0.3。依据：M1-S2D.1-C1 复核（revise，T3 seed 20262100 与 M2 Stage3 保留区 20262100–39 重叠；forbidden 不完整）；S2c/C223、H1b/C222、C216/C217、C208、C220/C221、M1 Stage2 v0.2、M1 Stage2 exec seed 清单。
**状态：预注册修订草案；仅设计期 headroom（冻结源/目标真值）；未训练 C-MDN/未运行候选规划/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不修改 S2c；执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.3 新文件；v0.1/v0.2 保留不改）

- 问题定义：[PROBLEM_M1_S2D_v0_3.md](PROBLEM_M1_S2D_v0_3.md)（`33EE4312…`）
- 执行设计：[DESIGN_M1_S2D_v0_3.md](DESIGN_M1_S2D_v0_3.md)（`58E26FB0…`）
- headroom 设计：[headroom_design_m1_s2d_v0_3.py](headroom_design_m1_s2d_v0_3.py)（`34B92436…`）→ [headroom_design_m1_s2d_v0_3.json](headroom_design_m1_s2d_v0_3.json)（`B4C99ADD…`）
- schema：[schema_m1_s2d_v0_3.json](schema_m1_s2d_v0_3.json)（`5C6D95D9…`）
- 记录/用量：[record_m1_s2d_prereg_v0_3.md](record_m1_s2d_prereg_v0_3.md)、[usage_m1_s2d_prereg_v0_3.json](usage_m1_s2d_prereg_v0_3.json)

## 1. 必改落实

| # | 挑战问题 | v0.3 落实 |
|---|---|---|
| ① **T3 与 M2 Stage3 重叠** | T3 20262081–20262100，末 seed 20262100 落在 M2 Stage3 保留区 20262100–39 | **T3 重划 20262141–20262160**（20 seeds）；T1 20262041–60、T2 20262061–80 不变；每 target R=20/共 60；**20262100 不再使用**；M2 Stage3 保留区不解除 |
| ② **forbidden 集不完整** | 未列 M2 Stage3 20262100–39，overlap=[] 不完整 | **补全 forbidden ranges**：M1 Stage1/C208 20261112–13；M1 v0.2 20261201–03；**M2 Stage2 20261200–39**；M1 Stage2 exec 20261300–49；**M3 Stage2 20261400–99**；**M3 20261500–99**；**M3 Stage3 20261600–90**；H1b 20261800–49；S2c 20261900–59；**M2 Stage3 20262100–39**；`forbidden_old_seeds_count=533`；重算 **overlap_with_forbidden=[]、cell_blocks_disjoint=true** |
| ③ 保持 | — | 60 cells/R20；schema 五字段；T2 valid=4093（nominal 4096、不谎报）；headroom 值/CI；目标 θ'；候选仅源训练/目标禁用训练调参；六比较/Holm6/δ=.05/单侧下尾/raw-paired/T2T3 不合并/主成功仅 T1/等价审计；headroom seeds 20262011–30/data 20262031/eval 20262032；两跑/caps/schema/11 失败/停止/边界 |

## 2. 执行 cells / forbidden（关键修正）

| target | 执行 cell seeds | R |
|---|---|---|
| T1_scale_drift | **20262041–20262060** | 20 |
| T2_slope_drift | **20262061–20262080** | 20 |
| T3_background_drift | **20262141–20262160** | 20 |
| **合计** | — | **60** |

- **forbidden ranges**：M1 Stage1/C208 20261112–13；M1 v0.2 20261201–03；M2 Stage2 20261200–39；M1 Stage2 exec 20261300–49；M3 Stage2 20261400–99；M3 20261500–99；M3 Stage3 20261600–90；H1b 20261800–49；S2c 20261900–59；M2 Stage3 20262100–39。
- `forbidden_old_seeds_count=533`；`overlap_with_forbidden=[]`；`cell_blocks_disjoint=true`；执行 cells/data/eval 与全集无交集；T3 旧块 20262081–20262100 作废。
- schema/JSON 五字段保持：R_execution_per_target=20、n_targets=3、n_cells=60、cluster=replicate、CI_method 95% t(df=19)；T2/T3 每 target Holm R=20。

## 3. headroom（保留；先于候选）

- baseline=P_empirical_mean_source（N_train=4096 源样本/动作、动作级经验均值、忽略 x）；目标独立 eval X=4096；R=20（20262011–30）；真值目标解析。
- **T1 .51107412 CI [.46843293,.55371531]**；**T2 .56758207 CI [.56039835,.57476580]**；**T3 .39007047 CI [.38530525,.39483569]**；均≥2δ=.10 → **executable**；未重设环境；headroom 设计期实测（候选未见前），不冒充执行 R。
- **T2 有效行数 4093 冻结**（nominal 4096；T1/T3=4096；不谎报）。

## 4. 六比较/Holm/分析（保持）

- 主 target T1：primary candidate（源训练）vs P_empirical_mean_source；secondary P_empirical_mean_target_adapted（3584 源+512 目标/动作同预算）、P_max_entropy、P_conditional_density_MC（共用 C-MDN、D=0 不称独立）、P_random、P_softmax_expected_reward。
- D=regret_cand−regret_base<0；δ=.05；Holm family=6、单侧下尾；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；每 target R=20、cluster=replicate、95% t；不用规划 MDE 当功效；T2/T3 不合并、主成功仅 T1；等价审计。

## 5. 执行/预算/失败/停止

- seeds：headroom 20262011–30；data 20262031/eval 20262032；cells 三块（60）；overlap=[]；两跑逐字节；caps 1800 s/2 h/8 GB/0 wells；pilot 实测冻结；schema/11 失败/停止；本任务不训练/不运行候选。
- 停止：headroom<.10（任一 target）→重设/冻结或 unreachable_gate；等价→no increment；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 边界：机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 6. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2D_v0_3.md` | `33EE4312969D34832AA657DB009D67965F243B17E11B15E8D0281240BB73A444` |
| `DESIGN_M1_S2D_v0_3.md` | `58E26FB0A181529CED49CC46253BC0CC0A32A28AF2050EF511C53A4E9A186FA9` |
| `headroom_design_m1_s2d_v0_3.py` | `34B9243630930DE75BB7FC6A8A131D67F3B876181111E9AE40920230142323A3` |
| `headroom_design_m1_s2d_v0_3.json` | `B4C99ADD968F8C8173C56C726FD77E3382AA74F6EA7418715E2A132AA286BED7` |
| `schema_m1_s2d_v0_3.json` | `5C6D95D9B596F73BEC0AFAA567FE7DB528A23F4CCFD1FBC4D812D52CE920D94D` |
| report/record/usage | 见 `usage_m1_s2d_prereg_v0_3.json` |

**确定性**：`headroom_design_m1_s2d_v0_3.json` 两跑逐字节一致；JSON 无 telemetry；headroom wall≈5.1–5.9 s 仅 usage/报告。

## 7. 建议

1. **建议轻量复核**：重点 T3 新块 20262141–60（20262100 不再使用）、完整 forbidden ranges/count=533、overlap=[]/cell_blocks_disjoint=true、60 cells/R20、schema 五字段、T2 4093、headroom/六比较/δ/Holm/等价/seeds/caps/失败/边界保持。
2. 复核通过 + Lead 批准后才可执行 **M1-S2d 候选规划比较**（执行时才训练/规划；本任务不运行）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练 C-MDN/运行候选/效果/代码晋升/旧判定修改；不把 S2c 正结果写成真实数据/药理/真实决策/迁移/机制/新颖性。
