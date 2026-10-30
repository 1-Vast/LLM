# R198-A2v2 PROTOCOL_DRAFT — 约束库 / constructive 判别体检（A1 支撑模块）

**状态：DRAFT，未冻结、未执行。** 并入 A1 整体候选冻结时才生效；本轮**不运行效果/训练/回放/拟合，不读响应做效果**。冻结前须经独立挑战复审；冻结后不得事后改端点/折/阈值/MDE/预算。
关联：[spec_v2.md](spec_v2.md)（v2 规格）、[challenge_A2.md](challenge_A2.md)（v1 挑战）、[REVISION_A2.md](REVISION_A2.md)（逐条落实）。

## §0 输入与冻结项

| 项 | 冻结值/规则 |
|---|---|
| 数据 | GDSC Jaaks **Original fitted**：`…/Original screen_All tissues_fitted data.csv`；SHA256 `1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278`；198,893,607 B |
| 端点 | **`SYNERGY_DELTA_EMAX`**（唯一主端点；Lead 确认见 R198 record §1；P-B/P-B2 冻结口径） |
| 注释 | GDSC 表内每臂单标签：`ANCHOR_PATHWAY`(17)/`LIBRARY_PATHWAY`(21)、`ANCHOR_TARGET`(40)/`LIBRARY_TARGET`(58)；**不用 P-A2 映射**（两套口径不混用） |
| 只读列（构造/切分/约束阶段） | `COMBI_ID, BARCODE, Tissue, CELL_LINE_NAME, ANCHOR_NAME, LIBRARY_NAME, ANCHOR_TARGET, LIBRARY_TARGET, ANCHOR_PATHWAY, LIBRARY_PATHWAY, ANCHOR_CONC, LIBRARY_CONC, ANCHOR_DRUG_TYPE, LIBRARY_DRUG_TYPE`（**无响应列**） |
| 响应白名单（仅 replay 评估阶段） | `SYNERGY_DELTA_EMAX`（以及预注册的单药拟合列 `LIBRARY_EMAX/XMID/AUC` 仅供 C1′ QA）；其它响应列禁止 |
| 切分 | drug-level 5 折 × 13 药；种子 **20261027**；`folds.json`（分配+每折计数）冻结 SHA |
| 反馈预算 | constructive: k∈{6,12,24,36} 网格；真实 replay: **k=24** |
| seeds | 模拟世界 `seed_base=20261027`，每世界 = seed_base + index；bootstrap/置换种子写入运行配置 |
| 时间/预算 | 单命令 ≤30 min（CPU；无 GPU）；总运行预算在冻结时按模拟批数核算（预注册） |

## §1 切分与四集合（drug-level，互不相交）

1. **折**：65 药按 `random.Random(20261027).shuffle(sorted(unique_drugs))` 排列后取 `perm[i::5]`，5 折 × 13 药；**分配表冻结**（不按字母/系列切）。实测 both-unseen 药对数 = 45/66/72/82/108，对应 cell×pair 单元 = 1,898/3,693/3,588/4,613/6,232（median cells/pair=47；以冻结 `folds.json` 为准；最小折 45 对/1,898 单元必须在功效表里作为最坏情形报告）。
2. **Ref（参考）** = 两药都不在本折 held 集合的药对单元；用于 θ/关系表/区间估计。
3. **S（反馈）** = 本折 both-unseen 池中，按响应盲规则抽 **k=24** 个 cell×pair：先按药对分层（每药对至多 1 个单元）、再按 Tissue 分层、固定种子；抽样代码与 S 列表 SHA 在**接触任何 y 之前**落盘。
4. **E（评估）** = 本折 both-unseen 池中 S 之外的 cell×pair 单元；E 的响应在 Stage 1 完成前隔离。
5. **U（行动菜单）** = 本折 both-unseen **药对**集合（药对层面；与 E 单元层面预注册分离）；U 的响应不参与任何选择/调参。
6. 断言（代码级）：`Ref ∩ S = ∅`（按药对分组）、`S ∩ E = ∅`、`S 的 cell×pair ∉ E`、U 与 S 按药对不相交；任一失败 → `data_unavailable` 停止。

## §2 约束库（冻结表）

### C2′（主约束）pathway-pair 交互方向共享
- 单位：(ANCHOR_PATHWAY×LIBRARY_PATHWAY) 组；**主检验：药对数 ≥4 的 165 组（覆盖 1,698 药对 / 90,589 cell×pair 单元）**；敏感性：≥2 药对 275 组（1,969 对）；单药对组不检验。
- 统计量：组内每条（药对,细胞）的交互符号（`SYNERGY_DELTA_EMAX` 对 0 的符号；0 记 neutral 且预注册 ≥0.1σ 死区）与组参考符号的一致率 `p_group`；对照 = 同规模随机块（保持组内药对数、两臂通路水平的可观测性与剂量布局），统计量 `T = p_group − p_random`；按药对与细胞双向聚类 bootstrap（B=2,000）给 CI。
- 零分布：药物层面置换 pathway 标签（保持每臂水平计数与药对图），1,000 次；另报尺寸匹配随机块（C152 式）。
- 多重比较：按 (anchor 通路) 族内 BH q=0.10；报告所有组，不只显著组。
- 输出：`constraint_id, group_key, n_pairs, n_units, p_group, T, CI, null_p, sign_flip_contexts, in_condition_units, out_condition_units, candidate_states, fixed_probe_list`。

### C1′（target 单药谱；QA only）
- 仅 library 臂 58 标签（51 单药 + 7 双药）；单药谱 = 同药在共同细胞上的 `LIBRARY_XMID`（或 EMAX）向量；相似度 = 组内 Spearman 中位；对照 = 打乱药↔target（层内保组大小、匹配 `LIBRARY_DRUG_TYPE`）；
- **只报描述性**；不进门控、不删约束。若未来显著：只支持"单药功能谱相似"，**禁止**"同靶点=同功能"。

### C4′（组织 exploratory）
- 3 组织；同组织内 vs 跨组织的 C2′ 一致率差；Tissue×(anchor 通路) 有 0 细胞格（记录），只作 exploratory 输出给 A1。

### C6′（注释谱系 QA）
- KEGG/Hallmark 基因集重叠与 C2′ 组相似度的秩相关；仅 QA。

### 交出：C3→R196v2；C5→R197v2/校准线（A2 不实现）
### 排除：C7 剂量占据（超出 A2 支撑范围，登记）；C8/C9/C10 不可检验（同 v1）。

## §3 Constructive 判别体检（主实验）

### 3.1 世界生成器（只用元数据维度；不读响应）
- 维度复制：65 药 / 实际药对图（2,025 对）/ 125 细胞 / 3 组织 / 165 个主组（+275 敏感性）/ cell×pair 单元按实际图；噪声/结构参数为设计网格：
  - `y = b_cell + b_pair + b_dose + g_group + s·z + ε`
  - `b_cell, b_pair ~ N(0, 0.5²)`；`b_dose` 为 2 水平（anchor/library 剂量布局）；`g_group` 为组效应；`ε ~ N(0, σ²)`，σ∈{0.5,1.0,2.0}（以 `SYNERGY_DELTA_EMAX` 预注册单位为准）。
- 注入（每类 ≥20 独立世界 × 3 σ × 3 δ；δ∈{0.5σ,1σ,2σ}）：
  - **I**：仅 nuisance 偏移（`b_cell` 加 δ、`b_pair` 加 δ、`b_dose` 加 δ），`g` 不变；
  - **II**：`g_group` 在预注册语境子集（1 组织或 1 细胞组，≥5 个独立语境）符号翻转 −2δ，条件外不变；
  - **III**：加未表征状态 z（2 水平，随机指派到细胞；`z` 效应对 y 为 δ），模型/关系里不包含 z；
  - **null**：无注入（只有 ε）。
- **标签生成方式写死**：I/II/III/null 标签由注入生成器给出（这是 construct 的定义），**不是**从响应数据反推；replay 无标签（§4）。

### 3.2 判别器 K_A2（只用约束统计；预注册规则）
1. 先做可行性/噪声检查：S 上的 C2′ 违反数、残差 r_I（nuisance 标量重估后 χ² 比）。
2. **I**：`r_I ≤ q_0.10(零分布)` 且 C2′ 违反率 ≤ 基线（预注册 0.05）→ 判 I。
3. **II**：C2′ 违反显著（CI 排除 0）且 条件内一致率 − 条件外一致率 ≥ **δ_scope=0.20**（内/外各 ≥10 单元，k≥20 才可判），且 ≥**5** 个独立语境符号翻转（与 A1 挑战修正对齐）→ 判 II。
4. **III（仅 constructive）**：全释放后残差结构化且与候选状态 z 分层相关（预注册候选：tissue/drug_type/dose_layout + A4 提供的状态；每状态 ≥6 单元）→ 判 III；真实 replay 不认证 III（只输出 `III_proxy_flag`，交 A4）。
5. 否则 `unresolvable`（必填原因：缺单元/条件不可分/状态不可测/多解释同分布）。

### 3.3 主终点与验收（预注册）
| # | 终点 | 验收 |
|---|---|---|
| E1 | I vs {II,III} 平衡正确率 | ≥0.80 |
| E2 | II vs III 平衡正确率（constructive） | ≥0.70 |
| E3 | null 假类率（type-I） | ≤0.10 |
| E4 | unresolvable 率（非 null 注入） | ≤0.25 |
- 每格 ≥20 世界；每终点做 ≥500 次模拟批（预注册模拟器代码+种子）；MDE(80% power) 用模拟给出；**若任一终点 MDE > 对应 δ_min → `design_uninformative`，不得进入 replay**。
- 判定：4 项全过→`constructive_pass`；E1 过而 E2 不过→`constructive_partial`（只报 I 可分，II/III 交 A1/A4）；E1 不过→`constructive_fail`（不换阈值重试）。

### 3.4 预算-功效表（k 冲突解决）
| k | 可判 |
|---|---|
| 6 | 仅 I vs null |
| 12 | I；II 仅提示（内/外各 6 <10 → 不达门槛） |
| 24 | I + II（12/12 ≥10）+ 语境翻转 ≥5 |
| 36 | I + II + III constructive（12/12/12，两状态×6） |
- **真实 replay 固定 k=24（只 I/II）**；III 真实认证归 A4；v1 的"k∈{6,12,24} 同时判三类"删除。

## §4 真实 replay（次级；仅 constructive_pass/partial 且 Lead 允许后）

- 每折独立：Ref→参考/关系表；S=k=24；更新器由 A1 提供；E=余下 both-unseen 单元；U=药对菜单。
- **只报**（预注册）：① C2′ 违反统计量分布与零分布对比；② 归因分布（K_A2 计数，含 unresolvable）——**描述性，不报"归因正确率"**；③ U 上 top-k 的预测排序与描述性后悔——**不给收益结论、不评 acquisition**。
- 禁止：用 E/U 响应调参/选折/改阈值；把描述当选药收益；把 replay 当"三类已被区分"的证据。
- 失败类别：`insufficient_units`（折内单元/组覆盖不足）、`not_identifiable`（多解释同分布）、`design_uninformative`。

## §5 A1/A4/A5 接口（冻结 schema）

- A2→A1 JSON 字段（每违反/组）：`constraint_id, group_key, n_pairs, n_units, stat, ci_low, ci_high, null_p, bh_q, sign_flip_contexts, in_condition_units, out_condition_units, candidate_state_text, fixed_probe_list`。
- **主判定归属**：真实 replay 归 A1；A2 的 K_A2 只在 constructive 是主检验，replay 只作数据侧证据。
- **一致性检查**：同一 constructive 世界上 K_A2 vs A1 签名 → Cohen's κ；κ≥0.60 `interface_consistent`，否则 `interface_divergent`（描述性，不验证）。
- **仲裁**：replay 冲突 → `interface_disagreement`，不取单一归因；A2 让位 A1；冲突样本全保留。
- A4：III 表征/认证；A2 只给候选状态与每状态 k=6 探针。A5：probe 收益比较；A2 的探针只作固定评估协议。
- 引用 C176/C177 作废状态；不引 C130 数字/R197 结论当证据。

## §6 失败类别与停止条件（写死）

`data_unavailable`（注释/折/组无法冻结）；`insufficient_units`（折内 <45 对 / 组覆盖 <165 / k<24 而要求 II）；`design_uninformative`（MDE > δ_min 或预算表不达）；`constructive_fail`；`constructive_partial`；`interface_divergent`/`interface_disagreement`；`not_identifiable`（replay 描述用）。
**停止**：constructive 任一主终点失败且 MDE 已足够 → 停 A2 模块（不救）；`data_unavailable` → 停；replay 出现不可判 → 只记录。**不得**把任何失败写成"关系不存在/机制无效"。

## §7 不得运行声明与冻结清单

- 本轮：**未运行**训练/回放/拟合/统计（除元数据计数）；未读响应值做效果；未改 A1 产物/其它目录/INDEX/git。
- 冻结清单：
  - [ ] `folds.json`（种子 20261027；每折 13 药/45–108 对/1,898–6,232 单元；SHA）
  - [ ] `constraints_check.json`（331/275/165 组；每折组覆盖；零分布校准；C1′ 13 doubleton 组）
  - [ ] constructive 模拟器代码 + 种子 + ≥500 批 MDE 结果
  - [ ] K_A2 阈值与接口 schema；`unresolvable` 计数规则
  - [ ] 端点 `SYNERGY_DELTA_EMAX` 列义确认（引用 R198 record）
  - [ ] seeds/SHA/失败类别/usage/时间预算（单命令 ≤30 min）
  - [ ] 明确：constructive 先于 replay；replay 不报归因正确率/收益
