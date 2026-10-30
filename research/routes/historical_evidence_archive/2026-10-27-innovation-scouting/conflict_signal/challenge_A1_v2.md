# R198-A1v2 复审（challenge_A1_v2.md）——同一挑战者对 5 必改落实的只读复审

2026-10-27 · 挑战者：endpoint-auditor（task-36 同一挑战者；未参与 A1 设计）· 对象：`research/2026-10-27-innovation-scouting/conflict_signal/{spec_v2.md, protocol_draft_v2.md, REVISION_A1.md, relations_check_design.md, record_v2.md, usage_v2.json}`（A1v2 = 对 [challenge_A1.md](challenge_A1.md) 的修订响应）。
方式：**只读审查 + 纯算术/元数据复核**（`tmp/challenge_a1v2_checks.py`、`tmp/challenge_a1v2_checks2.py`、`tmp/challenge_a1v2_checks3.py` → `tmp/challenge_a1v2_checks*.json`）；**不运行效果/relations_check/体检/MDE 预检，不读任何 S/U 响应，不改 A1 v1/v2 产物**。
完整性：v2 六个文件与 record_v2 §6/usage_v2 登记一致（spec_v2 `52959E29…C4D765`、protocol_v2 `15C7DA58…5260A`、REVISION `5CF8661F…FE4589`、relations_check `00D087AD…A79D207`、record_v2 `C7C8C2FD…8FED03`、usage_v2 `9AE2C942…B52D`）；A1 v1 四件 SHA 与 challenge_A1 记录一致（spec `488F719D…`、protocol `550E9AE1…`、prior_art `1753352C…`），**无事后改动**。

## 0. 总判决

**revise（≤5 必改）；当前版本不得进入 Stage 0 冻结，修完后可进入 Stage 0（relations_check + constructive 体检 + MDE 预检），Stage 0 通过前不得进入 Stage 1/效果轮。**

一句话：v2 把 v1 最致命的"判据不可成立/关系集不可执行/对照缺失/协议不可执行"大部分补上了，**X_flip 的 n/α/MDE 算术这次是对的**（我逐项复算：p=0.0031738、0.0002441，power 0.8816/0.6590）；但**关系集验收与 Stage 1 上下文算术在 Jaaks 资源上仍自相矛盾**：tissue-specific 关系 + n_ctx=12 + "每 tissue ≥3 条" 在 Pancreas（29 细胞）上不可行；P0a 的区间宽度验收依赖 P0d（当前 blocked）的决策效用范围 → P0a 永远无法 PASS；覆盖 ≥50% 的分母未定义（按 229 候选关系计需 ≥115 条，远大于 R_min=20）；"MDE=p1≥0.95 时 80% 功效"的标注与真值（80% 功效在 p1≈0.9307）不符。**这些是算术/协议定义问题，可修，但修之前跑 Stage 0 只会以 `data_unavailable` 收场且分不清"资源不可达"与"协议自相矛盾"。**

**最致命 3 条**

1. **Stage 1 的 X_flip 在 tissue-specific Cond_r 下不可达（不是"风险"，是算术）**：X_flip 的上下文是 S 细胞且必须落在同一 Cond_r（含 tissue 细胞组）；S=24 按 tissue 分层只有约 6–10/组织（按 matched 96 比例：Breast 8.25、Colon 8.75、Pancreas 7.0；按 Original 125 比例：Breast 9.8、Colon 8.6、Pancreas 5.6）< n_ctx_min=12。Jaaks Pancreas 只有 **29** 个 Original 细胞（matched 28），而 reference A/B 每 tissue 各需 ≥12 → 24 个，**24+12=36 > 29**：即使把 S 全给 Pancreas 也不够。故"每 tissue ≥3 条关系 + n_ctx=12"与 S=24 不能同时成立；A1v2 只在 REVISION §3 "残余"里写"可达性待 Stage 0 实测"，**没有算出这个结构性不可行**，Stage 0 会先"通过"关系构造，Stage 1 才死在 X_flip 上。
2. **P0a 验收自相矛盾**：区间宽度验收 = `≤min(2.0σ_r, 0.10×决策效用范围)`，但"决策效用范围"只在 P0d（δ_min/成本/效用，当前 `blocked_by_utility_definition`）才定义 → **P0a 永远无法 PASS**（P0a 在前、P0d 在后且 blocked）。覆盖 ≥50% 的分母也没写：按 229 个候选关系网格计，50% = **≥115 条通过关系**（远大于 R_min=20；我复核：A42/B42 切分下 96 匹配细胞上有 **154** 个候选同时满足 A/B ≥12 细胞，故 supply 够、但要求从 20 变成 115 必须写清）；按 cell×condition 计则完全是另一个含义。`relations_check` 的 PASS/FAIL 因此不可判定。
3. **MDE 标注错误 + 依赖/上下文定义未冻结**：n=12 时精确单侧 80% 功效发生在 **p1≈0.9307**（0.95 时功效 0.8816；0.90 时 0.6590），所以"预注册 MDE = 真实一致翻转率 0.95 时 80% 功效"是自相矛盾的标注（0.95 是保守设计目标，不是 MDE）；且没有 n-p1 表（我复算：p1=0.90 需 n=14/k=12（power 0.842）、0.85 需 n=19/k=15（0.856）、0.98 需 n=7/k=7（0.868））与"可用上下文上限"的对照。另：spec_v2 §3.1 说上下文是"（细胞组对,…）的一组独立复验单位（如一个 cell-pair 组）"，relations_check §4.4 又说"上下文=不同细胞"——**两处定义冲突**；若按 cell-pair 组，S=24 连单组织 12 个上下文都不够（需 24 细胞/组织）。sign test 把 12 个共享药对/板/批的细胞当独立 Bernoulli，P0b 若用 iid 生成则 type-I/功效会偏乐观。

## 1. 六项判决摘要

| # | 复审项 | 判定 | 一句话依据 |
|---|---|---|---|
| ① | 判据可成立（n/α/BH/MDE/两评分裁决） | **WEAK（算术 PASS；MDE 标注/依赖/上下文定义 FAIL 子项）** | p=0.00317、power 0.882/0.659 都正确（复算通过）；但 MDE 标注与真值不符（80% at p1≈0.9307）、缺 n-p1 表、sign test 独立性与 context 定义未冻结 |
| ② | 分类可证伪（setup_error/多解释/χ² 依赖/σ 带/d_rel） | **WEAK** | 第四解释、无顺序默认、χ² 依赖、σ 带、d_rel 降级都已写（PASS）；但 M_setup 无正式概率模型、惩罚拟合准则/δ_fit 未定义、κ 可能被违反关系污染、退出上限 15%/10% 无推导 |
| ③ | 关系集可执行（R_min/n_ctx/A-B/S-U/screen/lineage/Stage 0） | **FAIL** | Pancreas 29 细胞 vs reference 24+S12=36 算术不可行；"每 tissue≥3" 与 n_ctx=12 冲突；P0a 宽度验收依赖 blocked 的 P0d；覆盖分母未定义（关系网格口径需 ≥115 条）；S=24 分层 ~8/tissue <12；可达性只作"风险披露"未作算术结论 |
| ④ | 机制对照（M1 (a)–(d)、QP 不等价、P1/P2、释放集、M2 VOI、Stage 2 门控） | **WEAK（多数 PASS）** | (a)–(d)+基线、QP 不等价、P1 样本外/P2 主、释放集规模/近似/60 s、M2 VOI/decision-focused 对照、Stage 2 门控都已补；但惩罚拟合/δ_fit、J 候选生成、P2 依赖 blocked 的 δ_min 仍未写死 |
| ⑤ | 协议/门控/措辞（P0a–P0d、δ_min blocked、U、预算、失败类别、Stage 1 判类、A4/A5、措辞） | **WEAK（多数 PASS）** | P0a–P0d、blocked 状态、C141、预算墙钟、失败类别、Stage 1 只判 (i)/(ii)/(setup)、(iii) proxy、A4/A5 接口、措辞模板、标题修正都已落实；但 P0a/P0d 顺序与宽度依赖、退出上限分母、spec_v2 §4.4 与 relations_check 的 64/16 vs 84/24/17 数字不一致、P0b 用参考统计量生成注入的泄漏风险未处理 |
| ⑥ | 总判决 / 是否可进入 Stage 0 | **revise（≤5 必改）；修完可进入 Stage 0，当前不可** | 见 §0/§7；Stage 0 = relations_check + constructive + MDE 预检，本身不产效果；但现版本 Stage 0 验收不可判定 |

## 2. ① 判据算术逐项复核（WEAK：算术 PASS，标注/依赖/定义 FAIL）

**复算结果（`tmp/challenge_a1v2_checks.py`/`checks2.py`，精确二项）：**

| 量 | A1v2 写的 | 我复算 | 判定 |
|---|---|---|---|
| n=12 时 P(X≥11 \| p=0.5) | 0.00317 | **0.0031738** | ✓ |
| n=12 时 P(X=12) | 0.000244 | **0.0002441** | ✓ |
| α=0.01 的拒绝域 | k≥11 | k≥11（k=10 的 p=0.0193>0.01） | ✓ |
| power(p1=0.95) | 0.882 | **0.88164** | ✓ |
| power(p1=0.90) | 0.659 | **0.65900** | ✓ |
| "MDE=p1≥0.95 时 80% 功效" | 0.95 | **80% 功效在 p1≈0.93074**（0.95 时 0.8816） | **标注不符** |
| "更低 p1 须增大 n、不得放宽 α" | 已写死（spec_v2 §3.1 / P4.6） | ✓ 已写 | ✓（但缺 n 表） |
| n-p1 表 | 无 | p1=0.98→n=7,k=7（0.868）；0.95→n=11,k=10（0.898）；0.93→n=11,k=10（0.823）；0.90→n=14,k=12（0.842）；0.85→n=19,k=15（0.856） | **需补** |
| BH：m=10 primary, q=0.10, 首个阈值 0.01 | 写死 | p=0.0031738 ≤0.01 → 通过第一步 | ✓ |
| 两评分流程裁决规则 | P4.5 | 已写（setup 优先→setup；ii 签名但 M_ii 未领先→ambiguous；其余→ambiguous；无第三方） | ✓ |

**仍然 FAIL/WEAK 的子项：**

1. **MDE 标注必须改**：80% 功效的 MDE 是 p1≈0.9307；v2 把"p1≥0.95 时 80% 功效"写成 MDE 定义，自相矛盾（0.95 是保守设计目标，不是 MDE）。建议：① 明确 `MDE(80% power, n=12, α=0.01) = p1≈0.931`；② 保留"设计目标 p1≥0.95（power 0.882）"作为保守要求；③ 补 n-p1 表并说明 S 端可用上下文上限（见 ③）。
2. **独立性/type-I 未校准**：精确符号检验把 12 个上下文当独立 Bernoulli；上下文是细胞（见 ③ 的定义冲突），共享药对/剂量/板/批 → 存在正相关/过散布。P0b 只写"用参考统计量生成注入"，**没有写依赖结构**；若注入是 iid，则 recall/precision/type-I 只验证 iid 假设，不能验证真实依赖。必须：P0b/P0c 用**依赖生成模型**（cell/tissue/batch 随机效应；上下文内相关 ρ）模拟，报告 type-I 与 power 对 ρ 的敏感性；或用 block permutation/κ 膨胀给出主检验的校准（并说明 κ 取值来源与污染风险，见 ②）。
3. **上下文定义冲突**：spec_v2 §3.1 "一个上下文= …（细胞组对, 方向, 剂量布局）的一组独立复验单位（如同一 Cond_r 内的一个 cell-pair 组）" vs relations_check §4.4/3.6 "上下文=不同细胞，互不共享；n_ctx=12（B 内可计算细胞数）"。两者对 n_ctx 的资源需求差 2 倍（cell vs cell-pair）；必须先冻结一种，并与 S 规模/组织约束对齐。
4. **"每 tissue ≥3" 与 n_ctx=12 的联合约束未检查**（见 ③）：这是算术不可行，不只是 MDE 标注问题。

## 3. ② 分类可证伪（WEAK）

**PASS 的部分（v1 的 FAIL 已实质修复）：**
- **第四解释 `setup_error` 已加**（spec_v2 §2(iv)）：区间覆盖诊断、σ 带翻转、异方差/聚集、批次吸收后 `C_conf` 消失；失败类别 `model_misspecified`（含 `noise_model_invalid`/`interval_miscalibrated`）已进 P6。
- **取消顺序默认**（spec_v2 §3.3、P4.1–P4.3）：四解释同数据/同预算按惩罚拟合比较，"释放廉价不是 (ii) 的证据"；加同尺寸随机释放、soft-penalty、无释放 constrained ridge 对照。
- **χ² 依赖感知**（spec_v2 §3.2、P4.4）：双层块置换/聚类 bootstrap（≥2,000）或 κ 方差膨胀（引 C174 的 ~10.33× 警告）；σ 在 [σ_lo,σ_hi] 带内分类一致，否则 `ambiguous_conflict`。
- **d_rel 降级**为描述量（spec_v2 §2(i)）✓。

**WEAK 的子项（冻结前必须修）：**
1. **M_setup 没有正式概率模型**：v2 只说"区间/σ/批次重估后的更新"，但没有给出与 M_i/M_ii 可比拟的似然/预测分布。四解释"惩罚拟合比较"因此不可执行、也不可证伪（setup 成了吸收一切的标签）。必须写死 M_setup 的生成模型（如：batch 随机效应、σ 的自由估计、区间重校准参数）与拟合/预测公式。
2. **惩罚拟合准则/δ_fit 未定义**：spec_v2 §3.3 只说"{样本外拟合, 复杂度/代价, Δ_pred(U)}"，没有权重、评分公式、δ_fit 数值、CV/held-out 切分（留出上下文/细胞的具体规则）。没有这些，判类规则无法执行，也无法在 P0b 中检验。
3. **κ 估计可能被关系违反污染**：κ 由参考数据估（spec_v2 §3.2），但参考数据恰是关系构造与违反检验的数据；若参考中存在被违反关系，κ 被抬高/压低的方向不明。必须：用 nuisance-only/留出参考半/置换估计 κ，或报告 κ 在 [κ_lo,κ_hi] 带内结论稳定性（并说明 P10 问题 3 的答案）。
4. **退出上限 15%/10% 无推导**：`not_identifiable ≤15%`、`ambiguous_conflict ≤10%` 被写成 design_invalid 触发线，但没有从 P0b 的期望退出率或任何分布推出；多解释比较下 ambiguous 可能天然 >10%。必须：由 P0b 的注入体检/预期率推导上限（或按 Stage 1 实际 eligible 单元数给操作定义与分母），否则设计一跑就 `design_invalid`。

## 4. ③ 关系集可执行（FAIL）

### 4.1 已落实/可保留（PASS 部分）

`R_min=20/R_max=200`；`n_ctx_min=12`；构造半 A（42）/校准半 B（42）方向一致率 ≥0.90 + 半交换；区间只在 B 估、宽度 ≤min(2σ_r, 0.10×效用范围)、`|μ_r|≥0.5σ_r`；覆盖 ≥50%；每 tissue ≥3；primary ≤10；S/参考/U 三元不交（参考 84、S 24、U≈17）；screen/batch 进 nuisance；跨 screen 只作敏感性；**非重聚合 lineage 段**；MDE 预检与 `insufficient_precision`/`data_unavailable` 停；`relations_check.json`/`relations.csv` SHA 冻结；"被丢弃原因分布"要求。**这些方向都对，且比 v1 实质进步。**

### 4.2 FAIL 的算术/协议矛盾（必须先修）

**(a) tissue-specific 关系 + n_ctx=12 在 Pancreas 上不可行（决定性）。**
- 我复核 Jaaks Original 125 细胞的 tissue 分布：**Breast 51、Colon 45、Pancreas 29**；A0 matched 96：Breast 33、Colon 35、Pancreas 28。
- 关系构造要求 A/B 每 tissue 各 ≥12 细胞（A 半选方向、B 半估区间/上下文），即每 tissue reference ≥24；X_flip 的上下文是 S 中同一 Cond_r（含 tissue）的 ≥12 细胞。Pancreas：reference 24 + S 12 = **36 > 29**。**即使把 S 全部 24 个细胞都给 Pancreas，也不够 12（只剩 5）**；Breast/Colon 在总量上可凑（51/45），但 S=24 分层后每 tissue 也只有 ~8 <12。
- 因此"每 tissue ≥3 条关系"（P0a 全局验收）与"每条关系 n_ctx≥12"（X_flip）**不能同时成立**；Stage 0 可以构造出 Pancreas 关系（reference 侧 31 个候选满足 A/B≥12；见 4.3），但 Stage 1 的 X_flip 会因 S 组织细胞数 <12 而必然失败。A1v2 把可达性写成"待 Stage 0 实测"不够——**这是协议结构矛盾，不是资源未知**；Stage 0 实测只会确认并浪费一轮。
- 修法（三选一，Lead 决策）：① 把主族 G 改为**跨 tissue 池化**（tissue 作 nuisance/分层，不要求 per-tissue n_ctx），per-tissue 关系降为 exploratory/仅 Stage 0 构造；② 主族只保留 Breast/Colon（明确外部有效性限制），删除"每 tissue ≥3"或改为"≥2 tissue"；③ 承认 n_ctx=12 与本资源不兼容 → `data_unavailable`/另定资源。**不得**只降低 n_ctx（n=5 连 α=0.01 都不可达；n=7 power 仅 0.698 at p1=0.95；n=11 才 0.898）或放宽 α。

**(b) P0a 验收自相矛盾（顺序/分母）。**
- 区间宽度验收引用"0.10×决策效用范围"，但效用范围/δ_min 在 P0d 定义且**当前 `blocked_by_utility_definition`** → P0a 无法 PASS。必须：Stage 0 只用 `2.0σ_r` 宽度判据；`0.10×效用范围` 移到 P0d/Stage 1 冻结后再验；或把 P0d 重排到 P0a 之前（若效用可先定义）。
- 覆盖 ≥50% 的分母未定义：按我复核的 229 个候选关系网格（96 matched 细胞），50% = **≥115 条通过关系**，与 `R_min=20` 相差近 6 倍；若按 cell×condition 单元计则是另一口径。必须冻结分母（建议：关系网格 = `G×anchor×设计×library 对`，并明确 115 这个实际要求；或明确覆盖按单元计并给公式/数字）。

**(c) S=24/参考 84/U 17 与 125 vs 96 的分配细节未写清。**
- `relations_check` §0 输入是 A0 `matched_conditions.csv`（96 细胞），但 §1 的分配写"Jaaks Original 的 125 个细胞"；reference 84 必须 ⊆ 96 matched（否则其关系候选不存在），S/U 则来自余下 41（12 matched  leftovers + 29 unmatched）。文档未写这条约束，也未写 S 细胞需要 Original 条件覆盖（Cond_r 匹配）的预检。必须：写死"reference ⊆ matched 96；S/U 可含 unmatched；S 侧 Cond_r 覆盖由独立 runner 以 metadata-only 预检"。
- spec_v2 §4.4 的示例"参考 64/S 16/U 其余"与 relations_check/record 的"84/24/17"不一致；冻结以哪个为准必须写清（v2 目前两处并存）。

**(d) 关系供给/可达性披露的评价（部分 PASS）**：
- 我复核：96 matched 细胞上候选关系 229 个；按 A42/B42（Breast14/Colon16/Pancreas12）示例切分，**154** 个候选同时满足 A/B ≥12 细胞（Breast 86、Colon 37、Pancreas 31）→ `R_min=20` 的 reference 侧供给**可行**；但（i）这是示例切分非冻结切分（冻结后可能变化）；（ii）覆盖 50% 若按关系网格需 ≥115 条，供给 154 虽够但余量小；（iii）**真正的瓶颈在 S 侧 X_flip，不在 reference 侧**——A1v2 的"可达性风险"披露只覆盖了 reference 侧的一部分，未覆盖 S 侧组织细胞数与 tissue-specific 上下文，故判 FAIL（披露不完整）。

## 5. ④ 机制对照（WEAK；多数 PASS）

**PASS：**
- M1 必比 (a) 等式保护投影核、(b) 同区间无释放 constrained ridge、(c) soft-penalty/层级先验、(d) 尺寸匹配随机释放 + 全量重训/普通适配/层级/GP（spec_v2 §5.1、P3）。
- **等价性条件写清**：等式约束且无激活约束才等价投影核/普通 ridge；区间激活绑定时是 QP，不等价 → 不得要求数值等同，只做 KKT/自校验（§5.1）✓。
- **P1 去循环**：样本外诊断增量；**P2 为主机制检验**（J_min 释放 vs 同尺寸随机释放 vs 无释放 constrained ridge vs soft-penalty；未查询决策损失）✓。
- **最小释放集规模/近似**：|R_old|≤200、精确 |R|≤30（分支定界/LP，60 s/单元）、否则贪心+LP 下界并报 gap、`J_max=min(5,ceil(0.10|R_old|))`、无认证 → `ambiguous_conflict` ✓。
- **M2 先例/对照**：补 decision-focused sequential design、GoBOED、EVSI/ENBS、Poke&Strike；Stage 2 必比 VOI baseline；无区分测量 → `no_discriminating_measurement` ✓。Stage 2 门控在 P0a–P0d + Stage 1 pass 之后 ✓。

**WEAK（必须补）：**
1. 惩罚拟合/δ_fit 与 J 候选生成规则仍未写死（见 ②），导致 M_i/M_ii(J)/M_setup 的比较不可执行；P2 的"J_min 释放"依赖 J_min 的认证规则（已有规模/时间上限），但 J 候选族（哪些 J 进入比较）未定义。
2. P2 的主指标 δ_min 仍 blocked → P2 的 MDE 无法预检；这是协议允许的 blocked 状态，但 Stage 1 冻结清单必须把"δ_min 已定义 + P0c 通过"作为硬条件（v2 P9 已部分写，需与 P2 对齐）。
3. M2 的"每成本决策翻转概率"依赖 A5 成本接口（A5 未冻结）→ Stage 2 只能条件化；v2 已写"Stage 2 不启动" ✓。

## 6. ⑤ 协议/门控/措辞（WEAK；多数 PASS）

**PASS：**
- P0a–P0d 前置、δ_min 未定义 → `blocked_by_utility_definition`（不编造）✓；U 菜单/成本/C141（只排组合不排细胞）✓；预算/墙钟（Stage 0 ≤30/20/15 min；Stage 1 每臂 ≤45 min、总 ≤2 h；bootstrap/置换 ≥2,000；释放 60 s/单元）✓；失败类别完整（data_unavailable/insufficient_precision/design_invalid/model_misspecified/not_identifiable/ambiguous/explained_by_baseline/conflict_only_in_development/proxy_only/leakage/pass_to_stage2/completed_null）✓；**Stage 1 只判 (i)/(ii)/(setup)，(iii) 只 `proxy_only`** ✓；A4/A5 协调 ✓；措辞模板（operational 归因；不写新颖性/机制/迁移/决策收益；`not_identifiable`/`insufficient_precision`/`proxy_only`/`completed_null` 不得写成阴性/不存在）✓；标题 R198-A1 修正 ✓。

**WEAK（必须补）：**
1. **P0a/P0d 顺序与宽度依赖**（见 ③(b)）；P0b/P0c/P0d 的执行顺序与失败短路规则要写成流程图（当前 P0a–P0d 列表未写"先测哪个、失败是否阻断"）。
2. **退出上限分母**：`not_identifiable ≤15%`、`ambiguous ≤10%` 的"反馈单元"是哪些（S 中 eligible Cond_r 单元？全部 S 单元？）未写；且上限未从 P0b 推导（见 ②）。
3. **P0b 注入生成器**：v2 写"用参考统计量生成"——若直接用参考残差/关系结构生成注入，则注入与判据共享统计量，体检会自证；必须写独立生成器（已知 i/ii/setup 的合成模型，参数由参考估计但**不把参考的违反结构注入**），并明确 iid/依赖两种生成。
4. **spec_v2 §4.4 与 relations_check/record 的参考细胞数不一致**（64/16 示例 vs 84/24/17）；冻结前统一并说明示例是否作废。
5. **P0c 的"80% 功效 ±0.05"**：容差与"预注册 δ_min"的关系、样本量/模拟次数（当前只写 Stage 0 ≤15 min）、以及"n_eff 只来自同一 96 细胞 → insufficient_precision"的判定公式需写死。
6. **P0a 之 S 侧预检**（见 ③）：P0a 应在不读响应前提下（独立 runner 以 metadata）预检"每关系在 S 侧可用的 Cond_r 细胞数 ≥12"，否则 Stage 0 PASS 而 Stage 1 必死。

## 7. ⑥ 总判决、是否可进入 Stage 0、5 条必改（≤5）

**总判决：revise（≤5 必改，修完重审后可进入 Stage 0）。当前版本不得进入 Stage 0 冻结，也不得进入 Stage 1/效果轮。**
- **是否可进入 Stage 0**：**否（当前版本）**。Stage 0 本身（relations_check + constructive 体检 + MDE 预检）是对的方向，但现版本的 P0a 验收不可判定（宽度依赖 blocked 的 P0d、覆盖分母未定义）且 S 侧 n_ctx 在 tissue-specific 下不可达；先修下列 5 条，再跑 Stage 0，否则只会以 `data_unavailable`/`design_invalid` 收场且无法归因。
- 修好后 Stage 0 的产出即：relations.csv/relations_check.json（含被丢弃原因）、constructive 体检结果、MDE 预检；**Stage 0 通过前不进入 Stage 1，任何 Stage 0 数字不作效果证据**。

**必改（5 条，可执行）**

1. **修 tissue/context/分配算术（③ 的关键）**：写死细胞可行性表（Original Breast 51/Colon 45/Pancreas 29；matched 96: 33/35/28）；若坚持 tissue-specific + n_ctx=12 + 每 tissue≥3 → Pancreas 36>29，**算术不可行**，必须改 G 为跨 tissue 池化（tissue 进 nuisance/分层，per-tissue 关系降 exploratory）或主族限 Breast/Colon 并披露外部有效性，或停（`data_unavailable`）；不得降 n_ctx（n=7 power 0.698、n=5 α=0.01 不可达）或放宽 α。同时冻结 context 定义（cell vs cell-pair），统一 spec_v2 §3.1 与 relations_check §4.4，并在 P0a 增加"每关系 S 侧可用 Cond_r 细胞 ≥12（metadata-only，独立 runner）"的预检。
2. **修 P0a 验收与顺序（③ 的 PASS/FAIL 可判定性）**：覆盖 ≥50% 冻结分母（建议关系网格：229 候选 → ≥115 条通过；或明确改 cell×condition 单元口径并给数字）；区间宽度 Stage 0 只用 `2.0σ_r`，`0.10×效用范围` 移到 P0d 之后；重排 P0a–P0d（或明确依赖图与失败短路），使 P0a 在 δ_min blocked 时仍可判定。
3. **修 MDE/统计标注与依赖校准（① 的核心）**：写 `MDE(80%, n=12, α=0.01)=p1≈0.931`；保留 `p1≥0.95` 为保守设计目标（power 0.882）；补 n-p1 表（0.90→14/k=12、0.85→19/k=15、0.98→7/k=7）；P0b/P0c 用依赖生成模型（cell/tissue/batch 随机效应）校准 type-I/power 并报 ρ/κ 敏感性；明确 primary 家族选择（稳定性排序）与 BH/α 的组合关系。
4. **修第四解释与模型比较（② 的核心）**：给 M_setup 正式概率模型（batch 随机效应/σ 估计/区间重校准）与共享预测似然；写死惩罚拟合准则（公式、权重、δ_fit、CV/held-out 切分）与 J 候选族生成规则；κ 用 nuisance-only/留出半/置换估计并报带内稳定性；退出上限（15%/10%）从 P0b 期望率推导或给 operational 分母。
5. **修遗留一致性与体检生成器（⑤ 的核心）**：统一 spec_v2 §4.4 与 relations_check/record 的参考/S/U 数字（84/24/17 为准，示例 64/16 作废或改正）；P0b 注入用独立生成器（不得注入参考违反结构；含 iid 与依赖两种）；P0c 的 ±0.05 容差、模拟次数、n_eff 判定公式写死；P0a–P0d 流程与失败短路写成可执行清单；保留 A4/A5 接口、Stage 1 只判 (i)/(ii)/(setup)、(iii) proxy 与措辞模板。

## 8. 保留项（v2 的实质进步，应保留）

- X_flip 的精确算术（n=12/k≥11/α=0.01）与"低 p1 增大 n、不得事后放宽 α"的纪律（spec_v2 §3.1、P4.6）——**数值我复算正确**。
- 第四解释 setup_error + 无顺序默认 + 多解释比较 + 尺寸匹配随机释放 + soft-penalty/区间 ridge：这是对 v1 "偏向 (ii)" 的正确修复（§2(iv)/§3.3/P4）。
- χ² 依赖感知（双层块置换/κ）+ σ 带一致性 + d_rel 降级（§3.2）。
- 关系集：R_min/R_max、A/B 分离+交换、区间宽度、覆盖、S/参考/U 不交、screen nuisance、lineage、SHA 冻结、`data_unavailable` 停（§4、relations_check）。
- 机制对照 (a)–(d) + QP 不等价说明 + P1 样本外/P2 主 + 释放集规模/近似/60 s + M2 VOI 先例/对照（§5.1–5.3、P3）。
- 协议：P0a–P0d、δ_min blocked、U/C141、预算、失败类别、Stage 1 三类、(iii) proxy、A4/A5 接口、措辞模板、标题修正（protocol_v2）。
- 诚实披露：REVISION §7 仍存缺口（relations_check/体检/MDE 未运行、R_min 可达性未知、δ_min blocked、(iii) 不可认证、A5 未冻结）——应保留并升级为"算术结论"而非仅"未知"。

## 9. 复核证据与本轮边界

- **复核脚本**：`tmp/challenge_a1v2_checks.py`（n=12 精确二项、power、BH、tissue 细胞数、allocation 算术、候选关系供给）→ `tmp/challenge_a1v2_checks.json`；`tmp/challenge_a1v2_checks2.py`（修正 min-n 表、A/B 候选供给）→ `checks2.json`；`tmp/challenge_a1v2_checks3.py`（A42/B42 精确切分候选供给）→ `checks3.json`。
- **关键数字**：Original 125 细胞 Breast 51/Colon 45/Pancreas 29，matched 96: 33/35/28；tissue-specific（reference A/B≥12 each + S≥12）=36 > Pancreas 29；S=24 分层 ~8/tissue；候选关系 229，A42/B42 下 154 个 A/B 均 ≥12（Breast 86/Colon 37/Pancreas 31）；覆盖 50% 关系网格 = 115 条；n-p1 表见 §2；BH m=10 q=0.10 首阈 0.01，p=0.0031738 通过。
- **完整性**：v1 四件 SHA 未变（spec `488F719D…`、protocol `550E9AE1…`、prior_art `1753352C…`、record `4926B4EF…`）；v2 六件 SHA 与 record_v2 §6 一致（见页首）；**未改任何 A1 产物、其它目录、INDEX/SYNTHESIS/git**；只新增本文件与 `tmp/`。
- **边界**：本轮**不运行效果/relations_check/constructive 体检/MDE 预检、不训练、不读 S/U 或参考响应做效果**；所有数字是元数据/纯算术/协议审查，不是生物学或效果证据；挑战结论不构成对 A1 作者身份或既往记录的改写。
- **给 Lead 的建议**：若保留 A1 线 → 先按 5 必改修订（尤其 tissue/S 算术与 P0a 验收），再**由同一挑战者**复审一次，之后才进入 Stage 0；若 Lead 认为 pooled-G 改变了原科学命题（关系不再 tissue-specific），则需在记录中把命题收窄为"跨组织池化的关系冲突"，并把 per-tissue 关系降为 exploratory——不得两边都写。
