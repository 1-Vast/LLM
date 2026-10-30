# R201-B 独立挑战（task-105）：双预算决策设计

2026-10-28。角色：独立挑战者（非提案者、未参与 B、不运行效果/不拟合/不读响应值）。对象：[PROBLEM_B.md](PROBLEM_B.md)、[DESIGN_B.md](DESIGN_B.md)、[design_B.py](design_B.py)、[design_B.json](design_B.json)、[report_B.md](report_B.md)、[record_B.md](record_B.md)、R201 BRIEF、`agent-cell-colearning/report.md` D2、D1/D3/ON2-EX/ON3/PEEK、A5 cost、C187/C190。**本轮只做设计/算术挑战；不运行效果、不拟合、不读响应；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_to_lead_mvp，也不是 stop）。**

B 的形式化骨架和 T1/T2/T3 的分层是清楚的，MDE/预算算术大部分正确（T1 500→0.0886、T2 n=6/30→0.8087/0.3617 与 rank 2.2875/0.7625、T3 393 key→142,894.8 CU、A5 100k→275 key、C136 1600 key→581,760 CU、B_C 与 ON3 锚均与我独立重算一致）；O'Neil 判 `evaluation_cannot_distinguish`、T3 `data_unavailable/cost_uncalibrated`、T1 仅计算证据、D1/D3/A1/C187 不重复、PEEK/非盲边界都基本正确。**但 T1 模拟器预注册前有三个必须先修的设计缺陷：**

1. **"同总成本"与 H_B 的"最佳单一预算"没有可核查的等成本定义**：π_dual 同时花 `(B_C,B_E)`；C7 的 compute-only / experiment-only 各只花一个预算，另一个闲置。若只是"同一预算对、允许欠花"，则 π_dual 实际总花费更高，H_B 的比较根本不公平；若要求"同总花费"，必须预注册**单预算臂如何把未用预算换成其维度**（compute-only 把 `B_E` 换成额外计算秒；experiment-only 把 `B_C` 换成额外 CU/测量）及换算规则/上限/filler。当前 DESIGN §5 只说"同一 `(B_C,B_E)` 预算对、允许欠花"，不足以支持 H_B 的"同等总成本"。
2. **compute/evidence 判据不可操作**：`g_C=(h_out−h_in)/Δ_decision` 需要 (i) 每个模型族可计算的 certificate bounds `h_in/h_out`、(ii) `Δ_decision` 由 δ_min/效用尺度换算——但 δ_min 目前 `blocked_by_utility_definition`，效用未冻结；`P(decision flip)`、`MDE_decision(B_E)`、`headroom`、`EV>cost` 都依赖同一未定义的效用/headroom。**判据链的入口和出口都悬空**。此外没有规则处理 "B_C 耗尽而 g_C>1"（应 `compute_budget_exceeded`/未决，不能自动买实验，也不能静默停）；`g_C≤1` 的 `h` 在无证书模型（GP/BOED/树）上如何定义也未写。T1 可以定义合成 utility/证书，但必须显式写"T1 用合成效用/证书，不能外推"；当前 PROBLEM/DESIGN 没有把 T1 的合成判据与真实效用分开。
3. **主终点与 MDE/δ 不同尺度**：primary 是 top-k hit（k=5，绝对差），MDE 公式却是 decision-accuracy（paired binary worst-case）与 rank Δρ 的 Fisher-z 近似；top-k hit 的方差、独立单元、null 分布未校准。T1 的 0.0886 是"decision accuracy MDE"在 n=500 下的解析值，不能直接当作 top-k hit 的 MDE；T2 的 0.3617/0.8087 同理。T3 的 393 "decision units" 与 393 "anchored keys" 混用，未定义 decision unit 是否等于 key（一个 top-k 决策需要多个 key 时，CU 会被低估）。必须用模拟器/null 校准 top-k hit 的 SE/MDE，并写死 decision unit 与成本映射。

**能否进入 T1 模拟器预注册：现在不能（revise）；完成必改 1–5 后可提交 `approve_to_lead_mvp`（只批 T1 预注册，不批 T2/T3 执行）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 形式化/判据 | **WEAK** | 决策状态（P、M_t、B_C、B_E、A、π）清楚 ✓；compute/evidence/compute_sufficient/evaluation_cannot_distinguish 分类方向正确 ✓；与 AL/BOED/COPEx 的关系诚实、不称新颖性 ✓。**但判据不可操作**：`g_C=(h_out−h_in)/Δ_decision` 的 `h` 证书表示、`Δ_decision` 与效用换算、`headroom`、`EV>cost` 均未定义；δ_min 标 `blocked_by_utility_definition`，却同时用于 g_C/MDE/判定；`compute_limited` 的"top-k 决策集改变或 g_C>1"需要先加算力，属半循环；B_C 耗尽而 g_C>1 的 fallback 未写；GP/BOED/树等无证书模型如何提供 h 未写。 |
| ② | 设计/比较器/等成本 | **FAIL/WEAK** | C0–C7 齐全、明确同信息/同更新器/同调参预算、禁止 rows/keys/wells 冒充等成本、A5 三价格场景 ✓；C2/C3/C4/C5 是强对照 ✓；oracle 只描述 ✓。**但两个核心漏洞**：(a) **H_B 的"最佳单一预算"是 `max(D(compute_only),D(experiment_only))`**，在留出测试集上取 max 是数据依赖选择，未预注册选择集/多重性/嵌套验证；这会让零分布和比较不可复现。(b) **等总成本未定义**：同一 `(B_C,B_E)` 预算对下，单预算臂只花一侧，π_dual 花两侧；"允许欠花"使 π_dual 实际总成本更高。必须写死单预算臂的未用预算换算/再分配/filler，或定义"总花费相等 + 每臂可花上限"的会计，否则 H_B 不可检验。 |
| ③ | 终点/功效/零模型 | **WEAK** | primary top-k hit（k=5，独立 cell/fold 配对）可定义；次终点与零模型（随机决策/随机预算/shuffle/单预算/solver seed/菜单 label shuffle）方向正确 ✓；O'Neil n=6/30 的 decision MDE 0.8087/0.3617 与 rank 2.2875/0.7625 >0.10，判 `evaluation_cannot_distinguish` **算术与结论正确** ✓；T1 500→0.0886 算术正确 ✓；技术重复不增 n ✓。**但**：primary 是 top-k hit，MDE 公式却是 decision-accuracy/rank；top-k hit 的 null/SE 未校准；δ_min=0.10 top-k 与 `blocked_by_utility_definition` 自相矛盾（要么定义 top-k 的操作性阈值并去掉 blocked，要么用效用/regret 作 primary 并等效用冻结）；T3 的 decision unit=393 keys 未定义；T1 的 500 replicate 是否足以校准 top-k null 也未给。 |
| ④ | 可执行性/预算 | **WEAK（算术 PASS）** | 我独立重算：T1 500→0.088594；T2 n=6→0.808748/2.287485，n=30→0.361683/0.762495；T3 393→0.099929（rank 393→0.2006，rank 需 1,573→0.09999）；393×363.6=142,894.8 CU；100,000/363.6=275.0 keys；1,600×363.6=581,760 CU；B_C 300–3600s 与 ON3 1272.06/1130.61、raw 306.722s/5,000 perms 相容——全部与 design_B.json/report 一致 ✓。T2 回顾性只作操作/描述、T3 无报价/LOI/湿预算/独立培养→`data_unavailable/cost_uncalibrated` 判断正确 ✓；PEEK/非盲披露引用正确 ✓。**但**：T1 模拟器本身的 wall/预算未核算（500 replicate×多臂×B_C 网格）；T3 393 "decision units"=393 "anchored keys" 的成本映射未定义；"A5 100k 示例只买 275 keys"是 planning 不是可执行报价；B_C 计费是否含模拟器生成/评估/调参未写。 |
| ⑤ | 边界/停止 | **WEAK** | 只设计、不运行效果/不拟合/不读响应/无湿实验 ✓；不称新颖性/机制/迁移/决策收益/资源足够 ✓；D1/D3/A1/C187 不重复 ✓；停止条件（普通方法等效→撤新意、仅预测改善→停决策创新、MDE>δ/效用未定→未决、资源不可得→停、泄漏→design_invalid）方向正确 ✓。**但**：`blocked_by_utility_definition` 与已用 δ_min=0.10/g_C/MDE 判定并存，边界不一致；"T1 仅计算证据"与"H_B 是决策收益假设"需要更清楚地分开（T1 只能检验算法行为，不能检验 H_B 的业务/生物决策收益）；T3 的"393 decision units"和"393 keys"需统一。 |
| ⑥ | 总判决 | **revise** | 见 §3。 |

## 2. 三个关键设计缺陷

### 2.1 等总成本与"最佳单一预算"（H_B 的核心）

- H_B 写"同等总成本（同一 (B_C,B_E) 预算对，或同一总 CU + 同一实测 compute 秒）下，π_dual 高于最佳单一预算策略"。
- 但 DESIGN §5 的执行口径是"所有臂在同一 `(B_C,B_E)` 预算对下比较；允许欠花但 |花−预算| ≤ 最小动作/计算单元；预注册 filler"。
  - `compute-only`（C7）不买实验，B_E 未花；`experiment-only`（C7）不做主动计算，B_C 未花；π_dual 两项都花。若"欠花"不折回，π_dual 的总资源严格更多，H_B 的"同总成本"不成立。
  - 需要预注册：单预算臂把未用预算**换成其维度**（compute-only: B_C + λ·B_E；experiment-only: B_E + μ·B_C），λ/μ 的换算需来自 A5/实测 compute 成本或明确的同成本面；或定义"总花费上限=实际花费"并要求所有臂花满/记 filler；filler 必须同信息且不计入策略优势。
  - 仅写"同一预算对"不能替代"同一总花费"；A5 三价格场景可帮助校准 λ/μ，但仍需预注册。
- **"最佳单一预算"取 max**：`Δ_dec = D(π_dual) − max(D(π_compute_only), D(π_experiment_only))` 在留出评估集上取 max，是**数据依赖的 oracle 选择**；两个单预算臂的估计噪声会使 max 偏高（对 π_dual 保守）或偏低（若用同一测试集选臂）。必须预注册：在训练/验证集上选"最佳单预算"（嵌套），或在测试集上对两个比较做多重性校正/同时 CI，并报告两个单臂分别结果；不得在测试集上先选 max 再算 CI。
- 另：`C0/C1/C6` 不是"单一预算"；H_B 只用 C7 的 max；C0/C1 可作辅助但不应混入"最佳单一预算"。

### 2.2 compute/evidence 判据悬空

- `g_C=(h_out−h_in)/Δ_decision`：`h_in/h_out` 是"内外近似/证书界"，但 DESIGN 没有定义在模型族（Bayes/GP/树/集合/约束）上如何计算；若模型不提供可认证界，g_C 不可算，策略不能执行。
- `Δ_decision` 由 δ_min 与"效用尺度"换算；但 δ_min=0.10 top-k 本身暂定且 `blocked_by_utility_definition`；有效性/成本 EV 也依赖效用。**判据入口/出口都未 frozen**。
- `headroom`（oracle−static）对 T1 合成可算、T2 回溯可算、T3 前瞻 `oracle_unknown`；设计虽写 `oracle_unknown`，但没有"在 headroom 未知时策略如何行动"的规则（不能买实验？只能 compute？）。
- `compute_limited` 触发后"继续计算直到 g_C≤1 或 B_C 耗尽"；若 B_C 耗尽仍 g_C>1，没有明确类别（应 `compute_budget_exceeded`/`evaluation_cannot_distinguish` 或 `blocked_by_compute`），不能自动买实验，也不能静默停。
- 建议：T1 明确定义合成证书（e.g., 已知线性/约束族的 h_in/h_out）与合成效用/headroom，使 g_C 可算；真实 T2/T3 仅在冻结 utility/证书后再谈；`Δ_decision` 与效用换算写死在 T1 预注册。

### 2.3 主终点与 MDE/δ 不同尺度

- primary：`topk_hit = |top-k_policy ∩ top-k_oracle|/k`（k=5，绝对差），独立 cell/fold 配对。
- 设计 MDE：decision accuracy `2.801585√(0.5/n)`（paired binary worst-case）与 rank `2.801585√(2/(n−3))`；这些不是 top-k hit 的 MDE。top-k hit 是 0–1 的有界平均（k=5 时步长 0.2），其方差/独立单元/配对相关取决于菜单和 oracle；T1 500 replicate 若只按 decision-accuracy 公式估 0.0886，不能直接当成 primary 的 MDE。
- T2 的 `n=6/30` 决策 MDE 是 decision-accuracy 口径；如果 primary 是 top-k hit，MDE 0.8087/0.3617 的数值解释不同（可能更小或更大）；目前结论"O'Neil 不可判"方向正确，但应说明是 decision-accuracy MDE，不能把同一数字当 top-k MDE。
- T3 的 393 是 decision-accuracy 的 n；**若 primary 是 top-k hit，所需 n 可能不同**；且 393 "decision units" 与 393 anchored keys 的成本映射未定义（一个决策菜单用多个 key 时，C U 成本高于 393×363.6）。
- 建议：T1 预注册把 top-k hit 的 null 分布/MDE 用模拟器或解析 null 校准（500 replicate 内部分半/独立世界），并把 decision unit 定义成"独立 cell/fold 菜单"，不再混用 key 数；T2/T3 的 n 均按该决策单元重算；`δ_min=0.10` 要么作为 top-k hit 的操作性阈值（去掉 `blocked_by_utility_definition`），要么改用效用/regret 并等效用冻结；两者只能选一。

## 3. 必改（≤5，T1 模拟器预注册前完成）

1. **等总成本 + 最佳单一预算选择**：写死单预算臂未用预算的再分配/换算（compute-only 把 B_E 换成计算秒；experiment-only 把 B_C 换成 CU/测量；或总花费上限=实际花费+filler），预注册 λ/μ 或三价格场景下的换算；H_B 的"最佳单一预算"改为训练/验证集嵌套选择或多重性校正，禁止在测试集上先 max 再算 CI；明确 C7 两臂分别报告。
2. **判据可操作化**：为 T1 定义合成证书 `h_in/h_out`（模型族、容差、预算→精度映射）、合成效用/`Δ_decision`/`headroom`；写死 `g_C` 计算、`compute_limited`/`evidence_limited`/`compute_sufficient`/`evaluation_cannot_distinguish`/`compute_budget_exceeded` 的唯一判定树；处理 B_C 耗尽、headroom 未知（T3）、无证书模型（GP/树）的 fallback；真实 T2/T3 在 utility/证书冻结前不得用这些判据下结论。
3. **统一主终点/MDE/δ**：选 top-k hit 或效用/regret 之一为 primary；若 top-k，则用 T1 模拟器校准 top-k null/MDE（不能直接用 decision-accuracy 公式），定义 decision unit（独立 cell/菜单/fold）与 key 成本映射；T2/T3 的 n/MDE 按同一 decision unit 重算；T3 393 keys 不等于 393 decision units 的成本；在 δ_min/效用未冻结时标 `blocked_by_utility_definition` 并**不得**用同一 δ 跑判定，两者只能选一。
4. **T1 模拟器预注册细节**：世界生成（共享算子/隐藏计划差/噪声/预算成本）、500 个独立 replicate 的独立性/seed、oracle 与 top-k、真值可复算、null 校准（随机决策/随机预算/shuffle/solver-seed）、无泄漏单测、C0–C7 在模拟器中的等价实现、等成本实现、两跑逐字节一致、输出 schema（每臂/每 replicate 的 topk_hit、决策集、成本账、失败类别）、T1 wall/预算测试；模拟器资格门先于任何 T1 结果。
5. **T2/T3/边界/PEEK**：T2 只作操作/描述，不判 H_B，附 PEEK_DISCLOSURE_ON3（`B4CAD955…`）与 ON3 non-blind；T3 无报价/LOI/独立培养/湿预算 → `data_unavailable/cost_uncalibrated`（当前正确，保持）；T2/T3 不得把 n=6/30 或 393 keys 当主检验；报告/JSON/PROBLEM/DESIGN 三处的 `blocked_by_utility_definition`、T1 计算证据、不得称决策收益/迁移/新颖性保持一致；D1/D3/A1/C187 状态与停止条件不变。

## 4. 若后续提交 `approve_to_lead_mvp`（T1 预注册），应包含

- 模拟器生成器：已知共享算子 + 隐藏计划差 + 噪声 + B_C/B_E 成本，500 独立 replicate；oracle/top-k 真值可复算；菜单构造纯元数据、哈希预注册。
- 强基线等价物：C0–C7 在模拟器中的明确实现，尤其 C3 普通决策 AL、C4 GP/BOED、C5 通用求解器、C6 随机预算、C7 单预算；同更新器/同信息/同预算；无自带的额外模型/额外数据。
- 等成本实现：compute-only/experiment-only 未用预算的再分配/换算、filler、对照/重复/失败；同一总花费核算。
- 统计：primary top-k hit、decision unit、null/MDE（模拟器校准）、配对 bootstrap/置换、Δ_dec 与"最佳单一预算"选择集、多重性；δ_min/合成效用；失败类别（含 `compute_budget_exceeded`/`blocked_by_utility_definition`/`oracle_unknown`）。
- 确定性/输出：两跑逐字节一致、JSON schema、成本账、T1 wall/CPU/预算；模拟器资格门先过。
- 边界：T1 仅计算证据，不外推生物/决策收益；T2/T3 不执行；PEEK 披露；不得称新颖性/机制/迁移/决策收益。

## 5. 声明

- **本轮不运行效果/不拟合/不读响应/不做湿实验**：只读 B 产物与既有报告；design_B.json 的算术只做独立重算（MDE/预算），未执行模拟器、未读 O'Neil/ON3 响应值。
- **B 产物未改**：只写本文件与 `tmp/`。
- **最终建议**：**revise**；完成必改 1–5 后可提交 `approve_to_lead_mvp`（仅 T1 模拟器预注册）；T2/T3 仍不可执行（T2 只操作/描述、T3 data_unavailable）。若 Lead 要的是真实决策收益主检验，则当前本地资源不足，应 stop 并写所需测量/报价规格。

**一句话：B 的形式化与 T1/T2/T3 分层、MDE/预算算术（T1 0.0886、T2 0.8087/0.3617、T3 142,894.8 CU、B_C/ON3 锚）大多正确，O'Neil 不可判/T3 不可得/边界也基本正确；但"同总成本"没有定义单预算臂的未用预算再分配、H_B 的"最佳单一预算"在测试集取 max 是数据依赖、compute/evidence 判据的 h/Δ/效用/headroom/EV 仍悬空、primary top-k hit 与 decision-accuracy MDE 不同尺度且 T3 393 decision units=393 keys 未定义——判 revise：先修这五点，再谈 T1 模拟器预注册；T2/T3 不执行。**
