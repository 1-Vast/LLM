# R204-M1 S2c.1 轻量复核（task-197）：v0.2 headroom 阈值统一

2026-10-28。角色：同一独立挑战者（非提案者、未参与 S2c、不训练 C-MDN/不运行候选规划/不读真实数据）。对象：[PROBLEM_M1_S2C_v0_2.md](PROBLEM_M1_S2C_v0_2.md)（SHA `2692C4FB…`）、[DESIGN_M1_S2C_v0_2.md](DESIGN_M1_S2C_v0_2.md)（`FFC3A13C…`）、[headroom_design_m1_s2c_v0_2.py](headroom_design_m1_s2c_v0_2.py)（`40F44DD4…`）、[headroom_design_m1_s2c_v0_2.json](headroom_design_m1_s2c_v0_2.json)（`89C3586B…`）、[schema_m1_s2c_v0_2.json](schema_m1_s2c_v0_2.json)（`4DCFE96B…`）、report/record/usage、C216/C217/C222 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_exec_v0_2_to_lead（仅批准 M1-S2c 候选规划比较执行：机制账、compute-only、0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**

v0.2 已修掉 v0.1 的 headroom 门槛矛盾：
- **stop_conditions[0]** 已改为 **`headroom<2*delta (=0.10) -> before seeing candidate results: redesign and freeze environment, or design_invalid: unreachable_gate stop; do not execute`**；与 `headroom_design.requirement=mean baseline regret >=2δ=.10`、`redesign_rule if<.10` 完全一致；**未降为 .05** ✓。
- **schema/JSON 可判字段齐全**：`headroom_required=0.10`、`headroom_decision_rule`、`headroom_stop_category="design_invalid: unreachable_gate"`、`headroom_measured_design_time_before_candidate=true`、`no_candidate_results_used_for_headroom=true`（在 `headroom_design`/schema；顶层另有同名 null 但可判字段已在 headroom_design/schema）✓。
- **headroom 语义**：候选未见前设计期实测；本轮未重设环境；未来重设须在候选结果前记录冻结；不得用候选结果反选 ✓。
- **保持项**：旧/新分离（C216 0/16 projection、C217、H1b 16/16 仅密度、C208 一步投影撤）；冻结环境/Pθ；六比较/Holm family6/δ=.05/raw-paired/CI R≥20/等价审计；seeds 20261901–54（overlap=[]）；两跑/caps 1800s/2h/8GB/0 wells/schema/11 失败/边界；**headroom full .22625306 CI [.22094996,.23155615]、constrained .15141651 CI [.15007466,.15275836]** 保留 ✓。
- **边界**：机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only ✓。

**结论：可提交 Lead 批准 M1-S2c 候选规划比较执行（机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 阈值统一 | **PASS** | `stop_conditions[0]="headroom<2*delta (=0.10) -> ... unreachable_gate; do not execute"`；与 requirement `.10`/redesign_rule `<.10` 一致；未降 .05 ✓。 |
| ② | schema/JSON 可判字段 | **PASS** | `headroom_required=.10`、`headroom_decision_rule`、`headroom_stop_category`、`headroom_measured_design_time_before_candidate=true`、`no_candidate_results_used_for_headroom=true`；schema/JSON/stop_conditions 同步；执行器按 .10 ✓。 |
| ③ | headroom 语义 | **PASS** | 设计期实测、候选未见前；本轮未重设；未来重设须候选前记录冻结；不得候选结果反选 ✓。 |
| ④ | 保持项 | **PASS** | 旧/新分离；冻结环境/Pθ；六比较/Holm6/δ=.05/raw-paired/CI R≥20/等价审计；seeds 20261901–54 overlap=[]；两跑/caps/schema/11 失败/边界；headroom full .22625306 CI [.22094996,.23155615]、constrained .15141651 CI [.15007466,.15275836] ✓。 |
| ⑤ | 边界 | **PASS** | 机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only ✓。 |
| ⑥ | 总判决 | **approve_exec_v0_2_to_lead** | 仅 S2c 候选规划比较；不批真实数据/效果。 |

**非阻塞实现备注**：
1. 顶层 `headroom_measured_design_time_before_candidate`/`no_candidate_results_used_for_headroom` 是 `null`，但可判字段已在 `headroom_design`/schema 为 true；执行器应读 `headroom_design.*` 或 schema，不要读顶层 null 误判缺失。
2. `headroom` full/constrained 值/CI 未变；`R_reps=20`；`delta=.05`；`2δ=.10`；`headroom<.10` 必须 stop/redesign，不执行。
3. 六比较/Holm family6/raw-paired/CI R≥20/等价审计保持；执行前 final pilot 实测冻结；caps 1800s/2h/8GB/0 wells。
4. 不把 H1b 密度通过写成旧 H1 通过；不把 C208 一步投影写成 M1 增量。

## 2. Lead M1-S2c 候选规划比较执行批准文本（建议）

> **批准范围**：批准 **M1-S2c 候选规划比较执行**（机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：C216 旧 H1 0/16 `design_invalid: projection`、C217 归因、H1b 16/16 仅密度、C208 一步投影撤；Pθ 同 H1b（c .5²/M .1²/d .1²、σ、box[-2,2]^4、K=3/[.5,.3,.2]、seeds 20261301/02/03）；X d64 主/d16 次、A4、r=wᵀy−λ||y||²、π0 full/constrained、S4096/动作、known-truth 解析；**headroom full .22625306 CI [.22094996,.23155615]、constrained .15141651 CI [.15007466,.15275836]，均≥2δ=.10；headroom<.10→redesign/freeze before candidate 或 `design_invalid: unreachable_gate`，不得执行/降δ/换seed**；六比较（primary candidate vs P_empirical_mean；secondary max-entropy/cond-density-MC/SB/random/softmax-expected-reward）、D<0、δ=.05、Holm family6、单侧下尾、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、raw/paired 分开、CI R≥20/cluster、不把 planning MDE 当已证功效；等价审计；seeds headroom20261901–20/data20261921/eval20261922/cells20261931–54；两跑同 seeds 独立进程/逐字节/telemetry；caps 1800s/2h/8GB/0 wells；final pilot 实测冻结；schema/11 失败/停止；不输出 effect/regret/top-k/方法比较/真实数据。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把 H1b 密度通过写成旧 H1 通过；把 C208 一步投影写成 M1 增量；把 headroom .10 降为 .05；候选结果后重设 headroom；改旧判定/容差；晋升代码；恢复停止实验。

## 3. 声明

- **本轮不训练 C-MDN/不运行候选规划/不读真实数据**：只读 S2c v0.2 预注册/headroom JSON/schema/Stage2 链；只写本文件与 `tmp/`；未改 prereg 产物。
- **总判决：approve_exec_v0_2_to_lead**。stop_conditions .10 与 requirement/redesign 一致、schema 五字段可判、headroom 设计期语义/未重设、headroom 值/六比较/δ/Holm/CI R≥20/seeds/caps/11 失败/边界均核验通过；仅顶层 null 字段读取、headroom 值保持、final pilot、旧/新分离为非阻塞执行备注。仅批准 S2c 候选规划比较执行（机制账/compute-only/0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性。

**一句话：v0.2 已把 stop_conditions[0] 统一为 headroom<2δ=.10→redesign/unreachable_gate（不再 .05），schema/JSON 五字段可判，headroom full .22625306/constrained .15141651 与 CI、六比较/Holm6/δ=.05/raw-paired/CI R≥20/seeds/caps/11 失败/边界均保持——判 approve_exec_v0_2_to_lead（仅 M1-S2c 候选规划比较执行：机制账/compute-only/0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**
