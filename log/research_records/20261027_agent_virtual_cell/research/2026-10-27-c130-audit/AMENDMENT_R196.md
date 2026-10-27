# AMENDMENT_R196.md —— PREGISTERED AMENDMENT-001（R196 v2 重跑协议）

2026-10-27，R196 v2。**在 `r196_v2.py` 存在与任何 v2 结果产生之前冻结。**
依据：[challenge_R196.md](challenge_R196.md)（task-29 独立挑战，判 **revise**，5 条必改）与 [REVOCATION_R196.md](REVOCATION_R196.md)（Lead 生效：v1 verdict 撤回）。本修正案**只覆盖 R196 v2**；v1 的 `PROTOCOL_R196.md`、`r196.py`、`r196.json`、`r196_rows.csv` 保留不改，v1 报告/记录按撤回后口径登记。
协议冻结后不再修改；实现偏离记录在 `record_r196_v2.md`。

## 0. v1 撤回与修正案要解决的问题

v1 的 5 条必改（挑战 §3 / 撤回 §3）：① 主推断单位必须是 **held-out 药物/药物划分**（drug-cluster 主 CI + MDE80≤δ_min）；② 预注册 **≥10 个独立药物划分**，fold dispersion 升级为正式 sensitivity；③ **统一 grouped/row-level 内层 λ 指标**并隔离 H196b，row-level 加 C130 ≤1000 网格桥接；④ δ_min/稳定带 **operational 化**并与 drug 单位 MDE 联动；⑤ 固定措辞模板 + 披露预冻结 peek + 声明 C130 CI 非参照 + 可比性声明。

## 1. 数据、端点、特征、臂（与 v1/C130 一致，冻结）

- 输入：Jaaks Original fitted，SHA256 `1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278`；只读 `CELL_LINE_NAME`/`ANCHOR_NAME`/`LIBRARY_NAME`/`ANCHOR_PATHWAY`/`LIBRARY_PATHWAY`/`SYNERGY_DELTA_EMAX`。
- 聚合：`(cell, anchor + " + " + library)` 取 `mean(SYNERGY_DELTA_EMAX)` → **108,259 单元 / 125 细胞 / 65 药 / 2,025 有向药对**（与 v1/C130 同构）。
- 注释 = 38 维双侧通路 one-hot（17 anchor 水平 + 21 library 水平）；身份 = 130 维两侧药名 one-hot。
- 臂（v2）：
  | arm | 特征 | 作用 |
  |---|---|---|
  | **`annotation`（主）** | `[ID, ANN]` | C130 的"+通路"臂 |
  | `annotation_only` | `[ANN]` | 去掉身份块诊断 |
  | `identity` | `[ID]` | both-unseen 测试预测**必为常数**（v1 已验证 5/5 折 constant）；v2 中按 §4 约定 `ρ=0.0`，**不拟合**（v2 在 partition 0 上跑一次常数性检查，断言通过后对全部 50 折沿用该构造性结论） |
  | `rowlevel_ext` | `[ID, ANN]` | 行级内层 CV，**扩展网格**，折均指标 |
  | `rowlevel_c130_grid` | `[ID, ANN]` | 行级内层 CV，**C130 原网格 ≤1000**，折均指标（C130 桥接） |
  | `grouped_c130_grid` | `[ID, ANN]` | grouped 内层 CV，C130 网格（同网格 H196b 对称桥接） |
  | `capacity` ×10 seeds | `[ID, RND]` | 同维随机连续特征对照（仅 partition 0） |
  | `shuffle` ×10 seeds | `[ID, ANN_shuf]` | 药物层标签置换零分布（**完整 10 划分设计**） |

## 2. 外层设计：**10 个独立药物划分**（冻结）

- 药物集 = 65 个药物名（anchor∪library 并集，角色共同留出）。对划分 `p = 0..9`：`SEED_PART = 20261027 + 100·p` 随机排列后均分 **5 折（13 药/折）**。
- 每划分内：测试=两药均在 held；训练=两药均不在 held；one-seen 排除。
- 冻结设计数字（与 v1 同一构造；各划分的行数略有不同、见 `r196_v2.json`）：每折测试行 ≥2,500、每划分 ≈20,700；125 细胞全覆盖；每折训练药 52。
- 内层折：划分 p 的外层折 f 内，把该折 52 个训练药用 `SEED_INNER = 20261027 + 500000 + 1000·p + f` 均分 3 折（18/17/17）；内层验证=both-unseen 类比；内层训练=两药都不在 inner-held；**scaler 只用该内层训练行拟合**。
- 行级内层：同外层折内，用 `SEED_ROW = 20261027 + 600000 + 1000·p + f` 把外层训练**行**随机 3 折（C130 口径；**scaler 在每折内拟合**，与 v1 的 `foldscaled` 变体一致——这是与 v1 `c130` 变体（折前标准化）不同的唯一实现选择，理由：挑战 ③ 要求统一折内标准化口径；折前标准化会引入已知内层泄漏）。

## 3. 内层 λ 选择：**统一为折均 Spearman**（冻结）

- 内层指标（grouped 与 row-level 完全相同）：对 3 个内层折分别（各自训练集/折内 scaler）得到验证预测并计算 Spearman，取 **3 个 Spearman 的算术平均**。**不再使用跨折拼接的 pooled Spearman。**
- λ 网格（冻结）：
  - 扩展网格 `L_EXT = {0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000}`（11 个）——用于 `annotation`、`annotation_only`、`rowlevel_ext`、`shuffle`；
  - C130 原网格 `L_C130 = {0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000}`（9 个）——用于 `rowlevel_c130_grid` 与 `grouped_c130_grid`。
- 选择：内层指标最大的 λ；**并列取最小 λ**；若某臂全部 λ 的内层指标未定义（常数预测）→ 回退 λ=网格中位（`L_EXT`→100，`L_C130`→10），记录 `fallback`。
- 报告：每 (划分,折,臂) 的 λ、触上限次数（`L_EXT`=10000 / `L_C130`=1000）、回退次数、网格内 λ 一致性。

## 4. 打分、主估计量与主推断单位（冻结；**核心修正**）

- **单折增益**：`gain_{p,f} = ρ(annotation)_{p,f} − ρ(identity)_{p,f}`，其中 `ρ(identity)_{p,f} = 0.0`（**显式约定**：both-unseen 测试行的 identity 预测为常数，Spearman 未定义；这是 C130 前提的显式化，不是估计值）。`ρ(annotation)` 由 5 折外推（每折一个模型、每折训练集不含测试药物的任何一行）。
- **主估计量**：`Δ = mean_{p,f} gain_{p,f}`（10 划分 × 5 折 = **50 个折级增益**的等权均值）。
- **主 CI（药物单位）= drug-cluster bootstrap**：对 65 个药物名做**双侧（anchor 角色 × library 角色）有放回重抽**（各 multinomial(65)），每次按重数 `m_anchor(a)·m_library(b)` 复制该折测试行后重算折级 Spearman，得到 50 折均值；B=2,000（`SEED_BOOT_DRUG = 20261027 + 700000`）；CI = 2.5/97.5 分位。
- **主 MDE80** = `2.802 × SD(bootstrap Δ)`（与主 CI 同口径）。
- **次级/敏感性（不作判定）**：cell-cluster bootstrap（125 细胞，2,000）、pair-cluster bootstrap（2,025 有向药对，1,000）、two-way（cell×pair 多路，1,000）、**划分级**（10 个划分增益的均值/SD/t-CI df=9/percentile）、**折级正式 sensitivity**（50 个折级增益的 SD/t-CI df=49/leave-one-partition-out）。
- **零模型对照**：capacity 与 shuffle 的 `ρ − 0`（identity 为 0）同口径；另报 `annotation − capacity_seed0` 的 drug-cluster CI（描述性）。

## 5. δ_min 与稳定带的 operational 定义（冻结；核心修正）

- **δ_min = 0.05** 的 operational 定义（不是"项目习惯"）：对 Spearman ρ，用 Kendall τ ≈ (2/π)·arcsin(ρ) 换算，ρ=0.05 ⇔ τ≈0.0318 ⇔ **随机抽取一对"未见组合"时正确排序的概率相对机会水平提高约 1.59 个百分点**。取 δ_min = 0.05 即"审计要求能被分辨的最小**秩信息量**增益"——它**不是**决策效用阈值，也不支持任何决策收益宣称。
- **与 drug 单位 MDE 联动（硬条件）**：`replicated_under_audit` 要求 **主 MDE80（药物单位）≤ δ_min**，即设计必须能在审计目标单位上以 80% 功效分辨 δ_min；否则 `inconclusive`。
- **稳定带上界取消**（采纳挑战 §3.4 的选项 b）：不设上界、不因"过大"判失败。若点估计 >0.20，仅记录 `large_gain_flag=true` 作为"可能偏置/泄漏"的descriptive 提示（无对应诊断，不参与判定）。
- 判定规则（只此三档）：
  1. **`inconclusive`**：主 MDE80 > δ_min **或** 任一设计体检（§6）失败；
  2. **`replicated_under_audit`**：主 CI 下界 > 0 **且** 点估计 ≥ δ_min **且** 主 MDE80 ≤ δ_min 且设计体检全过；
  3. **`weakened`**：其余（记录子类型 `ci_includes_zero` / `below_minimum_effect`；**不得**写"C130 被推翻"）。
- H196b：**同样内层指标 + 同网格**对比：`rowlevel_ext − grouped(ext)`（主）与 `rowlevel_c130_grid − grouped_c130_grid`（C130 网格桥接）；差值 CI = 配对 drug-cluster bootstrap（同一重抽）；`material_optimism_flag = (差值 > 0.05)` 仅作可靠性标记，**不改变**上面三档判定（按 task-20 冻结规则；BRIEF 的 H196b 口径按此记录）。

## 6. 设计体检（**先于最终打分**；冻结）

| # | 检查 | 通过条件 |
|---|---|---|
| E1 | 折结构 | 10 划分 × 5 折；每 (划分,折) 测试行 ≥300；50 折合计 ≥20,000；pooled 覆盖 ≥100/125 细胞；每折训练药=52 |
| E2 | 内层药物重叠=0 / 内层验证 both-unseen | 断言全部通过；每内层验证折 ≥200 行 |
| E3 | 内层指标统一 | 代码审计：grouped 与 row-level 都是"3 折 Spearman 的算术平均"；`record_r196_v2.md` 记录 |
| E4 | λ 网格固定 | `L_EXT`(11) 与 `L_C130`(9) 写死；报告每格选择与触上限 |
| E5 | 测试标签仅最终打分 | 标签以 NaN 掩码视图传给 λ 选择/拟合；测试标签只在打分函数读；计数 = 50 折 × 拟合臂数 |
| E6 | 零分布校准 | shuffle 10 seeds 的折均 ρ（每 seed=50 折均值）：\|mean\| ≤0.02 且 2.5–97.5% 区间含 0 |
| E7 | **MDE 设计门（药物单位）** | `MDE80_design = 2.802 × SD_drugboot(shuffle_seed0)` ≤ δ_min；否则 verdict=`inconclusive`（此时仍**描述性**报告主臂数字，不做推断） |
| E8 | 引擎等价性自检 | 计数式快速 ridge 引擎 vs 稠密矩阵实现：同一 (划分,折,内层折) 的预测最大绝对差 <1e-8 |
| E9 | 输入/特征 SHA、确定性、预算 | SHA 与 §1 一致；重复运行产物 SHA256 一致；单命令 ≤15 min |

## 7. 措辞模板（冻结；写入 report）

- `replicated_under_audit` 只允许："**在 AMENDMENT-001 的审计修正协议、固定 10 个药物划分与声明的主推断口径（held-out 药物）内，both-unseen 增益点估计 ≥δ_min 且药物聚类 CI 下界 >0、主 MDE80 ≤δ_min**"；**必须并列** drug-cluster CI/MDE 与折/划分离散；**不得**写"C130 复现/独立确认/量级恢复/决策有用/机制"。
- `weakened` 不得写"C130 被推翻/注释无用"；只能写"在本协议下未达到审计级可靠的最低标准"。
- `inconclusive` 不得写"阴性"；只能写"审计目标单位功效不足/设计体检未过，未决"。
- **C130 的 CI [0.0947,0.1409] 不是本修正案的参照区间**（切分/λ 网格/内层口径不同）；row-level 对照是"同一外层划分下的桥接诊断"，不是 C130 复现。
- **预冻结 peek 披露**：v1 机制原型曾跑 annotation-only（≈0.149）与零模型；主臂 annotation/identity/row-level 未在冻结前运行。v2 的规则、阈值、网格、划分种子、判定规则均来自挑战/撤回文本与 v1 协议，**不以 v2 结果为转移**。
- **不是外部复现/独立确认/决策收益**；不换端点/注释/切分制造收益。

## 8. 产物与确定性

`AMENDMENT_R196.md`（本文件，先冻结）、`r196_v2.py`、`r196_v2.json`、`r196_v2_rows.csv`、`report_r196_v2.md`、`record_r196_v2.md`、`usage_r196_v2.json`（同目录；不改 v1 产物）。
`r196_v2.json` 键排序、无时间戳；固定种子全列于 `settings`；输入/特征/脚本/协议 SHA256 记录。确定性：两次运行 `r196_v2.json`/`r196_v2_rows.csv` SHA256 一致。

## 9. 明确不做

不换端点/注释系统/切分来制造收益；不做外部复现/独立确认/决策收益/机制；不改 C130/R163 产物；不改 v1 产物；不把本重估写成"C130 被推翻"；v2 结果在 task-32 独立挑战通过前不得解释。
