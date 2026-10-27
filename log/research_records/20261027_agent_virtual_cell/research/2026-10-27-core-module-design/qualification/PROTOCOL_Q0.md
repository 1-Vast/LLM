# R199-Q0 协议：组合功能替换关系 Δ(c;a,a';b) 的数据资格审计（metadata-only）

**版本 v1，FROZEN（在任何 Q0 门槛计算前冻结）** ｜ 2026-10-27 ｜ 执行：drugcomb-auditor（task-53）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-27-core-module-design/qualification/` 与 `tmp/`；不改其它目录/INDEX/SYNTHESIS/git。
**边界**：不训练/不拟合/不估效果；响应列只做**存在性/空值**检查，不读数值做效应；不重开 R196/R197 旧判定（C176/C177 作废状态）；不写机制/迁移/决策收益；不声称新颖性。

## 0. 预冻结侦察声明

冻结前只做了：`research/2026-10-27-innovation-round-r199/BRIEF.md`、`core-module-design/report.md`、`ERRATA_A3.md`/`a3.json`、`REVOCATION_R196.md`、R196v2/R197v2 记录等的**阅读**；以及候选文件的**列名/行数/实体数/重复结构**核对（不计算三向交叉门槛判定）。下列门槛、统计量、判定规则在本轮任何 Q0 计数前写死；`q0.py` 从原始文件**重算全部数字**，不使用侦察结果。

## 1. 对象与定义（冻结）

- 一次**测量**：`y(c,a,b)` = 细胞 `c` 中药物 `a`（成员）与药物 `b`（伙伴）在**合法暴露** `E=(剂量设计 D, 暴露时间 T, 端点 M)` 下的功能响应均值。
- **替换关系**：`Δ(c;a,a';b) = E[y(c,a,b)] − E[y(c,a',b)]`；固定 `c`、`b`，`a,a'` 为同一伙伴下可替换成员（同角色：在 Jaaks 中 `b`=anchor、`a,a'`=library；也报告 `b`=library、`a,a'`=anchor 的次方向）。
- **合法暴露（Legal exposure）**：
  1. `a`/`a'` 的两次组合测量必须共享同一细胞 `c`、同一伙伴 `b` 的身份；
  2. 伙伴 `b` 的浓度档必须**相同**（同浓度集合/设计）；每个成员各自的剂量曲线按预注册**完整曲线平均规则**（不得看结果挑剂量档）；
  3. 暴露时间、检测方法/端点、批次记录可核对（至少设计列存在）；
  4. 不允许把外推/插值剂量当测量；不允许跨端点拼接。
- **三向交叉单元**：`(c, b, {a,a'})`，满足 `y(c,a,b)` 与 `y(c,a',b)` 均测到且合法暴露检查通过。
- **可替换成员对**：同一 `(c,b)` 下可互相替换的成员无序对 `{a,a'}`（要求该 `(c,b)` 下成员数 ≥2）。
- **跨细胞覆盖**：固定 `(b,{a,a'})`，在多少个不同 `c` 上可计算 Δ。
- **禁止**：把同一 96 细胞（Jaaks O/V）换聚合当作新数据/独立证据；不把 barcode/技术重复当独立培养；不跨 study 混剂量/端点当同暴露。

## 2. 候选数据（逐一资格）

| 候选 | 本地路径 | 端点/结构 | 备注 |
|---|---|---|---|
| Jaaks Original | `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv` | `SYNERGY_DELTA_EMAX`（viability 派生）；2 anchor 浓度 × 7 library 剂量设计；296,707 行/125 细胞/46 anchors/65 libraries/108,259 keys | 主开发资源；与 Validation 共享 96 细胞 |
| Jaaks Validation | 同目录 Validation 文件 | 同上；97 细胞/23,505 行 | 同资源；**不是独立 lineage** |
| DrugComb v1.5 full | `tmp/a3_v15_summary.csv`（1.42 GB；SHA 见 R195/A3） | 组合 summary；`synergy_bliss/zip/...`、`S*`；无数值剂量；1,432,351 行/34 study/combo cells 288 | study/剂量混杂；A3 已核 41 共享细胞/4,179 单元 |
| DrugComb v1.4 summary | `research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv` | 组合 summary；466,033 combo blocks/112 细胞/62,826 药对；无 study 列、无数值剂量 | 与 v1.5 同 lineage（block_id 100% 可映射） |
| BeatAML | `data/external/beataml2_20261017/` | 单药 probit 曲线（AUC/IC50）；无组合 | 无 `a,b` 同测 |
| Mix-seq | `data/external/mixseq_scperturb/mcfarland_2020.h5ad` | 单细胞转录组（单药 + 对照） | 无组合、无功能端点 |
| O'Neil | `data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls` | 组合 viability（viability1–4、mu/muMax、X/X0）；368,832 行/39 细胞/38 药/3 BatchID；数字剂量列 | 同 lab/批次未认证；可作对照候选 |

## 3. 五个资格门槛（冻结）

### G1 交叉规模
- 单资源**合法三向交叉单元** ≥ **5,000**；
- 贡献 ≥1 单元的独立细胞 ≥ **30**；
- 有 ≥2 可替换成员的 `(c,b)` 上下文 ≥ **200**；
- 跨细胞覆盖：≥ **10** 个 `(b,{a,a'})` 上下文在 ≥ **3** 个细胞可算 Δ。
（未过 → `data_unavailable`/`cross_scale_insufficient`，停。）

### G2 合法暴露
- 数值剂量/浓度列存在且可解析、每单元 partner 浓度档匹配、剂量曲线平均规则可执行；暴露时间/检测方法有文档或表内记录；
- 通过率 ≥ **95%** 的单元。
- 状态：`pass`（全可验证）/ `conditional`（设计级可验证但暴露时间或成员剂量曲线仅部分记录）/ `fail`（无数值剂量或无法匹配）。

### G3 独立功能终点
- 要求：功能响应是**独立测量**，而不是由同一原始读数再编码/代数派生；最好存在与主端点正交的功能读数（如 apoptosis/caspase、靶点参与、live imaging）。
- 状态：`pass`（存在独立功能读数）/ `conditional`（仅有 viability 派生协同端点 → 只能作"协同排序"任务，不得称药效/临床）/ `fail`（无组合功能端点或仅转录组代理）。

### G4 重复/批次
- 每个 `y` 至少 **2** 次重复，且重复可标定噪声；独立培养/批次有记录（不同日/passage/培养瓶）。
- 状态：`pass`（独立培养/批次 ≥2 且噪声可估）/ `conditional`（只有技术/barcode 重复，独立培养未认证）/ `fail`（无重复）。
- 技术重复 ≠ 独立培养；barcode 不相交 ≠ 独立培养（R2 教训）。

### G5 与 Jaaks 重叠/非重聚合 lineage
- 报告与 Jaaks 125 细胞/条件/药物的实体重叠；要求存在**非 Jaaks lineage** 的目标细胞/条件，且不是同一资源换聚合。
- 状态：`pass`（目标资源与 Jaaks 细胞重叠 ≤10% 且有独立 lineage）/ `conditional`（部分重叠但有非 Jaaks 细胞/不同来源）/ `fail`（同资源、同 96 细胞换聚合、或目标细胞全部与 Jaaks 重叠）。

### 判定规则（冻结）

- **`qualified`**：G1–G5 全 `pass` 且 Δ 的 MDE80（按 §4）≤ `δ_min_provisional`。
- **`qualified_with_conditions`**：G1 `pass`；G2–G5 均 ∈ {pass, conditional} 且至少一项 conditional；无 fail；MDE80 ≤ **0.15**；列出全部条件（任务收窄/需新测量/独立 lineage 限制）。
- **`not_qualified`**：任一门槛 `fail`，或 G1 fail，或 MDE80 > 0.15；写失败类别 + 所需测量规格；**不得进入第 2 步**。
- **总体判定（source→target 公平比较）**：单资源 `qualified` 不够；要执行"固定反馈比较更新器"，还需要：
  - 一个 **source 资源**（可估 Δ；G1/G2 至少 conditional）；
  - 一个 **target 资源**（G1 至少 pass；G2–G4 至少 conditional；G5 至少 conditional，即存在非 Jaaks 细胞或不同 lineage）；
  - **source 与 target 的端点同族/可比较**（同一 y 定义或预注册可换算；Jaaks 的 `SYNERGY_DELTA_EMAX` 与 O'Neil 的原始 viability 不是同族，若 target 无单药参照/无 ΔEMAX 压缩则不可比较）；
  - **source 与 target 的细胞/条件不相交**（可预注册留出；不能把同一 96 细胞换聚合）。
  - 总体 `qualified` = 存在这样的 source-target 对且全部 G1–G5 与 MDE 门槛通过；总体 `qualified_with_conditions` = 存在这样的对且仅按上述 per-resource 条件通过；否则总体 `not_qualified`（逐条失败类别 + 所需测量规格）。
- **`δ_min_provisional = 0.10`**（ΔEMAX 尺度；敏感性 {0.05, 0.10, 0.15}）；**这是临时值**，第 2 步前必须由 A5 决策成本/真实效用冻结替换；本轮不据此宣称决策收益。
- 判定不因换指标/切分/端点或事后挑剂量档而变；所有阈值运行前冻结。

## 4. Δ 可估性与 MDE 先验（冻结公式）

- **单元 Δ 估计**：`Δ̂(c;a,a';b) = mean_i y(c,a,b) − mean_j y(c,a',b)`（i,j 为重复；缺失重复按预注册规则，不用结果挑重复）。
- **噪声来源（预注册，按不确定性敏感性报告）**：σ_e ∈ {0.041（A0 borrowed R4 σ_e=0.0408）, 0.058（A2 `q2.json` single-key σ=√0.003351）, 0.109（A2 `noise_variance_mean_per_observation`=0.011968 的平方根）}。
- **单元 SE 近似**：`SE_unit = σ_e·sqrt(1/n_a + 1/n_a')`（n_a、n_a' 为两侧重复数；无独立重复时以技术重复上限代入并标注）。
- **聚类后**：`SE_cluster = SE_unit/sqrt(n_eff)`，`n_eff` = 预注册独立上下文数（默认 `min(独立细胞数, 跨细胞上下文数)`；也报告以细胞/伙伴双向聚类的保守口径）；**不得把 92,039 条 unit 当独立 n**。
- **MDE 先验**：`MDE80 = 2.801585 × SE_cluster`（沿用 P-B/R196 的 2.801585 约定），报告 n_eff ∈ {24, 48, 96, 192} 与 σ_e 三档的表；并给"达到 MDE80≤0.10 所需 n_eff"。
- **更新器比较可行性**：只有 `MDE80 ≤ 0.10` 且 G1–G5 允许时才可说"可执行"；MDE80 ∈ (0.10,0.15] → `qualified_with_conditions`（需更多重复/更多上下文）；>0.15 → `not_qualified`（精度不足）。

## 5. 输出与判定

- `q0.json`：所有计数、每候选逐门槛状态、MDE 表、判定、失败类别、输入/脚本 SHA（JSON 键排序、无时间戳）。
- `report_q0.md` / `record_q0.md` / `usage_q0.json`。
- 失败类别：`cross_scale_insufficient` / `exposure_unverifiable` / `endpoint_not_independent` / `replicates_missing` / `lineage_reaggregation` / `precision_insufficient` / `no_combination_data`。
- 所需测量规格：若 `not_qualified`，给出"要满足五门槛最小需测"的清单（细胞数/成员×伙伴交叉/独立功能读数/独立培养批/独立 lineage），不硬凑。

## 6. 纪律与边界

- metadata-only：读列名/ID/剂量设计/行数/重复计数；**不读响应数值做效应**；不训练/不拟合/不估 Q。
- 不重开 R196/R197 旧判定：R196v2 `inconclusive`（C176）、R197v2 `inconclusive`（C177 状态）；这些既不支持机制成立，也不证明条件规律不存在；本 Q0 不引用其效果数字。
- 不把 A3 的 41/4,179 当 Q0 证据（ERRATA_A3/C175：A3 只对冻结大规模门槛）；不把 Jaaks O/V 96 细胞换聚合当新数据。
- 不写机制/迁移/决策收益/新颖性；阴性完整记录；确定性（JSON 键排序、无时间戳、输入/脚本 SHA）；单命令 ≤15 min。
