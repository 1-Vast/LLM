# DESIGN_B —— 双预算决策预注册草案（R201-B；设计轮，不执行）

2026-10-27/28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：`PROBLEM_B.md`、R201 `BRIEF.md`、`agent-cell-colearning/report.md` D2、`acquisition_stage3/cost_model.md`、`core-module-design/oneil_dev/exec_calibration/report_calib.md`、`report_on3_exec.md`、`PEEK_DISCLOSURE_ON3.md`、`d3_feedback/`、`d1_information/DECISION_D1_STOP.md`、C187/C190。
**本文件是预注册草案，不是冻结协议；本轮不执行、不拟合预测、不读响应值、不买湿实验；不得据此声称决策收益/新颖性/机制/迁移。**

## 0. 设计判定（一屏）

- **主假设可形式化，但本地 O'Neil 无法作为主检验**：decision-accuracy MDE（30 cells pooled）= **0.3617**，fold-level n_eff=6 时 **0.8087**；rank Δρ MDE（n=6）= **2.2875**（pooled30=0.7625）→ 远大于 δ_min=0.10 → 本地判 `evaluation_cannot_distinguish`（precision_insufficient），**不买实验、不跑效果**。
- **合成模拟器可做算法证伪**：500 个独立模拟 replicate → decision-accuracy MDE **0.0886 ≤0.10**，可作为**计算证据**的预注册实验（不是生物/决策收益证据）。
- **前瞻湿实验当前 `data_unavailable / cost_uncalibrated`**：达到 0.10 MDE 需约 **393 个独立决策单元**；按 A5 anchored key central 363.6 CU 计约 **142,894.8 CU**（>A5 100k 示例；示例只能买 275 keys）；C136 的 1,600-key 80% 门槛约 **581,760 CU**；无报价/LOI、无独立培养/湿预算。
- **设计算术**：`design_B.json` SHA `38A1FBD0A8FB1A0FF1C3EFF2B262538DCD44D9917B0DC38D1122C6A12FE97808`；脚本 `design_B.py` 仅算术、无数据读取、无拟合。

## 1. 主假设 H_B（可证伪）

**H_B**：在**同等总成本**下（同一 `(B_C, B_E)` 预算对，或同一总 CU + 同一实测 compute 秒；计入对照/重复/失败板/轮次/失败重买），`π_dual` 在**留出未测计划**上的决策收益（预注册 top-k 指标）**高于最佳单一预算策略**（compute-only / experiment-only），且该收益**不是预测提分的替代**。

- 主比较：`Δ_dec = D(π_dual) − max(D(π_compute_only), D(π_experiment_only))`；D = 未测计划 top-k 决策收益（见 §6）。
- 机制/过程量：`g_C`（计算认证缺口）、`P(decision flip under M_t)`、实验 power/MDE、每 CU 期望决策收益；这些只作诊断，不替代主终点。
- **预测非替代**：预测指标（Spearman/MAE 等）只作辅助/阴性对照；若预测提升而 `Δ_dec` 不成立 → `no_decision_benefit`，停决策创新。
- **非结果依赖**：主指标/切分/预算/δ_min 在看任何执行结果前冻结；O'Neil 既有 non-blind/peek 只可用于披露，不用于选择本设计。

## 2. 层级（Tiers）

| Tier | 目的 | 资源 | 允许结论 |
|---|---|---|---|
| **T0 本轮** | 形式化 + 预算/MDE 算术 + 预注册草案 | 只读既有报告；`design_B.py` 算术 | 仅设计；无收益/新意 |
| **T1 合成模拟器** | 算法机制可证伪（决策集随机化、预算分配、计算/实验切换） | 本机 CPU；500 独立 replicate；已知 ground truth | **仅计算证据**；不外推生物/决策收益；模拟器资格先过 |
| **T2 O'Neil 回顾性 dev** | 管线/操作检查（manipulation check） | O'Neil complete-case 4×4、target30、5 折；响应值仅执行时使用（需另立协议） | **仅开发性/描述性**；因 MDE 已不可识别，**不作主决策推断**；必须带 non-blind/peek 披露 |
| **T3 前瞻湿实验** | 真实独立决策收益 | 需 wet budget/报价/独立培养/板位 | 当前 `data_unavailable`；不运行 |

## 3. 决策菜单/数据构造（若执行 T1/T2）

- **策略/计划**：计划 p = (cell, partner, member, dose-context/role, round)；候选集 P 固定为预注册 cell×pair 宇宙；未测计划 P_unseen 从不进入训练/更新，仅用于最终决策评估。
- **菜单构造（纯元数据）**：固定资源、固定 cell×pair 宇宙、固定端点/效用；一次性枚举，不用响应/headroom 选菜单；菜单哈希预注册（A5-C1 教训）。
- **T1 合成器**：构造已知共享算子 + 隐藏计划差结构 + 噪声 + 预算成本；500 个**独立 replicate**（非技术重复）；每个 replicate 重新生成世界/训练/留出计划；模拟器资格门：oracle 可复算、null 校准、compute 预算与精度关系可复现、无泄漏；资格不过 → `design_invalid` 停。
- **T2 O'Neil**：使用既有 complete-case；5 折细胞留出；计划/剂量网格按冻结定义；不得把技术重复当独立 n；必须披露 non-blind/peek 与 O'Neil 限制；因 decision MDE>0.10，**T2 不判主假设**。

## 4. 比较器（同信息/同预算/同成本）

| id | 策略 | 关键控制 |
|---|---|---|
| C0 | 固定计算 + 随机实验 | 同 (B_C,B_E)、同实验菜单/打包/轮次；随机选择 |
| C1 | 固定实验 + 更多计算 | 同实验；B_C 加到与 π_dual 相同；无实验选择 |
| C2 | 全历史重训 | 同全部历史/特征/更新器；无主动实验/无预算分配 |
| C3 | 普通决策 AL | 按决策不确定性/期望决策价值选实验；同更新器/同调参 trials |
| C4 | GP / BOED | 同信息/同预算；BOED 用决策损失；超参 trials 计入 |
| C5 | 通用求解器（同信息全局/约束生成） | 同证书缓存/同 compute 计费；作为强对照 |
| C6 | 随机预算分配 | 零模型：同总预算随机分 B_C/B_E；同菜单 |
| C7 | compute-only / experiment-only | 单预算极端；同总成本；用于主比较 |
| oracle | 描述性上界 | 仅算 headroom，不作竞争臂；不得用于选菜单 |

- 所有臂共用**同一反馈/更新器**（学生/更新规则固定）；策略不得自带未计费模型/额外数据/LLM 预算；调参 trials/seed/计算 cap 同一预注册；`π_dual` 不得多拿信息。
- **禁止**：以不同 cell 集合/不同 setup 会计/不同结论口径比较；以 wells/keys/rows 代替等成本；以预测指标替代决策指标。

## 5. 预算/成本对照（等成本写死）

- **双预算**：`(B_C, B_E)` 为预算对；所有臂在**同一预算对**下比较；允许欠花但 `|花−预算| ≤ 一个最小动作/最小计算单元`；预注册 filler（同信息、计入 CU/NB）。
- **计算侧**：B_C ∈ {300, 600, 1200, 2400, 3600} s（实测 CPU-second）；ON3 v1.2 实测 wall 1272.06/1130.61 s（B6 5,000 perms、bootstrap 5,000）；raw budget 306.722 s/5,000 perms 只作预算锚；所有求解/认证/重拟合/构图/缓存重认证计费；超时→`design_invalid: compute_budget_exceeded`。
- **实验侧**：B_E 用 A5 规划 CU；anchored key central **363.6 CU**（34–68 wells/action；setup/cell 另计）；示例预算 100,000 CU 仅买约 **275 anchored keys**；达到 decision MDE 0.10 需约 **393 keys ≈142,894.8 CU**（13362–26724 wells）；C136 1,600 keys/80% ≈ **581,760 CU**；含重复/失败板/对照/批次；setup 会计规则 charged vs sunk 必须全局一致并预注册；无货币报价 → 仅 planning CU，不写美元结论。
- **三场景**：A5 optimistic/central/conservative 价格下策略按各自预算**重跑**；排序不一致 → `cost_sensitive`，不报赢家。
- **对照/重复/失败板**：每策略计入同一对照与重复倍数（预注册 1/2/3）；失败孔/QC 按 A5 `fail_frac` 计费；不得把失败板排除在成本外。
- **轮次/板位**：同 rounds（最多 R_max 预注册）、同 plate 打包规则/eta、同 batch 上限；新细胞 setup 与独立培养另计。

## 6. 主终点/次终点与 MDE/δ_min

### 6.1 主终点（唯一）

**未测计划 top-k 决策收益**：对每个留出菜单（held-out cell/fold 的未测计划集合），策略输出 top-k 计划集；`topk_hit = |topk_policy ∩ topk_oracle| / k`（k=5 预注册；oracle 为留出菜单的真实 top-k，仅用于评估、不进入策略）。主效应 `Δ_dec = mean(topk_hit_dual − topk_hit_best_single_budget)`，按独立 cell/fold 配对；不得换 k/换指标/换聚合。

### 6.2 次终点（预注册，不作主推断）

- 归一化后悔：`Regret = (U_oracle − U_selected)/(U_oracle − U_static)`（效用定义需先冻结；否则 blocked）；
- 选择准确率（top-1 命中）；
- 预测辅助：留出计划响应/排序预测 Spearman/MAE（辅助，不是主终点）；
- 迁移：另立协议；B 不做主推断。

### 6.3 MDE/δ_min/判定

- **δ_min 暂定 0.10**（top-k hit 绝对差）；**业务效用定义未冻结前标 `blocked_by_utility_definition`**，不得假装可冻结。
- 独立单元 = 独立 held-out cell/折（技术重复/wells/keys 不算 n）；聚类在 cell/fold/batch；区间用配对 bootstrap（按独立单元）。
- 设计阶段 MDE（保守）：
  - decision accuracy（paired binary，worst-case SE）：`MDE80 = 2.801585 × sqrt(0.5/n_independent)`；
  - rank Δρ：`MDE80 = 2.801585 × sqrt(2/(n−3))`（D3 口径）。
- 数值：n=6 → decision MDE **0.8087**、rank MDE **2.2875**；n=30 → **0.3617 / 0.7625**；n=200 → 0.1401/0.2823；n=393 → **0.0999**；n=500 → **0.0886**；n=1,573 → rank 0.0999。
- 判定门（冻结前预注册）：`MDE_decision(B) ≤ δ_min ≤ headroom` 才可执行主比较；否则 `evaluation_cannot_distinguish`（记未决，不判失败/不存在）；`headroom` 由菜单 oracle−static 预计算（回溯菜单）；前瞻菜单 oracle 未知 → `oracle_unknown`，不得假装已知。

## 7. 零模型/失败类别/停止条件

- **零模型**：随机决策；随机预算分配；shuffle 计划效用（只评估，不进策略）；compute-only 同预算；experiment-only 同预算；solver-seed shuffle；菜单 label shuffle。零模型用于校准 top-k hit 的 null 分布与 MDE，不得用于选策略。
- **失败类别（预注册）**：`data_unavailable`、`design_invalid`（precision/leakage/cost/utility）、`evaluation_cannot_distinguish`、`no_increment`、`no_decision_benefit`、`cost_sensitive`、`oracle_unknown`、`protocol_deviation`、`compute_budget_exceeded`。
- **停止条件**：
  1. 同信息全局求解/共享参数后验/标准约束生成/普通决策 AL/BOED 在等预算完成同任务且不劣 → **撤一般算法新意**，只保留问题/边界；
  2. 决策收益不成立（CI 含 0/低于 δ）→ 停决策创新；预测改善但决策不改善 → `no_decision_benefit`；
  3. 只在当前背景/模拟器成立 → 停迁移/现实主张；
  4. MDE>δ 或 `blocked_by_utility_definition` → 未决并记录所需测量；
  5. 资源/成本不可得 → `data_unavailable/cost_uncalibrated`，不运行；
  6. 泄漏/实现偏差/协议偏离 → `design_invalid` 停。

## 8. 与 AL/BOED/COPEx 的关系（不得声称新颖性）

- 先例（CoMap/LAWM/MDA/COPEx、decision-focused AL、BOED/EVSI/ENBS、约束生成/动态约束）已覆盖一般概念；本设计**不主张**新 AL/BOED/COPEx 算法、不主张首次双预算、不主张预测分歧采样。
- 差别仅在**具体共享对象**（跨计划共同反事实/约束算子 + 计算认证状态）与**具体更新运算**（计算证书收紧 + 真实反馈统一修订共同对象，再改变计划选择），以及成本账进入决策状态；是否新意须由同信息/同预算对照裁决，**提前认定无效**。
- 若普通方法等效 → `no_increment`/撤新意；**不得用结果换指标/门槛**（D1 教训）。

## 9. 可执行性与所需测量（本轮结论）

- **本地可做**：T0 设计（本文件）、T1 合成器（可构建；需模拟器资格）、T2 O'Neil 回顾性 dev（仅操作/描述；决策 MDE 不可识别，不判主假设）。
- **本地不可做**：T3 前瞻湿实验（无 wet budget/报价/LOI/独立培养/板位；`data_unavailable/cost_uncalibrated`）；O'Neil 30 cells 无法达到 δ_min=0.10 的决策/rank MDE（所需独立单位≈393/1573）。
- **所需测量/缺口**：① 报价/LOI 替换 A5 系数（否则 CU 仅 planning）；② 湿预算与细胞/板位/独立培养；③ 业务效用尺度/δ_min 操作化（否则 blocked）；④ 若用 O'Neil：PEEK 披露 + 仅开发性；⑤ 模拟器资格（oracle/噪声/预算 scaling/泄漏）；⑥ 独立挑战与 Lead 批准后才可冻结/执行。

## 10. 边界

- 仅设计；不运行效果/拟合预测/读响应/湿实验；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；技术重复≠独立培养；O'Neil 限制不变；**冻结 ≠ 资源足够/关系成立/Stage 1/效果**。
- 继承 non-blind/peek：设计写作在 ON3 v1.2/QUICK 之后；未用其结果选择本设计；若未来用 O'Neil 数据必须带 PEEK 披露，不得称盲验/独立确认/预注册确认。
- D1（stop）/D3（design_invalid）/A1（data_unavailable）/C187（pair-level AL 饱和）已否定路线不重复；本设计不退回普通 pair-level AL/预测提分。
