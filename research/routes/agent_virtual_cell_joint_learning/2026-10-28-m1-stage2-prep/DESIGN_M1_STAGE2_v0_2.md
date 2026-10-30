# DESIGN_M1_STAGE2_v0_2 —— R204-M1-S2.1 高维近似执行设计（reward/Pθ/近似方法冻结；不运行）

2026-10-28。依据：`PROBLEM_M1_STAGE2_v0_2.md`、`stage2_m1_schema_v0_2.json`、`stage2_m1_plan_v0_2.json`、M1 Stage1（C208：B2 等价→一步投影撤）、M1 v0.2、R203 decision/power、ERRATA C197/C199/C201/C207/C208。
**状态：Stage2 设计/预注册草案；不运行效果/训练/真实数据；机制账 only；compute-only 0 wells；Stage2 执行未批准；Stage3 未执行；不称药理/真实决策/迁移/机制/新颖性。**

## 0. 定位/前置

- Stage1 B2 等价：**一步投影公式撤**；Stage2 只研究高维/未知随机核/受限程序下联合生成推断保持条件药效 + 同预算规划/校准。
- Stage2 执行前置：另立预注册 + 独立挑战 + Lead 批准；当前无执行授权。
- 不报效果/增益/方法比较；真实功能决策在 Stage3，数据当前 `data_unavailable`。

## 1. Reward 有界性（冻结）

- Y 截断到 compact box **[-2,2]^4**；`r(y)=w^T y−λ||y||²`，`w=[.4,.3,.2,.1]`，`λ=.2`。
- **r_max=.375**（y=w/(2λ)）；**r_min=−5.2**（box 顶点）；连续 ⇒ 上下有界。
- `Q_g∝π0Pθ exp(r/τ)`；**归一化有限**；τ∈{.5,1}；**G1/H3 bounded reward 前提成立**；不 clip、不把无界核当有界。
- target Q 归一化用 tensor Gauss-Legendre **64 nodes/dim**；固定规则。

## 2. Pθ 唯一生成器（冻结）

- X~N(0,I_64)；A=4；Y∈[-2,2]^4；**唯一 3 分量截断 GMM、对角协方差、条件异方差**；**无 Student-t 选项**。
- K=3；权重 [0.5,0.3,0.2]；param_seed **20261201**；train_seed **20261202**（N=4096）；eval_seed **20261203**（N=2048）。
- 参数：`c~N(0,.5²)` (4,3,4)；`M~N(0,.1²)` (4,3,4,64)；`d~N(0,.1²)` (4,3,64)。
- `μ_{a,k}(x)=c+Mx`；`σ_{a,k}(x)=.1+.4·sigmoid(d^T x)`；对角协方差 `σ²I`。
- 截断：`Z(x,a)=Σ_k w_k Π_j[Φ((2−μ_j)/σ)−Φ((−2−μ_j)/σ)]`；`Z>0`；`Pθ=ΣwN/ Z`；target Q 由 `Pθ exp(r/τ)` 归一化。
- **H1/H2/H3 同一生成器**；target 样本不作标签；Doob 非可执行药物。

## 3. Stage2 候选 C-MDN（冻结）

- 条件混合密度网络：K=3 logits + 均值4 + 对角 log-scale4；hidden 128、2 层 ReLU；截断支持。
- 训练：NLL；Adam lr=1e-3、weight_decay=1e-5、batch=256、epochs=200；不把 target 样本作标签。
- 规划：候选核采样 4096/动作；合法动作集；target-weighted action score；**不声称一步投影**；不作效果/增益主张。
- 复杂度：训练 O(train_N d H)、规划 O(eval_N A S d)，H=128、S=4096。
- **不做方法比较**；Stage2 只做近似/校准/规划诊断。

## 4. H1/H2/H3（冻结容差；执行预注册前）

### H1 近似随 d/N

- d∈**[8,16,32,64]**（X 前 d 维）；N∈**[512,1024,2048,4096]**（train 前 N 行）；eval 2048/seed 20261203。
- 指标：**256-bin（4 bins/Y 维）histogram TV**。
- **容差表 TV max**：
  | d | 512 | 1024 | 2048 | 4096 |
  |---|---|---|---|---|
  | 8 | .12 | .10 | .08 | .07 |
  | 16 | .14 | .11 | .09 | .08 |
  | 32 | .16 | .13 | .11 | .10 |
  | 64 | .18 | .15 | .13 | .12 |
- 超容差→`design_invalid: projection`；**不得执行中放宽**。

### H2 Sinkhorn/constrained SB

- log-domain Sinkhorn；ε∈**[.1,.25,.5,1,2]**；max iter **2000**；marginal tol **1e-8**。
- 至少一个 ε 收敛；否则 `design_invalid: projection`。
- 固定约束：action marginal=π0；target outcome marginal=Q_g 的 y 边际；不实现成另一错误目标条件化。

### H3 exact small-case oracle

- 小例：d_X=2、A=2、Y=2；同截断 GMM 族。
- oracle：tensor Gauss-Legendre **128 nodes/dim** 精确 target Q/action。
- 候选 C-MDN 拟合；指标：候选 target-action 分布 vs 精确 oracle 的 **TV**（256 eval x）；容差 **TV≤.05**。
- 仅规划质量诊断；**不报 effect/gain**。

## 5. 保留检查/校准

- G1 条件药效保持；G2 支持/程序；G4 无泄漏；G5 两跑；G6 schema/预算。
- G3 近似/投影；H1/H2/H3。
- 校准：条件药效保持（目标前后 Pθ 不变/样本不作标签）、支持/程序、近似/投影误差、无泄漏、两跑/schema/预算。
- 失败：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止：标准控制复制→撤；目标改 Pθ→calibration；无支持→support；Sinkhorn/近似不收敛→projection；无合格功能/功效→停。

## 6. 等预算对照（仅规格）

B1 random MPC；B2 max-entropy；B3 conditional density+MC；B4 constrained SB；B5 same-info DF。同数据/物理反馈/信息集/cap/调参≤20/合法实验包；target 样本不作标签；标准控制等预算复制/超过/解析等价→`rename_maxent`/撤；不得只比错误目标条件化。**不执行比较**。

## 7. Stage3 主端点（不执行）

独立功能决策效用/后悔；δ=.05；headroom/MDE；cluster=独立培养/背景/任务；**6,282/1,573 仅 Fisher-z**；当前 data_unavailable；Stage3 另立预注册+挑战+Lead；不得用合成/RNA 替代。

## 8. 预算/边界/骨架

- caps **1800 s/2 h/8 GB/0 wells**；两跑逐字节；JSON 无 telemetry；超限→`design_invalid: compute_budget_exceeded`。
- `stage2_m1_plan_v0_2.py` 仅规划/单测/计时：reward 边界、生成器形状、截断质量、seed、Sinkhorn、内存；**不训练/不比较/不读真实数据**。
- Stage2 执行未批准；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX。
- **一步投影已撤**；B2 等价是 rename_maxent 证据，不是 M1 增量；M1 不与 M2/M3 混同；N1 no_increment 不作 M1 Stage2 证据。
