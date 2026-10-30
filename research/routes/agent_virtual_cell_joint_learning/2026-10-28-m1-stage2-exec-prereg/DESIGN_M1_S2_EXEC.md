# DESIGN_M1_S2_EXEC —— R204-M1 Stage2 合成执行设计（仅机制账；不运行）

2026-10-28。依据：[PROBLEM_M1_S2_EXEC.md](PROBLEM_M1_S2_EXEC.md)、`exec_plan_m1_s2.json`、`schema_m1_s2_exec.json`、M1 Stage2 v0.2 链、Lead 接受决定、M1 Stage1/C208。
**状态：执行预注册设计；未运行 Stage2 训练/效果/真实数据；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage2 执行须另立独立挑战+Lead 批准。**

## 0. 执行前核验/门顺序

1. **SHA 链**：12 文件（M1 Stage2 v0.2 八件 + Lead 接受决定 + Stage1 json/report/decision）全部匹配（本地已核验 chain_pass=true）；执行时重核；失败→`design_invalid: chain_mismatch`。
2. **Stage1 状态**：C208 `failed_gates=[]`、`no_effect_results=true`、G1/G2/G4 PASS、B2 `rename_maxent_detected=true`、`m1_increment_claimed=false`；**一步投影已撤**。
3. **seed 独立核验**：执行 seeds 20261301+ 与 C208/Stage1/M1 v0.2/M2 Stage2/M2 Stage3/M3 保留区间交集为空；执行时重核，不得改 seed。
4. **pilot 冻结**：执行前用最终实现重跑 pilot（planning/单测口径），冻结 canonical timing 到单独 telemetry 文件；文档/JSON 引用同一 snapshot；超 caps→`compute_budget_exceeded`。
5. **schema/失败模板先写**：`schema_m1_s2_exec.json` 在运行前冻结。
6. **Stage2 通过后**：本预注册仅 Stage2 诊断；Stage3 另立预注册+独立挑战+Lead 批准；真实数据/湿实验不批。

## 1. 生成器/候选实现（冻结）

- **唯一 Pθ**：X~N(0,I_64)、A=4、Y∈[-2,2]^4；3 分量截断 GMM、对角协方差、条件异方差；K=3、权重 [.5,.3,.2]；c~(4,3,4)、M~(4,3,4,64)、d~(4,3,64)；μ=c+Mx、σ=.1+.4sigmoid(d^Tx)；截断 Z(x,a) 见 PROBLEM；**无 Student-t**；train 4096/eval 2048；param/train/eval seeds 20261301/02/03。
- **target Q**：`Q_g∝π0Pθexp(r/τ)`；r 有界 [−5.2,.375]；τ∈{.5,1}；tensor Gauss-Legendre 64 nodes/dim 归一化；target 样本不作标签；Doob 不可执行。
- **候选 C-MDN**：K=3 logits+mean4+diag log-scale4；hidden128/2 ReLU；NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；规划采样 4096/action；**不称一步投影**；不报效果/增益。
- **实现接口**：只读冻结 Pθ、reward、Gauss-Legendre 规则与候选规格；不复制/修改 Stage1/M2/M3 代码；不训练真实数据。

## 2. H1（近似随 d/N；冻结容差）

- d 顺序 **8→16→32→64**；N 顺序 **512→1024→2048→4096**（训练前 N 行、固定 train_seed）；eval 固定 2048/seed 20261303。
- 指标：256-bin（4 bins/Y 维）histogram TV；每个 (d,N) cell 使用固定 H1 seed（20261310–20261325，按 d,N 顺序）。
- **容差表（TV max）**：

| d | N512 | N1024 | N2048 | N4096 |
|---|---|---|---|---|
| 8 | .12 | .10 | .08 | .07 |
| 16 | .14 | .11 | .09 | .08 |
| 32 | .16 | .13 | .11 | .10 |
| 64 | .18 | .15 | .13 | .12 |

- 任一 cell TV>容差→`design_invalid: projection`；**执行时不得放宽容差/改 cell 顺序**；H1 结果只作近似诊断。

## 3. H2（Sinkhorn/constrained SB）

- log-domain Sinkhorn；ε∈{.1,.25,.5,1,2}（固定顺序）；maxiter 2000；marginal tol 1e-8；约束 action marginal=π0、target outcome marginal=Q_g 的 y 边际。
- **至少一个 ε 收敛**（max row/col marginal error≤1e-8）；否则 `design_invalid: projection`；记录每个 ε 的迭代数/误差；不实现为另一错误目标条件化。

## 4. H3（small-case exact oracle）

- small-case：d_X=2、A=2、Y=2、同截断 GMM 族；oracle 用 tensor Gauss-Legendre **128 nodes/dim** 精确 target Q/action。
- 候选 C-MDN 拟合；指标：候选 target-action 分布 vs 精确 oracle 的 **TV**（256 eval x）；容差 **TV≤.05**。
- 超过→`design_invalid: projection`；**H3 仅 small-case，不是高维 exact oracle**；高维误差由 H1 判；H3 仅规划质量诊断，不作效果。

## 5. G1–G6 继承

| 门 | 规则 | 失败类别 |
|---|---|---|
| G1 | target guidance 不改 Pθ；target 样本不作标签；可执行 Rπ 保持 P(y\|a)=Pθ | calibration |
| G2 | 支持/程序合法性 | support |
| G3 | 近似/投影（H1/H2/H3） | projection |
| G4 | 无泄漏（评估独立于拟合/策略选择；target 不作标签） | leakage |
| G5 | 两跑结果 JSON 逐字节 | two_run_mismatch |
| G6 | schema 先写 + caps 1800 s/2 h/8 GB/0 wells | compute_budget_exceeded |

## 6. 等预算对照（仅规格登记）

B1 random MPC；B2 maximum-entropy；B3 conditional density+MC；B4 constrained Schrödinger bridge；B5 same-information Diffusion Forcing；同数据/物理反馈/信息集/cap/调参≤20/合法实验包；target 样本不作标签；标准控制等预算复制/超过/解析等价→`rename_maxent`/撤；**不执行比较/不报方法差异**。

## 7. 两跑/预算/telemetry/schema

- **两跑**：run1/run2 独立进程、同 seeds；结果 JSON（无 telemetry）逐字节一致；`run_shas` 记录；不一致→`design_invalid: two_run_mismatch`。
- **预算**：caps 1800 s/2 h/8 GB/0 wells；执行前最终实现 pilot 重跑并冻结 canonical timing；planning 参考仅来自 `timing_m1_stage2_prep_v0_2.json`（per-rep ~.00115 s、projected ~.0115 s、memory ~.0067 GB；**不是执行实测**），执行必须实际重测。
- **schema**：`schema_m1_s2_exec.json` 冻结 top/H1/H2/H3/G1–G6/失败/forbidden fields；JSON 无 telemetry；失败只写类别。
- **停止/撤主张**：B2 等价/一步投影已撤，不得写 M1 增量；H1 超容差/H2 不收敛/H3 TV>.05→`projection`；任何失败不改旧判定/门槛；不放宽容差/改阈值/换端点。

## 8. 边界/批准清单

- 机制账 only；合成 compute-only、0 wells；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210）。
- **批准清单**：① 12 文件链核验+Stage1 状态；② 独立 seeds/两跑/telemetry 分离；③ Pθ/C-MDN/H1–H3 冻结（含容差表/N 顺序/H2/H3）；④ G1–G6/B1–B5 规格/失败类别/停止；⑤ caps/pilot 冻结/schema；⑥ 边界。
- Stage2 执行须另立独立挑战 + Lead 批准；Stage3 另立预注册。
