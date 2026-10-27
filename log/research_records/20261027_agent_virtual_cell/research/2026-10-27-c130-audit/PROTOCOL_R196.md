# PROTOCOL_R196 —— C130 冻结结论的审计级可靠性重估（药物分组内层调参 + 独立评估单元 + 聚类 CI）

2026-10-27，R196。**在任何最终打分计算之前冻结。** 角色：独立 runner（未参与 C130/R163 的开发；本协议的全部规则、门槛、切分、种子、λ 网格均取自 R196 BRIEF/task-20 与 HANDOFF 方法审计的批评，**不来自任何结果**）。
协议冻结后不再修改；实现与协议不符时按 §13 记录**偏离**，不回头改口径、不做事后门槛调整。

**版本**：v1（2026-10-27T18:0x 前后写定；`r196.py` 尚不存在）。

## 0. 范围、判定词汇与不作的主张

- 问题：**在审计修正后的协议下（药物分组内层调参、独立药物评估单元、细胞聚类 CI、MDE 先验），C130 的 both-unseen 增益是否仍然成立、量级是否稳定？** 同时报告**行级内层 λ** 复现作为对照，量化潜在乐观幅度。
- 判定词汇（只用这三种）：`replicated_under_audit` / `weakened` / `inconclusive`。
- **不是外部复现、不是独立确认、不是决策收益/机制主张**。C130 的原始结果不改写；本协议只提供同一资源、同一端点下的审计级重估。若结果为阴性，阴性同样完整记录。

## 1. 输入、端点与注释（冻结）

| 项 | 值 |
|---|---|
| 输入 | `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`（SHA256 `1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278`，与 R163/E163 一致） |
| 读取列 | `CELL_LINE_NAME`, `ANCHOR_NAME`, `LIBRARY_NAME`, `ANCHOR_PATHWAY`, `LIBRARY_PATHWAY`, `SYNERGY_DELTA_EMAX`（**不读其它响应/拟合列**） |
| 端点 | `SYNERGY_DELTA_EMAX`（与 C130 相同） |
| 聚合 | 按 `(cell, anchor + " + " + library)` 取 `mean(SYNERGY_DELTA_EMAX)`（与 C130/E163 相同）；丢弃非有限值 |
| 分析单元 | **108,259** 个 cell×directed-combo 单元；**125** 细胞；有序药对 **2,025**；无序药对 1,294；tissue 3 类（不进入特征） |
| 注释（项目冻结通路模板） | `ANCHOR_PATHWAY`（17 个文本水平）+ `LIBRARY_PATHWAY`（21 个文本水平）→ **38 维 two-sided one-hot**（与 C130/R190-E1 的 21 水平模板同源；每药的通路标签在数据内固定，已断言） |
| 身份 | 两侧药名 one-hot：`onehot(anchor, 65) ‖ onehot(library, 65)` = **130 维**（与 C130 相同构造；药物全集 65，其中 46 个也作 anchor） |
| 设备/预算 | CPU；单命令 ≤15 min；不下载新数据；不改 `src/`；不晋升代码 |

输入事实（冻结）：端点为连续 synergy 增量，mean 0.0006 / sd 0.0768 / range [-0.756, 0.693]。

## 2. 协议前勘察声明（诚实披露）

写本协议前**只读勘察**了：输入文件结构（296,707 行 → 108,259 单元；125 细胞；65 药；2,025 有序药对；17+21 通路水平）、C130/R163 的 `PROTOCOL_E151.md` / `e163_tuned_headline.py` / `E163_RESULTS.json`、HANDOFF 方法审计（内层行级调参 100% 验证行为已见药、34/40 次 λ 触网格上限 1000、40 次重叠重分割的 bootstrap 不是独立 CI、scaler 在内层划分前拟合）、独立重审报告（加性模型只学平均倾向、恒定 Spearman 未定义却记 0 等）。

**机制原型**（`tmp/r196_proto.py`、`tmp/r196_proto2.py`，只用于验证实现与运行时间）运行了 identity / 打乱注释 seed0 / 容量对照 seed0 / **annotation-only** 四个臂。前三个是零模型（打乱与容量对照的 cell 聚类 MDE80 ≈ 0.021–0.025）；**annotation-only 臂的机制检查返回 per-fold mean ρ ≈ 0.149**（在此披露；它未用于修改本协议的任何规则、门槛、λ 网格、折数、折种子、CI 构造或判定阈值——这些在写原型前已由 task-20/BRIEF/审计文本确定）。主臂 **annotation（identity+pathway）** 与行级对照**未**在原型中运行，其数字将在冻结后首次产生。

## 3. 特征与 arms（冻结）

四个特征块：`ID` = 130 维两侧身份 one-hot；`ANN` = 38 维两侧通路 one-hot；`RND` = 38 维 iid N(0,1) 连续特征（容量对照，按 seed 固定）；`ANN_shuf` = 把通路标签在**药物层**按角色分别随机置换后重建的 38 维 one-hot（打乱注释）。

| arm | 特征 | 角色 |
|---|---|---|
| **`annotation`（主）** | `[ID, ANN]` | C130 的"+通路"臂（主对比的正臂） |
| `identity` | `[ID]` | C130 的 baseline 臂 |
| `annotation_only` | `[ANN]` | 去掉身份块后的注释臂（增益来源诊断） |
| `capacity`（10 seeds） | `[ID, RND]` | 同维随机连续特征对照（容量/自由度对照） |
| `shuffle`（10 seeds） | `[ID, ANN_shuf]` | 打乱注释标签零分布（10 个置换种子） |
| `rowlevel_ann` / `rowlevel_id` | `[ID, ANN]` / `[ID]` | **行级内层 λ 对照**（复现 C130 口径）；两个变体见 §5 |

**主对比**：`gain = ρ(annotation) − ρ(identity)`（C130 同一定义）。在 both-unseen 测试池里 identity 的预测是**常数**（见 §6 的显式约定），因此 `ρ(identity)=0.0` 是显式扩展而非估计值；`gain` 在数值上等于 `ρ(annotation)`。这一点必须与任何"标准相关增益"区分。

## 4. 外层设计（药物分组、冻结）

- 药物分组：把 **65 个药物名**（anchor∪library）用 `SEED_OUTER=20261027` 随机排列后均分为 **5 折（每折 13 药）**；同一药物名不允许跨折（**anchor/library 角色按同一药物名共同留出**，防止同名前缀在另一角色泄漏）。
- 每个外层折 f 的 held = 该折 13 药。行分类：
  - **测试（both-unseen）**：anchor∈held 且 library∈held；
  - **训练**：anchor∉held 且 library∉held；
  - **one-seen**：恰一药在 held（既不训练也不进主测试；只作描述性对照，报告量）。
- 冻结设计数字（已用冻结种子精确计算）：每折测试行 = **5,772 / 2,664 / 2,538 / 5,223 / 4,540**，**合计 20,737**（占 19.15%，覆盖全部 125 细胞，395 个有序药对）；训练行 = 64,139 / 75,437 / 76,670 / 63,269 / 65,999；one-seen 行 = 38,348 / 30,158 / 29,051 / 39,767 / 37,720。
- 主估计量：**5 个外层折的 per-fold 增益的均值**（C130 的 split-level 估计量类比；pooled out-of-fold 作为敏感性报告）。测试标签只在最终打分函数中使用（结构上：λ 选择与预测生成不接触测试标签；打分阶段才读 `y[test]`）。

## 5. λ 调参（主分析 = 药物分组内层 CV；冻结）

- λ 网格（**扩大**；理由：HANDOFF 审计发现原网格 34/40 次触上限 1000）：
  `{0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000}`（11 个，固定顺序）。
- 每个外层折内部：把该折**训练集里的 52 个药物**用 `SEED_INNER_BASE + f = 20261027+1000+f` 随机排列后均分为 **3 个内层折（18/17/17 药）**；内层折 j 的 held = 该折药；内层训练行 = 外训练集中两药都不在 inner-held；内层验证行 = 外训练集中**两药都在 inner-held（both-unseen 类比）**。
- 内层指标：对每个 λ，在 3 个内层折分别拟合（**标准化只用该内层折的训练行拟合**，修掉 HANDOFF 指出的"scaler 先于内层划分"泄漏），把 3 个内层验证折的预测**拼接**后计算一个 Spearman（pooled inner-validation Spearman）。
- 选择：取内层指标最大的 λ；**并列取最小 λ**（确定性）。若某臂所有 λ 的内层预测均为常数（指标未定义，例如 `identity` 臂）→ **回退 λ = 网格中位（100）**，并记录 `fallback_all_constant`；该 λ 对该臂在 both-unseen 测试时的预测无影响（仍为常数）。
- 冻结内层设计：每外层折的内层验证行合计 = 20,326 / 24,222 / 25,733 / 20,941 / 20,719；内层训练行合计 = 84,465 / 99,659 / 102,503 / 84,210 / 86,718。
- **行级对照（H196b）**：同一外层分折与同一特征，只把 λ 选择换成 C130 的行级内层 CV：
  - 变体 `rowlevel_c130`：外层训练集整体标准化后（C130 口径），把外层训练**行**随机 3 折（`SEED_ROW_BASE+f = 20261027+2000+f`），内层指标 = 3 折 Spearman 的均值，其余同 C130；
  - 变体 `rowlevel_foldscaled`：同样行级 3 折，但 scaler 在每个内层训练折内重新拟合（隔离"行级 λ 选择"与"scaler 泄漏"两个审计点，只作诊断）。
  - 两个变体都只对 `annotation` 与 `identity` 两臂运行；主报告行级 vs 分组的**增益差**。

## 6. 约定与评分（冻结）

- **标准化**：对所有 λ 选择与最终拟合，特征按训练行 `mean/std` 标准化（`std=0 → 1`）；**λ 选择时内层标准化只用内层训练行**；最终拟合用外层训练行。
- **ridge**：闭式解 `(ZᵀZ + λI + 1e-9·diag(ZᵀZ+1)) w = Zᵀ(y−ȳ)`，预测 `ȳ + Z_te w`（与 C130 同构）。
- **常数预测的显式约定（重要）**：若某折测试预测的极差 `ptp(pred) ≤ 1e-9·max(1, |pred|max)`，则该折 Spearman **未定义**，按**显式约定记 0.0** 并标记 `constant`（`identity` 臂在 both-unseen 池即为此情形；这是 C130 前提的显式化，不是估计出的"零相关"）。非有限 Spearman 也按 0.0 记并标记。每折的 `defined/constant` 计数必须报告。
- **per-fold 指标**：每折、每臂在测试行上计算 Spearman；主估计量 = 5 折均值； pooled out-of-fold 指标作敏感性（pooled 时常数按 100% 常数处理记 0.0）。
- **CI（主）**：**细胞聚类 bootstrap** —— 以 125 个细胞为聚类单元、有放回重抽 125 个细胞（`SEED_BOOT=20261027+3000`，2,000 次）；每次按细胞重数复制该细胞行（cell multiplicity，等价于在重抽数据上重算），对每折重算 Spearman，5 折取均值 → 得到 `gain` 的 bootstrap 分布；CI = 2.5/97.5 分位。
- **CI 敏感性**：① **药对聚类** bootstrap（以 395 个 (anchor,library) 有向药对为聚类单元，1,000 次）；② **双向聚类**（cell × 药对多路 bootstrap：细胞重数 × 药对重数相乘复制行，1,000 次）。均用同一估计量构造。
- **MDE80**：同 CI 口径 —— `MDE80 = 2.802 × SD_boot(gain)`（细胞聚类，2,000 次）；另报药对/双向口径的 MDE80。

## 7. 零模型与校准（冻结）

- `capacity`：`[ID, RND]`，`RND` 由 `SEED_CAP_BASE+seed = 20261027+4000+seed` 生成，seed=0..9；逐 seed 跑完整外层/内层/打分流水线，报告 per-fold mean ρ 的均值与 2.5–97.5% 范围。
- `shuffle`：`[ID, ANN_shuf]`，药物层标签置换（anchor 46 药之间、library 65 药之间分别置换），`SEED_SHUF_BASE+seed = 20261027+5000+seed`，seed=0..9；同上。
- **零分布校准判据（设计体检）**：10 个 shuffle seed 的 mean ρ 的均值绝对值 ≤0.02，且 2.5–97.5% 范围包含 0；capacity 同样报告（不设硬门槛，仅校准）。

## 8. 设计体检（**先于最终打分**；冻结阈值）

以下检查全部通过才进入最终打分；任一失败 → **`inconclusive`**，记录后停止，不救。

| # | 检查 | 通过条件 |
|---|---|---|
| D1 | 折结构 | 5 折×13 药；每折测试行 ≥300；合计测试行 ≥2,000；pooled 测试池覆盖 ≥100/125 细胞；每折训练药 = 52 |
| D2 | 内层药物重叠 = 0 | 每个内层折：`inner-held ∩ inner-train drugs = ∅`，且内层验证行两药均在 inner-held（断言）；每内层验证行 ≥200 |
| D3 | 内层验证 = both-unseen 类比 | 断言：所有内层验证行的两药都不在该内层折训练中出现（按构造检查） |
| D4 | λ 网格固定 | 11 个 λ；报告每折选择值、触上限（10000）次数、回退次数 |
| D5 | 测试标签仅最终打分 | 代码结构：λ 选择与预测生成函数不接收测试索引的 y；`test_label_reads` 计数 = 1 次/折/臂（打分时） |
| D6 | 零分布校准 | shuffle 10 seeds：\|mean ρ\| ≤0.02 且范围含 0 |
| D7 | MDE 先验 | **`MDE80_design = 2.802 × max(SD_boot(shuffle seed0), SD_boot(capacity seed0)) ≤ δ_min = 0.05`**；否则 `inconclusive` |
| D8 | 输入/特征/注释 SHA | 输入文件 SHA256 与 §1 一致；`Xid`/`Xpath` 特征矩阵 SHA256（确定性生成）记录 |
| D9 | 确定性 | 固定种子、JSON 键排序、无时间戳；重复运行产物 SHA256 一致；单命令墙钟 ≤15 min |

## 9. 判定规则（冻结）

- **δ_min = 0.05**（operational 理由，写死）：这是本项目在同类"秩增益"端点上反复使用的最小有意义差值（R195/A0 的 δ_min=.05；R196 BRIEF 建议值）；它比 C130 点估计 0.1183 低 2.3 倍，因此检验的是"审计后是否仍有超过项目可忽略阈值的最小增益"，**不要求**回到 0.1183；同时 D7 要求 MDE80 ≤0.05 保证该阈值在功效上可分辨。
- **稳定带 = [0.05, 0.20]**（先验）：下界 = δ_min；上界 = C130 点估计的 1.69 倍，超过上界视为"量级异常"，同样不判 replicated。
- 主检验对象：`gain = mean_f [ρ(annotation)_f − ρ(identity)_f]`，其中 `ρ(identity)_f = 0.0`（§6 显式约定）。
- **`replicated_under_audit`**：细胞聚类 CI 下界 **> 0** 且点估计 **≥0.05** 且点估计 **≤0.20**；且 D1–D9 全通过。
- **`weakened`**：未达 replicated 且满足以下任一（记录子类型）：点估计 <0.05（`below_minimum_effect`）；CI 含 0（`ci_includes_zero`）；点估计 >0.20（`above_stability_band`）。
- **`inconclusive`**：D 检查失败或 `MDE80_scoring > δ_min`（主对比的实际 MDE 超过最小可分辨效应）→ 停，不做"阴性"解读。
- **H196b（对照）**：报告 rowlevel vs grouped 的增益差及配对细胞聚类 CI；预注册"物质性乐观"标记：`rowlevel_gain − grouped_gain > 0.05`。该标记**不改变**上述三判定（按 task-20 的冻结规则），但在报告中作为可靠性降级标记显式记录（BRIEF 的 H196b 口径）。

## 10. 描述性补充（不作决策收益宣称）

- top-k（k = 5%、20%）：每外层折测试池内按预测排序取前 k%，命中率 = 所选行中 `y ≥ 该折测试池 75 分位` 的比例；与 identity（常数预测 → 按行序确定性截取，等价随机子集，期望命中 25%）及随机期望比较；同时报所选 top-k 的 mean y。全部标为**描述性**。
- equal-budget：同一 k 下 annotation 与 identity 的 top-k mean y 差（描述性）。

## 11. 产物（新建目录 `research/2026-10-27-c130-audit/`；只写该目录与 `tmp/`）

`PROTOCOL_R196.md`（本文件，先冻结）、`r196.py`、`r196.json`、`r196_rows.csv`（per fold × arm 明细）、`report_r196.md`、`record_r196.md`、`usage_r196.json`。
- `r196.json`：全部设定、设计体检、λ 选择、per-fold ρ、主增益与三种 CI、MDE80、零模型 10+10 seeds、行级对照、top-k、审计哈希、判定与条件；JSON 键排序、无时间戳。
- `r196_rows.csv`：`fold, arm, scheme, lambda, n_test, rho, rho_kind, n_constant` 等列（确定性排序）。

## 12. 明确不做

不换端点/换注释系统/换切分制造收益；不把本重估写成外部复现/独立确认/决策收益/机制；不改 C130/R163 产物、其它目录、INDEX/SYNTHESIS/git；不做外部资源再资格；不运行 R187/R188 类抽样；不做元学习/RSI；不因结果改规则。
