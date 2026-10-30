# PROBLEM_M1_S2C_v0_2 —— R204-M1-S2C.1 规划价值检验预注册（headroom 阈值统一 .10；不运行候选）

2026-10-28。对象：R204-M1-S2c 规划价值检验预注册。本文件修正 v0.1（[PROBLEM_M1_S2C.md](PROBLEM_M1_S2C.md)，保留不改），落实 M1-S2C-C1 必改：**headroom 停止阈值从 "<δ(.05) 停" 统一为 "<2δ=.10 停/重设"**，并补 schema/JSON 可判字段；**不训练 C-MDN、不运行候选规划、不报效果**。依据：C208/C216/C217/C220/C221/C222、H1b/C222、M1 Stage2 v0.2、R204 BRIEF/report。
**状态：预注册修订草案 v0.2；仅设计期 headroom（冻结真值）；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。执行须另立独立挑战+Lead 批准。**

## 0. M1-S2C-C1 必改落实

| # | 矛盾 | v0.2 修正 |
|---|---|---|
| ① **headroom 停止阈值不一致** | v0.1 requirement=mean baseline regret≥2δ=.10，但 `stop_conditions[0]="headroom<δ(.05) -> do not run"`；若 headroom∈[.05,.10) 会继续执行，违反 2δ 门槛 | **`stop_conditions[0]` 改为 "headroom<2*delta (=0.10) -> 在未见候选结果前重设并冻结环境，或 `design_invalid: unreachable_gate` 停止；不执行"**；与 requirement/redesign_rule 完全一致；**不把 .10 降为 .05** |
| ② **schema/JSON 无可判字段** | — | 新增 **`headroom_required=0.10`、`headroom_decision_rule`、`headroom_stop_category="design_invalid: unreachable_gate"`**；schema/JSON/stop_conditions 同步；执行器按 **2δ=.10** 判，不按 .05 |
| ③ **headroom 语义** | — | 明确 headroom 是**候选未见前的设计期实测**；本轮未重设环境；若未来重设，必须在候选结果前记录并冻结新环境；**不得用候选结果反选 headroom** |
| ④ 保持 | — | 旧/新分离（C216/C217/H1b/C208 不变）；冻结环境/Pθ/六比较/Holm/δ=.05/raw-paired/CI R≥20/等价审计/seeds 20261901–54/两跑/caps 1800 s/2 h/8 GB/0 wells/schema/11 失败/边界；**headroom 值保留**（full .22625306 CI [.22094996,.23155615]；constrained .15141651 CI [.15007466,.15275836]） |

## 1. 分离（不变）

- C216 旧 H1 **0/16 FAIL、`design_invalid: projection` 不变**；C217 归因不变；**H1b 16/16 仅密度近似可分辨，不是旧 H1 通过**；**一步投影仍撤（C208）**；不称药理/真实决策/迁移/机制/新颖性；不改旧判定/容差。

## 2. 冻结环境（不变）

- Pθ 同 H1b：c~N(0,.5²)、M~N(0,.1²)、d~N(0,.1²)；σ=.1+.4sigmoid(dᵀx)；Y∈[-2,2]^4；K=3/[.5,.3,.2]；seeds 20261301/02/03。
- X~N(0,I_d)，主 d=64（次级 d=16）；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；π0 full（4 动作均匀）/constrained（仅 {0,1}）；规划 MC S=4096/动作；known-truth 独立解析截断正态矩（高精度，不复用训练/验证）。

## 3. 设计期 headroom（不变；先于候选）

- baseline planner = P_empirical_mean（每合法动作 N_train=4096 合成样本的动作级经验平均 reward，忽略 x）；独立 eval X=4096；R=20（20261901–20）；真值解析。
- **结果**：full **.22625306** CI **[.22094996,.23155615]**；constrained **.15141651** CI **[.15007466,.15275836]**；均 **≥0.10** → **executable**；**未重设环境**。
- **headroom 是设计期实测（候选未见前）**；若未来重设，记录在候选结果前并冻结；不得用候选结果反选。

## 4. 六比较族/Holm（不变）

- Primary：candidate vs **P_empirical_mean**；secondary：P_max_entropy/P_conditional_density_MC/P_constrained_SB/P_random/P_softmax_expected_reward。
- **D_j=regret_candidate−regret_baseline_j**；改善 D<0；δ=**0.05**；统一 **Holm family=6、单侧下尾**；primary 成功=mean D≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05。
- **raw regret 与 paired D 分开保存**；CI 按独立 replicate（R≥20，cluster=replicate）；**不用规划 MDE 当已证功效**；等价审计（candidate 与 empirical-mean/max-entropy 等价→no increment）。

## 5. 执行/预算/失败/停止（阈值已统一）

- **独立 seeds**：headroom 20261901–20；执行数据 **20261921**、eval **20261922**、cell seeds **20261931–20261954**；与 H1b/C216/C217/旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测并冻结 canonical；schema/失败模板先写；JSON 无 telemetry。
- **失败类别 11**：`design_invalid: projection|calibration|leakage|unreachable_gate|equivalence|precision_insufficient|two_run_mismatch|chain_mismatch|compute_budget_exceeded`、`no_increment`、`inconclusive`。
- **停止条件（写死）**：
  1. **headroom<2δ=.10 → 在未见候选结果前重设并冻结环境，或 `design_invalid: unreachable_gate` 停止；不执行**（不得降 .10 为 .05）；
  2. 等价→no increment；
  3. CI 无法排除 0 或 −δ→inconclusive；
  4. 标准方法等预算复制/超过→no_increment/撤；
  5. 超 caps→compute_budget_exceeded；
  6. 任何失败不改旧判定。
- 不训练 C-MDN/不运行候选规划/不报效果（本任务）。

## 6. 边界

机制账 only；合成 compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。
