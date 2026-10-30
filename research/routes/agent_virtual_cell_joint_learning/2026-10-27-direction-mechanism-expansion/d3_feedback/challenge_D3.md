# R200-D3 独立挑战（task-89）：固定反馈未查询泛化设计

2026-10-27。角色：独立挑战者（非提案者、未参与 D3、不运行效果/不拟合/不比较 acquisition、不读原始响应做统计）。对象：[PROTOCOL_D3.md](PROTOCOL_D3.md)、[d3.py](d3.py)、[d3.json](d3.json)、[report_d3.md](report_d3.md)、[record_d3.md](record_d3.md)、`exec_calibration/calib.json`（ON2-EX）、`core-module-design/oneil_dev/{PROTOCOL_ON2.md,on2.json,PEEK_DISCLOSURE_ON3.md,report_on3.md,challenge_ON3*}`、R200 BRIEF、`condition-shift/a0.json`/`q2.json`、`cross-domain-directions/`、`independent-reassessment/`。**本轮不运行效果、不拟合、不读原始 viability 响应；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_to_lead_exec，也不是 stop）。当前设计有一个可算错的致命量、一个没有功效依据的 primary、以及一个未披露的非盲历史；修完后可再走"另立 D3 执行协议"（仍需 Lead 批准与执行前复挑战）。**

最致命 3 条：
1. **MDE 先验算错/单位不匹配（可复核的算术错误）**：D3 的单元是**单 anchor 行**（2 members ×4 technical reps = **8 wells/unit**，PROTOCOL_D3 §1.1/§1.2、d3.json `resource.unit.wells_per_unit=8`），但 MDE 直接照抄 ON2-EX 的 `se_unit=0.0251494031`/`sigma_e=0.1422665081`——那是 **full 4×4 网格单元**（每成员 16 行×4 reps=64 wells；`se_unit=σ/√32`，calib.json `se_unit_denominator_sqrt=32.0`）。单 anchor 单元的 Δ 方差是 2σ²/4=σ²/2，`SE_unit=σ/√2=0.1006`，按同一公式 **MDE80=2.801585×0.1006/√6=0.11506>δ_min=0.10**（用 batch1-target 的 σ=0.1384458 → **0.11197**，也 >0.10）。**按 D3 自己的 `measured MDE80>0.10 → design_invalid` 规则，本设计先验门应 FAIL，而不是 PASS。** 另：即使用 full-grid 口径，D3 资源是 batch1 target30，应使用 calib `batch1_target_cells` 的 σ=0.1384458/MDE=0.02799，而不是 all-batches 的 0.1422665/0.02876；两处口径都不匹配。
2. **primary 是 Spearman Δρ，但没有任何 rank-level MDE/功效依据**：D3 自己承认 `MDE80 只对 mean-Δ/MAE 尺度，不是 Spearman power 保证`（PROTOCOL §4.2、d3.json `mde.rank_precision_note`），却又把 mean-Δ MDE 当 design prior/gate，并规定"measured MDE>0.10 → design_invalid"。primary H_D3 要求 **Δρ≥0.10**（秩相关差 0.10，很大），而 120 个反馈单元、单 anchor 层、6 个 held-out 细胞聚类的 rank 精度未计算；null bootstrap 只能给"是否排除 0"，给不了"是否能分辨 0.10"。没有 rank-level 的 MDE/null power，H_D3 的可证伪性不完整，执行后很可能只能落 `evaluation_cannot_distinguish`；应预注册 rank-level 的 null/模拟功效门槛，或把 H_D3 降为描述性。
3. **未披露 ON3 的 non-blind/peek 历史，且 D3 与 ON3 用同一 O'Neil 数据**：ON3 的 `PEEK_DISCLOSURE_ON3.md` 记录实现方已看到 `tmp/on3_exec_quick_debug.invalid.json`（含 **Δρ mean=0.0277068、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、每折 B0–B5** 等 primary/results），ON3 有效执行因此是 non-blind/peeked；`report_on3.md` §0.1 明确"不得称盲验/独立确认"。D3 的 PROTOCOL/report/d3.json **完全没提 ON3 peek**，只写"本任务未读原始响应值"；D3 设计写于 ON3 quick artifact 之后、同一 O'Neil complete-case 资源上，必须披露继承非盲、不得称 blind/pre-registered confirmation，并说明设计/阈值/切分是否受 ON3 QUICK 影响（若未受影响，也要写"未用于选择"）。这是预注册可信度问题。

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 资源资格与预算自洽 | **WEAK（资源数字 PASS；MDE/成本口径不自洽）** | 340,088 units/2,149 contexts/30 cells/5 folds（68,152/66,743/66,556/69,738/68,899；427–432 contexts）与 ON2 v2.2/ON2-EX 的 batch1 target30 一致（我可从 complete-case 重算复核：same units/folds）；96.91% 完整成员上下文、batch3 全失 0/5,040、702 个 15-row pair-cell、9 个 Jaaks 重叠排除、技术重复 4/member 且非独立 n——这些都披露 ✓。**但** MDE 用了 full-grid 的 SE（见 §2.1），与 8 wells/unit 的单 anchor 单元不匹配；另外"每个 unit 8 wells / 11.0 plate-equiv"只是**模拟测量成本**（数据已在资源里，并非新测），必须写成假设而非实际测量；反馈包 24 units/fold 的抽样算法（stratified hash 的 stratum/配额）未定义。 |
| ② | 唯一 primary 与 secondary 划分防选择性比较 | **WEAK** | 只有一个 primary：U_conflict−C2，其余 updater/control 都标 secondary/描述性 ✓；不得给 U_conflict 额外数据/特征/调参写死 ✓。**但** `d3.json primary_hypothesis.secondary_contrasts` 含 **"U_conflict − best ordinary control"**——"best" 是看结果后选最大，属于选择性比较；即使 secondary 也不能这样预设。另：BRIEF 要求强基线含"充分调参树模型（DrEval 2026 标准）、精确闭包、矩阵补全、直接响应预测"，D3 的 C0–C6 缺树/GBM、矩阵补全、精确闭包等强基线（C6 projected kernel 不等价），对照集不满足 BRIEF 的"强基线"要求。 |
| ③ | 反馈/成本/等信息可核查 | **WEAK** | 24 units/fold、120 total、1 轮、同包、response-independent、query=0、同历史/特征/预算等写死 ✓；算术 24×8=192 wells=2 plates、10% failure→2.2 plates/fold→11.0 total ✓。**但**：hash/stratified 的具体 stratum、配额、seed 派生、支持细胞内如何避免同 member/context 重复未定义；失败/补板/替换规则未定义（若真实湿实验）；所有 arm 的"同调参/计算预算"没有可核查的 cap（C2 全历史重训 vs C5 GP vs U_conflict 的计算量差可能很大）；反馈包 8 wells/unit 与已有数据的关系（reveal 而非新测）未说明；N1/N2 各 1,000 次重训的算力预算未核算。 |
| ④ | 终点/功效/零模型 | **FAIL** | ① MDE 单位错误（§2.1）；② primary rank 无功效/MDE（§2.2）；③ pooled Spearman 跨 5 折模型拼接，折间尺度/截距会污染全局排序，protocol 未预注册 per-fold 标准化或 per-fold Δρ 均值作为 primary/co-primary；④ N1/N2 可实现但计算量巨大（1,000×5 folds×多 arm 重训），未给预算；N2 random pack 与"response-independent hash pack"几乎同分布，作为零模型信息量低；⑤ 零模型/CI 的 cluster 重采样单位与配对方式（held-out cell 配对 bootstrap）未写死。 |
| ⑤ | 失败类别/停止/边界 | **WEAK** | 类别与停止条件写得很全 ✓；仅开发性、不比较 acquisition、不与 ΔEMAX 拼接、不称独立/迁移/决策收益/机制/新颖性 ✓。**但**：(a) `mde.stop_rule` 说 MDE>δ_min → `design_invalid`，而 `stop_conditions` 又说 "measured MDE80>δ_min **或 rank null CI includes 0** → `evaluation_cannot_distinguish`"——同一失败条件映射到两个类别，必须写死唯一映射；(b) `no_increment` 与 `evaluation_cannot_distinguish` 的边界未定义（Δρ>0 但 <δ_min、CI 排除 0 时算哪个？）；(c) 结果若只有反馈点改善，停止迁移主张 ✓，但需定义"未查询点改善"的度量/阈值；(d) 非盲/peek 披露缺失（§2.3）。 |
| ⑥ | 总判决 | **revise** | 见 §3–§4；修完并通过执行前复挑战方可另立执行协议。 |

## 2. 三个致命问题的细节

### 2.1 MDE 单位/口径（算术错误，可复核）

- D3 单元定义：`Δ(c;a,a';b) = mean viability(a,b,anchor,4 reps) − mean viability(a',b,anchor,4 reps)`；**8 wells/unit**（2 members ×4 reps；PROTOCOL §1.1、d3.json resource.unit）。
- ON2-EX 标定：`sigma_e=0.1422665081`，`se_unit=0.0251494031 = σ/√32`，`se_unit_denominator_sqrt=32.0`（calib.json constants/primary；即每成员 4 partner doses ×4 member doses ×4 reps=64 wells，Δ 方差 2σ²/64=σ²/32）。
- 单 anchor 单元：每成员仅 4 reps；Δ 方差 2σ²/4=σ²/2；`SE_unit=σ/√2=0.1005976`；`MDE80=2.8015852181×0.1005976/√6=0.1150578`（用 batch1-target σ=0.1384458171 → SE=0.0978960，MDE=**0.1119678**）。
- **结论**：MDE 先验应是 ~0.112–0.115 > δ_min=0.10 → 按 D3 的 `measured/prior MDE` 门应 `design_invalid`。当前 d3.json 写 0.0287644381 是把 full-grid 的 SE 错用于 single-anchor 单元；另外 ON2-EX 的 scope 应取 batch1 target（0.1384458/MDE 0.02799），而非 all-batches complete-case（0.1422665/0.02876）。
- 可能的修法（必须预注册其一）：(a) 改单元/聚合，使每成员 wells 增加（例如单 member-dose、average over 4 partner doses：16 wells/member、8 wells? 需重算；或 full 4×4：64 wells/member，成本大幅上升）；(b) 若有依据地把 n_eff 从 6 提到 30（5 折合并的 30 个 held-out 细胞；需解释聚类/配对），单 anchor MDE≈0.0501，但这仍是 mean-Δ 而非 rank，不能单独救 §2.2；(c) 不再用 mean-Δ MDE 作为 primary gate，另立 rank-level 功效门（§2.2）；但不得保留当前"MDE 0.02876≤0.10"的 prior pass。

### 2.2 primary 是 rank，但没有 rank 功效/MDE

- H_D3：`Δρ=ρ(U_conflict)−ρ(C2) ≥0.10`（Spearman，pooled + per fold）。
- 当前 MDE80=0.02876 是 **mean-Δ/MAE 尺度**（D3 自己写明）；对 Spearman Δρ 不构成功效保证。协议用"rank null/bootstrap + CI 排除 0"代替，但这只回答"是否有可区分差异"，不回答"能否分辨 δ_min=0.10"，且 null CI 的宽度无法先验保证。执行前应有 **rank-level MDE**：在 null/替代模拟中估计 Δρ 的 SE（按 held-out cell 配对/聚类），MDE_rank=2.801585×SE(Δρ)；要求 MDE_rank≤0.10，否则 `design_invalid: precision_insufficient`（或直接把 H_D3 降为描述性，不设可证伪 primary）。若无法做到，不能批准为"检验 H_D3"的执行。
- 另：**pooled Spearman 跨折尺度**：5 折各自训练模型、各自预测其 6 个 held-out 细胞；把不同折模型的预测拼接后算全局 ρ，会混入折间截距/尺度差。必须预注册 (i) per-fold ρ 的均值/配对差为主（或 co-primary），或 (ii) 每折内 z 标准化后再 pooled；并报告两种口径；否则 primary Δρ 可能由折间尺度而非更新器驱动。

### 2.3 非盲/peek 继承（预注册可信度）

- ON3 `PEEK_DISCLOSURE_ON3.md`：实现方已看到 `tmp/on3_exec_quick_debug.invalid.json`（QUICK=1,N_PERM=20,BOOT_B=100，含 `delta_rho_mean=0.0277068`、CI [0.01828,0.03572]、positive_folds=4、delta_rho_min_rank=0.10、per-fold B0–B5 等）；ON3 v1.1 有效执行 **non-blind/peeked**，不得称盲验/独立确认。
- D3 设计写于该 artifact 之后、同一 O'Neil complete-case 资源；D3 PROTOCOL/report/d3.json **没有 ON3 peek 段**，d3.json attestation 的 `response_values_read=false` 只说明 D3 builder 本轮未读响应，不覆盖实现方已见的 ON3 QUICK primary/results。必须写死：D3 是 **non-blind/inherited-peek** 设计；不能称 blind/pre-registered confirmation/independent；并披露 ON3 QUICK 的 Δρ/CI/positive folds 是否被用于 D3 的方向/阈值/切分/反馈预算/对比选择（若未用，按 ON3 的模板写"未用于选择"；若用了，必须如实登记并降级）。
- 这一条不影响可执行性，但影响结果解释；D3 若在 ON3 执行结果（on3_exec.json 22:38）之前设计，需说明时间线；若之后，需追加 ON3 正式结果是否影响设计。

## 3. 其他必须修的细节（并入必改）

- **controls 与 primary/secondary**：
  - 删除 `"U_conflict − best ordinary control"` 这类结果依赖的 secondary；若要比较"ordinary best"，须预注册固定 comparator（如 C2）或预注册"max over pre-specified controls + 多重性校正"的明确规则，并明确只作描述。
  - 补 BRIEF 要求的强基线：充分调参的树/GBM（DrEval 2026 标准）、精确闭包/矩阵补全、直接响应预测（若可实现）；至少说明为何 C6 projected kernel 不是 tree/GBM 的替代；否则"强对照"不满足 BRIEF。
- **feedback pack**：写死 selection 的具体算法（stratum=cell/partner/member 的层级、每层配额、seed 派生、去重、每 support cell 最多/最少几 unit）；失败/补板/替换规则；8 wells/unit 是"模拟采购预算"而不是实际新测量；11.0 plate-equivalents 的失败板假设要可核查；query=0 的评估数据来自现有资源要写明。
- **equal budget**：预注册每 arm 的计算/调参预算上限（wall/CPU、超参搜索 trials、内层 CV 次数、随机种子数），并在执行时记录；否则 C2 全历史重训 vs C5 GP vs U_conflict 的"等预算"不可验证。
- **null/CI**：N1/N2 各 1,000 次的算力预算、配对/聚类 bootstrap 单位（held-out cell 配对）、N1 置换的合法零（feedback labels within pack）、N2 的随机机制与 selection 分布的差异；N2 当前几乎与 selection 同分布，需更换或降为描述。
- **决定规则唯一映射**：`design_invalid`（MDE/rank-MDE>δ、泄漏、端点混用）vs `evaluation_cannot_distinguish`（rank CI 含 0/null 不能区分）vs `no_increment`（Δρ<δ 且 CI 排除 0/等效）vs `data_unavailable`；写死 AND/OR 与单侧/双侧、多重性；不得两个类别覆盖同一条件。
- **updater 实现**：U_conflict 的"冻结 pair/partner 可加关系"是什么模型、残差冲突分数、更新方程、超参、正则；C2/C3/C4/C5/C6 的实现与调参范围；执行协议须给伪代码/SHA/unit tests；本轮不执行，但不能留到执行时自由选择。
- **单 anchor 的限度**：anchor 固定 member dose index=4 × partner dose index=4（最高剂量档）；需说明最高剂量档的 viability 饱和/floor 风险（不是事后选，但限制外推）；只测一个 dose anchor，不能声称跨剂量泛化。

## 4. 必改（≤5，必须在"另立执行协议"前完成）

1. **修正 MDE/精度并写死执行前门**：按单 anchor 8 wells 重算 SE/MDE（σ=0.1422665 或 batch1-target σ=0.1384458；结果 0.112–0.115>0.10），或预注册改变单元/聚合（如增加 partner-dose 平均、全 4×4 单元）并用对应 wells/成本重算；若无法使单 anchor 的 mean-Δ MDE≤0.10，则停止以"mean-Δ MDE pass"作为设计门，并明确 `design_invalid`。不得保留当前的 0.02876 作为 prior pass。
2. **加 rank-level 功效门**：预注册 H_D3 的 rank MDE（2.801585×SE(Δρ)，SE 由 held-out cell 配对/聚类估计；或 null/替代模拟），要求 MDE_rank≤0.10，否则 `design_invalid: precision_insufficient`；同时写死 per-fold Δρ 均值/标准化 pooled 的口径，避免跨折尺度污染。
3. **补 ON3 non-blind/peek 披露与影响声明**：在 D3 PROTOCOL/report/d3.json/执行协议中写死：D3 是 non-blind/inherited-peek（引用 PEEK_DISCLOSURE_ON3 SHA、ON3 QUICK artifact SHA/内容），不得称盲验/独立确认；说明 ON3 QUICK 的 primary/results 是否用于 D3 的任何选择（未用/用了各写模板）；若 D3 设计晚于 ON3 正式结果，登记是否受影响。
4. **固定反馈/成本/等预算可核查**：写死 pack 的 stratum/配额/seed/去重/失败替换；8 wells/unit/11.0 plate-eq 作为模拟采购预算并给成本表；每 arm 的调参/计算预算上限与记录；N1/N2 算力预算；删除 "best ordinary control" 的结果依赖 secondary，补 BRIEF 强基线（树/GBM、矩阵补全、直接响应预测或明确理由）。
5. **统一失败/停止映射并补 updater 代码级规格**：写死 `design_invalid`/`evaluation_cannot_distinguish`/`no_increment`/`data_unavailable` 的唯一判定树（含 MDE/rank-MDE/CI/null 的 AND/OR）；U_conflict 与各 control 的模型/更新方程/超参/调参网格/unit tests/泄漏单测/两跑确定性/输出 schema，作为执行协议冻结项。

**建议路径**：先做 `revise`（不 approve）；修订后由 Lead 批准另立 D3 执行协议，并在执行前做一次"代码级预检"（MDE/rank-MDE、pack 固定、泄漏单测、预算测试、双跑）再跑效果。

## 5. 执行协议前必须补的代码级细节（若后续 approve）

- **updater 实现**：U_conflict/U_residual/U_posterior/U_leverage 的伪代码、模型（pair/partner 可加项、残差冲突定义）、更新式、超参网格、正则、停止/收敛；C0–C6 的实现与调参范围；不得给 U_conflict 额外信息/预算。
- **训练/计算预算**：每 arm 的 wall/CPU 上限、超参 trials、内层 CV 次数、seed 数；C2 全历史重训与 C5 GP 的成本记录；预算超限的失败类别。
- **统计实现**：held-out cell 配对 cluster bootstrap（B≥1,000）、pooled/per-fold ρ 的口径与折内标准化、N1 feedback-label permutation 1,000（合法零）、N2 random-pack 1,000（与 selection 分布差异）、N3 no-feedback；MDE/rank-MDE 估计脚本与门。
- **泄漏单测**：held-out 细胞不进入反馈/调参/标准化/特征选择；support cells 反馈包不含 held-out；pack hash 只依赖 ID/seed；query=0 断言；batch3/15-row pair-cell 不进入 primary；不得与 ΔEMAX 拼接/混端点。
- **两跑确定性与输出 schema**：JSON 键排序、无时间戳、allow_nan=False；两跑逐字节一致；输出 packages/units/contexts/plates/wells/failure 记录；usage 记录实际 wall/CPU/成本。
- **预算测试**：24 units/fold×8 wells=192 wells=2 plates/fold；11.0 plate-eq total（含 10% failure）；失败/补板/替换规则；query=0；所有 arm 同包同成本；plate-equivalent 是模拟预算而非真实测量。
- **披露**：ON3 peek/non-blind、ON2 v2.2 post-observation、single-anchor 派生、highest-dose anchor、technical reps not n、batch3 all lost、702 15-row pair-cell、no dual-agent reference、no ΔEMAX splicing；结果只写开发性描述。

## 6. 声明

- **本轮不运行效果/不训练/不拟合/不比较 acquisition/不读原始响应做统计**：只读了 PROTOCOL_D3/d3.py/d3.json/report/record、ON2-EX calib、ON3 peek 披露、R200 BRIEF 等元数据/文本；未执行 d3.py/未读 O'Neil 响应值。MDE 重算只是算术复核（不是效果）。
- **v1 产物未改**：D3 文件保持原样；本文件只写本目录 challenge 与 `tmp/`。
- **最终建议**：**revise**（不是 approve_to_lead_exec，也不是 stop）；完成必改 1–5 后可提交 Lead 批准另立执行协议，执行前复挑战一次。

**一句话：D3 的资源/切分/边界基本扎实（340,088 units/2,149 contexts/30 cells/5 folds、11.0 plate-eq、同包反馈），但 MDE 把 "每成员 64 wells 的 full-grid SE" 错套到 "每成员 4 wells 的 single-anchor 单元"——正确 MDE≈0.112–0.115>δ_min=0.10，按自己的门应 design_invalid；primary 是 Spearman Δρ 却没有 rank-level MDE/功效；再加上 ON3 的 non-blind peek 未披露、反馈包/等预算/对照集/失败映射与 updater 代码级规格未写死——判 revise：先修 MDE/rank 功效、补 ON3 peek 披露、固定反馈/成本/预算与对照/失败映射、补 updater 规格，再谈执行协议。**
