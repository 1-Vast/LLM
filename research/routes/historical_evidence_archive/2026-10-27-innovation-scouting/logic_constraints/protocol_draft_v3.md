# R198-A2v3 PROTOCOL_DRAFT — 约束库 / constructive 判别体检（A1 支撑模块；并入前修订）

**状态：DRAFT，未冻结、未执行。** 并入 A1 整体候选冻结时生效；**本轮不运行效果/模拟器/训练/回放/拟合，不读响应做效果**。冻结后不得改端点/折/阈值/MDE/预算/记账规则。
关联：[spec_v3.md](spec_v3.md)、[challenge_A2_v2.md](challenge_A2_v2.md)、[REVISION_A2_v3.md](REVISION_A2_v3.md)、设计版 `folds.json`/`constraints_check.json`（SHA 见 record_v3）、模拟器 `constructive_sim.py`（落盘未运行，SHA 见 record_v3）。

## §0 输入与冻结项

| 项 | 冻结值/规则 |
|---|---|
| 数据 | GDSC Jaaks **Original fitted**：`data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`；SHA256 `1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278`；198,893,607 B |
| 端点 | **`SYNERGY_DELTA_EMAX`**（唯一主端点；Lead 确认见 R198 record §1） |
| 注释 | GDSC 表内每臂单标签（ANCHOR_PATHWAY 17 / LIBRARY_PATHWAY 21 / TARGET 40/58）；**P-A2 映射不用** |
| 只读列（约束/切分/构造阶段） | `COMBI_ID, BARCODE, Tissue, CELL_LINE_NAME, ANCHOR_NAME, LIBRARY_NAME, ANCHOR_TARGET, LIBRARY_TARGET, ANCHOR_PATHWAY, LIBRARY_PATHWAY, ANCHOR_CONC, LIBRARY_CONC, ANCHOR_DRUG_TYPE, LIBRARY_DRUG_TYPE`（无响应列） |
| 响应白名单（仅 replay 评估） | `SYNERGY_DELTA_EMAX`；C1′ QA 允许 `LIBRARY_EMAX/XMID`（不参与主判定） |
| 折 | drug-level 5 折×13 药；seed 20261027；`folds.json` 冻结 SHA |
| k 网格 | constructive：6/12/20/24/36；replay：**k=24** |
| seeds | 世界生成 seed_base=20261027（每世界 seed_base+idx）；分类/MDE 模拟种子写入运行配置 |
| 预算 | 单命令 ≤30 min；constructive 估计 ≤5 min（§6）；无 GPU |

## §1 切分 / S / U（写死；消除 U/S 矛盾）

1. **折**：`sorted(unique_drugs)` → `random.Random(20261027).shuffle` → `perm[i::5]`；5 折×13 药；分配表见 `folds.json`（SHA 冻结）。
2. **both-unseen 池（每折）**：directed 对 **45/66/72/82/108**；unordered 对 **33/49/48/49/58**；cell×directed-pair 单元 **1,898/3,693/3,588/4,613/6,232**；总数（源）2,025 directed / 1,294 unordered / 108,259 单元。
3. **S = 24 cell×directed-pair 单元**，响应盲：每折 `random.Random(20261027+fold)` 洗牌 both-unseen directed 对；取 24 个**不同 directed 对且不同 unordered 对**（先保证 3 个 tissue 各 ≥2 对再补足）；每对用法向该对的细胞集合均匀抽 1 个 cell（cells 排序）。S 列表设计版在 `folds.json.S24`；接触任何 y 前落盘。
4. **U（行动菜单，主口径 unordered）** = 本折 both-unseen **unordered 对所有 − S 覆盖的 24 个 unordered 对**；大小 **9/25/24/25/34**。fold 0 U=9<10 → 预注册 top-k=5；其余 top-k=10。
5. **U（鲁棒性口径 directed）** = both-unseen directed 对 − S 的 24 directed 对；大小 **21/42/48/58/84**；top-k=10。
6. **四集合 disjoint 断言（代码级，冻结前实现）**：`Ref ∩ S = ∅`（按药对组）；`S ∩ E = ∅`；`S 的 directed/unordered 对 ∉ U`（U 定义保证）；S 单元只 reveal 一次；任一失败 → `data_unavailable`。
7. **删除** v2 的"U 与 S 按药对不相交"错误断言；v3 以"U=both-unseen − S 涉及对"实现同一目的（防止已 reveal 药对进入 U 评估）。

## §2 约束库（冻结表；C2′ 主，单位有向）

- **C2′（主）**：组 = (ANCHOR_PATHWAY, LIBRARY_PATHWAY)；主检验 **directed 药对数 ≥4 的 165 组（1,698 对 / 90,589 单元）**；敏感性 ≥2 组 275（1,969 对）；单药对组只登记。
- 统计量：组内 (药对,细胞) 交互符号一致率 `p_group`（死区 |ΔEMAX|<0.1σ 记 neutral）− 同规模随机块；按药对/细胞双向聚类 bootstrap（2,000）；零分布：药物层通路标签置换（保持每臂水平计数与药对图；1,000 次）+ 尺寸匹配随机块（C152 式）。
- 多重：按 anchor 通路族内 BH q=0.10；报告全部组。
- **无序口径敏感性**：305 组/≥2=215/≥4=117（仅报告，不作主判定）。
- **C1′（QA only）**：library 臂 58 标签（51 单 + 7 双，无 ≥3 组）；只描述，不门控、不删约束；即使显著禁止"同靶点=同功能"。
- **C4′（exploratory）**：3 组织；组织×通路 0 细胞格记录于 `constraints_check.json`。
- **C6′（QA）**：基因集重叠 vs 组相似度。
- **C3→R196v2、C5→R197v2**：不实现、不重推。
- **候选状态（≤6，III 检出/接口用）**：Tissue；`*_DRUG_TYPE`；剂量布局（浓度档设计列）；**BARCODE 派生批次组（2 水平，构造 §4.1 规则）**；细胞系身份 8 组（`folds.json.cell_groups_8`）；A4 状态列（若可用，版本冻结）。

## §3 Constructive 判别体检（主实验；本轮不运行）

### 3.1 世界生成器（元数据维度；响应盲）
- 维数：65 药 / 2,025 directed 对 / 125 细胞 / 3 组织 / 165 主组 / 90,589 单元；细胞分 8 组（`folds.json.cell_groups_8`）。
- `y = b_cell + b_pair + b_dose + g_group + h_state·z + ε`；`b_cell,b_pair ~ N(0,0.5²)`；`b_dose` 2 水平；`g_group` 组效应；`z` = BARCODE 派生批次组（2 水平；**可观测、在元数据中真实存在、模型/关系不使用**）；σ∈{0.5,1.0,2.0}（预注册单位）；`ε~N(0,σ²)`。
- **注入**（每类 24 世界 = 3σ×2δ×4；δ∈{1σ,2σ}）：
  - I：b_cell/b_pair/b_dose 加 δ；g 不变；
  - II：g 在 **8 细胞组中的 5 组**翻转 −2δ（其余 3 组不变）→ 语境翻转数=5（满足 ≥5 独立语境）；
  - III：`h_state·z` 非零（2 水平）→ 可观测状态效应；模型/关系不含 z；
  - null：只有 ε。
- 标签由生成器给出（construct 定义），**不是**从响应反推；replay 无标签。

### 3.2 K_A2 判别器（预注册规则；与 A1 的差异见 §5）
1. 可行性/噪声：r_I（nuisance 标量重估后 χ²/基线 χ²）≤ 零分布 q_0.10 分位；C2′ 违反率 ≤基线 0.05。
2. **I**：规则 1 成立且无条件内外差（|差|<δ_scope/2）且无状态结构 → 判 I。
3. **II**：C2′ 违反显著（CI 排除 0）∧ 条件内−外一致率差 ≥ **δ_scope=0.20**（内/外各 ≥10 单元；k≥20）∧ **≥5 个独立语境符号翻转**（语境=细胞组）→ 判 II。
4. **III**：全释放后残差结构统计量显著（三选一主：dip 统计量；备：2 vs 1 成分潜类 BIC 差；分组方差比）**且** 在 ≤6 候选状态的多重比较（max-statistic 置换零，1,000 次）中某候选过校正阈值（**z 必须靠数据被识别，不得直接喂入**）→ 判 III 并输出 `identified_state`；若结构显著但无候选过阈值 → `unresolvable`。
5. 否则 `unresolvable`（必填原因：缺单元/条件不可分/状态不可测/多解释同分布）。

### 3.3 终点、δ_min、MDE、abstention（预注册；挑战必改 3 落实）
| 终点 | 定义 | 目标/机会 | δ_min（同单位：正确率差/率差） | 判定 |
|---|---|---|---|---|
| E1 | I vs {II,III} balanced accuracy（**分母=全部非 null 世界；abstention 计错**） | 目标 0.80 vs 机会 0.50 | **0.30** | ≥0.80 且 MDE≤0.30 |
| E2 | II vs III balanced accuracy（同上记账；仅 II/III 世界） | 0.70 vs 0.50 | **0.20** | ≥0.70 且 MDE≤0.20 |
| E3 | null 上 false-class 率（abstention 计为无假类=正确） | 0.10 vs 名义 α 0.05 | **0.05** | ≤0.10 且 MDE≤0.05；null resolved rate ≤0.50（描述卫生上限） |
| E4 | 非 null 世界 unresolvable 率 = 1 − resolved rate | 0.10 vs 0 | **0.10** | ≤0.10 且 MDE≤0.10；**E4b：每类 resolved rate ≥0.85** |
- **MDE**：80% 功效下可分辨的正确率/率差（与 δ_min 同单位），每终点 ≥1,000 模拟批；`MDE > δ_min` ⇒ `design_uninformative`（不进 replay）。
- **算术自洽**：E4≤0.10 ⇒ resolved≥0.90；E1 all-worlds ≥0.80 ⇒ resolved acc ≥0.889；E2 ⇒ ≥0.778。若放宽 E4 到 0.25 则 E1 0.80 数学上不可同时满足——因此 E4 冻结为 0.10（v2 的 0.25 撤回）。

### 3.4 预算-功效表（挑战必改 2 落实；不再有 6+20+12=38）
| k | 单元分配 | 可判 | 复用规则 |
|---|---|---|---|
| 6 | 3 in/3 out；z 3/3 | I vs null | I 用 6；II/III 不判 |
| 12 | 6 in/6 out；每层 z 3/3 | I + III | I 用 12；III 用 z 各 6；II 不达（6/6<10） |
| **20** | **10 in/10 out；每层 z 5/5** | **I + II + III** | I 用 20；II 用 10 vs 10；III 用 z 各 10 |
| 24（replay） | 20 结构化 + 4 备用 | I + II（真实） | 备用只增 I 精度；III 只出 proxy flag |
| 36 | 20 结构化 + 16 独立确认批次（8/8；z 4/4） | I+II+III + 稳定性复验 | 16 批次**不放宽阈值**（8/8<10 → II 不达），只描述方向复现 |
- II 的"≥5 独立语境"= 8 个预注册细胞组中 5 组翻转（构造满足）；判别时按组计数、按组置换零。
- 预算核算：96 世界 × ~90,589 单元 ≈ 8.7M 数值；MDE 4 终点×4 k×1,000 批=16,000 次轻量分类 → **估计 ≤5 min，硬上限 30 min**；模拟器代码落盘不运行。

## §4 真实 replay（次级；仍不报归因正确率/收益）
- 条件：constructive_pass（或 Lead 明确允许 partial 后）；每折 Ref/S/E/U 按 §1；更新器由 A1 提供（A2 不实现）。
- 只报：C2′ 违反分布；归因分布（K_A2 输出计数，含 unresolvable，**描述**）；unordered-U top-k 预测排序/描述性后悔（fold0 top-k=5；directed-U top-k=10 鲁棒性）；**禁止**归因正确率/收益/机制。
- 失败类别：`insufficient_units`/`not_identifiable`/`design_uninformative`；不得写阴性。

## §5 接口（schema `a2_to_a1/v3`；挑战必改 5 落实）
- 字段/类型（冻结）：见 spec_v3 §6；含 `residual_structure:{name,stat,p}`、`identified_state:str|null`。
- **κ≥0.60 仅兼容性检查**：A1/A2 在同一构造世界的一致性；κ 高≠验证；A1/A2 同类判别**不互相当独立验证**；`X_flip`/`δ_scope` 只作口径对齐、不互作验证。
- 仲裁：replay 冲突→`interface_disagreement`；不取单一归因；A2 让位 A1；全部保留报告。
- A4/III、A5/acquisition、C3/C5 归属不变；引 C176/C177。

## §6 预算/时间与冻结清单
- 预算：constructive 估计 ≤5 min；硬上限单命令 ≤30 min；replay（若做）<10 min；无 GPU；全部 CPU。
- 冻结清单：
  - [x] `folds.json`（SHA 记 record_v3；含折/S24/U/cell_groups_8）
  - [x] `constraints_check.json`（SHA 记 record_v3）
  - [x] `constructive_sim.py`（落盘**未运行**；SHA 记 record_v3）
  - [ ] `SYNERGY_DELTA_EMAX` 列义确认（引 R198 record）
  - [ ] 候选状态版本（BARCODE 派生规则/细胞系 8 组/A4 状态）写死
  - [ ] MDE 模拟结果（≥1,000 批）在冻结后执行并在 report 记录
  - [ ] 明确：constructive 先于 replay；replay 不报正确率/收益；C1′ QA only
