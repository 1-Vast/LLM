# R204-M1 S2c 规划价值预注册独立挑战（task-195）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 S2c、不训练 C-MDN/不运行候选规划/不读真实数据）。对象：[PROBLEM_M1_S2C.md](PROBLEM_M1_S2C.md)（SHA `5F4E690C…`）、[DESIGN_M1_S2C.md](DESIGN_M1_S2C.md)（`E1030AB4…`）、[headroom_design_m1_s2c.py](headroom_design_m1_s2c.py)（`E45B1231…`）、[headroom_design_m1_s2c.json](headroom_design_m1_s2c.json)（`1C8B64A4…`）、[schema_m1_s2c.json](schema_m1_s2c.json)（`FD5A2774…`）、report/record/usage、C216/C217/C222 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_to_lead；也不是 stop）。**

核验 PASS：
- **分离**：C216 旧 H1 **0/16 FAIL/design_invalid: projection 不变**；C217 归因不变；H1b **16/16 仅密度可分辨、不是旧 H1 通过**；一步投影仍撤（C208）；不称药理/真实决策/迁移/机制/新颖性 ✓。
- **冻结环境**：Pθ 同 H1b（c .5²/M .1²/d .1²、σ=.1+.4sigmoid(dᵀx)、box[-2,2]^4、K=3/[.5,.3,.2]、seeds 20261301/02/03）；X d=64 主/d=16 次；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2、τ=1）；π0 full/constrained；S=4096/动作；known-truth 独立解析截断正态矩、不复用训练/验证 ✓。
- **设计期 headroom**：P_empirical_mean（每动作 N_train=4096 动作级经验平均 reward、忽略 x；eval X=4096；R=20；真值解析）；full mean baseline regret **.22625306 CI [.22094996,.23155615]**；constrained **.15141651 CI [.15007466,.15275836]**；均≥2δ=.10→executable、未重设环境；redesign_rule `<.10` 写死、不降 δ/不换 seed ✓。
- **六比较/Holm**：primary candidate vs P_empirical_mean；secondary max-entropy/conditional-density-MC/SB/random/softmax-expected-reward；D<0、δ=.05、统一 Holm family=6、单侧下尾；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；raw regret 与 paired D 分开；CI 按独立 replicate R≥20、cluster=replicate；不用规划 MDE 当已证功效 ✓。
- **等价审计**：candidate 与 P_empirical_mean/P_max_entropy 动作逐点相同/单调/解析覆盖→equivalence、停止增量；标准等预算复制/超过→no_increment/撤 ✓。
- **执行/seeds/caps/schema/失败**：headroom 20261901–20；data 20261921、eval 20261922、cells 20261931–54；与旧集 disjoint；两跑同 seeds 独立进程逐字节、telemetry 单独；caps 1800s/2h/8GB/0 wells；final pilot 实测冻结；schema 先写；11 失败类别；停止条件 ✓。
- **边界**：机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only ✓。

**但预注册的停止条件与 headroom 要求直接矛盾：**
- `headroom_design.requirement = mean baseline regret >= 2δ = 0.10`，`redesign_rule = if <0.10: redesign/freeze before candidate or unreachable_gate stop`；
- 但 `stop_conditions[0] = "headroom<delta -> do not run"`，即 **<0.05 才停**。
- **若未来 headroom 落在 [0.05,0.10)**，按 `stop_conditions` 会**继续执行**，违反 `requirement` 的 **2δ=.10** 门槛，也违反任务 ③“均≥2δ=.10→executable；<0.10 重设或 unreachable_gate”。这是预注册门槛的实质性不一致，必须在执行前统一。

**结论：先修 §2 的 1–2，再提交 Lead 批准 M1-S2c 候选规划比较执行（机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 分离 | **PASS** | C216 0/16 projection 不变；C217 归因不变；H1b 16/16 仅密度；C208 一步投影撤；不称药理/真实决策/迁移/机制/新颖性 ✓。 |
| ② | 冻结环境 | **PASS** | Pθ 同 H1b；X d64/d16；A4；r；π0；S4096；known truth；seeds ✓。 |
| ③ | headroom | **FAIL/PARTIAL** | full .22625306 CI [.22094996,.23155615]；constrained .15141651 CI [.15007466,.15275836]；均≥.10、executable、未重设环境、不降 δ/不换 seed ✓。**但 `stop_conditions` 写 `<delta`（.05），与 requirement/redesign `<2δ`（.10）矛盾**（§0）。 |
| ④ | 六比较/Holm | **PASS** | primary candidate vs P_empirical_mean；5 secondary；D<0、δ=.05、Holm6、单侧；mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；raw/paired 分开；CI R≥20/cluster；不把 planning MDE 当已证功效 ✓。 |
| ⑤ | 等价审计 | **PASS** | candidate 与 P_empirical_mean/P_max_entropy 逐点/单调/解析覆盖→equivalence；标准等预算复制/超过→no_increment/撤 ✓。 |
| ⑥ | 执行/seeds/caps/schema/失败 | **PASS** | headroom 20261901–20；data/eval/cells；两跑；caps；final pilot；schema；11 失败；停止 ✓。 |
| ⑦ | 边界 | **PASS** | 机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；public-only ✓。 |
| ⑧ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **统一 headroom 停止阈值**：把 `stop_conditions[0]` 从 `"headroom<delta -> do not run"` 改为 **`"headroom<2*delta (=0.10) -> redesign/freeze before candidate or unreachable_gate stop"`**；与 `headroom_design.requirement`/`redesign_rule` 完全一致。若未来 full/constrained 任一 headroom<.10，**不得执行**、不得降 δ/换 seed/重设环境后偷跑。
2. **在 schema/headroom JSON 中把 2δ 门槛写成可判字段**：`headroom_required = 0.10`、`headroom_decision_rule`、`headroom_stop_category=design_invalid: unreachable_gate`；`stop_conditions` 同步；避免执行器按 .05 判。
3. **明确 headroom 是“设计期实测”而非“未来候选结果后重设”**：`redesign_rule` 已写 before candidate；报告/JSON 保持“未重设环境”；若需重设，记录在 candidate 未见前并冻结新环境；不得用候选结果反向选 headroom。
4. **保持**：旧/新分离、冻结环境、full/constrained headroom 值/CI、六比较/Holm/δ=.05/raw-paired/CI R≥20、等价审计、seeds/data/eval/cells、两跑/caps/schema/11 失败/边界；不训练/不执行候选规划。
5. **禁止**：把 `.10` 门槛降为 `.05`；把 H1b 密度通过写成旧 H1 通过；把 C208 一步投影写成 M1 增量；改旧判定/容差；真实数据/湿实验；称药理/真实决策/迁移/机制/新颖性。

## 3. 修完后建议的 Lead M1-S2c 候选规划比较执行批准文本（机制账/compute-only/0 wells）

> **批准范围**：在必改 1–2 完成并复核后，批准 **M1-S2c 候选规划比较执行**（机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：C216 旧 H1 0/16 `design_invalid: projection`、C217 归因、H1b 16/16 仅密度、C208 一步投影撤；Pθ 同 H1b（c .5²/M .1²/d .1²、σ、box[-2,2]^4、K=3/[.5,.3,.2]、seeds 20261301/02/03）；X d64 主/d16 次、A4、r=wᵀy−λ||y||²、π0 full/constrained、S4096/动作、known-truth 解析；**headroom full .22625306 CI [.22094996,.23155615]、constrained .15141651 CI [.15007466,.15275836]，均≥2δ=.10；headroom<.10→redesign/unreachable_gate，不得执行/降 δ/换 seed**；六比较（primary candidate vs P_empirical_mean；secondary max-entropy/cond-density-MC/SB/random/softmax-expected-reward）、D<0、δ=.05、Holm family6、单侧下尾、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、raw/paired 分开、CI R≥20/cluster、不把 planning MDE 当已证功效；等价审计；seeds headroom20261901–20/data20261921/eval20261922/cells20261931–54；两跑同 seeds 独立进程/逐字节/telemetry；caps 1800s/2h/8GB/0 wells；final pilot 实测冻结；schema/11 失败/停止；不输出 effect/regret/top-k/方法比较/真实数据。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把 H1b 密度通过写成旧 H1 通过；把 C208 一步投影写成 M1 增量；把 headroom .10 降为 .05；候选结果后重设 headroom；改旧判定/容差；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不训练 C-MDN/不运行候选规划/不读真实数据**：只读 S2c 预注册/headroom JSON/schema/C216/C217/C222 链；只写本文件与 `tmp/`；未改 prereg 产物。
- **总判决：revise**。旧/新分离、冻结环境、headroom 数值/CI、六比较/Holm、等价审计、seeds/两跑/caps/schema/11 失败/边界基本正确；但 **`stop_conditions` 的 `headroom<delta` 与 `requirement/redesign` 的 `2δ=.10` 矛盾**，未来 [.05,.10) 会误执行。修完 1–2 后可提交 Lead 批准 M1-S2c 候选规划比较执行（机制账/compute-only/0 wells）。

**一句话：S2c 预注册的旧/新分离、冻结环境、full .22625306/constrained .15141651 的 headroom 与 CI、六比较/Holm/δ=.05/raw-paired/CI R≥20、等价审计、seeds/两跑/caps/schema/11 失败/边界都核验通过；但 `stop_conditions` 写 `headroom<delta`(.05) 与 `requirement/redesign` 的 `2δ=.10` 直接矛盾，[.05,.10) 会误执行——判 revise：统一 headroom 停止阈值为 .10，再提交 Lead 批准 M1-S2c 候选规划比较执行。**
