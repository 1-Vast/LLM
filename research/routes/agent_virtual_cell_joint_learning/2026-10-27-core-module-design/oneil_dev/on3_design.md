# ON3 设计说明（DRAFT，设计阶段；不运行效果）

2026-10-27 · 角色：ON1/ON2/ON2.2 执行者（非提案者）。配合 [PROTOCOL_ON3.md](PROTOCOL_ON3.md) 的 DRAFT v0.1；**本文件解释设计选择、替代方案、风险与给挑战者的问题；不含任何响应值统计、未训练/未运行效果。**

## 1. 目标与可检验量（写死）

- **对象**：O'Neil complete-case 内部细胞 5 折留出下的 `Δ(c;a,a';b)`。
- **可检验量（描述性）**：held-out 掩码单元的预测秩相关 Spearman ρ、MAE、top-k overlap（描述）；以及相对强静态基线 B2 的 Δρ（预注册增量规则）。
- **不是**：迁移/外推、决策收益、机制、独立确认、更新器比较、新算法。

## 2. 为什么用"细胞留出 + 单元掩码"设计（关键设计选择）

**问题**：ON2 允许的数据只有组合 viability + 细胞/伙伴/成员身份/剂量；**没有细胞协变量**（无组织/表达/单药参照被资格化）。若做"纯冷细胞"预测（held-out 细胞的所有数据都不可用），任何"cell×partner×member 条件结构"都退化为 cell-blind 静态结构——无法检验"条件结构"是否带来增量。

**选择**：5 折**细胞留出**（训练细胞不参与拟合）+ held-out 细胞内部**20% 单元确定性掩码**；held-out 细胞的**非掩码 80% 单元**作为 transductive context（用于估计该细胞的 cell 偏移/低秩因子），**掩码单元只作评价、绝不进入任何模型路径**。这样：
- 保留了"跨细胞"的泛化结构（模型只用训练细胞拟合）；
- 给 held-out 细胞一个**可识别的条件上下文**（其非掩码单元），使 B3/B4 的 cell 条件结构有信息可用；
- 用固定 hash 掩码 + 泄漏审计控制"偷看评价值"的风险。

**替代方案（未采用，供挑战者审）**：
1. **纯冷细胞预测**：无 cell context → 只能比较静态结构；与问题"条件结构"不匹配。
2. **跨细胞 link prediction**（预测 held-out 细胞的某些 (partner,role,pair) 而未观测该 cell 任何数据）：需要 cell 协变量（无）或单药参照（未资格）→ 不可识别。
3. **用单药工作簿做 cell 协变量**：单药表存在（39 细胞/38 药/6 技术重复），但 ON2 明确"未单独资格、primary 不用"；若未来先立单药资格协议，可作为**敏感性**，不得进 primary。
4. **细胞内随机 20% 掩码 + 全细胞训练**（不严格细胞留出）：会泄漏同细胞信息到"训练"；本设计保持细胞留出严格性，同时允许 transductive context（已披露）。

**披露**：本设计是"细胞留出 + transductive context"，**不是**纯零样本冷启动；结论只能写"在该设计下是否存在描述性预测增量"，不能写"可迁移到新细胞/新资源"。

## 3. 数据/切分细节

- cohort：complete-case 363,090 行（98.44%）；**主分析 BatchID=1（357,876 行）**；batch2（5,214）不进 primary（避免 batch 混合；batch2 仅披露/可选敏感性且不得进训练/指标）；batch3 全失（0/5,040，披露）。
- 目标 30 非 Jaaks 重叠细胞；5 折继承 ON2（6/6/6/6/6；附录 A）；**不重分折**。
- 单元 Δ：完整 4×4 网格（16 行）；角色分层；符号按归一名；k=1 行排除；**702 个 15 行 pair-cell → 不完整 member context → 排除并计数**；主分析不插补；确定性行均值单插补仅敏感性（不是 MI；不参与主指标）。
- 评价掩码：`SHA256("ON3|batch|cell|partner|role|a|a'|ON3-mask-20261130")` 升序取前 20%（每 fold，ceil）；每 fold 预期掩码 13,311–13,948 单元；每 held-out 细胞 ≥500；每 fold 掩码上下文 ≥50；mask 只依赖 key/seed，与响应无关；冻结后不改。

## 4. 比较器（设计理由）

| 代号 | 作用 | 关键点 |
|---|---|---|
| B0 | 全局均值 | 最低信息基线；检验"是否只是均值" |
| B1 | 静态可加（role+partner+member-pair） | 静态主效应的强基线；backoff 冻结 |
| B2 | 静态强（partner×member-pair） | **主比较基线**（"强静态基线"）；最保守的增量来源 |
| B3 | B2 + held-out 非掩码 context 偏移 | 检验"cell 上下文"是否带来信息（不引入 cell 身份特征） |
| B4 | 层级 + 低秩（cell×pair） | **条件结构主模型**；rank/λ 网格冻结；ALS 25 iter；cell 因子由非掩码 context 估计 |
| B5 | HistGBM（容量对照/强预测器） | 检验"强容量但无 cell 结构"是否也能拟合；特征不含 cell id；target-encoding 仅训练 fold |
| B5-shuf | B5 + 训练 cell 标签打乱 | 容量对照的负控制 |
| B6 | B4 + held-out context 跨细胞打乱 | 打乱零模型；用于 null 校准与增量判据 |

- 全部使用**同一掩码/同一折/同一评价单元**；不预设模型胜出；不做 test-set 调参；超参只有训练细胞 inner CV（leave-one-cell-out within 24 training cells）。
- **不比较更新器**（任何固定反馈/更新器比较须另立协议+挑战）。

## 5. 指标与增量判定

- 主：Spearman ρ（pooled masked units per fold；5 折 mean/SD；per-cell median）。
- 次：MAE（paired with B0；5 折 mean/SD）。
- 描述性 top-k：k∈{1,3,5}；上下文内 masked units ≥k；precision@k/overlap；报告 base rate/上下文数；**无决策收益含义**。
- 增量（相对 B2）：mean Δρ≥0.10；≥4/5 folds Δρ>0；细胞聚类 paired bootstrap 95% CI 排除 0；观测 Δρ > B6 null Δρ 95th。全满足→"描述性增量"；否则 `no_increment`。
- 无法区分：观测 ρ 落 B6 95% 内 → `evaluation_cannot_distinguish`；MDE80>δ_min → `design_invalid`。

## 6. 功效/MDE

- 用 ON2-EX 实测 σ̂_e=0.1422665081（不沿用借用先验）：SE_unit=0.0251494031、MDE80=0.0287644381（n_eff=6）、δ_min=0.10；calibration_passed。
- MDE80 是均值 Δ 尺度先验；rank 指标用 B6 零分布；MAE 的 MDE 不做精确映射；技术重复不作独立 n；n_eff=6 保守。
- 预期掩码量：每 fold 13,311–13,948；总量约 66.6k–69.7k 掩码单元；足够估计 Spearman/MAE（但不是独立 n）。

## 7. 泄漏审计与零模型（设计）

- 掩码扰动测试（掩码值 +1e6 预测不变）；cell 身份不作为特征；batch1 only；无 Jaaks/ΔEMAX；无剂量外推；无 test 调参；mask 不含响应；单药值不进 primary；折分配继承。
- B6 null：held-out context 跨细胞打乱（保持 partner/role 分层）；B4 null 分布 95% 覆盖 0 且 mean|ρ|≤0.10 才允许进入结果解释；否则 `design_invalid`。
- 审计须有代码级单测/断言与输出 schema（执行时冻结）。

## 8. 失败类别/停止

- `data_unavailable`：数据门（含 ON3 掩码覆盖）。
- `design_invalid`：泄漏审计/零模型/MDE>δ_min。
- `evaluation_cannot_distinguish`：观测落 null 范围/不可估计。
- `no_increment`：增量规则不满足（描述性停止）。
- 不换指标/切分/端点/掩码/比较器凑结果；不重跑换 seed 追结果。

## 9. 风险与限制（必须随协议读）

1. **transductive context 不是纯冷启动**：结论不能写"可迁移到新细胞/新资源"。
2. **20% 掩码是设计选择**：冻结于 seed；换 fraction/seed 可能改变结果，不得事后调。
3. **MDE 尺度**：MDE80 针对均值 Δ；rank/MAE 用 null 校准，不能把 0.02876 当所有指标的检定力。
4. **小样本/5 折 6 细胞**：bootstrap 按细胞聚类；fold 间异质性大时保守解释。
5. **B5 容量可能过拟合**（小数据）；B5-shuf 用于区分容量效应。
6. **无细胞协变量**：条件结构只能通过 held-out 非掩码 context 进入；这不是"细胞表征"证据。
7. **top-k 无决策收益**：不得写选药/实验收益。
8. **单药参照未用**：若未来使用须先单独资格（同 lab/技术重复≠独立培养）。
9. **缺失机制未知**：不假设 MCAR/MAR；702 个 15 行 pair-cell 排除。
10. **阴性 ≠ 结构不存在**：只记录本资源/本设计下未观察到描述性增量。

## 10. 什么结果会否定/停止

- B0/B1/B2 已解释大部分秩/误差，条件模型无增量 → `no_increment`；
- 条件模型观测指标与 B6 零分布不可区分 → `evaluation_cannot_distinguish`；
- 泄漏审计失败/零模型异常/MDE>δ_min → `design_invalid`（停止，不解释结果）。

## 11. 给独立挑战者的问题（请审）

1. "细胞留出 + 20% 单元掩码 + transductive context" 是否可接受为**开发性描述**设计？还是必须用纯冷细胞/其它切分？
2. 20% 掩码比例与 seed 是否应改为预注册随机或固定分层（例如按 partner/role 分层 20%）？
3. 增量阈值（Δρ≥0.10、4/5 folds、bootstrap CI、null 95th）是否合理？是否应与 MDE/最小实际意义对齐？
4. B2 作为"强静态基线"是否足够强（是否需要单药/伙伴主效应的更强基线）？
5. 单药工作簿是否应在本协议外先立资格、再作敏感性？
6. B5 的容量网格/特征是否构成"强预测器"充分对照？是否需要额外容量匹配？
7. 是否需要把 top-k 指标降为纯附录（避免被误读为决策收益）？
8. 零模型 B6 的打乱粒度（跨细胞 context 打乱 vs 细胞标签打乱）是否足够？

## 12. 预注册检查单（执行前须冻结）

- [ ] 数据 cohort/批次/细胞/折/掩码 seed 与比例；
- [ ] Δ 定义/符号/角色/剂量规则；k=1 与 702 15-row 处理；
- [ ] 比较器 B0–B6 公式/backoff/网格/超参搜索空间；
- [ ] 指标定义与增量规则、bootstrap B/seed/聚类层级；
- [ ] σ̂_e/MDE/δ_min（实测值）；
- [ ] 泄漏审计 9 项与零模型校准阈值；
- [ ] 失败类别/停止条件/报告措辞模板；
- [ ] 执行脚本/输出 schema/两跑确定性/单命令 ≤45 min。
