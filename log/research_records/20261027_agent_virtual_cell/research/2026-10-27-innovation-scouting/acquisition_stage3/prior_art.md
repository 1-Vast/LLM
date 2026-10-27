# R198-A5 先例核验：等合法预算取证比较的设计先例覆盖

2026-10-27。配套 [spec.md](spec.md)。**本文件不声称新颖性**；只回答"本设计要做的等成本 acquisition 比较，哪些部分已被覆盖/部分覆盖/未发现"。检索为**有界检索**（见 §3），主要锚点来自本项目已核验的一手证据清单（R189-I003 [evidence.md](../../2026-10-27-detectability-acquisition/evidence.md) 的 F01–F16，逐字引文已由当时核验员回查；跨领域 [evidence_notes.md](../../2026-10-27-cross-domain-directions/evidence_notes.md)；[方法先例审计](../../2026-10-27-handoff-method-audit/report.md)）。**"未发现"只作检索结果，不写成"不存在"。**

## 1. 结论（先给判定）

**总体：组分层面上被覆盖 / 部分覆盖；未发现直接先例的对象只剩"把完整采购成本（对照、单药参照、失败孔、重复、批次）+ 菜单 oracle 头空间门槛 + 未查询决策损失三者合一的等成本比较"——但这只是评估/工程组合，不构成新算法主张**（与 R189 线 B 对"I003 MDE 闸"的结论一致：只能作评估修正，不能换名重提）。

- **decision-focused acquisition / BOED**：**已覆盖**（决策价值最大化、序贯、提前停止、regime/预算轴）。
- **BATCHIE / 整板级批量选择 / PDBAL**：**已覆盖**（条件组合模型 + 后验更新 + 整板选择 + 动作距离）。
- **GP / 知识梯度（KG）采集**：**已覆盖**（经典 BO，batch KG 是标准扩展）。
- **生物 AL 的批次/容量约束**：**部分覆盖**（"每批大小受设备容量限制"已被实践承认；4–5 重复/组合；但没有把 control/单药参照/失败/批次全部计价的 acquisition 比较）。
- **成本/保真度感知 acquisition**：**部分覆盖**（多保真度 BO 把"不同成本的不同实验"作保真度；EVSI/ENBS 把决策价值对样本量与成本；但都不是组合筛选板的完整成本账）。
- **统计功效/MDE 与 acquisition 的结合**：**未发现**作为 acquisition 闸门的直接先例（R189 F14：EPMC power×acquisition 零命中；OpenAlex decision-focused∧acquisition 零命中；只作记录）。
- **菜单接近 oracle 的停止规则**：BO 有 regret/oracle-gap 概念；**部分覆盖**（未发现组合筛选 acquisition 的"headroom < MDE → 停"直接先例）。

## 2. 逐条覆盖表

| # | 先例/工作 | 覆盖了什么 | 状态 | 锚点 |
|---|---|---|---|---|
| 1 | **GoBOED**（arXiv 2605.26093，2026-05-25） | 决策聚焦 BOED：按"鲁棒决策损失下降"选实验；chance constraints；作者列出"完全序贯自适应"为未来方向 | **已覆盖**（决策价值 acquisition 的动机与框架） | F01–F04（引文见 R189 [evidence.md](../../2026-10-27-detectability-acquisition/evidence.md)） |
| 2 | **Decision-Focused Sequential Experimental Design**（arXiv 2602.05340，2026-02-05） | 序贯 + 决策聚焦 + 提前停止；停止由决策损失容差决定 | **已覆盖**（序贯/停止） | F05–F06 |
| 3 | **R-IDeA**（arXiv 2506.07805） | "acquisition 分数 × sigmoid 门控"乘积结构（门变量是模型错设残差，不是测量可分辨性） | **已覆盖（结构）**；闸变量不同 | F07 |
| 4 | **Regime 评估**（arXiv 2605.04895） | 先验质量/预算 regime 会翻转 acquisition 结论 | **已覆盖（评估层）** | F08–F10 |
| 5 | **BATCHIE**（Nat Commun 2024/2025，`s41467-024-55287-7`） | 条件组合模型、后验更新、**整板 selection**、PDBAL 后验样本距离动作 | **已覆盖**（整板级批量 acquisition 的领域近邻） | [BATCHIE 全文](https://www.nature.com/articles/s41467-024-55287-7)；F13；R2 数据映射 |
| 6 | **GP 知识梯度 / batch KG** | 经典贝叶斯优化 acquisition；batch KG 用 fantasy 选批 | **已覆盖**（经典方法，非本设计差异） | Frazier et al. 2009（knowledge-gradient，SIAM J Control Optim）；R2 用 16-fantasy batch KG |
| 7 | **Poke & Strike**（arXiv 2509.00178）、**SPI-Active**（arXiv 2505.14266） | 任务敏感度决定所需辨识精度/何时停止；可执行输入激发辨识方向 | **部分覆盖**（决策相关精度/停止的先例；依赖仿真真值或同个体轨迹，不能直接迁入细胞筛选） | 跨领域 [evidence_notes.md](../../2026-10-27-cross-domain-directions/evidence_notes.md)；A1 spec §5 M2 引用 |
| 8 | **生物 AL 的批次/容量约束**（Sci Rep 2025, DOI 10.1038/s41598-025-85600-3） | "每周期实验批次大小受实验设备容量限制"；组合实验 4–5 重复 | **部分覆盖**（容量/重复被承认；无完整成本账） | F15 |
| 9 | **EVSI/ENBS 决策价值 vs 样本量/成本**（临床试验） | 决策价值与样本量/成本的成熟框架 | **已覆盖（原则）** | F11；VOI sample-size（[EMA 展示](https://www.ema.europa.eu/en/documents/presentation/presentation-41-value-information-approach-sample-size-determination-confirmatory-clinical-trials-small-populations-nigel-stallard_en.pdf)；Value in Health 文献族） |
| 10 | **多保真度 BO/实验成本**（ACS Cent Sci 2024/2025，`10.1021/acscentsci.4c01991`） | 把"不同成本/精度的实验"当保真度，做成本感知采集 | **部分覆盖**（成本=保真度代理；非组合筛选的 control/ref/失败/批次账） | [原文](https://pubs.acs.org/doi/10.1021/acscentsci.4c01991)（本轮仅题录/摘要级，未核方法） |
| 11 | **Inference Set Design**（arXiv 2410.19631） | 为推断目标选数据（efficient biological data acquisition） | **部分覆盖**（理念近邻，非板级/成本级比较） | [ar5iv 全文](https://ar5iv.labs.arxiv.org/html/2410.19631)（未逐段核） |
| 12 | **药物反应预测的主动学习**（SHIFT-DRP，JCIM 2025/2026，`10.1021/acs.jcim.5c02453`） | 动态多尺度主动学习（模型侧） | **部分覆盖**（模型/样本选择，不涉及采购成本与决策净收益） | [原文](https://pubs.acs.org/doi/10.1021/acs.jcim.5c02453)（检索命中，未核方法） |
| 13 | **Bayesian optimization 剂量-反应实验**（KIT 出版，2026） | BO 用于剂量-反应实验设计 | **部分覆盖**（BO 设计；非组合菜单/成本账） | [KIT](https://publikationen.bibliothek.kit.edu/1000186837)（题录级） |
| 14 | **I003 / R189 线 B 的"MDE/功效作 acquisition 闸"** | 以每动作重复数 r 与板内 σ 算 MDE 作准入闸 | **未发现直接先例**（F14 零命中）——但 R189 判定只能作评估修正，不构成新算法；本 A5 不重提 | F14；R189 [record](../../2026-10-27-detectability-acquisition/record.md) |
| 15 | **本项目自身先例**：R2 整板/KG 回放、R187 药对 AL、C154、C144、C136 | 菜单接近 oracle（regret 0.004343）；pair-level uncertainty 无优势（MDE 0.0142）；+1,835 行仅动 ±0.003；分配近中性、总量驱动；1,600 keys 的验证成本 | **项目内部先例/阴性**（不是文献覆盖，是本设计的现实约束） | R2 [report](../../2026-10-26-agent-cell-evidence-r2/report.md)；R187 [report](../../2026-10-27-agent-cell-identifiability-r187/report.md)；SYNTHESIS C136/C144/C154 |

## 3. 检索方法与预算（有界）

- **本地一手证据优先**：R189-I003 的 F01–F16（当时由独立核验员按"35 条逐字引文回查、0 miss"记录）；跨领域证据清单（P 级阅读）；方法先例审计；R2/R187 原报告。
- **bounded web pass（2 个 pass，共 ~7 条查询，2026-10-27）**：
  - P1：`decision-focused active learning drug combination screening acquisition budget cost`；`batch Bayesian optimization plate selection drug combination screening cost-aware`；`cost-aware experimental design drug combination screening controls replicates plate budget`；`value of information sample size drug screening cost effectiveness experimental design`。
  - P2：`cost-sensitive active learning high-throughput drug screening experimental cost per well`；`Bayesian optimization experimental design dose-response cost per experiment drug discovery`；`plate-based active learning batch selection biological assay budget constraint`。
  - 命中为上述先例的近邻（BATCHIE 全文、SHIFT-DRP、多保真度 BO、inference set design、VOI 样本量）；**未命中**"把 control/单药参照/失败/重复/批次全部计价的等成本 acquisition 比较"的直接先例。
- **限制**：检索非穷尽；部分条目只到摘要/题录（未读方法）；检索不能证明"无人做过"。**本设计据此不主张新颖性**。

## 4. 与 A5 设计的关系（写死）

1. **A5 的比较器不是原创**：S2 随机、S3 贪心、S4 GP-KG、S5 决策 AL/VOI、S6 PDBAL/BATCHIE 类都是已发表方法或标准基线；A5 的工作是**把它们放在同一合法菜单、同一更新器、同一 total CU 下比较**，并预注册成本/统计/停止规则。
2. **A5 的成本模型不是新方法**：物理 wells + planning CU + 三场景敏感性 + 等成本核查是工程会计；其价值在**可审计与公平**，不在新颖性。
3. **A5 的停止规则（headroom < MDE、成本抵消、无稳定增量）部分有先例**（decision-focused 停止、regret/oracle-gap、EVSI/ENBS 原则）；组合成"菜单级准入闸"是**评估修正**，不是新算法。
4. 若第 2 步（修订迁移）未成立，A5 不执行；若执行且某策略胜出，只能作为"在该菜单/该预算/该更新器下的工程结论"，不得写成新算法、机制或临床主张（跨领域报告 §7/§8 的统一解释）。

## 5. 引用清单（本轮实际使用）

- GoBOED arXiv:2605.26093；Decision-Focused Sequential ED arXiv:2602.05340；R-IDeA arXiv:2506.07805；regime arXiv:2605.04895；Poke&Strike arXiv:2509.00178；SPI-Active arXiv:2505.14266；Inference Set Design arXiv:2410.19631。
- BATCHIE: https://www.nature.com/articles/s41467-024-55287-7。
- 生物 AL 容量约束：Sci Rep 2025, DOI 10.1038/s41598-025-85600-3。
- 多保真度 BO：DOI 10.1021/acscentsci.4c01991。
- SHIFT-DRP：DOI 10.1021/acs.jcim.5c02453。
- BO 剂量-反应：https://publikationen.bibliothek.kit.edu/1000186837。
- VOI 样本量：[EMA 展示](https://www.ema.europa.eu/en/documents/presentation/presentation-41-value-information-approach-sample-size-determination-confirmatory-clinical-trials-small-populations-nigel-stallard_en.pdf)。
- 本地一手锚点：R189 [evidence.md](../../2026-10-27-detectability-acquisition/evidence.md)（F01–F16）、跨领域 [evidence_notes.md](../../2026-10-27-cross-domain-directions/evidence_notes.md)、[handoff method audit](../../2026-10-27-handoff-method-audit/report.md)、R2 [report](../../2026-10-26-agent-cell-evidence-r2/report.md)、R187 [report](../../2026-10-27-agent-cell-identifiability-r187/report.md)、SYNTHESIS（C136/C144/C154）。
