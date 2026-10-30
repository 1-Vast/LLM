# report_m1_s2c_prereg_v0_2 —— R204-M1-S2C.1 修订预注册报告（headroom 阈值 .10；不运行候选）

2026-10-28。对象：R204-M1-S2c 规划价值检验预注册 v0.2。依据：M1-S2C-C1 挑战（revise，headroom 阈值矛盾）、C208/C216/C217/C220/C221/C222、H1b/C222、M1 Stage2 v0.2。
**状态：预注册修订草案；仅设计期 headroom（冻结真值）；未训练 C-MDN/未运行候选规划/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.2 新文件；v0.1 保留不改）

- 问题定义：[PROBLEM_M1_S2C_v0_2.md](PROBLEM_M1_S2C_v0_2.md)
- 执行设计：[DESIGN_M1_S2C_v0_2.md](DESIGN_M1_S2C_v0_2.md)
- headroom 设计：[headroom_design_m1_s2c_v0_2.py](headroom_design_m1_s2c_v0_2.py) → [headroom_design_m1_s2c_v0_2.json](headroom_design_m1_s2c_v0_2.json)
- schema：[schema_m1_s2c_v0_2.json](schema_m1_s2c_v0_2.json)
- 记录/用量：[record_m1_s2c_prereg_v0_2.md](record_m1_s2c_prereg_v0_2.md)、[usage_m1_s2c_prereg_v0_2.json](usage_m1_s2c_prereg_v0_2.json)

## 1. 必改落实

| # | 挑战问题 | v0.2 落实 |
|---|---|---|
| ① **headroom 停止阈值不一致** | v0.1 requirement=≥2δ=.10，但 stop_conditions[0]="headroom<δ(.05) 停"；若 headroom∈[.05,.10) 会继续执行 | **stop_conditions[0] 改为 "headroom<2*delta (=0.10) -> 未见候选前重设并冻结环境，或 `design_invalid: unreachable_gate` 停止；不执行"**；与 requirement/redesign_rule 完全一致；**不把 .10 降为 .05** |
| ② **schema/JSON 无可判字段** | — | 新增 **`headroom_required=0.10`、`headroom_decision_rule`、`headroom_stop_category="design_invalid: unreachable_gate"`**；schema/JSON/stop_conditions 同步；执行器按 2δ=.10 判 |
| ③ **headroom 语义** | — | 明确为**候选未见前设计期实测**；本轮未重设环境；若未来重设须在候选结果前记录并冻结；不得用候选结果反选 |
| ④ 保持 | — | 旧/新分离、冻结环境/Pθ、六比较/Holm/δ=.05/raw-paired/CI R≥20/等价审计/seeds 20261901–54/两跑/caps 1800 s/2 h/8 GB/0 wells/schema/11 失败/边界；headroom 值保留 |

## 2. headroom 值（保留）

- P_empirical_mean：N_train=4096/动作（动作级经验均值，忽略 x）；独立 eval X=4096；R=20（20261901–20）；真值解析。
- **full：mean .22625306，95% CI [.22094996, .23155615]**；**constrained：mean .15141651，95% CI [.15007466, .15275836]**；均 **≥.10** → **executable**；**未重设环境**。

## 3. 六比较/Holm/执行/边界（保持）

- primary candidate vs P_empirical_mean；secondary P_max_entropy/P_conditional_density_MC/P_constrained_SB/P_random/P_softmax_expected_reward；D=regret_cand−regret_base<0；δ=.05；Holm family=6、单侧下尾；raw/paired 分存；CI replicate≥20；等价审计（与 empirical-mean/max-entropy 等价→no increment）。
- seeds：headroom 20261901–20；执行 data 20261921/eval 20261922/cells 20261931–54；overlap=[]；两跑逐字节；caps 1800 s/2 h/8 GB/0 wells；pilot 实测冻结；schema/11 失败/停止写死。
- 边界：机制账 only；不训练 C-MDN/不运行候选/不报效果；不改旧判定；不称药理/真实决策/迁移/机制/新颖性；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 4. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2C_v0_2.md` | `见 usage_m1_s2c_prereg_v0_2.json` |
| `DESIGN_M1_S2C_v0_2.md` | `见 usage_m1_s2c_prereg_v0_2.json` |
| `headroom_design_m1_s2c_v0_2.py` | `40F44DD4EBDFB187E5E388E639B7552094BEB464A10CD8C540A3FEE92070D5B1` |
| `headroom_design_m1_s2c_v0_2.json` | `89C3586B596013A23651C768913BB84A41EA33B2DA00718BA590B21375013741` |
| `schema_m1_s2c_v0_2.json` | `4DCFE96B516AFEB6222145F081B90453079C9208EF4DEC23ED8192BB8A9668EF` |
| report/record/usage | 见 `usage_m1_s2c_prereg_v0_2.json` |

**确定性**：`headroom_design_m1_s2c_v0_2.json` 两跑逐字节一致；JSON 无 telemetry；headroom wall≈3.4–3.6 s 仅 usage/报告。

## 5. 建议

1. **建议轻量复核**：stop_conditions[0] 是否与 requirement（≥.10）完全一致；schema `headroom_required/decision_rule/stop_category` 是否可判；headroom 语义（设计期、未用候选结果）是否写清；headroom 值/六比较/δ/Holm/CI/seeds/caps/失败/边界是否保持。
2. 复核通过 + Lead 批准后才可执行 **M1-S2c 候选规划比较**（执行时才训练/规划；本任务不运行）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练 C-MDN/运行候选/效果/代码晋升/旧判定修改；不把 H1b 密度通过写成旧 H1 通过；不把一步投影写成 M1 增量。
