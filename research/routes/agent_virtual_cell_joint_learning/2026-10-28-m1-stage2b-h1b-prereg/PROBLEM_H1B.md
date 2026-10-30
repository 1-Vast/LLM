# PROBLEM_H1B —— R204-M1-S2B H1b 可分辨测量预注册（floor 校准先行；不运行方法）

2026-10-28。对象：R204-M1 高维近似（Stage2 H1 测量）的**新 H1b 测量协议**预注册，回应 C217 归因（旧 H1 判据低于 oracle 有限样本 floor）。依据：C215/C216/C217 产物、M1 Stage2 v0.2 设计链、M1 Stage1/C208、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C208/C209/C213/C215/C216/C217。
**状态：预注册草案；仅做 floor 校准（解析/MC）与测量协议设计；未运行 C-MDN、未报效果、未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。H1b 执行须另立独立挑战+Lead 批准。**

## 0. 旧/新协议严格分离（写死）

| 项 | 状态 |
|---|---|
| C216 旧 H1 结果 | **0/16 FAIL；`design_invalid: projection` 保持不变** |
| C217 归因 | **旧 H1 冻结容差低于 oracle 有限样本 floor；归因保持不变** |
| 旧 H1 容差 | **不改**（d8 [.12,.10,.08,.07]、d16 [.14,.11,.09,.08]、d32 [.16,.13,.11,.10]、d64 [.18,.15,.13,.12]） |
| H1b 定位 | **全新的、单独预注册的测量协议**；不是"修正旧 gate"、不是"重跑旧 H1 使其通过"、不得用 H1b 改判 C216/C217 |
| 失败后果 | H1b 失败也不改旧判定/门槛；旧 gate 结论仍为 `design_invalid: projection` |

## 1. 冻结 Pθ（floor 校准用；与 C216 一致）

- K=3 截断 GMM，权重 [.5,.3,.2]；c~N(0,.5²) (4,3,4)、M~N(0,.1²) (4,3,4,64)、d~N(0,.1²) (4,3,64)；μ=c+Mx、σ=.1+.4·sigmoid(dᵀx)；Y∈[-2,2]^4；param/train/eval seeds **20261301/20261302/20261303**。
- floor 校准只从 Pθ 采样/解析，不训练 C-MDN、不看 M1 方法结果。

## 2. H1b 测量定义（新协议；写死）

- **测量对象**：固定动作 a=0；X~N(0,I_d)（d 为单元维度）；Y~Pθ(·|x,a=0)，截断到 box。
- **TV 估计器**：对 4D Y 做固定 **hash 分箱**：每维 8-bit 量化 `q_j=clip(floor((y_j+2)/4·256),0,255)`，code=`q0+256q1+65536q2+16777216q3`，**cell=code mod B**；TV=(1/2)Σ_c|p̂1(c)−p̂2(c)|（两个独立样本，各 N_eval）。
- **测量参数（floor 校准选择）**：**B=16、N_eval=32768、K=1**；oracle-vs-oracle 两样本 TV 的 worst-case over d q95=**0.01642609**、mean=**0.01221141**。
- **K 定义**：K 个独立两样本 TV 的平均；本选择 K=1（单次两样本 TV）；执行时每个 cell 用固定 eval seed，两跑同 seeds。
- **floor 校准网格**：B∈{16,32,64,128,256} × N_eval∈{2048,8192,16384,32768} × K∈{1,4,16}；d∈{8,16,32,64} 取 worst-case；MC reps 300；p 估计 400k/d。
- **选择规则（预注册，不得按 M1 结果调）**：在 q95_worst≤0.02 的 combo 中最小化成本 B·N_eval·K，再按 q95 最小 tie-break；若无 combo 满足且最小 q95>0.03 → `precision_insufficient` 停止（不强行设计）。本结果为 **selected**。

## 3. 容差规则（由 floor 推导，写死）

- **`tol_d = ceil(3 × floor_q95_d × 1000)/1000`**；`floor_q95_d` 为 d 特定 oracle floor q95；**floor_q95_d ≤ tol_d/3** 恒成立。
- **容差表**（预注册）：d8 **.049**、d16 **.050**、d32 **.049**、d64 **.048**（全局 .050）。
- **pass/fail**：H1b cell (d,N_train) pass ⇔ `TV_h1b(d,N_train) ≤ tol_d`；任何 cell 超容差 → `design_invalid: projection`（H1b 内部失败类别），**不改 C216/C217**。
- 不得用 M1 方法结果反推/调整 tolerance；不得改旧 H1 容差。

## 4. H1b 执行协议（预注册，不运行）

- **16 cells**：d∈{8,16,32,64} × N_train∈{512,1024,2048,4096}（与旧 H1 网格同，但测量协议全新）。
- **测量**：每 cell 用训练规模 N_train 训练候选 C-MDN（H1b 执行时才做；本任务不做），以固定 eval seed 采样 N_eval=32768 候选 Y（a=0）与独立 oracle 样本同 N_eval；hash 分箱后 TV；与 tol_d 比较。
- **独立执行 seeds**：floor 校准 **20261801–20261810**；H1b 数据 **20261811**、eval **20261812**、cell seeds **20261821–20261836**（16 cells）；与旧 Stage2 seeds（20261301–03、20261310–…、20261401、20261500、20261601、20261701）**disjoint**；两跑同 seeds、独立进程、结果 JSON 逐字节、telemetry 单独。
- **caps**：1800 s/2 h/8 GB/0 wells；执行前用最终实现跑 pilot（H1b 全测量流程）实测并冻结 canonical timing；per-cell schema/失败模板先写。
- **失败类别**：`design_invalid: projection|calibration|leakage|two_run_mismatch|chain_mismatch|compute_budget_exceeded`、`precision_insufficient`、`inconclusive`。
- 不输出 decision utility/regret/top-k/方法比较/效果；H1b 只判测量近似（非药理/真实决策/迁移证据）。

## 5. 可判定性论证（写死）

- **C-MDN 需达到的 TV 才 pass**：`TV_candidate ≤ tol_d`，即 d8≤.049、d16≤.050、d32≤.049、d64≤.048。
- **可检出 excess（高于 floor）**：`tol_d − floor_q95_d` = d8 **.03288**、d16 **.03357**、d32 **.03278**、d64 **.03219**。
- **旧 C217 C-MDN excess**：median **.0599**、max **.2037** → 远大于可检出 excess；在 old-excess 下近似 **power≈1**（pass≈0），说明 H1b 对旧量级近似误差可检出，不会被 floor 噪声判死。
- **判定**：selected 参数满足 `floor q95 ≤ tol/3`；无需 `precision_insufficient`/stop；若未来执行发现参数不满足（如 caps 导致 eval 不足）则按预注册停止，不强行设计。
- 不把 H1b 通过/失败与真实功能/决策收益挂钩；H1b 仅测量近似协议。

## 6. 边界

机制账 only；不运行 C-MDN/不报效果；不改 C216/C217/旧容差/旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；H1b 执行须另立独立挑战+Lead 批准。
