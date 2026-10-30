# report_B_v0_2 —— R201-B.1 修订报告（等总成本/判据/primary/T1 预注册；**未运行**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。针对 `challenge_B.md`（R201-B-C1，revise 5 必改，SHA `45E18D67…`）提交 v0.2 修订。**仅设计/算术；未运行 T1/T2/T3、未拟合预测、未读响应值、无湿实验；不称新颖性/机制/迁移/决策收益。**

## 0. 交付

| 文件 | SHA256 |
|---|---|
| `PROBLEM_B_v0_2.md` | `618C6EDA5897524EA9A763F8EFFD15CFD55476A8B081907A74B866E35CC01158` |
| `DESIGN_B_v0_2.md` | `6E30C98D770BBFE6F8A0F93C1CAB9E0E3B7C619463B054243A71C5197CD68911` |
| `design_B_revision.py`（仅算术；无数据读取/拟合） | `57749DA797DBD0907CE5AE13739ADF69969DD6BA4049B37B518D87576DDB3423` |
| `design_B_v0_2.json` | `128E129D953FEAF1852A5EBC971A976B9576B4A66A131AF9AE56773FA65128BC` |
| `report_B_v0_2.md` / `record_B_v0_2.md` / `usage_B_v0_2.json` | 见各文件 |

## 1. 5 必改落实

### ① 等总成本与"最佳单一预算"可核查
- **单预算臂再分配**：T1 合成成本面 `κ`（compute-second per CU）预注册场景 **{0.1,1,10}**；总成本 `T=B_C+κ·B_E_CU`。
  - compute-only：`B_C_eff=B_C+κ·B_E_CU`，实验=0；
  - experiment-only：`B_E_eff_CU=B_E_CU+B_C/κ`，计算=0；
  - 残余 filler 同维随机无信息、计入账本；所有臂 `|花费−T|≤一个最小动作/计算单元`；账本逐项报 compute s/CU/wells/plates/keys/rounds/filler。
- **禁止测试集 max**：best-single 只在 training/validation **inner split** 选；测试集只做两个主对比（dual vs compute-only-filler、dual vs experiment-only-filler），**Holm 校正**、分别报告点估计+配对 CI；max 仅描述性（同时 CI）。C7 两臂分别报告；C0/C1 不混入 best-single 定义。
- T1 例：`(B_C=1200s, B_E=16 keys=5817.6 CU)`、κ=1 → T=7017.6s；compute-only `B_C_eff=7017.6s`；experiment-only `B_E_eff=7017.6 CU`；dual 1200s+5817.6 CU——等总成本可审计。T2/T3 无报价/LOI → 不做成本结论（`cost_uncalibrated`）；A5 CU 仅 planning。

### ② compute/evidence 判据可操作化
- **T1 合成证书/效用**：每个 plan 有真实 `u∈[0,1]`；决策差区间 `[h_in,h_out]` 含真实差；compute 预算按预注册阶梯收缩；`Δ_utility=0.10`（T1 合成效用尺度，独立于 primary accuracy δ）；`g_C=(h_out−h_in)/Δ_utility`；T1 可算 `headroom=oracle−static` 与实验 `EV`。
- **唯一判定树**：无证书/效用 → `certificate_unavailable/blocked`（T2/T3、GP/树/BOED 默认，不判 H_B、不买实验）；`g_C>1` 且 B_C 足 → 继续计算；**B_C 耗尽且 g_C>1 → `compute_budget_exceeded`（未决，不自动买实验、不静默停）**；`g_C≤1` 且证书集决策唯一 → `compute_sufficient` 停；否则 evidence-limited：headroom 未知 → `oracle_unknown` 停（T3 fallback）；`MDE>δ`/power<0.8/headroom<Δ → `evaluation_cannot_distinguish` 停；否则买 EV/CU 最大实验、更新、下一轮；轮次耗尽 → unresolved。
- **T1 判据不可外推**：T1 合成 utility/certificate/headroom/EV 只在该模拟器有效；T2/T3 在 utility/证书冻结前不得下结论。

### ③ primary/MDE/δ 统一
- **Primary 改为 top-1 selection accuracy**（[0,1]），每个独立 decision unit 一个选择；MDE 用 paired-binary 保守公式 `MDE80=2.801585×sqrt(0.5/n_units)`。
- 数字：n=6 → **0.808748**；n=30 → **0.361683**；n=393 → **0.099929**；n=500 → **0.088594**；n=1,573 → **0.049949**。T2 n=6/30 仍 >0.10 → `evaluation_cannot_distinguish`，不作主检验。
- **δ_min=0.10 为操作性统计阈值**（selection accuracy 绝对差），**不再 trigger `blocked_by_utility_definition`**；blocked 仅用于 secondary regret/EV/headroom 与真实世界价值主张。
- **Decision unit = 独立 held-out cell/fold 菜单**；不是 well/key/row。
- **Key→CU 映射（T3）**：r keys/decision unit ∈{1,5,10}；393 decision units → 393×r keys；r=1 **142,894.8 CU**、r=5 **714,474.0 CU**、r=10 **1,428,948.0 CU**（wells/setup/重复/失败另计）；**393 keys≠393 decision units**；无报价→`cost_uncalibrated`。

### ④ T1 模拟器预注册细节
- 世界生成：per replicate 共享算子 θ + 隐藏 plan-difference γ + 噪声 σ；观测 O/未测菜单 M；菜单 metadata-only+hash。
- **500 独立 replicate**，seed=`20261130+replicate_id`，世界不复用；oracle/top-k 由真值复算（评估专用）。
- null 校准：γ=0/近似无信号、菜单效用 shuffle、随机决策、随机预算、solver-seed shuffle、菜单 label shuffle；FP≤α。
- 无泄漏单测：γ 不进特征、未测 plan 不进训练、oracle 只评估、成本账含所有计算/实验/filler、arm 无额外数据/模型。
- C0–C7 等价实现（固定计算+随机实验/固定实验+更多计算/全历史重训/普通决策 AL/GP-BOED/通用求解器/随机预算/单预算+filler）；同 update/信息/调参。
- 等成本：同 T、κ 三场景；两跑逐字节一致；输出 schema（每 arm/replicate：selection_accuracy/topk_hit/regret/chosen/oracle/成本账/compute_steps/experiments/filler/failure_class）；**pilot wall 预算：单次 T1 ≤45 min、两跑 ≤90 min；超限 → `design_invalid: compute_budget_exceeded`**。
- **资格门（先于 T1 结果）**：oracle 可恢复/null 校准/成本账/无泄漏/C0–C7 等价/两跑/schema/wall；任一 fail → `design_invalid`。

### ⑤ T2/T3/边界一致
- **T2**：仅回顾性操作/描述，不判 H_B；必须附 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`（ON3 non-blind/peeked）；n=6/30 不作主检验；`evaluation_cannot_distinguish`。
- **T3**：保持 `data_unavailable/cost_uncalibrated`；393 decision units≠393 keys；前瞻 oracle 未知→`oracle_unknown`；不执行。
- 三轮统一：`blocked_by_utility_definition` 仅 secondary/真实价值；T1 仅计算证据；不称决策收益/迁移/新颖性/机制/独立确认；D1/D3/A1/C187 不重复。

## 2. 预算/统计算术（design_B_v0_2.json）

- MDE（primary selection accuracy）：n=6/30/393/500 → **0.808748 / 0.361683 / 0.099929 / 0.088594**；rank（secondary）n=6/30/1573 → 2.287485/0.762495/0.099993。
- T3 成本（r keys/decision unit，393 decision units）：r=1 **142,894.8 CU**；r=5 **714,474.0 CU**；r=10 **1,428,948.0 CU**；A5 100k 示例仅 275 keys（planning，非可执行报价）；C136 1,600-key≈581,760 CU。
- 计算锚：B_C 300–3600s；ON3 v1.2 实测 wall 1272.06/1130.61s（B6 5,000 perms、bootstrap 5,000）；raw 306.722s/5,000 perms；计算/认证/生成/评估/调参全部计费。
- T1 500 独立 replicate；等总成本 κ 三场景；两跑；wall 预算门。

## 3. 可执行性/裁决

| Tier | v0.2 状态 |
|---|---|
| T0 形式化/算术 | 完成（本目录） |
| T1 合成模拟器 | **预注册可提交**（仅 T1；未运行；资格门先过） |
| T2 O'Neil | 仅描述/操作；MDE 不可判；不判 H_B；PEEK |
| T3 前瞻湿实验 | `data_unavailable/cost_uncalibrated`；393 keys≠393 decision units |

## 4. 建议

- 提交 **approve_to_lead_mvp（仅 T1 模拟器预注册）**：请独立挑战者只读复核等成本/filler、判定树 fallback、primary/δ 统一、T1 预注册细节、T2/T3 边界；通过后 Lead 再决定是否批准 T1 冻结/执行。
- **不申请 T2/T3 执行**；T1 仅计算证据，不外推生物/真实决策收益；若 Lead 要真实决策收益主检验，当前资源不足，应 stop 并写所需测量/报价规格。
- 不称新颖性/机制/迁移/决策收益/资源足够/独立确认；冻结≠资源足够/关系成立/Stage 1/效果。
