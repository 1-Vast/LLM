# record_m1_s2c_prereg.md —— R204-M1-S2c 预注册执行记录（headroom 设计；不运行候选）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-194（R204-M1-S2C-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-m1-s2c-planning-prereg/` 与 `tmp/`；**未改 H1b/C216/C217/M1 设计链/M2/M3/N1/A-B-D 产物**；**未训练 C-MDN/未运行候选规划/未报效果/未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 分离（旧 H1/C216 不变、H1b 仅密度、一步投影撤、不称药理等） | ✅ PROBLEM §0：C216 0/16/design_invalid 不变；C217 归因不变；H1b 16/16 仅密度可分辨；一步投影仍撤；无药理/真实决策/迁移/机制/新颖性 |
| ② 冻结环境 | ✅ Pθ 同 H1b（c .5²/M .1²/d .1²、σ、box[-2,2]^4、K=3/[.5,.3,.2]、seeds 20261301/02/03）；X d=64 主/d=16 次级；A=4；r=wᵀy−λ||y||²、w=[.4,.3,.2,.1]、λ=.2、τ=1；π0 full/constrained；规划 MC 4096/动作；known-truth 解析高精度 |
| ③ 设计期 headroom（先于候选） | ✅ P_empirical_mean（N_train=4096/动作、忽略 x）在独立 eval X（4096）上 R=20；真值解析；**full mean .22625306 CI[.22094996,.23155615]，constrained .15141651 CI[.15007466,.15275836]**；均 ≥2δ=.10 → executable；未重设环境；不降 δ/换 seed |
| ④ 六比较族/Holm/分析 | ✅ primary candidate vs P_empirical_mean；secondary 5 个；D<0、Family=6 统一 Holm、单侧下尾、δ=.05；raw regret 与 paired D 分存；CI 按独立 replicate（R≥20，cluster=replicate）；不用规划 MDE 当功效 |
| ⑤ 等价审计 | ✅ candidate 与 P_empirical_mean/P_max_entropy 动作逐点/单调/解析覆盖→equivalence/no increment；标准方法等预算复制/超过→no_increment/撤 |
| ⑥ 独立 seeds/两跑/caps/schema/失败 | ✅ headroom 20261901–20；执行 data 20261921/eval 20261922/cells 20261931–54；overlap=[]；两跑同 seeds/逐字节/telemetry 单独；caps 1800/7200/8GB/0 wells；schema 先写；失败类别 11；final pilot 冻结要求 |
| ⑦ 停止条件 | ✅ headroom<δ→不运行；等价→no increment；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定 |
| ⑧ 输出 report/record/usage+schema+headroom；标 completed+send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~16:12 | 读 task-194 并 claim；读 C222/H1b/C216/C217/C220/C221、M1 Stage2 v0.2、corrections |
| ~16:18 | 写 `headroom_design_m1_s2c.py`（冻结 Pθ 采样/解析真值、P_empirical_mean headroom、六比较/Holm/equivalence/seeds/schema） |
| ~16:22 | 首跑 analytic 真值出现 NaN（极端截断概率下溢）→ 改 log-space/mask；重跑 headroom：full .22625、constrained .15142，均≥.10；main 设为 full；两跑逐字节一致 |
| ~16:26 | 写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做设计期 headroom**：冻结 Pθ；P_empirical_mean（N_train=4096/动作、动作级经验均值、忽略 x）在独立 eval X（4096）上的 baseline regret；真值用 **解析截断正态矩**（高精度，不复用训练/验证样本）；R=20 replicate。
2. **headroom 结果**：full **.22625306**（CI .22094996–.23155615）、constrained **.15141651**（CI .15007466–.15275836）；均 ≥2δ=.10；**未重设环境**；decision=executable；**不降 δ/不换 seed**。
3. **六比较族**：primary candidate vs P_empirical_mean；secondary P_max_entropy/P_conditional_density_MC/P_constrained_SB/P_random/P_softmax_expected_reward；D=regret_cand−regret_base<0；Holm family 6、单侧下尾、δ=.05；raw/paired 分存；CI replicate。
4. **等价审计**：与 empirical-mean/max-entropy 逐点/单调/解析覆盖→equivalence/no increment。
5. **执行 seeds**：20261921/22、cells 20261931–54；headroom 20261901–20；overlap=[]；两跑逐字节；caps 1800/7200/8GB/0 wells；schema/失败/停止写死。
6. **确定性**：`headroom_design_m1_s2c.json`（`1C8B64A4…`）两跑逐字节一致；JSON 无 telemetry；headroom wall≈3 s 仅 usage/报告。
7. **边界**：机制账 only；未训练 C-MDN/未运行候选/未读真实数据；不改旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- headroom（设计期，先于候选）：full **.22625306** CI [.22094996,.23155615]；constrained **.15141651** CI [.15007466,.15275836]；均≥.10 → 可执行；未重设环境。
- baseline：P_empirical_mean（动作级经验均值、N_train=4096/动作、忽略 x）；eval X 独立 4096；R=20；真值解析截断正态矩。
- 六比较族/Holm 6/δ=.05/raw-vs-paired/CI replicate；等价审计；seeds 20261921+；caps/schema/失败/停止。
- 无 C-MDN/无候选规划/无效果；本轮仅 headroom+预注册。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2C.md` | `5F4E690C05DFD80F2922F5F4CB859AD5F86E284A3BE8B49A734CB138EDF4DDF3` |
| `DESIGN_M1_S2C.md` | `E1030AB49F689AD85E09EC837B0E477C24A9715AC625EFCA68801A7AA6F71ECD` |
| `headroom_design_m1_s2c.py` | `E45B123100846415F45074DD48E2E7B4E0B3E1375C27E57B027C2FC6E9B6BCC2` |
| `headroom_design_m1_s2c.json` | `1C8B64A49C969A3EFBF87CF1C9E8419B6B99063DBABB062FAB96D4B5B8634A4C` |
| `schema_m1_s2c.json` | `FD5A2774C94F79A4F17A0A8AB68559B7D29D3AFDCC90EC98871E049AC66880C1` |
| report/record/usage | 见 `usage_m1_s2c_prereg.json` |
| 只读引用（未改） | H1b `h1b_result.json` `2ECA912B…`；C216 `m1_stage2_rerun.json` `B2CD0195…`；C217 `diag_m1_s2.json` `6FBD1016…` |

## 5. 缺口与下一步

- **S2c 尚未执行**（本任务仅 headroom 设计）；执行时训练候选/规划/六比较；须另立独立挑战+Lead 批准。
- 执行前：重核冻结链/headroom、最终实现 pilot 实测冻结、两跑/schema/失败模板核验；不改旧判定。
- 机制账 only；不晋升代码/不改旧判定/不恢复停止实验。
