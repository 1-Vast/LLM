# report_m1_stage2_rerun —— R204-M1-S2-RERUN 纠正性重跑报告（机制账；不报效果）

2026-10-28 · 角色：独立实现者（endpoint-auditor）。依据：Lead `DECISION_R204_M1_S2_RERUN.md`、冻结 `DESIGN_M1_STAGE2_v0_2.md` / `PROBLEM_M1_STAGE2_v0_2.md`、M1 Stage2 exec prereg、C215。
**状态：纠正性重跑完成；机制账 only；compute-only；0 wells；无 decision utility/regret/top-k/方法比较/效果结论；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；Stage3/真实数据未执行。**

## 0. 判定（一屏）

- **verdict = `design_invalid: projection`**；`status = design_invalid`；**未写 qualification_pass**。
- **H1 0/16 PASS**（16/16 超冻结容差）；**H2 5/5 收敛 PASS**；**H3 TV=0.01340352≤.05 PASS**；**G3 FAIL**；G1/G2/G4/G5/G6 PASS。
- **未改尺度/阈值/顺序/预设救结果**；**上次无效运行（C215）仍为 invalid_run，不作证据**。
- pilot/main 实测 caps PASS；两跑逐字节一致；结果 JSON 无 telemetry。

## 1. 冻结尺度核对（行锚）

| 项 | 冻结值 | 文件/行锚 |
|---|---|---|
| c | `c~N(0,.5²)` | DESIGN_M1_STAGE2_v0_2.md **line 23**；PROBLEM_M1_STAGE2_v0_2.md **lines 31** |
| M | `M~N(0,.1²)` | 同上 |
| d | `d~N(0,.1²)` | 同上 |
| σ | `σ=.1+.4·sigmoid(dᵀx)` | PROBLEM **line 34**；DESIGN line 24 |
| box | `Y∈[-2,2]^4` | PROBLEM **line 28/35** |
| K/权重 | K=3、[.5,.3,.2] | PROBLEM line 29；DESIGN line 21-22 |

**本次执行使用 `.5/.1/.1`**；未使用上次偏离的 `.05/.005/.05`。

## 2. 上次无效运行披露（C215）

- 上次 task-170 结果 SHA `90DE7498C75710CC944A8617D3812F08F728EDC5C97734289533021177422C57`，登记 **`invalid_run: protocol_deviation`**。
- 偏离点：Pθ 尺度使用 `c~N(0,.05²)`、`M~N(0,.005²)`、`d~N(0,.05²)`（10×缩小），与冻结 `.5²/.1²/.1²` 不符；并声称“冻结链只给形状”。
- **该次 H1 16/16、H2、H3、G1–G6、两跑结果全部不得作为证据，未登记 qualification_pass。**
- 本次 corrected rerun 严格按冻结尺度；**未 post-hoc 改尺度**。

## 3. 链核验

- 12 文件 SHA（exec prereg `frozen_inputs`）+ Lead `DECISION_R204_M1_S2_RERUN.md`（`6CF1256C…`）实算 match；`chain.pass=True`；无 `design_invalid: chain_mismatch`。
- Stage1 状态 `no_effect_results`、failed_gates 空；seeds 与禁用集 overlap=[]、unique=true。
- 上次 invalid run 的 SHA 与偏离点已写入结果 `previous_invalid_run`。

## 4. H1（16 格，全部 FAIL）

| d \ N | 512 | 1024 | 2048 | 4096 |
|---|---:|---:|---:|---:|
| 8  | .2197 (> .12) | .1782 (> .10) | .1597 (> .08) | .1284 (> .07) |
| 16 | .2568 (> .14) | .1992 (> .11) | .1504 (> .09) | .1416 (> .08) |
| 32 | .3091 (> .16) | .2554 (> .13) | .2007 (> .11) | .1714 (> .10) |
| 64 | .3667 (> .18) | .2983 (> .15) | .2476 (> .13) | .2041 (> .12) |

- **16/16 FAIL**；H1 容差表、d/N 顺序、eval seed 未改；**未为结果放宽**。
- 说明：corrected frozen scale 下，C-MDN 近似未达到预注册 TV 容差 → `design_invalid: projection`；不是效果/决策结论。

## 5. H2/H3

- **H2 5/5 收敛**：ε=.1→2.0；max marginal error ≤**9.9e-9**≤1e-8；iterations 17–303≤2000；marginal/ε/阈值未改。**PASS**。
- **H3 small-case**：GL **128/dim** oracle；256 eval x；TV **0.01340352≤.05**；**PASS**。
- **H3 仅 small-case**，不是高维 exact oracle；H1 是 16 格高维近似判据。

## 6. G1–G6

| 门 | 结果 | 说明 |
|---|---|---|
| G1 条件药效 | **PASS** | target 样本不作标签；Pθ 不被 target 更新；可执行条件核结构保持 |
| G2 支持/程序 | **PASS** | 4 动作支持；π0 严格正；无 unsupported program |
| G3 近似/投影 | **FAIL** | H1 0/16；H2/H3 pass；失败=projection |
| G4 无泄漏 | **PASS** | train/eval 独立；target 不作标签 |
| G5 两跑 | **PASS** | 两独立进程 result JSON 逐字节 |
| G6 schema/预算 | **PASS** | schema 先写；pilot/main caps PASS |

失败类别：`design_invalid: projection`；未改阈值/端点/seed。

## 7. 执行/预算/两跑

- **final-implementation pilot（2 reps，含 H1 16 C-MDN/Q_g GL64/H3 GL128）**：
  - wall **159.6908 s**（rows 161.7126/157.6689）；CPU **281.2109 s**；memory **0.071407 GB**。
- **main run**：wall **158.0514 s**；CPU **277.0 s**；memory **0.071739 GB**。
- caps **1800 s/2 h/8 GB/0 wells**；**PASS**。
- 两跑 `m1_stage2_rerun.json` 逐字节 **`B2CD01954F88F40111AFC286ECD7B67A45CB57E96B3D95C06E35936447B72107`**；checks/diagnostics 亦一致；timing 单独。
- 结果 JSON 无 telemetry；schema/失败模板先写。

## 8. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `m1_stage2_rerun.json`（两跑一致） | `B2CD01954F88F40111AFC286ECD7B67A45CB57E96B3D95C06E35936447B72107` |
| `m1_stage2_rerun_checks.csv` | `16CE3F959FEB30F923CCA1BD109D1215B5FB2B71D457989BE6531578F080F585` |
| `m1_stage2_rerun_diagnostics.json` | `202124431295B56E4F04D88C5D97D6EC1BE0BE74DD0CB1DF48E62FB9893ECC0E` |
| `schema_m1_stage2_rerun.json` | 见 usage |
| `timing_m1_stage2_rerun.json` | 见 usage；result SHA `B2CD0195…` |
| `run_m1_stage2_rerun.py` / report / record / usage | 见 usage |

## 9. 结论/边界

- **corrected rerun 未通过冻结 H1**；**verdict=`design_invalid: projection`**，**不是 `qualification_pass_frozen_scale`**；**这是近似/校准失败，不是效果/决策/药理/机制结论**。
- **上次 invalid_run 不因本次重跑变为有效**；其 90DE7498… 仍不得作证据。
- **不得改尺度/阈值/顺序/预设重跑救结果**；进一步重跑需另立预注册+独立挑战+Lead 批准。
- Stage3/真实数据未执行；data readiness open（C203/C205/C210/C214）；不得用合成/RNA 替代独立功能决策。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据。
