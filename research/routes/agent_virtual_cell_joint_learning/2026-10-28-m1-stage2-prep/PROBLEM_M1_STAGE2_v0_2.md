# PROBLEM_M1_STAGE2_v0_2 —— R204-M1-S2.1 高维近似设计（reward/Pθ/近似方法冻结；不运行）

2026-10-28。对象：M1 Stage2 高维近似设计。本文件修正 v0.1（`PROBLEM_M1_STAGE2.md`，保留不改），落实 M1-STAGE2-PREP-C1 三项必改：**reward 有界性语义**、**唯一 Pθ 生成器**、**Stage2 候选/近似方法与容差**。
**状态：设计/预注册草案；不运行效果/训练/真实数据；机制账 only；compute-only 0 wells；Stage2 执行未批准；Stage3 未执行。不称药理/真实决策/迁移/机制/新颖性。**

依据：M1 Stage1（C208：B2 等价→一步投影撤）、M1 v0.2、R204 BRIEF/report、R203 decision/power、ERRATA C197/C199/C201/C207/C208。

## 0. 定位（不变）

- Stage1 已检出 **B2 max-entropy 与 π* 解析等价**；`m1_increment_claimed=false`；**一步投影主算法撤回**。
- Stage2 只研究**未验证候选**：高维/未知随机核/受限程序下，联合生成推断能否保持条件药效并以同预算得到规划/校准；**不得写成一步投影增量**。
- M1 不与 M2/M3 混同；N1 no_increment 不作 M1 Stage2 证据。

## 1. Reward 有界性（必改 1；冻结）

- **Y 是 compact box** `Y∈[-2,2]^4`；Pθ 为**截断** GMM（不是无界 GMM/Student-t）。
- **r_g(y)=w^T y−λ||y||²**，`w=[0.4,0.3,0.2,0.1]`，`λ=0.2`。
- 在 compact box 上连续 ⇒ **上下有界**：
  - `r_max=||w||²/(4λ)=0.30/0.8=`**0.375**（y=w/(2λ) 在 box 内）；
  - `r_min=`**−5.2**（box 顶点，w 全正取 y=−2 各维）。
- **target Q_g**：`Q_g∝π0 Pθ exp(r_g/τ)`；`r` 有界 + compact Y ⇒ **归一化常数有限、期望存在**；τ∈{0.5,1.0}。
- **G1/H3 的“有界奖励”前提成立**；不需要 clip，也不把无界 GMM 当有界。
- target Q 的归一化用**tensor Gauss-Legendre 64 nodes/dim**在 box 上计算；这是设计/执行前的固定规则。

## 2. 唯一 Pθ 生成器（必改 2；冻结）

- **X**：`X~N(0,I_64)`；**A=4**；**Y∈[-2,2]^4**。
- **Pθ**：**唯一 3 分量截断 GMM、对角协方差、条件异方差**；**不设 Student-t 选项**。
- **K=3**，混合权重 `[0.5,0.3,0.2]`。
- 参数（param_seed=**20261201**）：
  - `c_{a,k}~N(0,0.5²)` shape (4,3,4)；
  - `M_{a,k}~N(0,0.1²)` shape (4,3,4,64)；
  - `d_{a,k}~N(0,0.1²)` shape (4,3,64)。
- **h(X)**：`μ_{a,k}(x)=c_{a,k}+M_{a,k}x`；**scale** `σ_{a,k}(x)=0.1+0.4·sigmoid(d_{a,k}^T x)`；协方差 `σ² I_4`。
- **截断**：`Pθ(y|x,a)=Σ_k w_k N(y;μ,σ²I)1[y∈box]/Z(x,a)`；`Z(x,a)=Σ_k w_k Π_j[Φ((2−μ_j)/σ)−Φ((−2−μ_j)/σ)]`；`Z>0` 有限。
- **target Q**：同上 `Pθ` + `exp(r/τ)`，用固定 quadrature 归一化；**不是 Doob 可执行药物**。
- **seed/拆分**：param_seed 20261201；train_seed **20261202**（N=4096）；eval_seed **20261203**（N=2048）；**H1/H2/H3 同一生成器**。
- target 生成样本**不作实测标签**；Pθ 只由真实给药更新（Stage3 才可能）。

## 3. Stage2 候选/近似方法（必改 3；冻结）

- **候选 C-MDN**：条件混合密度网络（K=3 分量 logits、均值4、对角 log-scale4；hidden 128、2 层 ReLU）；**截断支持**；训练 NLL，Adam lr=1e-3、weight_decay=1e-5、batch=256、epochs=200。
- **规划器**：从候选核采样 y（4096/动作）；合法动作集；target-weighted action score；**不声称一步投影**；**不作效果/增益主张**。
- **复杂度**：训练 `O(train_N·d·H)`；规划 `O(eval_N·A·S·d)`，H=128、S=4096。
- **H1 近似随 d/N**：
  - d∈**[8,16,32,64]**（取 X 前 d 维，固定前缀）；N∈**[512,1024,2048,4096]**（train 前 N 行，固定 seed）；
  - eval 固定 2048/seed 20261203；指标：**256-bin（4 bins/Y 维）histogram TV**；
  - **预注册容差表**（TV max）：
    | d | N512 | N1024 | N2048 | N4096 |
    |---|---|---|---|---|
    | 8 | .12 | .10 | .08 | .07 |
    | 16 | .14 | .11 | .09 | .08 |
    | 32 | .16 | .13 | .11 | .10 |
    | 64 | .18 | .15 | .13 | .12 |
  - 超容差→`design_invalid: projection`；**Stage2 执行前冻结**。
- **H2 Sinkhorn**：log-domain；ε∈**[.1,.25,.5,1,2]**；max iter **2000**；marginal tol **1e-8**；至少一个 ε 收敛；否则 `design_invalid: projection`。
- **H3 exact small-case**：小例 `d_X=2/A=2/Y=2`，同截断 GMM 族；oracle 用 tensor Gauss-Legendre **128 nodes/dim** 精确 target Q/action；候选 C-MDN 拟合；指标=候选 target-action 分布 vs 精确 oracle 的 **TV**（256 eval x）；容差 **TV≤.05**；仅规划质量诊断，**不作效果**。
- H1/H2/H3 **均未执行**；只做规划/骨架/单测。

## 4. 保留的检查/校准

- **Stage1 保留**：G1 条件药效保持；G2 支持/程序；G4 无泄漏；G5 两跑；G6 schema/预算。
- **Stage2 新增**：G3 近似/投影；H1/H2/H3。
- 校准：条件药效保持（目标前后 Pθ 不变/样本不作标签）、支持/程序、近似/投影误差、无泄漏、两跑/schema/预算。
- 失败类别：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 5. 等预算对照（仅规格）

B1 random MPC；B2 max-entropy；B3 conditional density+MC；B4 constrained SB；B5 same-info DF。同数据/物理反馈/信息集/cap/调参≤20/合法实验包；target 样本不作标签；标准控制等预算复制/超过/解析等价→`rename_maxent`/撤；不得只比错误目标条件化。

## 6. Stage3 主端点（不执行）

独立功能决策效用/后悔；**δ=.05 normalized**；headroom/MDE 先检；cluster=独立培养/背景/任务；**6,282.1038/1,572.7759 仅 Fisher-z**；非整数、非门、非 paired DR；当前 **data_unavailable（C203/C205）**；不得用合成/RNA 替代；Stage3 另立预注册+挑战+Lead。

## 7. 预算/边界

- 合成 compute-only 0 wells；caps **1800 s/2 h/8 GB/0 wells**；两跑逐字节；JSON 无 telemetry；失败只写类别不报效果。
- **不运行 Stage2/3/训练/真实数据**；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX。
- **一步投影已撤**；B2 等价是 rename_maxent 证据，不是 M1 增量；Stage2 执行须另立预注册+独立挑战+Lead 批准。

## 8. 可执行骨架（仅规划）

`stage2_m1_plan_v0_2.py`：reward 边界/生成器形状/截断质量/seed/Sinkhorn/内存单测 + pilot 计时；不训练/不比较/不读真实数据。Stage2 实际执行未批准。
