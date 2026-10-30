# DESIGN_H1B —— R204-M1-S2B H1b 测量执行设计（floor 校准先行；不运行 C-MDN）

2026-10-28。依据：[PROBLEM_H1B.md](PROBLEM_H1B.md)、`floor_calib_h1b.json`、`schema_h1b.json`、C215/C216/C217、M1 Stage2 v0.2、M1 Stage1/C208。
**状态：预注册设计草案；仅 floor 校准（K=1 测量选择）与协议设计；未运行 C-MDN/未报效果/未读真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；H1b 执行须另立独立挑战+Lead 批准。**

## 0. 旧/新协议（冻结）

- C216 旧 H1 **0/16 FAIL、`design_invalid: projection` 不变**；C217 归因**不变**；旧 H1 容差表**不改**。
- H1b 是**新单独测量协议**；不得写成旧 gate 的修正/重跑；H1b 结果不改变 C216/C217。
- 本任务**不训练 C-MDN**、不产生 H1b 方法结果；只做 floor 校准与协议预注册。

## 1. floor 校准实现（可复算）

- **Pθ**：param_seed **20261301** 抽 c(4,3,4)~N(0,.5²)、M(4,3,4,64)~N(0,.1²)、d(4,3,64)~N(0,.1²)；权重 [.5,.3,.2]；σ=.1+.4sigmoid(dᵀx)；Y box[-2,2]^4；固定动作 a=0、X~N(0,I_d)；截断拒绝采样。
- **hash 分箱**：q_j=clip(floor((y_j+2)/4·256),0,255)；code=Σ q_j·256^j；cell=code mod B。
- **p 估计**：每个 d（8/16/32/64）用 400,000 oracle 样本估计 B 个 cell 概率（floor seed 20261801+d 派生；不训练）。
- **floor MC**：对每个 (B,N_eval,K,d)：300 MC reps；每 rep 用 multinomial(N,p) 抽两个独立样本，TV=½Σ|p̂1−p̂2|；K 个独立两样本 TV 取平均；记录 mean/q95；取 worst-case over d。
- **网格**：B∈{16,32,64,128,256}×N_eval∈{2048,8192,16384,32768}×K∈{1,4,16}（60 combos×4 d）。
- **选择规则（先于任何 M1 结果，写死）**：q95_worst≤0.02 的 combo 中最小化成本 `B·N_eval·K`，再 q95 tie-break；无满足且最小 q95>0.03→`precision_insufficient` 停止。结果：**B=16、N_eval=32768、K=1**，q95_worst **0.01642609**、mean **0.01221141**、decision=selected。
- **tolerance**：`tol_d=ceil(3·floor_q95_d·1000)/1000`；floor_q95≤tol/3；表 d8 **.049**、d16 **.050**、d32 **.049**、d64 **.048**；global .050；不得按 M1 结果调。

## 2. H1b 测量协议（预注册；执行时实现）

- **16 cells**：d∈{8,16,32,64}×N_train∈{512,1024,2048,4096}；每 cell 训练候选 C-MDN（H1b 执行时；本任务不做），固定 a=0、X~N(0,I_d)，采样 N_eval=32768 候选 Y；独立 oracle 样本同 N_eval、同 d、同 a；hash 分箱 B=16；TV 与 tol_d 比较。
- **K=1**：每 cell 一次两样本 TV（固定 eval seed）；两跑重复同 seeds；如需 K 平均则预注册固定为 1，不得事后再加 seed 救结果。
- **seeds**：floor 校准 20261801–20261810；H1b 数据 **20261811**、eval **20261812**、cell seeds **20261821–20261836**；与旧 Stage2 seeds disjoint；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- **执行门**：候选 C-MDN 训练/eval 流程按旧 H1b 规格（K=3、hidden 128、2 ReLU、NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；但 **H1b 测量参数 B/N_eval/K 为本文新定**，不是旧 H1 的 256-bin/2048）；不得改旧 H1 容差。
- **pilot**：执行前用最终实现（Pθ+候选+H1b 测量）跑 pilot（2 cells 或全流程缩写）实测 wall/CPU/memory，冻结 canonical timing；caps 1800 s/2 h/8 GB/0 wells。
- **schema/失败模板先写**：`schema_h1b.json` 冻结 top/per-cell/forbidden fields/失败类别；JSON 无 telemetry；失败只写类别。

## 3. 判定/失败/停止

- **pass/fail**：cell pass ⇔ TV_h1b≤tol_d；任一 cell 超→`design_invalid: projection`（仅 H1b 内部失败，不改 C216/C217）。
- **失败类别**：`design_invalid: projection|calibration|leakage|two_run_mismatch|chain_mismatch|compute_budget_exceeded`、`precision_insufficient`、`inconclusive`。
- **停止**：floor/测量参数无法满足 margin→`precision_insufficient`；两跑不一致→two_run_mismatch；超 caps→compute_budget_exceeded；不修改阈值/端点；不重新打开旧 H1。
- **可判定性**：pass 要求 candidate TV≤tol_d（d8 .049/d16 .050/d32 .049/d64 .048）；可检出 excess 高于 floor = .032–.034；旧 C217 excess median .0599 → 近似 power≈1（pass≈0）；说明 H1b 对旧量级误差可检出，且不会被 floor 判死。

## 4. 预算/边界/批准清单

- caps **1800 s/2 h/8 GB/0 wells**；floor 校准 wall ≈16 s（非执行 caps；仅校准）；执行前 pilot 实测冻结。
- 边界：机制账 only；不运行 C-MDN/不报效果；不改旧判定/容差/门槛；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **批准清单**：① 旧/新协议分离（C216/C217 不变）；② floor 校准网格/MC/选择规则与结果（B=16/N=32768/K=1、q95 .016426）；③ tolerance 规则/表（floor 推导、不按 M1 结果）；④ H1b 16 格测量/seeds/两跑/caps/schema/失败/停止；⑤ 可判定性（required TV/detectable excess/power）；⑥ 边界。H1b 执行须另立独立挑战+Lead 批准。
