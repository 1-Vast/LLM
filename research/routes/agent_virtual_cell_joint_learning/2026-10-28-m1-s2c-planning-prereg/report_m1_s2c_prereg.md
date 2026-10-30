# report_m1_s2c_prereg —— R204-M1-S2c 规划价值检验预注册报告（先 headroom；不运行候选）

2026-10-28。对象：R204-M1-S2c 规划价值检验预注册。依据：C208（一步投影撤）、C216（旧 H1 0/16）、C217（floor 归因）、C222（H1b 16/16 密度可分辨）、C220/C221 合同纠正、M1 Stage2 v0.2、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C208/C209/C213/C215/C216/C217/C220/C221/C222。
**状态：预注册草案；仅设计期 headroom（冻结真值）；未训练 C-MDN、未运行候选规划、未报效果、未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 交付物

- 问题定义：[PROBLEM_M1_S2C.md](PROBLEM_M1_S2C.md)（`5F4E690C…`）
- 执行设计：[DESIGN_M1_S2C.md](DESIGN_M1_S2C.md)（`E1030AB4…`）
- headroom 设计：[headroom_design_m1_s2c.py](headroom_design_m1_s2c.py)（`E45B1231…`）→ [headroom_design_m1_s2c.json](headroom_design_m1_s2c.json)（`1C8B64A4…`）
- schema：[schema_m1_s2c.json](schema_m1_s2c.json)（`FD5A2774…`）
- 记录/用量：[record_m1_s2c_prereg.md](record_m1_s2c_prereg.md)、[usage_m1_s2c_prereg.json](usage_m1_s2c_prereg.json)

## 1. 旧/新分离（写死）

- **C216 旧 H1 0/16 FAIL、`design_invalid: projection` 不变**；**C217 归因不变**；旧容差/判定不改。
- **H1b（C222）16/16 PASS 仅表示密度近似可分辨**，不是旧 H1 通过；不改变 C216/C217。
- **M1 一步投影主张仍撤（C208）**；本实验不写 M1 增量；不称药理/真实决策/迁移/机制/新颖性。

## 2. 设计期 headroom（先于候选）

- 冻结环境：Pθ 同 H1b（c .5²/M .1²/d .1²、σ=.1+.4sigmoid(dᵀx)、box[-2,2]^4、K=3/[.5,.3,.2]）；X~N(0,I_d)，主 d=64；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；π0 full/constrained；规划 MC S=4096/动作；known-truth 独立解析截断正态矩（高精度）。
- baseline planner **P_empirical_mean**：每合法动作 N_train=4096 合成样本估计动作级经验平均 reward（忽略 x）；独立 eval X（N_eval=4096）；R=20 replicate（20261901–20）；真值解析。
- **结果**：

| π0 | mean baseline regret | 95% CI(t₁₉) | chosen actions |
|---|---|---|---|
| **full（主）** | **0.22625306** | **[0.22094996, 0.23155615]** | {1,3} |
| constrained（敏感性） | **0.15141651** | **[0.15007466, 0.15275836]** | {1} |

- **gate：mean baseline regret ≥ 2δ=0.10**；两 π0 均满足 → **executable**；**未重设环境**（无需 redesign）；**不降 δ/不换 seed/不换环境救结果**。若未来 headroom<0.10，在未见候选结果前重设并冻结或 `unreachable_gate` 停止。

## 3. 六比较族/Holm/分析

- **Primary**：candidate vs **P_empirical_mean**；secondary：P_max_entropy、P_conditional_density_MC、P_constrained_SB、P_random、P_softmax_expected_reward。
- **D_j=regret_candidate−regret_baseline_j**；改善 D<0；δ=**0.05**；**统一 Holm（family=6）、单侧下尾**；primary 成功=mean D≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05。
- **raw regret 与 paired D 分开保存**；CI 按独立 replicate（R≥20，cluster=replicate）；**不用规划 MDE 当已证功效**；target 样本不作标签；不把 H1b 密度通过当规划价值。
- **等价审计**：candidate 与 P_empirical_mean/P_max_entropy 动作逐点相同/单调/解析覆盖→登记 equivalence、停止增量主张；标准方法等预算复制/超过→no_increment/撤。

## 4. 执行 seeds/两跑/预算/schema/失败/停止

- **headroom seeds** 20261901–20（已用）；**执行 seeds** 数据 **20261921**、eval **20261922**、cell seeds **20261931–20261954**（24 个）；与 H1b/C216/C217/旧集 disjoint（overlap=[]）；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- caps **1800 s/2 h/8 GB/0 wells**；执行前**最终实现 pilot 实测并冻结 canonical timing**；schema/失败模板先写；JSON 无 telemetry。
- **失败类别**：`design_invalid: projection|calibration|leakage|unreachable_gate|equivalence|precision_insufficient|two_run_mismatch|chain_mismatch|compute_budget_exceeded`、`no_increment`、`inconclusive`。
- **停止**：headroom<0.10→不运行；等价→no increment；CI 无法排除 0 或 −δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定。
- 本任务**不训练 C-MDN/不运行候选规划/不报效果**。

## 5. 边界

机制账 only；合成 compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；执行须另立独立挑战+Lead 批准。

## 6. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2C.md` | `5F4E690C05DFD80F2922F5F4CB859AD5F86E284A3BE8B49A734CB138EDF4DDF3` |
| `DESIGN_M1_S2C.md` | `E1030AB49F689AD85E09EC837B0E477C24A9715AC625EFCA68801A7AA6F71ECD` |
| `headroom_design_m1_s2c.py` | `E45B123100846415F45074DD48E2E7B4E0B3E1375C27E57B027C2FC6E9B6BCC2` |
| `headroom_design_m1_s2c.json` | `1C8B64A49C969A3EFBF87CF1C9E8419B6B99063DBABB062FAB96D4B5B8634A4C` |
| `schema_m1_s2c.json` | `FD5A2774C94F79A4F17A0A8AB68559B7D29D3AFDCC90EC98871E049AC66880C1` |
| report/record/usage | 见 `usage_m1_s2c_prereg.json` |

**确定性**：`headroom_design_m1_s2c.json` 两跑逐字节一致；JSON 无 telemetry；headroom wall≈3 s 仅记录在 usage/报告。

## 7. 建议

1. **提交独立挑战**：重点旧/新分离、headroom 结果（full .22625/CI、constrained .15142/CI，均≥.10，未重设）、六比较/Holm/δ/raw-vs-paired/CI、等价审计、独立 seeds/两跑/caps/schema/失败/停止、边界。
2. 挑战通过 + Lead 批准后才可执行 **M1-S2c 候选规划比较**（执行时才训练/规划；本任务不运行）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练 C-MDN/运行候选/效果/代码晋升/旧判定修改/恢复停止实验；不把 H1b/本实验写成旧 H1 通过。
