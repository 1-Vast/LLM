# PROTOCOL_D1_v0_2 —— R200-D1.1 修订协议（按 challenge_D1 `revise` 的 5 条必改）

2026-10-27。**在本修订的任何计算之前冻结。** 对象：v0.1 的 [PROTOCOL_D1.md](PROTOCOL_D1.md) / [d1.py](d1.py) / [d1.json](d1.json) / [report_d1.md](report_d1.md) / [record_d1.md](record_d1.md)（**不改动**，v0.1 保留为被修订版本）。
依据：[challenge_D1.md](challenge_D1.md)（task-93，判决 **revise**，5 必改）、[R200 BRIEF](../2026-10-27-innovation-round-r200/BRIEF.md)、v0.1 审计、R197v2（C179）、A0/q2/ERRATA_A3、R196v2、Q0/ON1–ON3 记录、`data/raw/oneil2026_qualification/` 实存资源。
角色：独立审计/设计修订员（未参与 R197 模型开发）。**只做 metadata/代数审计与设计修订：不训练/不拟合/不做效应或迁移统计；不读 O'Neil/Validation 响应值；Q 值只用于精确恒等式核验（v0.1 已冻结）。**

## 0. 本轮要给出的裁定

1. **资格修正**：O'Neil 是本地实存资源（`data/raw/oneil2026_qualification/`，7 文件、40,543,740 B；ON1/ON2/ON3 已用），判 **`not_qualified`**（`data_insufficient` + `no_operational_target`），**不是 `data_unavailable`**；`nyman2020` 统一为"目录存在但无有效数据文件 → `data_unavailable`"；T4 改为"**没有满足 A0 复用门槛的不同测量/培养目标**（O'Neil 是不同测量资源，但共享细胞 9/39 < 10，且无 A0 匹配条件/同端点）"。
2. **目标层级与功效锁定（先资格+功效，再看目标响应）**：
   - **T1**（同 screen 未测键，18,782 键）＝**内部前驱**（不是独立目标，不作迁移推断）；
   - **T2**（Validation 9,154 匹配键，**跨 screen 同键复测**）＝**唯一候选 primary**，仅当**预注册保守规划 MDE80 ≤ δ_min=0.05 且目标侧闭包门通过**；
   - **T3**（Validation-only 495 键）＝ **`design_invalid: precision_insufficient`**，最多 exploratory，**不得 primary**；
   - **T4**（不同测量/培养）＝ **无合格目标**（O'Neil 9<10 且无匹配键/同端点）；**若坚持"新键/闭包外结构"独立检验 → 本地无合格目标与功效 → stop**（§6 记录所需测量规格）。
   - **T2 只是同平台（GDSC/Jaaks 平台）、同端点（SYNERGY_DELTA_EMAX 定义）、跨 screen（独立板/run）、同键复测**；**不是**独立测量/独立培养/lineage 确认，**不得**写"闭包外结构/新键迁移"。
3. **设计操作化**（§4）：去闭包结构模型（源特征块/闭包排除/模型类/调参）、精确闭包重建基线（T1/T2/T3 各自定义与贡献）、目标侧闭包门（≤5% 预检/失败处置）、MDE 的 Δ 定义（Δ=**Spearman 差**）与 cluster 单位（目标侧 cell 主、plate/key 敏感性）、配对 bootstrap（B=2,000、seed=20261120、percentile 2.5/97.5）、等信息/等预算可核查 cap。
4. **明确裁定**（由 `d1_revision.py` 依 §3 冻结公式计算）：若 T2 保守规划 MDE80 > δ_min 或闭包门不过 → **`design_invalid: precision_insufficient`（无可执行最小实验）→ 总体 stop**，并写所需测量规格；若 ≤ δ_min 且其余门过 → 提交**仅 T2 跨 screen 同键复现**的设计（+T1 前驱、T3 exploratory），**不称独立测量/迁移**，再交独立挑战。

## 1. 事实修正依据（只读核验）

| # | 事实 | 依据 |
|---|---|---|
| F1 | O'Neil 本地存在：`data/raw/oneil2026_qualification/` 7 文件 40,543,740 B（含 combination response 38.8 MB、single-agent workbook、figshare receipts） | 目录实测；ON1 PROTOCOL 主输入：`15357163mct150843-sup-156849_1_supp_1_w2lrww.xls`（368,832 行、39 细胞、583 无序药对、viability1–4、X/X0） |
| F2 | O'Neil 与 Jaaks **9/39 细胞重叠**（9 个从目标集排除，开发目标细胞 30；`on1.json` DG5 "9/39 cells overlap Jaaks and are EXCLUDED from target set (30 non-overlap cells)"；`jaaks_overlap_frac=0.23076923`） | `on1.json`、`PROTOCOL_ON1.md` §13/§37 |
| F3 | O'Neil 端点 = **X/X0（生长归一化组合响应）**，与 Jaaks `SYNERGY_DELTA_EMAX` **不同端点定义**；O'Neil **无 A0 匹配条件/同端点** | `PROTOCOL_ON1.md` §19；v0.1 A0 匹配要求 |
| F4 | O'Neil 数据**在本项目之前已用于模型拟合/选择与 G/F 评价**，不是未暴露封存集 | `research/2026-10-27-oneil-transfer-qualification/report.md` §"已有数据与终点" |
| F5 | O'Neil 保守名称归一共享 = 5 细胞/27 cell×pair 键（宽松复核 9 归一名字/69 cell×pair）；两口径均 < D1 冻结 ≥10 共享细胞门槛中较宽的 9 也 <10 | `oneil-transfer-qualification/counts.json`、`report.md` |
| F6 | `nyman2020` 目录存在但 **0 个文件**（仅空子目录 `data/...`） | 目录实测 |
| F7 | Validation = 独立 screen/板/run（barcode 与 Original 不相交），同实验室平台、同端点定义；96 共享细胞 / 130 共同有向对 / 98 覆盖有向对 / 9,154 匹配键 / 6,223,367 匹配四元组；screen 与 batch 混淆 | v0.1 `d1.json E`、A0 `matching_qualified` |
| F8 | 目标键数：T1 = 27,936−9,154 = **18,782**；T2 = **9,154**；T3 = Validation 有效键 9,649 − 匹配 9,154 = **495** | v0.1 `d1.json F`、Validation 身份列复核 |

## 2. 目标资格表 v0.2（冻结判据，逐项）

**判据（沿用 v0.1 §5 的 A0 复用门槛，不降门槛）**：≥2 独立组（原始证据不共享板/孔）∧ 共享细胞 ≥10 ∧ 有向对 ≥10 ∧ 匹配四元组/键 ≥500；目标须为**不同测量/不同培养/不同筛选**的 Δ 或功能读数（**同一资源换聚合/换端点/barcode 分半一律 `same_resource_reencoding`**）；不同 screen 但同平台/同端点者只可作**跨 screen 同键复测**，必须显式标注，不得写成独立测量/培养/lineage。
**失败类别**：`data_unavailable`（无有效数据文件）/ `data_insufficient`（有资源但实体/匹配/规模不足）/ `no_operational_target`（无可用端点或派生量）/ `same_resource_reencoding` / `design_invalid`（预测阶段用）。

| 候选 | 本地事实 | 与 Jaaks 关系 | 判定 | 类别/理由 |
|---|---|---|---|---|
| **Jaaks Validation fitted** | 11.8 MB；barcode 不相交；454 板；23,347 有效行 | 96 共享细胞、98 覆盖有向对、9,154 匹配键、6.2M 匹配四元组；**同平台/同端点** | **`qualified_with_conditions`（仅跨 screen 同键复测层）** | 条件：非不同测量/培养/lineage；screen-batch 混淆；Validation 更小，功效须预注册（§3） |
| **O'Neil 2026** | 7 文件/40.5 MB；368,832 行；39 细胞/583 药对；X/X0 端点；batch1 主分析 | **9/39 共享细胞（<10）**；宽松 5 或 9 细胞、27/69 cell×pair 键；**无 A0 匹配条件/同端点**；已用于历史拟合/选择（非封存） | **`not_qualified`** | `data_insufficient`（9<10、27/69 键≪500）+ `no_operational_target`（X/X0 ≠ ΔEMAX，无匹配键） |
| DrugComb v1.4/v1.5 | v1.4 193 MB 本地；v1.5 已下载于 A3 | 41 共享细胞<200、4,179 匹配单元<10,000（A3 冻结大规模设计） | `not_qualified` | `data_insufficient`（C173） |
| PRISM 19Q4 单药 | 41 MB | 单药 logFC，无组合对比 | `not_qualified` | `no_operational_target` |
| BeatAML2 单药 | 19 MB | 单药 probit AUC | `not_qualified` | `no_operational_target` |
| GCP2020 | 28 metadata 文件 | 蛋白组（4 细胞系） | `not_qualified` | `no_operational_target` + `data_insufficient` |
| NCI-ALMANAC / VIS2024 / Nyman2020 / Hill2017 / JUMP-CP / BATCHIE / GDSC2 | 目录为空/无有效文件（nyman2020 仅空子目录） | — | `not_qualified` | `data_unavailable`（**统一表述**"目录存在但无有效数据文件"） |
| Original 同资源换端点（AUC/XMID/fAUC）/换聚合/barcode 分半 | 同表同 wells | — | `not_qualified` | `same_resource_reencoding` |
| Mix-seq / LINCS / SciPlex / Tahoe | 表达/形态 | — | `not_qualified` | `no_operational_target` |

**汇总**：`qualified=0`、`qualified_with_conditions=1`（Validation，仅跨 screen 同键复测层）、`not_qualified=8`。**T4（不同测量/培养）无满足 A0 复用门槛的目标**（O'Neil 是不同测量但 9<10 且无匹配键/同端点）。

## 3. 目标层级与功效锁定（先资格+功效，再看目标响应；不得事后换目标）

**目标表**：
| 目标 | 定义 | 单元数 | 性质 | 允许角色 |
|---|---|---|---|---|
| T0 | H197c 随机留出派生条目 | 92,039（留出 18,408/折） | v0.1 已证 100% 闭包可重建 | **仅审计对象**（不可作任何推断目标） |
| T1 | 同 screen 未测键（匹配宇宙 27,936−9,154） | **18,782** | 同资源内部插值；闭包不可重建新键 | **内部前驱**（不作独立目标/迁移推断） |
| T2 | Validation 匹配键的跨 screen 同键复测 | **9,154** | 独立 screen/板/run，同平台/同端点，同键 | **唯一候选 primary**（仅 MDE≤δ_min 且闭包门过） |
| T3 | Validation-only 冷键（跨 screen + 冷键） | **495** | 独立 screen + 冷键，但样本极小 | **`design_invalid: precision_insufficient`**；最多 exploratory |
| T4 | 不同测量/培养的组合目标 | 本地无满足门槛者 | — | **无合格目标 → stop 依据**（所需规格见 §6） |

**MDE 冻结公式（v0.2；不得用 2.802/√n 冒充 Spearman MDE）**：
- 主指标 `Δρ = ρ_S(M*) − max_B ρ_S(B)`（同一目标键集上的 **Spearman 秩相关差**；`ρ_S(·)=Spearman(pred, y_target)`；评估集 = 目标侧冻结点集；每个基线单独与主模型比较，取最大者为 `max_B`）。
- 目标侧聚类：**主 cluster = cell**（T2：96 个 Validation 细胞；T3：Validation-only 键涉及细胞数；T1：96）；敏感性 cluster = **plate/key**。
- 规划方差（design-stage，冻结）：`n_eff = n_units / DE`；`DE = 1 + (m̄_cell − 1)·ICC_cell + (m̄_cond − 1)·ICC_cond`（两路加性设计效应，取保守乘法/加性较大值并披露）；`Var(Δρ) = 2(1 − ρ_AB)/(n_eff − 3)`；`MDE80 = 2.801585·sqrt(Var(Δρ))`。
- **ICC 规划先验（只读 A0，披露映射假设）**：`ICC_cell = 0.03943517`（A0 `share_cellpair`）、`ICC_cond = 0.01428744`（A0 `share_cond_raw`）——**这些是 Q 方差份额，不是秩相关 ICC**；仅作规划先验，敏感性给 ×{0, 0.5, 1, 2}。
- **预测秩相关规划**：`ρ_AB ∈ {0, 0.5, 0.8}`（0 = 最坏独立预测；越大=主模型与最强基线预测越相似、配对差越小）。**主规划情景 = ICC 先验×1 且 ρ_AB=0（保守）**；敏感性格表全报。
- **设计门**：候选 primary 须 **MDE80_plan(主规划情景) ≤ δ_min=0.05**；否则该目标 `design_invalid: precision_insufficient`。
- **分析期 CI**：配对 cluster bootstrap（重采样目标侧 cluster，B=2,000，seed=20261120，percentile 2.5/97.5）；`evaluation_cannot_distinguish` = CI 含 0 且 |Δρ|<δ_min。
- **目标选择规则（写死）**：先资格、再按 T2→(若 T2 不过)无 primary；T3 一律 exploratory/design_invalid；T1 仅前驱；T4 无目标。**不得看 target 响应后换目标/换 cluster/换 δ/换 ρ_AB。**

**闭包门（target-specific，冻结）**：对**派生 Q 目标**（T0/派生次级端点）：在目标侧预注册 split 上计算 `A4` 式重建率（测试条目系数向量 ∈ 训练条目张成），**≤5% 才可通过**；否则 `design_invalid: closure_contaminated`。可预注册 split 族：S-random（随机条目——由 v0.1 证据预期不可通过）、S-structural（按 cell/partner/key 分组）——**只许按预定义族选择，不得按结果换**。对**键级目标**（T1/T2/T3）：键是原始单位，Q 代数闭包不能从其它键确定新键/跨 screen 同键值 → **键级主目标的闭包贡献 = 0（构造性）**，须报告"target closure rate = 0 by construction"；精确闭包重建基线仅在派生 Q 次级端点上有定义（见 §4）。

## 4. 主对比/基线/闭包排除的**可执行定义**（冻结）

**主模型 `M*`（"去闭包结构模型"）**：源侧训练、目标侧只读预测（不接触目标响应）：
- **源特征块**（只读、可冻结）：B1 细胞元数据（tissue/lineage，A0 提供）；B2 药物注释块（项目冻结注释模板：pathway/target/class，引用 P-A/P-A2 映射；不重新映射）；B3 源加性效应（在**源键矩阵的最大线性无关基**上估计的 cell 效应/condition 效应——v0.1 已给秩 3,005，基由固定贪心顺序确定）；B4 源结构交互（源键矩阵低秩 + 注释交互），在**闭包正交补**中拟合。
- **闭包排除操作（三选一，预先写死并用同一实现）**：① 源侧**训练集 = 最大线性无关基**（尺寸 = rank(A_source)=3,005，固定贪心）而非全部 92,039 派生条目；② 对源侧特征做闭包投影 `I − P_C`（`P_C = A⁺A`，A = v0.1 系数矩阵，冻结）后再拟合；③ 目标侧只评估**非闭包**单元（派生端点用 S-structural split 的 non-reconstructible 部分；键级目标按构造无闭包）。**主实现选①+③**；②作敏感性。
- **模型类/调参（同预算）**：`M*` = 低秩/层级结构模型（cell×condition 交互 + 注释块），超参网格预注册 ≤30 配置、内层 5 折（固定 seed），只用源侧训练数据选参。
**基线（同信息/同预算 cap）**：均值；源值直传（匹配 Original 键值）；源加性（cell+cond 均值）；充分调参树（DrEval 标准：内层 CV 选预算，≤30 配置，同特征块 B1–B4）；矩阵补全/低秩（秩 1–5 训练内选，只用目标训练行）；GP/核（B1+B2 特征）；**精确闭包重建**（见下）；直接响应预测（先预测原始键均值再派生）。
**精确闭包重建（逐目标定义）**：
- T0/派生次级端点：`z=argmin‖A_tr z−Q_tr‖`（最小范数解），`Q̂_te=A_te z`；报告 `max|err|`、`≤1e-9` 比例、目标侧重建率；**贡献 = 可重建条目的全部**（v0.1 已示 100%）。
- T1（新键）：键级目标无闭包通道 → **贡献 0（构造性）**；派生 Q 次级端点上，闭包重建使用 **target training entries**（同 screen 的其它 Q 条目），并给重建率。
- T2（跨 screen 同键）：键级目标 = 源值直传（零结构基线）≠ 闭包重建；**派生 Q 次级**（若构建 Validation Q）用 Validation 自身 training 条目闭包重建，报告重建率与贡献；**不得**把 T2 的源值直传称为"闭包重建"。
- T3（冷键）：键级目标闭包贡献 0；派生 Q 次级按 target training 重建并报告。
**等信息/等预算 cap（可核查）**：所有臂同一 B1–B4 特征块、同一 5 折内层 CV 与 seed、每模型 ≤30 配置、每模型 wall ≤600 s / CPU ≤1,200 s / 内存 ≤8 GB、同一目标 mask；报告逐臂配置数/实际 wall/CPU；`M*` 不得获得额外特征/预算。**直接响应预测**若使用目标侧单药列（Validation 有 ANCHOR_VIABILITY/LIBRARY_EMAX 列）须与 `M*` 同信息：主分析禁用目标侧单药列，敏感性另报并标注信息更多（不平等，不作 primary）。
**次级/派生端点**：目标侧 Q（若构建）— 只作**闭包污染诊断**与 A4 报告，不作主推断（v0.1 已示 100% 重建）。

## 5. 统计细节（写死）与失败类别/停止条件

- Δ 定义：`Δρ = ρ_S(M*) − max_B ρ_S(B)`（Spearman 差；**不是** mean-Δ of per-key residual；每个基线单独比较取最大）；point/CI 用同一 9,154 键（T2）、18,782（T1）、495（T3）。
- cluster：目标侧 **cell**（主）；plate/key 作敏感性；配对 bootstrap B=2,000、seed=20261120、percentile 2.5/97.5；不把派生条目数当独立 n。
- **零模型**：① 目标内 rank 置换（保 mask/tie 规则）；② 源→目标映射置换（细胞标签在 tissue 内置换、药物标签在注释类内置换，保持支撑）；③ 同维随机特征（容量对照）；④ 同资源换端点（Original AUC/EMAX 互换，**仅量化泄漏，不作目标**）。
- **失败类别（冻结）**：`data_unavailable`；`data_insufficient`；`no_operational_target`；`same_resource_reencoding`；`design_invalid: precision_insufficient`；`design_invalid: closure_contaminated`；`design_invalid: coverage`；`evaluation_cannot_distinguish`；`no_increment`。
- **停止条件**：无合格独立目标（T4）→ stop + 写所需规格；primary 目标 MDE_plan>δ_min → `design_invalid: precision_insufficient`（本轮裁定）→ stop；闭包门>5% → `design_invalid: closure_contaminated`；主模型 ≤ 最强基线 → `no_increment`；增益只在闭包可重建单元 → 停迁移主张、保留评价成果；**不得**因结果换端点/切分/δ/cluster/预算。

## 6. 所需测量规格（若坚持"新键/闭包外结构"独立检验 → stop 时记录）

独立组合资源须同时满足：① **不同测量模态或独立培养**（非同一 GDSC/Jaaks 平台/端点的再 screen）；② 与 Jaaks 实体空间共享 **≥10 细胞、≥10 有向对、≥500 匹配键/四元组**（A0 复用门槛）；③ 原始证据（板/孔/run）与 Original、Validation 均不相交；④ 有冻结聚合的组合 Δ 或功能 viability 读数（可映射到 A0 口径）；⑤ 目标单位/聚类结构足以在预注册保守规划下 MDE80≤0.05（或预先声明放宽 δ_min/增加单元）。
**本地现状**：O'Neil 满足①（不同测量）但 9/39<10 且无匹配键/同端点（`data_insufficient`/`no_operational_target`）；DrugComb 满足①但冻结大规模设计未过（C173）；其余为空目录/单药/表达资源。→ **本轮 T4 无合格目标**。

## 7. 5 条必改 → v0.2 落点对照

| challenge 必改 | v0.2 落点 |
|---|---|
| 1 修正目标资格（O'Neil/T4/nyman/汇总/所需规格） | §1 F1–F8、§2 表、`d1_v0_2.json → E_eligibility_v0_2`、report §2/§6 |
| 2 预注册目标层级/功效（T3 design_invalid、T2 MDE、T1 前驱、T4 无目标；T2 仅跨 screen 同键；不得事后换） | §3 目标表、MDE 公式与选择规则；`d1_v0_2.json → F_power` |
| 3 操作化主对比/基线/闭包门 | §4（源特征块 B1–B4、闭包排除①+③、精确闭包基线逐目标定义、闭包门 ≤5%、等信息 cap） |
| 4 MDE/δ/cluster/bootstrap/预算写死 | §3 公式、§5 统计细节、§4 预算 cap |
| 5 边界/措辞/三处一致 | §2 表、§3 T2 定义、§7/§8；report §0/§6；`d1_v0_2.json boundaries`；删"唯一独立操作性目标" |

## 8. 边界与产出

- 不训练/不拟合/不做效应或迁移统计；不读 O'Neil/Validation 响应值；不下载；不改 v0.1 文件与其他目录；只写本目录 v0.2 文件与 `tmp/`。
- 确定性：JSON 键排序/无时间戳/allow_nan=False；输入/脚本/协议 SHA 写入 `d1_v0_2.json`；两次运行逐字节一致；单命令 ≤15 min。
- 产出：本文件、`d1_revision.py`、`d1_v0_2.json`、`report_d1_v0_2.md`、`record_d1_v0_2.md`、`usage_d1_v0_2.json`。
- 术语：v0.2 的"资格/裁定"不改变 v0.1 已 PASS 的信息分解（秩/冗余/H197c/共享来源）；R197v2 0.7206 仍只作 C179 待检验对象；A0 1.43%/3.94%/94.63% 只作 Q 方差份额。
