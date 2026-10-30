# R200-D1.1 报告：目标资格修正 / 目标层级与功效锁定 / 闭包对比操作化（v0.2）

2026-10-27。角色：独立审计/设计修订员（未参与 R197 模型开发）。本报告按 **challenge_D1（task-93，`revise`，5 必改）** 修订 v0.1；**只做 metadata/代数审计与设计修订：不训练/不拟合/不做效应或迁移统计；不读 O'Neil/Validation 响应值**。
- 协议（运行前冻结）：[PROTOCOL_D1_v0_2.md](PROTOCOL_D1_v0_2.md)（SHA256 `f77d1c05bb4cf3ffb68529ea75fd6c1cb153b360a2dd376433ad3379f461a302`）
- 代码：[d1_revision.py](d1_revision.py)（SHA256 `7b67dfd452df9608b9f46ae5046a007f879a86c3c912669fec34fe774e3bc7a4`）
- 结果：[d1_v0_2.json](d1_v0_2.json)（SHA256 `aeb22543881a8a90dfb94f659c72d445d305a576fec1dd7b713649cf3547ae82`）、[record_d1_v0_2.md](record_d1_v0_2.md)、[usage_d1_v0_2.json](usage_d1_v0_2.json)
- 被修订：v0.1 [PROTOCOL_D1.md](PROTOCOL_D1.md) / [d1.json](d1.json) / [report_d1.md](report_d1.md)（**未改动**；其信息分解（秩/冗余/H197c/共享来源）PASS 部分继续有效）
- 状态：🟡 待 Lead 决策与**再次独立挑战**；本轮不进入最小实验。

## 0. 明确裁定：**stop（默认）—— 无可认证的最小实验**

| 目标 | 角色锁定 | 主规划 MDE80（保守场景） | 判定 |
|---|---|---|---|
| **T0** H197c 随机条目 | 仅审计对象（不可作推断目标） | — | v0.1 已证 100% 闭包可重建 |
| **T1** 同 screen 未测键（18,782） | 内部前驱（非独立目标） | **0.0896** | 不作主推断 |
| **T2** Validation 9,154 匹配键（跨 screen 同键复测） | **唯一候选 primary** | **0.0941 > δ_min=0.05** | **`design_invalid: precision_insufficient`** |
| **T3** Validation-only 495 冷键 | **exploratory only** | **0.2018** | **`design_invalid: precision_insufficient`**（不得 primary） |
| **T4** 不同测量/培养 | **无合格目标** | — | O'Neil 9/39<10 且无匹配键/同端点 |

**因此：按冻结的 MDE≤δ_min 设计门，T2 不能作为 primary；T3 更不能；T4 无目标 → `stop`：无可执行最小实验。** 所需测量规格见 §6。
**条件分支（须 Lead 明确决定，不得由 runner 事后选）**：
(a) 若 Lead 明确接受**乐观独立规划**（ICC=0、ρ_AB=0；本报告标注其为非保守假设）并经 AMENDMENT 预注册 → T2 规划 MDE80=**0.0414≤0.05**，可提交**仅"跨 screen 同键复现"**的窄化设计（+T1 前驱、T3 exploratory）再交独立挑战；**不得**写成独立测量/培养/lineage 或"闭包外/新键迁移"。
(b) 若 Lead 坚持"新键/闭包外结构"的独立检验 → 本地无合格目标/功效 → **stop**，所需测量规格见 §6。（本报告的默认裁定即此分支下的 stop。）

## 1. 5 条必改 → v0.2 落实

| # | challenge 必改 | v0.2 落点 |
|---|---|---|
| 1 | 修正目标资格事实（O'Neil/nyman/T4/汇总/所需规格） | §2 资格表（9 候选）；`d1_v0_2.json → facts_v0_2, E_eligibility_v0_2` |
| 2 | 锁定目标层级与功效（T3 design_invalid、T2 MDE、T1 前驱、T4 无目标；不得事后换） | §3 目标表 + MDE 公式/选择规则；`F_power` |
| 3 | 操作化主对比/基线/闭包门 | §4（源特征块 B1–B4、闭包排除①+③、精确闭包基线逐目标定义、闭包门 ≤5%、等信息 cap）；`G_closure_gate, H_operational_definitions` |
| 4 | MDE/δ/cluster/bootstrap/预算写死 | §3 公式、§5 统计细节；`F_power.bootstrap`、§4 cap |
| 5 | 边界/措辞/三处一致 | §2/§3/§5；`K_wording`；report/protocol/json 三处一致 |

## 2. 修正后的目标资格表（v0.2；9 候选）

**判据（不降门槛）**：≥2 独立组（原始证据不共享板/孔）∧ 共享细胞 ≥10 ∧ 有向对 ≥10 ∧ 匹配键/四元组 ≥500；目标须为不同测量/培养/筛选的 Δ 或功能读数（同资源换聚合/换端点/barcode 分半 = `same_resource_reencoding`）；不同 screen 但同平台/同端点者只能作**跨 screen 同键复测**并显式标注。

| 候选 | 本地事实（核验） | 与 Jaaks | 判定 | 失败类别/理由 |
|---|---|---|---|---|
| **Jaaks Validation fitted** | 11.8 MB；barcode 与 Original 不相交；454 板；23,347 有效行 | 96 共享细胞、98 覆盖有向对、9,154 匹配键、6,223,367 匹配四元组；同平台/同端点 | **`qualified_with_conditions`（仅跨 screen 同键复测层）** | 条件：非不同测量/培养/lineage；screen-batch 混淆；Validation 更小，功效须过门 |
| **O'Neil 2026** | **7 文件 / 40,543,740 B**（`data/raw/oneil2026_qualification/`；combination response 38.8 MB + single-agent workbook + figshare receipts）；368,832 行、39 细胞、583 无序药对、viability1–4、X/X0；ON1/2/3 已用 | **9/39 共享细胞（23.08%），<10**；保守名称归一 5 细胞/27 cell×pair 键（宽松 9/69 键）；**无 A0 匹配条件、端点 X/X0 ≠ SYNERGY_DELTA_EMAX**；历史已用于拟合/选择（非封存） | **`not_qualified`** | **`data_insufficient`（9<10、27/69≪500）+ `no_operational_target`（端点不可映射）**；**不是 `data_unavailable`** |
| DrugComb v1.4/v1.5 | v1.4 193 MB 本地；v1.5 已下载于 A3 | 41 共享细胞<200、4,179 匹配单元<10,000 | `not_qualified` | `data_insufficient`（C173） |
| PRISM 19Q4 单药 | 41 MB | 单药 logFC | `not_qualified` | `no_operational_target` |
| BeatAML2 单药 | 19 MB | 单药 probit AUC | `not_qualified` | `no_operational_target` |
| GCP2020 | 28 metadata 文件 | 蛋白组（4 细胞系） | `not_qualified` | `no_operational_target` + `data_insufficient` |
| NCI-ALMANAC / VIS2024 / **Nyman2020** / Hill2017 / JUMP-CP / BATCHIE / GDSC2 | **目录存在但无有效数据文件**（Nyman2020 仅空子目录 `data/`，0 文件） | — | `not_qualified` | `data_unavailable`（统一表述，修正 v0.1 的 `empty:false` 不一致） |
| Original 同资源换端点（AUC/XMID/fAUC）/换聚合/barcode 分半 | 同表同 wells | — | `not_qualified` | `same_resource_reencoding` |
| Mix-seq / LINCS / SciPlex / Tahoe | 表达/形态 | — | `not_qualified` | `no_operational_target` |

**汇总：qualified=0；qualified_with_conditions=1（Validation，仅跨 screen 同键复测层）；not_qualified=8。**
**T4 修正表述**：不是"本地不存在组合资源"，而是"**没有满足 A0 复用门槛的不同测量/培养目标**（O'Neil 是本地不同测量组合资源，但 9/39<10 且无 A0 匹配条件/同端点）"。
**v0.1 事实错误更正**：O'Neil 被判 `data_unavailable`（空目录）→ 改为 **`not_qualified`（`data_insufficient`+`no_operational_target`）**；Nyman2020 归类统一；汇总与所需规格同步更新。

## 3. 目标层级与功效锁定（先资格+功效，再看目标响应）

**目标表**：T0 仅审计（v0.1 100% 闭包可重建）；**T1**（18,782 键）内部前驱；**T2**（9,154 匹配键，**跨 screen 同键复测**）唯一候选 primary；**T3**（495 冷键）exploratory/`design_invalid`；**T4** 无合格目标。**选择规则写死**：资格与功效在目标响应读取前计算；T2 primary 仅当保守规划 MDE80≤δ_min 且闭包门通过；**不得**看结果换目标/split/δ/cluster/预算。

**MDE 冻结公式**：`Δρ = ρ_S(M*) − max_B ρ_S(B)`（同一目标键集的 **Spearman 差**）；`n_eff = n_units/DE`，`DE = 1+(m̄_cell−1)ICC_cell+(m̄_cond−1)ICC_cond`；`Var(Δρ)=2(1−ρ_AB)/(n_eff−3)`；`MDE80=2.801585·sqrt(Var)`。
**ICC 规划先验（只读 A0，披露为近似）**：cell=0.03943517、cond=0.01428744；**主规划情景 = priors×1 且 ρ_AB=0（保守）**；敏感性 ×{0,0.5,1,2} × ρ_AB{0,0.5,0.8} 全表见 JSON。

| 目标 | 单元 | cells/conds | m̄ | DE | n_eff | SD(Δρ) | **MDE80** | 过门? |
|---|---|---|---|---|---|---|---|---|
| T1 | 18,782 | 96/291 | 195.6/64.5 | 9.584 | 1,959.8 | 0.03197 | **0.0896** | ✗（前驱） |
| **T2** | **9,154** | 96/291 | 95.35/31.46 | **5.156** | **1,775.4** | **0.03359** | **0.0941** | **✗ design_invalid** |
| T3 | 495 | 66/224 | 7.5/2.21 | 1.274 | 388.7 | 0.07201 | **0.2018** | ✗ |
| T2 pair-level | 98 | — | 1.02/1.0 | 1.001 | 97.9 | 0.14516 | **0.4067** | ✗（仅描述） |

**T2 过门条件（敏感性）**：在保守 ICC 先验下，T2 要 MDE≤0.05 需要目标侧秩 ICC ≤ **0.003663**（仅为先验的 **9.3%**）或主模型-最强基线预测秩相关 ≥ **0.7177**；两者设计阶段均未知 → 保守情景不过。**乐观独立情景**（ICC=0、ρ_AB=0）MDE=**0.0414** ✓（但属非保守假设，须 Lead 明确批准 AMENDMENT）。阈值的 ρ_AB={0,0.5,0.8} 全表：DE 需 ≤1.457/2.913/7.272，ICC 需 ≤0.00366/0.01533/0.05025（=先验的 9.3%/38.9%/127.4%）。
**结论**：默认保守门 → **T2 `design_invalid: precision_insufficient` → stop**。

## 4. "去闭包结构模型"/精确闭包基线/闭包门的操作化（冻结）

- **主模型 M\***：源侧训练、目标侧只读预测。**源特征块**：B1 细胞元数据（tissue/lineage）；B2 药物注释块（项目冻结 pathway/target/class 模板，P-A/P-A2，不重映射）；B3 源加性效应（在**源派生条目最大线性无关基**上估计，基尺寸=rank=3,005，固定贪心顺序）；B4 源结构交互（低秩 cell×condition + 注释交互）在**闭包正交补**拟合。
- **闭包排除（预先写死）**：主实现①训练集 = 最大线性无关基（3,005 条，非全部 92,039）+③目标评估仅非闭包单元（键级目标按构造无闭包通道）；②源特征投影 `I−P_C`（`P_C=A⁺A`）作敏感性。
- **模型类/调参**：低秩/层级结构模型（cell×condition 交互 + 注释块），≤30 配置、内层 5 折（固定 seed），只用源侧训练数据选参。
- **基线（同信息/同预算）**：均值；源值直传；源加性；充分调参树（DrEval 标准）；矩阵补全/低秩（秩 1–5 训练内选）；GP/核（B1+B2）；**精确闭包重建**；直接响应预测。
- **精确闭包重建（逐目标）**：T0/派生端点 → 最小范数 `z` 解、`max|err|/≤1e-9` 比例、目标侧重建率（v0.1 已示 100%）；T1 新键 → 键级贡献 **0（构造性）**，派生次级用 target training 重建并报告；T2 同键 → 键级零结构基线是**源值直传**（不是闭包重建），派生次级（若构建 Validation Q）用 Validation training 条目重建并报告；T3 冷键 → 键级贡献 0，派生次级报告。
- **闭包门（目标特定）**：派生 Q 目标在预注册 split 上重建率 **≤5%** 才可；否则 `design_invalid: closure_contaminated`；split 族仅 S-random（随机条目，v0.1 证据预期失败）与 S-structural（按 cell/partner/key 分组），**不得按结果换**。键级目标闭包贡献记 0（by construction）并报告。
- **等信息/等预算 cap（可核查）**：同 B1–B4；同 5 折内层 CV/seed；每模型 ≤30 配置；每模型 wall ≤600 s、CPU ≤1,200 s、内存 ≤8 GB；同一目标 mask；逐臂报告配置数/实际 wall/CPU；M\* 不得获得额外信息/预算；目标侧单药列主分析禁用（敏感性另报并标注信息更多、不作 primary）。
- **统计细节（写死）**：Δ=Spearman 差；cluster=目标侧 **cell**（主），plate/key 敏感性；配对 cluster bootstrap B=2,000、seed=20261120、percentile 2.5/97.5；失败类别 `data_unavailable / data_insufficient / no_operational_target / same_resource_reencoding / design_invalid: precision_insufficient / design_invalid: closure_contaminated / design_invalid: coverage / evaluation_cannot_distinguish / no_increment`；零模型：目标内 rank 置换（保 mask）、源→目标映射置换（tissue 内细胞/注释类内药物）、同维随机特征、同资源换端点负对照（仅泄漏量化）。
- **停止条件**：无合格独立目标→stop+规格；primary MDE_plan>δ_min→`design_invalid: precision_insufficient`→stop；闭包门>5%→`design_invalid: closure_contaminated`；主模型≤最强基线→`no_increment`；增益只在闭包可重建单元→停迁移主张；不得换端点/切分/δ/cluster/预算。

## 5. 边界与措辞（v0.2 统一）

- **Validation**：独立 screen/板/run、**同实验室平台、同端点定义**、96 共享细胞的**跨 screen 同键复测**；**不是**独立测量/独立培养/lineage 确认；**不得**写"闭包外结构/新键迁移"。
- **删除绝对措辞**：v0.1 的"唯一独立操作性目标"删除；改为"唯一符合跨 screen 同键复测条件的 `qualified_with_conditions` 目标"。
- **T4/O'Neil**：见 §2 修正表述；O'Neil 不是空目录/`data_unavailable`。
- **R197v2 0.7206**：仍只作 **C179 未认证描述性、待检验对象**；不写结构成立/不存在。
- **A0 1.43%/3.94%/94.63%**：只作 **Q 方差份额**，不是预测信号份额、不是可迁移规律总量。
- **三处一致**：protocol v0.2 / 本报告 / `d1_v0_2.json` 使用同一资格判定、T1/T2/T3 角色与 T4 表述（record 检查）。

## 6. 所需测量规格（若坚持"新键/闭包外结构"独立检验 → stop 时记录）

独立组合资源须同时满足：① 不同测量模态**或**独立培养（非同平台/同端点再 screen）；② 与 Jaaks 实体空间共享 **≥10 细胞、≥10 有向对、≥500 匹配键/四元组**（A0 复用门槛）；③ 原始板/孔/run 与 Original、Validation 均不相交；④ 有冻结聚合的组合 Δ 或功能 viability 读数（可映射 A0 口径）；⑤ 目标单元/聚类结构在预注册保守规划下 **MDE80≤0.05**（或预先声明放宽 δ_min / 增加单元）。
**本地现状**：O'Neil 满足①但 9/39<10 且无匹配键/同端点（`data_insufficient`+`no_operational_target`）；DrugComb 冻结大规模设计未过（C173）；其余为空目录/单药/表达资源 → **本轮无合格目标**。

## 7. 产物与确定性

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_D1_v0_2.md` | `f77d1c05bb4cf3ffb68529ea75fd6c1cb153b360a2dd376433ad3379f461a302` |
| `d1_revision.py` | `7b67dfd452df9608b9f46ae5046a007f879a86c3c912669fec34fe774e3bc7a4` |
| `d1_v0_2.json` | `aeb22543881a8a90dfb94f659c72d445d305a576fec1dd7b713649cf3547ae82` |
| `report_d1_v0_2.md` / `record_d1_v0_2.md` | 见 `usage_d1_v0_2.json` |

**确定性**：同脚本第二次运行 `d1_v0_2.json` **逐字节一致**（两次运行 `d1_v0_2.json` 逐字节一致（`aeb22543881a8a90dfb94f659c72d445d305a576fec1dd7b713649cf3547ae82`；两次 wall 均 0.2 s））；单命令 wall = 0.2 s（两次）。v0.1 文件未改动（`d1.json` SHA 仍 `F0DC308F…`）。

## 8. 建议

- **默认建议：批准 stop**（D1 线以"信息分解成果（PASS）+ 资格/功效边界成果"归档；把 §6 所需测量规格写入下一轮资源计划）。
- 若 Lead 明确要在**乐观独立规划**下推进：需先写 AMENDMENT 预注册 ICC=0/ρ_AB=0，再提交**仅 T2 跨 screen 同键复现**的窄化设计给独立挑战；措辞不得越界（§5）。
- **建议再提交独立挑战**（challenge_D1 的 5 必改已逐项落实；挑战重点：O'Neil 分类、T2/T3 功效与层级、闭包门/操作化定义、MDE 公式与 cluster）。
