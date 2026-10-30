# report_m1_s2d_prereg —— R204-M1-S2d 错配/背景漂移规划价值预注册报告（先 headroom；不运行候选）

2026-10-28。对象：R204-M1-S2d 错配/背景漂移规划价值检验预注册。依据：S2c/C223（`planning_comparison_pass`，仅合成 known-truth）、H1b/C222、C216/C217、C208、C220/C221、M1 Stage2 v0.2。
**状态：预注册草案；仅设计期 headroom（冻结源/目标真值）；未训练 C-MDN、未运行候选规划、未报效果、未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不修改 S2c；执行须另立独立挑战+Lead 批准。**

## 0. 交付物

- 问题定义：[PROBLEM_M1_S2D.md](PROBLEM_M1_S2D.md)（`00394113…`）
- 执行设计：[DESIGN_M1_S2D.md](DESIGN_M1_S2D.md)（`86F5B08F…`）
- headroom 设计：[headroom_design_m1_s2d.py](headroom_design_m1_s2d.py)（`552F746C…`）→ [headroom_design_m1_s2d.json](headroom_design_m1_s2d.json)（`12A9B91B…`）
- schema：[schema_m1_s2d.json](schema_m1_s2d.json)（`20B13ADD…`）
- 记录/用量：[record_m1_s2d_prereg.md](record_m1_s2d_prereg.md)、[usage_m1_s2d_prereg.json](usage_m1_s2d_prereg.json)

## 1. 分离（写死）

- S2c 正结果仅**合成 known-truth**；不称真实数据/药理/真实决策/迁移/机制/新颖性；S2d 不修改 S2c。
- C216 旧 H1 0/16、`design_invalid: projection`、C217 归因、H1b 16/16 密度-only、一步投影撤（C208）**全部不变**；旧容差/判定不改。

## 2. 源/目标环境（预注册）

- 源 Pθ 同 H1b/S2c：c .5²/M .1²/d .1²、σ、box[-2,2]^4、K=3/[.5,.3,.2]；seeds 20261301/02/03；X~N(0,I_64)；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；S=4096/动作。
- 目标 Pθ'（3 种）：
  - **T1_scale_drift（主）**：c'~N(0,1.0²)，M/d 同源；X~N(0,I)；target c seed **20262001**。
  - T2_slope_drift：M'~N(0,.2²)，c/d 同源；X~N(0,I)；target M seed **20262002**。
  - T3_background_drift：θ 同源；X'~N(0,1.5²I)。
- π0' full（4 动作均匀）；**候选 C-MDN 仅源训练；目标数据禁用训练/调参**（目标数据只用于评价与 target-adapted baseline 512/动作标定）；known-truth 用目标 Pθ' 解析截断正态矩。

## 3. 设计期 headroom（先于候选；目标 Pθ'）

- baseline=P_empirical_mean_source（N_train=4096 源样本/动作、动作级经验均值、忽略 x）；目标独立 eval X=4096；R=20（20262011–30）；真值目标解析。
- **结果**：

| target | mean baseline regret | 95% CI(t₁₉) | headroom_ok |
|---|---|---|---|
| **T1_scale_drift（主）** | **0.51107412** | **[0.46843293, 0.55371531]** | true |
| T2_slope_drift | **0.56758207** | **[0.56039835, 0.57476580]** | true |
| T3_background_drift | **0.39007047** | **[0.38530525, 0.39483569]** | true |

- **要求每个目标 mean≥2δ=.10**；三目标均满足 → **executable**；**未重设环境**；**headroom 设计期实测（候选未见前）**；若未来任一<.10，未见候选前重设/冻结或 `design_invalid: unreachable_gate` 停止；**不降 δ/不换 seed/不换环境救结果**。

## 4. 六比较/Holm/分析

- 主目标 T1：primary **candidate（源训练）vs P_empirical_mean_source**；secondary P_empirical_mean_target_adapted（同预算 3584 源+512 目标/动作）、P_max_entropy、P_conditional_density_MC（共用 C-MDN，预计 D=0，不称独立）、P_random、P_softmax_expected_reward。
- **D=regret_cand−regret_base<0**；δ=.05；**Holm family=6、单侧下尾**；primary 成功=mean≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；raw/paired 分存；CI 独立 replicate（R≥20，cluster=replicate）；不用规划 MDE 当功效。
- T2/T3 为预注册次级/泛化目标：同六比较、每 target 内 Holm；不合并/pool；主成功仅 T1。
- **等价审计**：candidate 与 P_empirical_mean_source/P_max_entropy/P_conditional_density_MC 逐点动作/单调/解析覆盖→equivalence、停止增量；不得用目标训练/调参制造差异。

## 5. 执行/seeds/caps/schema/失败/停止

- seeds：headroom 20262011–30；执行 data **20262031**、target eval **20262032**、cells **20262041–20262088**；与 S2c/H1b/C216/C217/旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema/11 失败/停止写死；JSON 无 telemetry；本任务不训练/不运行候选。
- 失败类别 11：projection/calibration/leakage/unreachable_gate/equivalence/precision_insufficient/two_run_mismatch/chain_mismatch/compute_budget_exceeded/no_increment/inconclusive。
- 停止：headroom<.10（任一 target）→重设/冻结或 unreachable_gate；等价→no increment；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。

## 6. 边界

机制账 only；合成 compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2D.md` | `00394113A84DF84F50FF709BC841B74F84ED26F4984DC35329CF044E447AC68D` |
| `DESIGN_M1_S2D.md` | `86F5B08F37CFBE6C8F9C08670638EF8B66D5AFD98640CCD7B576C853283CE439` |
| `headroom_design_m1_s2d.py` | `552F746C4C5E4A1B2C63F2A47FF8ED4A71CD03E1ECD2ACF9AC410B8484EA47D8` |
| `headroom_design_m1_s2d.json` | `12A9B91BDEF709DFE413E5E63DC2EBFAB640807C6FFAE27D6BDDC6A91CD4E646` |
| `schema_m1_s2d.json` | `20B13ADD7A3EC832279103E4AE1366D514436DC50991A752F8BB888A9C5CD8D2` |
| report/record/usage | 见 `usage_m1_s2d_prereg.json` |

**确定性**：`headroom_design_m1_s2d.json` 两跑逐字节一致；JSON 无 telemetry；headroom wall≈5.3–5.7 s 仅 usage/报告。

## 8. 建议

1. **提交独立挑战**：重点分离/旧状态不变、源/目标 Pθ'（3 目标）、设计期 headroom 表（T1 .51107/T2 .56758/T3 .39007，均≥.10，未重设）、候选仅源训练/目标禁用训练调参、六比较/Holm/δ/raw-paired/CI/目标分层、seeds/caps/schema/11 失败/停止。
2. 挑战通过 + Lead 批准后才可执行 **M1-S2d 候选规划比较**（执行时才训练/规划；本任务不运行）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练 C-MDN/运行候选/效果/代码晋升/旧判定修改；不把 S2c 正结果写成真实数据/药理/真实决策/迁移/机制/新颖性。
