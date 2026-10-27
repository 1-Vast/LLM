# PROTOCOL_STAGE2（v1，2026-10-27 **FROZEN**）：DrugComb 外部复现——both-unseen 粗注释替代身份

> 冻结时间：2026-10-27（运行任何身份/注释模型或读取任何效应之前）。依据：`research/2026-10-27-innovation-round-r192/BRIEF.md`、C161–C166、P-A2/P-B/P-B2 冻结产物。冻结后不改；若独立挑战要求修改，写 AMENDMENT 并升版本，且在**运行效果代码之前**重新冻结。
> 本协议**不预设复现成立**；失败（含阴性）是有效结果。

## 0. 要复现的命题（与冻结结论的对应）

> 两个药在训练中**都未出现**时，药物粗注释（代替缺失的药物身份）恢复 `ΔEMAX` 排序信息；身份回归机会水平。

在 DrugComb v1.4 上的对应检验：在**留出药物**构成的 both-unseen cell×pair 池上，`annotation` 臂的排序（Spearman(pred, y)）显著为正、且优于 `identity`（按定义为 0）与两个随机对照；效应量至少达到原 CI 下界 δ_min=0.0947（P-B2 Tier A）。

## 1. 数据与冻结输入

| 输入 | SHA256（前缀） | 用途 |
|---|---|---|
| `research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv`（193,184,734 B） | `e08e3d35…` | 身份列 + 主端点 `synergy_bliss` |
| `research/2026-10-27-drugcomb-annotation/mapping_table_v2.csv`（S1 行；主策略 source_library=="S1"） | `705a5e64…6ed015` | 药物→KEGG 通路（单标签） |
| `mapping_table.csv`（v1 表，敏感性用） | `45ede635…38d4` | 映射版本敏感性 |
| P-B `PROTOCOL_PB.md` / `pb.json` | `1667F89C…` / `ED5D6C95…` | 端点/聚合/饱和性冻结规则 |
| P-B2 `PROTOCOL_PB2.md` / `pb2.json` | `87B1EDC9…` / `CC5047A8…` | MDE 方法（2.801585×SE、双向聚类 bootstrap、power 模拟） |

- **键**：`(cell_line_name 归一, 无序药对归一)`（NFKC→casefold→仅字母数字；药对两侧排序后拼接）。
- **主端点 y**：该单元内**全部非缺失 block 的 `synergy_bliss` 算术平均**（P-B 冻结聚合；块数 ≥1）。端点不饱和、构造可比性已审（C164）；**不换端点**。
- **映射**：v2（S1-A 主策略）；两药都必须有非 `unmapped` 的 S1 pathway 才进入分析宇宙。

## 2. 切分（冻结）

- 药物集合 M = v2 映射表 S1 行中 `pathway != unmapped` 的归一药名（**N=1,800**，排序后）。
- **PA 切分、r=0.50**：`k=max(1,round(0.50*N))=900`；`step=max(1,N//k)=2`；留出集 H = `sorted(M)[0::step][:k]`；训练药集 = M\H。
- **测试池（both-unseen）**：两药都在 H 的 cell×pair 单元；**训练池（strict）**：两药都在 M\H 的 cell×pair 单元。
- 本次 scoping 预期（**pre-flight 必须实测确认**）：测试池 **32,299 units / 5,342 pairs / 108 cells**；strict 训练池 **27,230 units**；可分析水平 **93**。
- 敏感性（预先声明、不参与主判定）：r=0.55 切分；E1 切分（留出建在全体 4,088 上）；v1 映射表；Jaaks 重合实体排除（18 细胞/40 药/241 键）。

## 3. Pre-flight 门槛（运行任何模型前必须先过；任一失败 → 停止并记录，不运行效果）

- **F1 规模**：测试池 units ≥14,387（P-B2 Tier B 最小所需，v1 外推；实测预期 32,299）且 pairs ≥2,000；strict 训练池 units ≥5,000（预期 27,230）。
- **F2 注释结构**：可分析水平 ≥12（每水平 ≥2 药、训练与留出均出现；预期 93）；两药均有注释的测试单元覆盖率 100%（由构造保证）；映射表与 v2 表 SHA 一致。
- **F3 检定力**：用 P-B2 冻结方法在实际 v2 测试池上计算 `MDE80_two_way` 与 `power@δ_min`；要求 **MDE80_two_way ≤ δ_min=0.0947** 且 **power@0.1183 ≥0.80 且 power@0.0947 ≥0.80**。预期（由 pairs 外推）：MDE80≈0.075、power@0.0947≳0.85。任一不满足 → 停。
- **F4 设计体检**：identity 臂在测试池预测为常数（设计断言）；annotation 臂预测非常数；两个随机对照非常数；测试药不出现在训练池；内层 λ 按药分组。任一失败 → `design_invalid`。

## 4. 特征臂（全部只用身份/注释；不使用响应构造特征）

1. `identity`：药物 one-hot（两侧；仅训练药出现）。留出药列在训练中恒 0 → 测试预测 = 截距（常数）；**ρ(identity) 按定义记为 0**（Spearman 未定义；同时报告 ridge 数值 sanity）。
2. `annotation`：药物 S1 pathway one-hot（两侧；水平取训练池中出现的水平，测试水平必须在训练出现——F2 保证）。**主臂**。
3. `size_matched_random`：把注释药物随机重分配到**与真实水平大小多重集相同**的伪水平（5 次抽样；保留药物→伪水平映射在同一训练/测试框架内）。
4. `shuffled_mapping`：随机打乱药↔水平映射（5 次，保持多重集）。
5. `constant`：训练池 y 均值常数（与 identity 等价，作 sanity）。
6. `annotation_v1` / `annotation_ruleB`（敏感性、不参与主判定）：v1 映射表 / 规则 B 标注。

## 5. 模型与调参（冻结）

- ridge 回归，特征标准化（均值/方差只在训练池拟合）；λ 网格 `[0.1,0.3,1,3,10,30,100,300,1000]`。
- **λ 选择：内层 3 折、按药物分组**（把训练药集排序后分 3 折；内层训练 = 两药都在内层训练药的单元；内层验证 = 两药都在内层留出药的单元，即 both-unseen；用内层验证 Spearman 均值选 λ）。测试药绝不进入标准化/调参。
- 预测只用训练池拟合；测试池只用于最终打分一次。
- 随机对照臂每次抽样用同一 λ 网格/同一内层流程。

## 6. 主指标、对照与判定（冻结）

- **主指标**：测试池 `Spearman(pred, y)`（连续 y）。
- **副指标**：top-quartile AUC、top-k 命中（k=100）；不作主判定。
- **对照**：`annotation − identity(=0)`、`annotation − size_matched_random`、`annotation − shuffled_mapping`、`annotation − constant(=0)`。
- **区间**：bootstrap **按留出药聚类**（重采样 900 个留出药及其测试单元）1,000 次，固定种子 20261027；另报按细胞双向聚类敏感性。MDE80 同法。
- **判定规则（先冻结）**：
  - **`replicated`**：annotation ρ 点估计 **≥0.0947** 且 bootstrap 95% CI 下界 **>0**，并且两个随机对照的 (annotation−对照) CI 下界 **>0**；
  - **`partial`**：annotation ρ 显著 >0（CI 下界>0）但点估计 <0.0947 或未同时优于两个对照；
  - **`not_replicated`**：annotation ρ CI 含 0 或 ≤0；或随机对照同样显著（无结构特异性）；
  - **`inconclusive`**：F3 未过（=失败类别，不救）。
- **δ_min=0.0947** 的正当化：= 原冻结结论 95% CI 下界（C130），是"最保守的可复现目标"；不是观察到的效应。

## 7. 防泄漏清单（冻结）

- 映射（v2）只用药物名/靶点/HGNC/MSigDB，不用响应；mapping 表在运行前冻结 SHA。
- 切分/λ/对照抽样/δ_min/MDE 全部在本协议中先冻结；测试标签只在最终打分使用。
- 内层 λ 按药分组；测试药不进标准化；Jaaks 重合实体只作敏感性排除，不影响主分析。
- 设计体检 F4 先于效果；任一失败即停。

## 8. 停止条件与失败类别

- F1–F4 任一失败 → `design_invalid`/`inconclusive`，**不运行效果、不换设计救**。
- 主判定为 `not_replicated` → 记录"在 DrugComb 上未复现该条件结构（限定 DrugComb/该端点/该映射）"，不换端点/指标/切分重试。
- 不得：把结果写成机制/临床证据；把 DrugComb 复现写成 Jaaks 结论的独立确认；把 annotation 收益归因于 drug identity 之外的任何东西。

## 9. 交付

`research/2026-10-27-drugcomb-replication/`：
- `PROTOCOL_STAGE2.md`（本文件，冻结版+AMENDMENT 记录）
- `preflight.py` / `preflight.json`（F1–F4，含输入与脚本 SHA256）
- `stage2.py` / `stage2.json` / `rows.csv`（臂×折的 ρ 与预测矩阵摘要）
- `report.md`（判定、数字、对照、MDE、敏感性、局限）
- `record.md`（时间线/预算/命令）、`usage.json`

## 10. 明确不做

不拟合 identity/annotation 之外的模型；不做 AL/RSI/元学习；不做机制/靶点占据/临床推断；不换端点/指标；不晋升代码。
