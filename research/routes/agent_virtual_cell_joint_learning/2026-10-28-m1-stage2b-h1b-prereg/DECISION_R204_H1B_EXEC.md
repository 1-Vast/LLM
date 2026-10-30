# Lead 批准：R204-M1 H1b 可分辨 TV 测量执行（仅机制账；compute-only；0 wells）

2026-10-28。依据：R204-M1-H1B-C1（i003）判 **approve_exec_to_lead**；旧/新协议分离、floor 校准（B=16/N_eval=32768/K=1、floor mean .01221141/q95 .01642609）、tol_d .049/.050/.049/.048 由 floor 推导、H1b 16 cells/seeds/两跑/caps/schema/失败/停止、边界均 PASS。

## 批准范围（仅 H1b 测量执行一次）
- 批准 R204-M1 **H1b 可分辨 TV 测量执行**（机制账、compute-only、0 wells）；**不批真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性**；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
- **旧 C216 旧 H1 0/16、`design_invalid: projection`、C217 归因、旧容差全部不变**；H1b 为新单独预注册测量协议，不是重跑/修正旧 gate；H1b 失败不改旧判定。
- 冻结 v0.x 链：PROBLEM_H1B `AE8BEE2A…`、DESIGN_H1B `10EF642A…`、floor_calib_h1b.py `9A0380B5…`、floor_calib_h1b.json `88715AA8…`、schema_h1b.json `A077BCCD…`、report `961721FF…`、record `47CC6FD5…`；执行前重核链 SHA，不匹配→`design_invalid: chain_mismatch`。
- 冻结测量：hash 分箱 TV（8-bit/维→code→cell=code mod B；a=0、X~N(0,I_d)、截断 Y）；B=16、N_eval=32768、K=1；16 cells d∈{8,16,32,64}×N_train∈{512,1024,2048,4096}；每 cell 候选 N_eval=32768、独立 oracle 同 N；TV≤tol_d pass（d8 .049/d16 .050/d32 .049/d64 .048）；超→`design_invalid: projection`（仅 H1b 内部）。
- 冻结 Pθ：c .5²/M .1²/d .1²、σ=.1+.4·sigmoid(dᵀx)、box[-2,2]^4、K=3/[.5,.3,.2]、param seed 20261301；候选 C-MDN 按 M1 Stage2 冻结设计（结构/训练不变；数值稳定措施披露）。
- 独立 seeds：floor 20261801–10、data 20261811、eval 20261812、cells 20261821–36；与旧集 disjoint；两跑同 seeds 独立进程、结果 JSON 逐字节、telemetry 单独；不得改 seed。
- caps 1800s/2h/8GB/0 wells；**执行前 final-implementation pilot 实测 16 cells wall/CPU/内存并冻结 canonical**（不得用 floor 校准 MC 时间代替；超 caps→compute_budget_exceeded）。
- schema/失败模板先写；失败类别 projection/calibration/leakage/two_run_mismatch/chain_mismatch/compute_budget_exceeded/precision_insufficient/inconclusive；**不输出 decision utility/regret/top-k/方法比较/效果**；JSON 无 telemetry。
- 非阻塞执行备注：tol 是 floor-derived、报告必须并列"旧 H1 不变"与"H1b 新协议"，**不得写成旧 gate 通过**；detectable_excess 是相对 floor q95 的近似、power≈1 仅针对 C217 旧 excess median .0599；不得修改 C216/C217 文件。

## 不批准
- 真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；把 H1b 写成旧 H1 的修正/重跑/通过；改公式/阈值/端点/旧容差；代码晋升；旧判定修改；恢复已停止实验。
