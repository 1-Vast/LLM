# report_m1_stage2_prep_v0_2 —— R204-M1-S2.1 三项必改落实报告（设计；不运行）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者（endpoint-auditor）。
**状态：M1-STAGE2-PREP-C1 三项必改已落实；仅设计/规划/结构单测/计时；不运行效果/训练/真实数据；机制账 only；compute-only 0 wells；Stage2 执行未批准；Stage3 未执行；不称药理/真实决策/迁移/机制/新颖性。**

依据：M1 Stage1（C208：B2 等价→一步投影撤）、M1 v0.2、R204 BRIEF/report、R203 decision/power、ERRATA C197/C199/C201/C207/C208。v0.1 产物保留不改。

## 1. 三项必改落实

| # | C1 必改 | v0.2 落点 | 状态 |
|---|---|---|---|
| 1 | **reward 有界性矛盾** | Y 冻结为 **compact box [-2,2]^4**，Pθ 为**截断** GMM；`r=w^T y−λ||y||²` 在 box 上连续 ⇒ **r_max=.375、r_min=−5.2**；target Q 归一化有限、期望存在；G1/H3 bounded-reward 前提成立；不 clip、不把无界核当有界 | PASS |
| 2 | **Pθ 生成器未冻结** | **唯一 3 分量截断 GMM、对角协方差、条件异方差**（无 Student-t 选项）：c/M/d 参数形状、h(X)、σ(X)、截断、Z、target Q quadrature、param/train/eval seeds、N 全部写死；H1/H2/H3 同一生成器 | PASS |
| 3 | **Stage2 候选/近似方法未定义** | 候选 **C-MDN**（K=3、hidden 128、训练/规划/复杂度）；**H1 d/N 子采样+TV 容差表**；**H2 ε 网格/迭代/收敛**；**H3 exact small-case oracle/planning quality 指标/容差**全部冻结 | PASS |

## 2. Reward 有界性（冻结）

- `w=[.4,.3,.2,.1]`、`λ=.2`、Y∈[-2,2]^4；连续函数在 compact 上**上下有界**。
- **r_max=.375**（y=w/(2λ)）；**r_min=−5.2**（box 顶点）；v0.2 单测观测 min=-5.2、max=.3663≤.375；bounded PASS。
- `Q_g∝π0Pθexp(r/τ)`；τ∈{.5,1}；归一化与期望有限；**G1/H3 前提成立**；target Q 用 tensor Gauss-Legendre 64 nodes/dim 归一化。
- 不 clip；不把无界 GMM/Student-t 当有界。

## 3. Pθ 唯一生成器（冻结）

- X~N(0,I_64)、A=4、Y∈[-2,2]^4；**唯一 3 分量截断 GMM、对角协方差、条件异方差**。
- K=3、权重 [.5,.3,.2]；param_seed **20261201**；train_seed **20261202** N=4096；eval_seed **20261203** N=2048。
- `c~N(0,.5²)` (4,3,4)；`M~N(0,.1²)` (4,3,4,64)；`d~N(0,.1²)` (4,3,64)。
- `μ=c+Mx`；`σ=.1+.4·sigmoid(d^T x)`；对角协方差；截断到 box；`Z(x,a)>0` 有限；`Pθ=ΣwN/Z`。
- target Q 由 `Pθ exp(r/τ)` 归一化；Doob 非可执行药物；target 样本不作标签。
- 单测：形状 PASS、截断质量 finite/positive、seed 可复现；**H1/H2/H3 同生成器**。

## 4. Stage2 候选/近似方法（冻结）

- **C-MDN**：条件混合密度网络；K=3 logits + 均值4 + 对角 log-scale4；hidden 128、2 层 ReLU；截断支持。
- 训练：NLL；Adam lr=1e-3、weight_decay=1e-5、batch=256、epochs=200。
- 规划：候选核采样 4096/动作；合法动作集；target-weighted score；**不声称一步投影**；不作效果/增益。
- 复杂度：训练 O(train_N·d·H)、规划 O(eval_N·A·S·d)，H=128、S=4096。
- **H1**：d∈{8,16,32,64}、N∈{512,1024,2048,4096}；X 前 d 维/train 前 N 行；eval 2048/20261203；256-bin TV；**容差表** d8 .12/.10/.08/.07、d16 .14/.11/.09/.08、d32 .16/.13/.11/.10、d64 .18/.15/.13/.12；超→projection。
- **H2**：log-domain Sinkhorn；ε∈{.1,.25,.5,1,2}；max iter 2000；marginal tol 1e-8；至少一 ε 收敛；否则 projection。
- **H3**：小例 d=2/A=2/Y=2；exact oracle（tensor GL 128/dim）；候选 target-action TV≤.05；仅规划质量诊断，不作效果。
- H1/H2/H3 **未执行**；只规划/结构单测。

## 5. 保留项/等预算/端点/失败/预算

- **一步投影已撤**：Stage1 B2 `rename_maxent_detected=true`、`m1_increment_claimed=false`；不写 M1 增量。
- 保留 G1/G2/G4/G5/G6；G3/H1/H2/H3 新增。
- 等预算：B1 random MPC、B2 max-entropy、B3 conditional density+MC、B4 constrained SB、B5 same-info DF；同数据/信息/反馈/cap/调参≤20；等效→rename_maxent/撤；**不执行比较**。
- Stage3 端点：δ=.05、headroom/MDE/cluster、**6,282/1,573 仅 Fisher-z**；data_unavailable；不执行。
- 失败类别：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- caps 1800 s/2 h/8 GB/0 wells；两跑逐字节；JSON 无 telemetry。

## 6. 骨架/单测/计时

- `stage2_m1_plan_v0_2.py` 仅规划/结构单测/计时；不训练/不比较/不读真实数据。
- 单测 PASS：reward 边界、生成器形状、截断质量、seed、Sinkhorn、内存 cap、H1/H2/H3 冻结。
- 两独立进程 `stage2_m1_plan_v0_2.json` 逐字节 **`73B8C0251A42ED229D5B3BA6D48C367730FD6A284AB47E110E224D56399C1527`**；timing 单独。
- pilot **1.35687e-03 s/rep**；projected **.013569 s**；full wall **.046166 s**；caps 1800s/2h/8GB；0 wells。
- `all_pass=true`、`failure_category=null`；未输出 effect/gain/method comparison。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `stage2_m1_plan_v0_2.json`（两跑一致） | `73B8C0251A42ED229D5B3BA6D48C367730FD6A284AB47E110E224D56399C1527` |
| `stage2_m1_schema_v0_2.json` | 见 usage |
| `timing_m1_stage2_prep_v0_2.json` | 见 usage；result SHA `73B8C025…` |
| `PROBLEM/DESIGN/report/record/usage v0_2` | 见 usage |

## 8. 建议/边界

- 三项必改已修；**建议轻量复核 reward 语义/Pθ 唯一生成器/H1–H3 方法与容差表**；通过后 Lead 可**接受 M1 Stage2 设计**（不执行）。
- Stage2 执行仍须另立预注册+独立挑战+Lead 批准；Stage3 需合格真实功能数据（当前 data_unavailable C203/C205）。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX；**一步投影已撤**；M1 不与 M2/M3 混同；N1 no_increment 不作 M1 Stage2 证据。
