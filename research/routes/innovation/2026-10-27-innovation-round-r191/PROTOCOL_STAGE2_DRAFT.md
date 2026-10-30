# PROTOCOL_R191-STAGE2（DrugComb 外部复现）——**DRAFT，未冻结**

> **状态**：草稿。只有在 P-A（`mapping_qualified`）与 P-B（`endpoint_usable`）都通过、且 Lead 完成 unseen-entity/切分裁定之后，本文件才填入数字并改为 `FROZEN`。冻结前不得运行任何效果代码。`<PA:...>`/`<PB:...>` 占位符由阶段 1 产物填入，冻结后不改。

## 0. 目的与非目标

- **目的**：在 DrugComb v1.4（与本项目训练资源不同的第二资源）内部，复现冻结结论的**条件结构**——当两个药在训练中从未出现时，粗注释（P-A 映射）是否恢复排序信息，而药物身份（identity）回归到机会水平/常数。对应 C130/C155–C156/C161。
- **非目标**：不声称新方法/新机制/临床收益；不把 DrugComb 上的成功迁移当作 Jaaks 结论的"独立确认"（仅"第二资源复现"）；不运行 AL/RSI/元学习；不做 raw dose-level 重拟合（除非 P-B 明确要求并另立协议）。

## 1. 数据与宇宙（待 P-A/P-B 冻结）

- 输入：`research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv`（SHA 已录）；P-A 的 `mapping_table.csv`（SHA）；P-B 的端点定义/聚合规则。
- 键：`(cell_line_name 归一, 无序药对归一)`；响应 `y` = P-B 规定的主端点（默认：块级 `synergy_bliss` 在 cell×pair 上的**均值**，块数 ≥1）。`<PB:primary_endpoint>`、`<PB:aggregation>`。
- 宇宙：两药均在 P-A 映射表内的 cell×pair 单元（`<PA:annotated_units>`），细胞 112（敏感性排除 Jaaks 重合的 18 细胞/40 药/241 键）。
- 药物集合：有注释药物 `<PA:n_annotated_drugs>`；确定性留药 20%：归一名排序 `names[0::5][:k]`，`k=round(0.2*N)`；both-unseen 单元 `<PA:both_unseen_units>`（要求 ≥800）、训练两药均有注释单元 `<PA:train_units>`（≥5,000）。

## 2. 特征臂（同信息、同预算；全部只用身份/注释，不含响应）

1. `identity`：药身份 one-hot（两侧）。held-out 药在训练中无行 → 系数为 0 → 测试预测为常数；按定义 ρ(identity)=0（Spearman 未定义时记 0 并在报告披露；同时跑 ridge 数值 sanity）。
2. `annotation`：P-A 单标签通路 one-hot（两侧）；主臂。
3. `size_matched_random`：把注释药物随机重分配到**与真实水平大小多重集相同**的伪水平（5 次抽样取均值/区间；同 C152 口径）。
4. `shuffled_mapping`：打乱药↔通路映射（保持水平大小），5 次；用于结构特异性。
5. `constant`：训练集均值（与 identity 常数预测等价）；`pair_mean` 在 both-unseen 下不可定义，须显式说明。

## 3. 模型与调参（冻结）

- ridge，特征标准化（训练折内拟合均值/方差）；λ 网格 `<PB/PA 既定>`；**内层 CV 必须按药物分组**（留出内层药物，R163 教训）：3 折、按药归一名排序分折；外层测试药物绝不进入标准化/调参。
- 两臂同 λ 网格、同折、同标准化流程。
- 主指标：both-unseen 单元上的 `Spearman(pred, y)`；副指标：top-quartile AUC、top-k 命中（按 P-B 定义）。
- 对照差值：`annotation − identity`（主复现对比；identity 按定义 0）、`annotation − size_matched_random`、`annotation − shuffled_mapping`。

## 4. 统计与检定力

- 区间：bootstrap **按留出药聚类**（主）和按药对聚类（敏感性）重采样 1,000 次；区间宽度与 MDE80 对照。
- 预注册最小效应 δ_min（P-B 给定，默认 0.03）；若 `annotation` 的 ρ 显著 >0 但 `annotation−identity` 的 CI 含 0 → **not_replicated**；若 >0 且 CI 下界>0 且 ≥δ_min 且优于两个随机对照 → **replicated（限定 DrugComb/该端点/该映射）**。
- 种子：20261027；无时间戳。

## 5. 防泄漏清单

- 映射（P-A）只用药物名/靶点/公开基因集，不用响应；**映射表在运行前冻结**；切分按药；内层按药分组；身份/注释特征均为训练数据独立来源；shuffle/size-matched 必做；Jaaks 重合实体只作敏感性排除，不进入主分析。
- 设计体检（先于效果）：identity 预测在测试池为常数（设计断言）；annotation 预测非常数；两随机对照预测非常数；折间单元数/水平覆盖与 P-A 一致。任一失败 → `design_invalid`，不报效果。

## 6. 停止条件与失败类别

- `design_invalid`（体检失败）；`not_replicated`（主对比不成立）；`inconclusive`（CI 跨零且 MDE>δ_min；=失败类别，不救）；`construct_mismatch`（P-B 发现端点不可比）。
- 不得：换指标/换切分/加模块重试；不得把 DrugComb 复现写成"机制"或"独立临床证据"；不得越权晋升代码。

## 7. 交付

`research/2026-10-27-drugcomb-replication/`：`PROTOCOL_STAGE2.md`（冻结版）、`r191.py`、`r191.json`、`rows.csv`、`report.md`、`record.md`、`usage.json`。偏离写 AMENDMENT 并披露。

## 8. 与总体目标的关系

这是冻结结论的**第二资源复现**（跨任务/跨资源验证的第一步），不是 Agent×VC 共同学习的新机制，也不绕过 RSI 前置条件（独立决策收益+跨任务迁移都成立才谈 RSI）。成立后才讨论"该条件规则能否进入 Agent 的决策/证据选择"；不成立则记录阴性边界。
