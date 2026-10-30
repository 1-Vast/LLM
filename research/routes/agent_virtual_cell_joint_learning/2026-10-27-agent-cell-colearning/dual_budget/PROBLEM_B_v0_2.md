# PROBLEM_B_v0_2 —— 双预算决策形式化（R201-B.1 修订；设计轮，不执行）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：v0.1 `PROBLEM_B.md`/`DESIGN_B.md`/`report_B.md`、`challenge_B.md`（R201-B-C1，revise 5 必改，SHA `45E18D67158BC7FE32FFF70B17953F58F29448AF52902DD56316B3DE27539B09`）、R201 `BRIEF.md`、`agent-cell-colearning/report.md` D2、D1/D3/ON2-EX/ON3 v1.2/PEEK/A5/C187/C190。**本文件只做形式化/设计；未运行效果、未拟合预测、未读响应值、无湿实验；不称新颖性/机制/迁移/决策收益。**

## 0. 本版（v0.2）修什么

| challenge 必改 | v0.2 处理 |
|---|---|
| ① 等总成本/最佳单一预算不可核查 | 写死单预算臂未用预算换算：`κ`（synthetic compute-second per CU）三场景；`compute-only: B_C_eff=B_C+κ·B_E`；`experiment-only: B_E_eff=B_E+B_C/κ`；残余 filler 同维、无信息、计入账本。**禁止测试集先 max 再 CI**：validation 嵌套选 best-single；两主对比（dual vs compute-only-filler、dual vs experiment-only-filler）分别报告 + Holm；max 只作描述（同时 CI）。 |
| ② 判据悬空 | T1 合成定义 `h_in/h_out`（区间证书）、`Δ_utility`、`headroom`、EV；唯一判定树（§3）；`B_C` 耗尽且 `g_C>1` → `compute_budget_exceeded`（不买实验、不静默停）；无证书模型（GP/树/BOED）→ `certificate_unavailable`（只作对照，不能跑 dual splitter）；headroom 未知 → `oracle_unknown`（不买）；T2/T3 在 utility/证书冻结前不下结论。 |
| ③ primary/MDE/δ 不同尺度 | **primary 改为 top-1 selection accuracy**（[0,1]）；MDE 用 paired-binary 保守公式；`δ_min=0.10` 为**操作性统计阈值**（不再 blocked）；top-k hit/regret 降为 secondary（T1 模拟器校准 null/MDE，不作主推断）；**decision unit = 独立 held-out cell/fold 菜单**；key→CU 映射 `r∈{1,5,10} keys/unit`（敏感性）；393 keys≠393 decision units。 |
| ④ T1 细节 | T1 预注册写入 `DESIGN_B_v0_2.md` §4：世界生成/共享算子/隐藏计划差/噪声/成本、500 独立 replicate+seed、oracle/top-k、null 校准、无泄漏单测、C0–C7 等价实现、等成本、两跑、schema、wall 预算、资格门。 |
| ⑤ T2/T3/边界 | T2 仅描述 + PEEK `B4CAD955…`；T3 保持 `data_unavailable/cost_uncalibrated`；T2/T3 不得把 n=6/30 或 393 keys 当主检验；三轮 `blocked_by_utility_definition`/T1 计算证据/不称决策收益一致。 |

## 1. 决策状态（形式化）

- **候选计划集 P**：预注册 cell×pair×dose-context 计划宇宙；未测计划 P_unseen 仅用于评估。
- **决策菜单 M**：每个独立 decision unit 一个菜单；菜单构造纯元数据、哈希预注册，不得按结果/headroom 选。
- **当前模型 M_t**：声明族（T1：带区间证书的合成族；T2/T3：无已冻结证书 → `certificate_unavailable`）。
- **计算预算 B_C**：实测 CPU-second（所有求解/证书/重拟合/构图/缓存重认证/填充计算计费）。
- **实验预算 B_E**：wells/plates/keys/rounds + A5 planning CU（非货币；含对照/重复/失败板/setup/filler）。
- **动作**：A_compute（提高精度/证书/重认证/填充） ∪ A_experiment（买计划/细胞/剂量/时间；plate 打包/对照/重复/QC）。
- **策略 π**：每轮选择计算、实验（买什么）、或停止。

## 2. 等总成本（可核查定义，核心修正）

### 2.1 T1 合成成本面（唯一允许用于成本结论的场所）

- 定义 `κ` = synthetic compute-second per CU，预注册场景 **{0.1, 1, 10}**；总合成成本（秒等价）：
  `T = B_C + κ·B_E_CU`。
- `π_dual` 在 `(B_C,B_E)` 内自由分配；`compute-only` 把实验预算全部换成计算：`B_C_eff = B_C + κ·B_E_CU`（实验=0）；`experiment-only` 把计算预算全部换成实验：`B_E_eff_CU = B_E_CU + B_C/κ`（计算=0）。
- **filler**：离散化残余（不足一个最小计算/实验单元）用同维随机无信息动作填满（计入账本，不影响信息）；所有臂 `|实际花费 − T| ≤ 一个最小动作/计算单元`，且账本逐项报告 compute seconds、CU、wells、plates、keys、rounds、filler。
- 例（`design_B_v0_2.json`）：`(B_C=1200s, B_E=16 keys=5817.6 CU)`、κ=1 → T=7017.6s；compute-only B_C_eff=7017.6s；experiment-only B_E_eff=7017.6 CU；dual 1200s+5817.6 CU；三臂等总成本可审计。
- **T2/T3 不做成本结论**：无真实报价/LOI/湿预算 → `cost_uncalibrated`；A5 CU 仅 planning，不写货币结论。

### 2.2 "最佳单一预算"选择（禁止测试集 max）

- 在每个 replicate/outer fold 内，**只用训练/验证（inner）split** 选 best-single（compute-only 或 experiment-only 按验证 selection accuracy 选；选择规则预注册、可在验证集算）。
- 测试集只做**两个独立主对比**：`dual − compute-only`、`dual − experiment-only`；两对比用 Holm 校正 α=0.05；每个对比报告点估计+配对 bootstrap CI。
- `best-single` 的 max 仅作**描述性**，用同时置信区间（Bonferroni/联合 bootstrap），**不得**作为主检验或先 max 再算 CI。
- C7 两臂分别报告；C0/C1 不混入"最佳单一预算"主定义（仅辅助）。

## 3. compute/evidence 判据（T1 合成可操作化 + 唯一判定树）

### 3.1 T1 合成证书/效用定义（不外推）

- **合成效用**：每个 plan 有真实效用 `u∈[0,1]`（simulator ground truth）；decision menu 的 oracle = argmax u；`headroom = E[u(oracle)] − E[u(static)]`（T1 可算）。
- **合成证书**：对每个决策差 `d=q−p`，模型族给出区间 `[h_in(d), h_out(d)]` 满足 `h_in ≤ u(q)−u(p) ≤ h_out`（T1 精确可算）；compute 预算按预注册精度阶梯收缩区间宽度（每 step 成本固定，T1 明示）。
- **Δ_utility = 0.10**（T1 合成效用尺度，独立于 primary accuracy δ_min=0.10；不混用）；`g_C(d)=(h_out−h_in)/Δ_utility`；`compute_limited` 当 `g_C>1`。
- **EV（T1）**：候选实验在某 menu 上的期望决策收益由 ground truth 枚举/解析计算（T1 可算）；`EV/CU` 用于选择实验；T2/T3 未冻结效用 → 不可算。
- **T2/T3**：无已冻结证书/效用 → 判据不可用；T2 仅描述（附 PEEK），T3 data_unavailable；不得用 T1 合成判据外推真实结论。

### 3.2 唯一判定树（写死；每轮每臂）

```
0) 若该臂无 utility/证书（T2/T3 默认；GP/树/BOED 无证书）:
   -> certificate_unavailable / blocked_by_utility_definition（记未决；不判 H_B；不买实验）
1) compute 阶段:
   while g_C > 1 and remaining B_C >= min_compute_unit:
       spend one pre-registered compute step（收缩证书；计费）
2) 若 g_C > 1 且 B_C < min_compute_unit:
   -> compute_budget_exceeded（未决；不得自动买实验，不得静默 stopping）
3) 若 g_C <= 1:
   3a) 相容证书集内所有世界给出同一决策 -> compute_sufficient -> 停止（不买实验）
   3b) 否则 evidence_limited:
       - headroom 未知 -> oracle_unknown -> 停止（不买；记录所需 oracle/pilot）
       - MDE_decision(B_E) > δ_min 或 power < 0.80 或 headroom < Δ_utility -> evaluation_cannot_distinguish -> 停止
       - 否则：买 EV/CU 最大的实验包；计费；更新 M_t；下一轮
4) 轮次耗尽 -> unresolved（记录；不强行判收益）
```

- **无证书模型 fallback**：GP/树/BOED 作为对照臂可用全部预算，但**不能执行 dual splitter**；其 compute 分配记为 `certificate_unavailable`，主对比仍可比较其决策收益；不得给它额外信息/数据。
- **T3 前瞻**：headroom/oracle 未知 → `oracle_unknown`；不得购买/判定。
- **T2**：保留既有 ON3/non-blind 上下文；仅描述性；不得把 n=6/30 当主检验。

## 4. Primary/Secondary/δ/MDE（统一尺度）

- **Primary（唯一）**：**top-1 selection accuracy**，每个独立 decision unit 一个选择，`[0,1]`；主效应 `Δ_acc = acc_dual − acc_best_single`（两个主对比分别 + Holm，见 §2.2）。
- **MDE（primary）**：`MDE80 = 2.8015852181 × sqrt(0.5/n_independent_decision_units)`（paired-binary 保守；n=独立 decision units，不是 wells/keys）。n=6→**0.808748**；30→**0.361683**；393→**0.099929**；500→**0.088594**；1,573→**0.049949**。
- **δ_min=0.10 为操作阈值**（selection accuracy 绝对差），不依赖业务效用；`blocked_by_utility_definition` **仅用于 secondary regret/EV/headroom 与真实世界决策价值主张**，不再用于 primary。
- **Decision unit**：独立 held-out cell/fold 菜单（一个选择/菜单）；technical wells/keys 不是独立单元。
- **Key→CU 映射（T3）**：预注册 `r keys/decision unit` 敏感性 r∈{1,5,10}；T3 393 decision units 对应 `393×r` keys，而非 393 keys；成本 = `393×r×363.6 CU`：r=1 **142,894.8 CU**；r=5 **714,474.0 CU**；r=10 **1,428,948.0 CU**；wells 13,362–26,724 / 66,810–133,620 / 133,620–267,240；setup/重复/失败板另计；无报价 → `cost_uncalibrated`。
- **Secondary**：top-k hit（k=5）、归一化 regret、选择准确率的分层、预测辅助；top-k/regret 的 null/MDE **只在 T1 模拟器中校准**（不直接用 decision-accuracy 公式）；T2/T3 不作主推断。
- **零模型**：随机决策/随机预算分配/shuffle 计划效用/compute-only/experiment-only/solver-seed shuffle/菜单 label shuffle；只用于 null 校准，不用于选策略。

## 5. 与 AL/BOED/COPEx 的关系（不称新颖性）

一般概念（决策价值选实验、BOED/EVSI/ENBS、动态约束实验设计 COPEx、约束生成、计算决策、GP/BO）已被覆盖；CoMap/LAWM/MDA/COPEx 已有联合/任务摘要/动态约束。本设计的差别仅限定为**具体共享对象**（跨计划共同反事实/约束算子 + 计算认证状态）与**具体更新运算**（计算证书收紧 + 真实反馈统一修订共同对象 → 改变下一次计划选择），以及**可审计双预算成本账**；**不主张**新 AL/BOED/COPEx 算法、不主张首次双预算、不主张预测分歧采样；是否新意须同信息/同预算同任务对照裁决，若等效 → 撤新意。

## 6. 已否定路线/继承边界

- D1 stop（precision_insufficient）、D3 design_invalid（单 anchor/rank MDE）、A1 data_unavailable（relations R=2<20/coverage 1.17%）、C187 pair-level AL 饱和（Δ=−0.0040）——**不重复**；本设计不得退回"再做普通 pair-level AL/更多预测/更多 wells"。
- 继承 non-blind/peek：设计写于 ON3 v1.2/QUICK 之后；未用其结果选择方向/阈值/预算/比较器；T2 必须附 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`，不得称盲验/独立确认/预注册确认。
- 技术重复≠独立培养；batch3 全失、702 个 15 行 pair-cell 等 O'Neil 限制不变；**冻结≠资源足够/关系成立/Stage 1/效果**；不称新颖性/机制/迁移/决策收益。
