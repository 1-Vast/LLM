# PROBLEM_M1_S2_EXEC —— R204-M1 Stage2 合成执行预注册草案（仅机制账；不运行）

2026-10-28。对象：R204-M1 Stage2 高维近似（合成执行）。依据：M1 Stage2 v0.2 设计链与 Lead 接受决定（`DECISION_R204_M1_STAGE2_ACCEPT.md` `6EC860D2…`）、M1 Stage1/C208（B2 等价→一步投影撤）、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C208/C209/C210。
**状态：执行预注册草案；未运行 Stage2 训练/效果/真实数据；仅规划/算术/骨架单测；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage2 执行须另立独立挑战 + Lead 批准。**

## 0. 定位与前置

- Stage1（C208）已检出 **B2 max-entropy 与 π* 解析等价**、`m1_increment_claimed=false`；**一步投影主算法主张已撤**。
- Stage2 只研究高维/未知随机核/受限程序下**联合生成近似能否保持条件药效 + 同预算规划/校准**；**不得写成一步投影增量**。
- **M1 不与 M2/M3 混同**；N1 `no_increment` 不作 M1 Stage2 证据；**data readiness 保持 open（C203/C205/C210）**。

## 1. 链核验（执行前；不匹配→stop）

`exec_plan_m1_s2.py` 本地只读核验 **12 文件 SHA**（chain_pass=true、mismatches=0）：
- M1 Stage2 v0.2：PROBLEM `63C0C228…`、DESIGN `642C3108…`、plan py `482E254F…`、json `73B8C025…`、schema `9C4DF027…`、timing `488C8EF6…`、report `BCE5DE11…`、record `CBA86C88…`、Lead 接受决定 `6EC860D2…`；
- M1 Stage1/C208：`m1_stage1.json` `EF701C66…`、report `E3701DA8…`、Stage1 决定 `EEA8CE76…`。
- 不匹配 → `design_invalid: chain_mismatch`、不报结果；执行时重核。

## 2. 执行 seeds（独立；不得复用）

| 用途 | seeds |
|---|---|
| Pθ 参数 / train / eval | **20261301 / 20261302 / 20261303**（与生成器 seed 分离；生成器参数只由 param_seed 决定） |
| H1 16 个 (d,N) cell 子采样 | **20261310–20261325**（按 d,N 固定顺序） |
| H2 5 个 ε | **20261326–20261330** |
| H3 | **20261331–20261332** |
| 两跑 replicate | **20261340–20261349**（10 个） |

- **禁复用**：C208/Stage1（20261112/20261113）、M1 v0.2（20261201/02/03）、M2 Stage2（20261200–20261239）、M2 Stage3（20262100–20262139）、M3 执行保留（20261500–20261599）；本地检查 **overlap=[]、unique=true**。
- **两跑**：同 seeds、独立进程；结果 JSON 逐字节；telemetry 单独文件（结果 JSON 无 telemetry）；**执行时不得改 seed**。

## 3. 执行范围（仅 Stage2 诊断；不报效果）

- **唯一 Pθ**：X~N(0,I_64)、A=4、Y∈[-2,2]^4；**3 分量截断 GMM、对角协方差、条件异方差**（K=3、权重 [0.5,0.3,0.2]；c~(4,3,4)、M~(4,3,4,64)、d~(4,3,64)；μ=c+Mx、σ=.1+.4sigmoid(d^Tx)；截断 Z>0 有限）；**无 Student-t 选项**；train N=4096/eval N=2048。
- **target Q_g ∝ π0 Pθ exp(r/τ)**：`r=w^Ty−λ||y||²`、w=[.4,.3,.2,.1]、λ=.2、**r_max=.375/r_min=−5.2**（compact box 有界）；τ∈{.5,1}；归一化 tensor Gauss-Legendre **64 nodes/dim**；target 样本**不作标签**；Doob 非可执行药物。
- **候选 C-MDN**：K=3 logits+mean(4)+diag log-scale(4)；hidden 128、2 层 ReLU；NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；采样规划 4096/action；**不称一步投影**。
- **H1**：d∈{8,16,32,64}×N∈{512,1024,2048,4096}；256-bin（4 bins/Y 维）histogram TV；eval 固定 2048/seed 20261303；**容差表（N 顺序写死）**：d8 [.12,.10,.08,.07]、d16 [.14,.11,.09,.08]、d32 [.16,.13,.11,.10]、d64 [.18,.15,.13,.12]；超容差→`design_invalid: projection`。
- **H2**：log-domain Sinkhorn；ε∈{.1,.25,.5,1,2}；maxiter **2000**；marginal tol **1e-8**；至少一个 ε 收敛；否则 `design_invalid: projection`。
- **H3**：small-case d_X=2/A=2/Y=2；oracle 用 tensor Gauss-Legendre **128 nodes/dim** 精确 target Q/action；候选 target-action 分布 vs oracle 的 **TV**（256 eval x）；**TV≤.05**；超过→`design_invalid: projection`；**H3 仅 small-case，不是高维 oracle**。
- **不得**输出 decision utility/regret/top-k/方法比较/增益；H1–H3 只作近似/校准/规划诊断。

## 4. 继承 G1–G6（执行时逐项）

- **G1 条件药效保持**：target guidance 不改 Pθ；target 样本不作标签；可执行 Rπ 保持 P(y|a)=Pθ；失败→`calibration`。
- **G2 支持/程序合法性**；失败→`support`。
- **G3 近似/投影**：H1/H2/H3；失败→`projection`。
- **G4 无泄漏**：评估独立于拟合/策略选择；target 样本不作标签；失败→`leakage`。
- **G5 两跑**：结果 JSON 逐字节；失败→`two_run_mismatch`。
- **G6 schema/预算**：schema 先写、caps 1800 s/2 h/8 GB/0 wells；失败→`compute_budget_exceeded`。

## 5. 等预算对照（仅规格登记；不执行）

B1 random MPC；B2 maximum-entropy；B3 conditional density+MC；B4 constrained Schrödinger bridge；B5 same-information Diffusion Forcing。同数据/物理反馈/信息集/cap/调参≤20/合法实验包；target 样本不作标签；标准控制等预算复制/超过/解析等价→`rename_maxent`/撤；**不作方法比较/效果**。

## 6. 失败/停止/撤主张

- **失败类别**：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **停止/撤主张**：B2 等价/一步投影已撤，**不得写 M1 增量**；H1 超容差→`projection`；H2 不收敛→`projection`；H3 TV>.05→`projection`；target 改 Pθ→`calibration`；无支持→`support`；泄漏/两跑/链/预算失败→对应类别；**任何失败不改变旧判定/门槛**；不得执行时放宽容差/改阈值/换端点救结果。

## 7. 预算/两跑/schema/边界

- caps **1800 s/2 h/8 GB/0 wells**；执行前用最终实现**重跑 pilot 并冻结 canonical timing**（文档/JSON 引用同一 snapshot；不得混用旧 pilot）；结果 JSON 无 telemetry；失败只写类别不报结果。
- **schema**：`schema_m1_s2_exec.json` 先写；H1/H2/H3 字段、G1–G6、失败模板、forbidden fields（decision utility/regret/topk/method comparison/gain/pharmacology/real decision/transfer/mechanism/novelty/real data）冻结。
- **边界**：机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210）；Stage2 执行须另立预注册+独立挑战+Lead 批准。
