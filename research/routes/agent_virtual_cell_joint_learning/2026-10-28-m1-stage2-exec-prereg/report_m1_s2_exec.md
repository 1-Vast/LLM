# report_m1_s2_exec —— R204-M1 Stage2 合成执行预注册报告（仅机制账；不运行）

2026-10-28。对象：R204-M1 Stage2 合成执行预注册。依据：M1 Stage2 v0.2 设计链与 Lead 接受决定、M1 Stage1/C208、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C208/C209/C210。
**状态：预注册草案；未运行 Stage2 训练/效果/真实数据；仅规划/算术/骨架单测；机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage2 执行须另立独立挑战+Lead 批准。**

## 0. 交付物

- 问题定义：[PROBLEM_M1_S2_EXEC.md](PROBLEM_M1_S2_EXEC.md)（`F7ED4520…`）
- 执行设计：[DESIGN_M1_S2_EXEC.md](DESIGN_M1_S2_EXEC.md)（`503618F4…`）
- 规划/骨架：[exec_plan_m1_s2.py](exec_plan_m1_s2.py)（`CFF1C734…`）→ [exec_plan_m1_s2.json](exec_plan_m1_s2.json)（`3DC88FEF…`）
- schema：[schema_m1_s2_exec.json](schema_m1_s2_exec.json)（`181A77E3…`）
- 记录/用量：[record_m1_s2_exec.md](record_m1_s2_exec.md)、[usage_m1_s2_exec.json](usage_m1_s2_exec.json)

## 1. 链核验（已通过）

`exec_plan_m1_s2.py` 只读核验 **12 文件 SHA 全部匹配（chain_pass=true、mismatches=0）**：M1 Stage2 v0.2 八件（PROBLEM `63C0C228…`、DESIGN `642C3108…`、plan py `482E254F…`、json `73B8C025…`、schema `9C4DF027…`、timing `488C8EF6…`、report `BCE5DE11…`、record `CBA86C88…`）+ **Lead 接受决定 `6EC860D2…`** + Stage1/C208（json `EF701C66…`、report `E3701DA8…`、决定 `EEA8CE76…`）。不匹配→`design_invalid: chain_mismatch`；执行时重核。
**Stage1 状态**：failed_gates=[]、no_effect_results=true、G1/G2/G4 PASS、B2 `rename_maxent_detected=true`、`m1_increment_claimed=false`；**一步投影已撤**。

## 2. 独立执行 seeds（overlap=[]）

| 用途 | seeds |
|---|---|
| Pθ param/train/eval | **20261301 / 20261302 / 20261303** |
| H1 16 cells | 20261310–20261325 |
| H2 5 eps | 20261326–20261330 |
| H3 | 20261331–20261332 |
| 两跑 replicate | 20261340–20261349 |

**禁用/不复用**：C208/Stage1 20261112/20261113；M1 v0.2 20261201/02/03；M2 Stage2 20261200–20261239；M2 Stage3 20262100–20262139；M3 保留 20261500–20261599。本地 **overlap=[]、unique=true**；两跑同 seeds 独立进程、结果 JSON 逐字节、telemetry 单独。

## 3. 执行范围（仅 Stage2 诊断；不报效果）

- **唯一 Pθ**：X=64/A=4/Y=4（box [-2,2]^4）；3 分量截断 GMM、对角协方差、条件异方差；c/M/d 形状 (4,3,4)/(4,3,4,64)/(4,3,64)；μ=c+Mx、σ=.1+.4sigmoid(d^Tx)；截断 Z>0 有限；**无 Student-t**；train 4096/eval 2048；param/train/eval seeds 20261301/02/03。
- **reward 有界**：r=w^Ty−λ||y||²、w=[.4,.3,.2,.1]、λ=.2 → **r_max=.375、r_min=−5.2**；target Q∝π0Pθexp(r/τ)、τ∈{.5,1}；Gauss-Legendre 64 nodes/dim 归一化；target 样本不作标签；Doob 不可执行。
- **候选 C-MDN**：K=3 logits+mean4+diag log-scale4；hidden128/2 ReLU；NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；采样 4096/action；**不称一步投影**。
- **H1**：d∈{8,16,32,64}×N∈{512,1024,2048,4096}；256-bin TV；**容差表**（N 顺序写死）：d8 [.12,.10,.08,.07]、d16 [.14,.11,.09,.08]、d32 [.16,.13,.11,.10]、d64 [.18,.15,.13,.12]；超→`design_invalid: projection`。
- **H2**：log-domain Sinkhorn ε∈{.1,.25,.5,1,2}、maxiter **2000**、marginal tol **1e-8**、至少一个 ε 收敛；否则 `projection`。
- **H3**：small-case d2/A2/Y2；oracle GL **128 nodes/dim**；候选 target-action vs oracle **TV≤.05**（256 eval x）；超→`projection`；**H3 非高维 oracle**。
- **不输出 decision utility/regret/top-k/方法比较/增益**。

## 4. G1–G6 / B1–B5 / 失败/停止

- **G1** 条件药效保持（不改 Pθ、target 不作标签）→calibration；**G2** 支持→support；**G3** 近似/投影（H1/H2/H3）→projection；**G4** 无泄漏→leakage；**G5** 两跑→two_run_mismatch；**G6** schema/预算→compute_budget_exceeded。
- **B1–B5 仅规格登记**（random MPC、max-entropy、conditional density+MC、constrained SB、same-info DF）；同数据/反馈/信息/cap/调参≤20；target 不作标签；标准控制等预算复制/解析等价→`rename_maxent`/撤；**不执行比较**。
- 失败类别：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止/撤主张：**B2 等价/一步投影已撤，不得写 M1 增量**；H1 超容差/H2 不收敛/H3 TV>.05→projection；任何失败不改旧判定/门槛；不放宽容差/改阈值/换端点。

## 5. 预算/两跑/schema/骨架单测

- caps **1800 s/2 h/8 GB/0 wells**；执行前用最终实现重跑 pilot 并冻结 canonical timing（文档/JSON 同一 snapshot）；telemetry 单独；JSON 无 telemetry。
- planning 参考（非执行实测）：prep timing per-rep **.00115028 s**、projected **.011503 s**、memory **.00668467 GB**（SHA `488C8EF6…`）；执行必须实际重测。
- **schema**：`schema_m1_s2_exec.json` 先写（top/H1/H2/H3/G1–G6/失败/forbidden fields）；G5 两跑逐字节。
- **骨架单测（仅算术/形状，不训练）全 PASS**：Pθ 形状/权重和、截断质量有限正、reward 边界、seed 可复现、tiny Sinkhorn（ε=.5，**23 iter**，marginal ≤1e-8）、H1 容差表 4×4、H2 ε 网格、H3 small-case；**无训练/无方法比较/无效果**。

## 6. 边界

机制账 only；合成 compute-only、0 wells；**不执行 Stage3/真实数据/湿实验**；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；**M1 不与 M2/M3 混同**；N1 不作 M1 Stage2 证据；data readiness 保持 open（C203/C205/C210）；Stage2 执行须另立预注册+独立挑战+Lead 批准；Stage3 另立预注册。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2_EXEC.md` | `F7ED4520C00EBEEC5D18371050634C3ECAA5B1E61FAB860924C0709FAC93A0CD` |
| `DESIGN_M1_S2_EXEC.md` | `503618F4CBA53F6C15A2BB144A31CB29F6C5D8B6BAE7CD3E3DBEB2B40DD30806` |
| `exec_plan_m1_s2.py` | `CFF1C734FADA3E6679B5482D5BCB20C3B4D0766AE9A9E957E86977C62FADB3A8` |
| `exec_plan_m1_s2.json` | `3DC88FEF2860E5374F781CF642DD55B62079586E3618E1E04915F99137407B5C` |
| `schema_m1_s2_exec.json` | `181A77E377FE0CD4870CB8D977F7ACDB127730F6598A96950FB13DEE7917B682` |
| report/record/usage | 见 `usage_m1_s2_exec.json` |

**确定性**：`exec_plan_m1_s2.json` 与 `schema_m1_s2_exec.json` 两跑逐字节一致；JSON 无 telemetry；计时参考来自只读 prep timing 文件。

## 8. 建议

1. **提交本执行预注册做独立挑战**：重点独立 seeds/两跑、Pθ 唯一性/reward 有界、C-MDN 规格、H1 容差表/N 顺序、H2 ε/iter/tol、H3 small-case TV、G1–G6、B1–B5 规格、caps/pilot/schema、失败/停止、边界。
2. 挑战通过 + Lead 批准后才可执行 Stage2（仅合成诊断、compute-only、0 wells）；执行前重核链、重跑 pilot 冻结 canonical timing；**不批 Stage3/真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练/效果比较/结果解读/代码晋升/旧判定修改/恢复停止实验。
