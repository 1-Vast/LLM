# record —— R191-PB 端点与测量体制审计（时间线 / 预算 / 决定 / 偏差 / 局限）

2026-10-27。角色：端点与测量体制审计员（独立于提案者）。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / numpy 2.4.6 / pandas 2.3.3 / scipy）。本文件记录**过程**；数字与判定以 [pb.json](pb.json) / [report.md](report.md) 为准。

## 1. 范围与纪律

- 只写 `research/2026-10-27-drugcomb-endpoint/` 与 `tmp/`；未修改 R190-E1 下载目录、其它研究目录、INDEX、SYNTHESIS、git、源数据。
- **不评估任何效应**：`pb.py` 中没有任何模型拟合/训练/特征选择/效应估计路径（grep 复核见 §7）。
- 响应值仅用于 PROTOCOL_PB §1 白名单的五类统计（分布/饱和性、列语义恒等式、可靠性、测量体制描述、MDE 方差估计）。

## 2. 协议前勘察（disclosure）

按任务"先冻结 PROTOCOL_PB.md 再跑"，冻结（SHA256 `1667F89C…882823`）之前做过的**只读**勘察只有：

1. **v1.4 结构预跑**（`tmp/pb_structure_prepass.py/json`，6.3 s）：只读 `block_id / drug_row / drug_col / cell_line_name / conc_*_unit` 与表头，**未读任何响应数值**。结果：组合块 466,033、cell×pair 380,418、药对 62,826、药 4,088、细胞 112、块/单元 1.225055、≥2 块单元 36,637、block_id 1…466,259、单位全 `uM`、无 study 列、无浓度数值列；both-unseen r=0.20 复算 16,078 单元/2,671 对/k=818（与 R190-E1 一致）。
2. **v1.4 表头/单位字符串**：列名 18 个、`conc_r_unit/conc_c_unit` 两个单位列。
3. **v1.5 分块样本表头**（26 列）与 R190-E1 的 `e1.json`（S1 study 表、both-unseen 交叉核对值）。
4. **一手文献**：Europe PMC 取 NAR 2021（PMC8218202）、NAR 2019（PMC6602441）、Malyutina 2019（PMC6544320）全文 XML；GitHub 取 SynergyFinder 实现源码（google/synergyfinderengineered @ 64876b1 的 8 个文件）；Zenodo API 三个 DrugComb 记录的元数据（确认 v1.4/v1.5 文件归属与 MD5）。Jaaks 拟合表只看了**表头**与文件大小（`SYNERGY_DELTA_EMAX/EXP_EMAX/OBS_EMAX` 列名的存在性），未看任何数值。
5. **网络探测**：`drugcomb.org` / `drugcomb.fimm.fi` / `api.drugcomb.org` 未再尝试（沿用 R190-E1 的不可达事实：R190-E1 §3）。取的公开文本总计约 **0.5 MB**（XML 362,582 B + R 源码 37,912 B + GitHub/Zenodo API JSON 若干 KB），远低于 2 GB 预算；未下载任何数据文件（v1.4/v1.5 复用 R190-E1 冻结输入）。

冻结后**未修改协议**。

## 3. 运行与耗时

| 步骤 | 命令 | 耗时/结果 |
|---|---|---|
| 结构预跑 | `python tmp/pb_structure_prepass.py` | 6.3 s |
| 首次正式运行（含 2 处实现 bug 修正前的版本） | `python pb.py` | 106.2 s（split 编码 bug：both-unseen 取错单元，已修正并**在 running 前修复**，不涉及判据） |
| 修正后运行 | `python pb.py` | 103.1 s（Lead 预探数值精确复现） |
| 加诊断/身份校验后运行 ×2 | `python pb.py` | 77.5 s / 83 s（正式最终版） |
| 确定性复核 | 连续两次运行比较 SHA256 | `pb.json` **逐字节相同** `ED5D6C951A3477E2F9A2A2BF57C79374117559F7248E701DE4EAD33EC3AD104B`；`endpoint_audit.csv` 亦相同 `7EAAFFCD…C8FE2E` |
| 身份分段诊断（辅助） | `python tmp/pb_identity_segments.py` | 只读身份列，验证 study 代理窗 |
| MDE 分解诊断（辅助） | `python tmp/pb_mde_diag.py` | 用 `import pb` 复用实现，验证 bootstrap SE 的量级来源 |

## 4. 相对冻结协议的实施偏差（全部为"增加披露"，未改判据/阈值）

1. **增加 Pearson 相关矩阵**（`redundancy.block_pearson / unit_pearson`）：协议只预注册了 Spearman 冗余判据；Pearson 是**事后增加的和解项**，用于解释 Lead 预探的 0.920/0.801（经核实是 Pearson，Spearman 为 0.805/0.734）。判据仍用 Spearman。
2. **增加 MDE 诊断分解**（`mde.*.diagnostic_decomposition`：permutation / pair-level / z-fixed）：明确标注 "post-pre-registration diagnostic decomposition"，**不改变预注册门槛**（门槛仍为双向聚类 bootstrap MDE80）。加入动机是诚实披露 MDE 的构成（验证"大 MDE 来自聚类+单元结构而非实现错误"）。
3. **增加 study 代理窗身份校验**（`window_quality`：v1.4 窗口 distinct 细胞数 vs 论文 S1 cell line 数）并把 MATHEWS 窗判为混合窗排除、把矩阵尺寸检验限定到 5 个验证窗：这是对协议 §9"报告 study 代理异质性"的**质量加固**（不改变"只描述、不选主端点"）。
4. 其余判据（S1–S7、A1–A4、R1–R3、C1–C5、δ_min=0.03、§12 判定规则）**与冻结版逐字一致**，未因看到数据调整。
5. 正式运行前修正的两处实现 bug（both-unseen 的 `member_code` 编码顺序、`np.maximum.at` 的 NaN 初始化）属实现错误，修正后才跑正式数字；修正过程与中间结果（16,078 校验失败 → 修正 → 16,078 ✓）在此披露。

## 5. 关键决定与理由

1. **主端点 `synergy_bliss`**：六候选中唯一与 `ΔEMAX` 同零模型（Bliss 独立）——这是可比性的必要条件；不与"哪个分布更好看"挂钩（全部 6 个指标在饱和性上都不差，选择完全由构造决定）。
2. **聚合 = block 均值**：block 是"一次实验/一张剂量矩阵"（NAR 2019 逐字），Jaaks 对重复测量做平均；A1/A2 稳健性通过（0.9990/0.8386）。
3. **判定 `endpoint_not_usable`**：严格按预注册门槛——MDE80(双向)=0.1149 > δ_min=0.03，升级路径 r=0.40 = 0.0614 也 > 0.03。**没有**因为端点本身干净就放宽 δ_min；把"是否改写 δ_min"作为 Lead 的协议修订选项显式列出（§9.3 / `judgment.reopen_conditions_for_stage_2`）。
4. **`css` 判不可用**：unit 级 S2（贴边 22.11% > 20%）+ S6（10.90% 越已发表的 [0,100] 构造界）；并记录 `css=(css_row+css_col)/2` 精确成立、`S=css−(ri_row+ri_col)` 精确成立——`S` 是 Malyutina `S_sum` 敏感性复合分，**不是** interaction residual。
5. **不换指标**：`synergy_zip/hsa/loewe/S/css` 一律不作主端点替代（PROTOCOL_PB §12.2；`judgment.no_metric_switch_note`）。

## 6. 响应值保护复核

- `pb.py` 是唯一读 v1.4 响应列的代码：`read_v14()` 把 12 个响应/派生列转为 float 数组；下游只调 `dist_stats / unit_aggregates / reliability / semantic identity / redundancy / MDE bootstrap`。**不存在**模型拟合、损失优化、臂比较或增益估计的代码路径。
- grep 复核（`tmp/pb_grep_audit.txt`，模式 `ridge|sklearn|fit\(|predict|coef|train\(|gain|通路−identity|identity arm|annotation arm`）：`pb.py` 6 处、`pb.json` 3 处、`report.md` 2 处、`PROTOCOL_PB.md` 9 处、`endpoint_audit.csv` 0 处。逐条看均为**良性**命中：`np.corrcoef`（相关矩阵）、"null-information prediction vector"/"design prediction"（零信息预测向量与设计假设）、"power gain"（检定力增益的措辞）、以及"禁止/不评估"的否定式声明；**没有** `ridge/sklearn/fit(/train(/coef` 拟合语义。`pb.json → response_value_use_attestation` 显式声明 identity/annotation 模型拟合、效应估计、响应派生训练/特征选择三项均为 False。
- Jaaks 拟合表的 `SYNERGY_*` 数值只用于 §7.3 尺度参照（sd/分位/阈值比例/恒等式残差）——不进入任何 DrugComb 判定。

## 7. 产物清单（SHA256 见 [usage.json](usage.json)）

| 文件 | 说明 |
|---|---|
| `PROTOCOL_PB.md` | 运行前冻结；SHA256 `1667F89C…882823` |
| `pb.py` | 离线确定性审计；SHA256 `5170E16F…3E35276` |
| `pb.json` | 全部数字+判定；两次运行逐字节相同 `ED5D6C95…AD104B` |
| `endpoint_audit.csv` | 逐指标统计（6 指标 × block/unit 两级 + 饱和/冗余/可靠性列） |
| `report.md` / `record.md` / `usage.json` | 报告 / 本文件 / 运行时账 |
| `sources/` | NAR2021/NAR2019/Malyutina 2019 fullTextXML + SynergyFinder R 源码 8 个（SHA256 记于 `pb.json → inputs`，附 commit `64876b1`） |
| `tmp/` | 结构预跑、身份分段诊断、MDE 分解诊断、运行日志、确定性对比副本、grep 审计 |

## 8. 局限（详见 report §11）

- v1.4 无 study/design 列、无浓度数值列、无 QC flag → study/design 归属与矩阵尺寸只能代理；summary 的"矩阵平均"口径由 SynergyFinder 实现＋NAR 文本核对，**未能**由 DrugComb 门户代码核实（门户不可达）。
- v1.5 分块样本是字节均匀非行随机；study 窗是真实范围的下界 → 代理窗有误分类/未指派（3.8%）。
- 同 cell×pair 多块 ≠ 技术重复，ICC 混合技术噪声/设计/study 效应。
- 与 Jaaks 无实体级响应配对 → 只有构造/尺度可比性，无数值等价性。
- MDE 为保守口径（双向聚类 bootstrap）；4 种聚类口径下 MDE80 均 0.076–0.115，判定对该选择稳健。
