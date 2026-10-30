# 定向最新先例与反例核查：便宜代理、独立功能与 Agent 选测

日期：2026-10-30（Asia/Shanghai）  
范围：2025--2026 年优先原始方法/顶刊；复核当前候选的组合命题：

> 用便宜代理药效（例如转录组或低成本 viability）先预测候选，保留一个独立功能终点；Agent 根据不确定性决定直接测功能、更新局部虚拟细胞状态，或拒绝迁移。

本报告是有界 closest-prior challenge，不是穷尽检索，也没有运行作者代码、打开封存结果或执行新实验。证据标签：

- **报告**：原论文/原始材料明确写出的做法或结果，未在本地复现。
- **推断**：从报告的输入、动作和终点得到的对当前候选的影响。
- **未知**：本次未能核实，不能当作不存在。

## 结论

1. **宽泛闭环已经有直接先例。** DrugReflector 已把转录组代理与表型终点配对，用表型反馈修订筛选 signature，并在新化合物上报告后续命中率提升；MDA 已把 LLM 提出机制、预测失败检查、后验更新和价值信息（VoI）选实验组合起来；BATCHIE 已在真实药物组合筛选中按后验不确定性批量选取下一批测量。因此“Agent 看代理/功能不一致并更新排序或选择下一次实验”不能作为新颖核心。
2. **完整的三件套在本次有界核查中未被同一篇原始工作明确占据，但这不是首次性结论。** CellQ/PACE 预印本最接近“虚拟细胞状态 + 外部功能读出 + 规则更新”，但其 110 化合物 PBMC 反馈主要改变聚合评分规则，未核实 Agent 是否在“直接测功能 vs 更新局部状态”之间做了预注册的成本决策，也没有等预算、未触达药物/背景的功能命中率证据。其筛选矩阵当前为受控访问。
3. **当前 I304/局部重用候选应停在条件性信息审计。** “局部更新/隔离”可由层级测量误差模型、潜在误差源变量、后验预测检查和标准 cost-aware VoI 实现。只有在匹配的代理--功能矩阵上，优于该普通模型并且在整药物/整背景 holdout 上减少昂贵功能测量，才有理由保留 Agent 特异性主张。

## 原始先例矩阵

| 工作（年份/状态） | 原文中实际做的事 | 与当前组合的重合 | 仍缺的部分 |
|---|---|---|---|
| **DrugReflector**, DeMeo et al., *Science* 2025, DOI `10.1126/science.adi8577` | **报告（PDF pp.2--6）**：CMap 转录组训练的三 MLP ensemble 从目标 signature 排化合物；先做 CD34+ 巨核/红系表型筛选，多供体确认；再用 12 个 hits、8 个 non-hits 的早期 scRNA 与 day-7 表型配对，修订输入 signature；后续新化合物筛选报告 top-100 命中率约再增两倍。 | 已占据“便宜 omics 代理 + 独立表型反馈 + 更新代理/排序 + 后续新候选”的生物学闭环。 | **未知**：本地未读补充材料，不能确认每个候选的成本策略、原始逐行配对和完整盲态划分。论文没有被核实为“Agent 选择直接功能测量还是只更新局部虚拟状态”的明确策略实验。 |
| **BATCHIE**, Tosh et al., *Nature Communications* 2025, DOI `10.1038/s41467-024-55287-7`, PMCID `PMC11696745` | **报告（摘要/方法）**：以 Bayesian tensor factorization 建模组合 viability；每轮从 posterior 模拟候选结果，按 Probabilistic Diameter-based Active Learning 选最大信息批次；前瞻 206 药物×16 癌细胞系，作者报告只探索约 1.4M 组合的 4% 即能预测未测组合，并对 Ewing sarcoma top 组合做随访验证。代码 MIT 开源，ALMANAC/GDSC2/MERCK 与 prospective 数据给出公开入口。 | 已占据“便宜/可规模化筛选 + 不确定性驱动下一批真实测量 + 外部验证”的药筛动作；也是当前 Agent/VOI 的强普通基线。 | 终点是 viability/therapeutic index 与组合 synergy，不是独立于代理的功能端点；不是单药虚拟细胞状态更新；没有 RNA 代理与功能 readout 的层级归因。组合响应不能自动转成单药功能迁移证据。 |
| **Model Discovery Agent (MDA)**, arXiv:2608.09696v1 (2026 preprint) | **报告（原文摘要、§2--3）**：LLM 根据数据提出候选机制；SMC/SBI 维护结构/参数后验；out-of-sample predictive check 失败时扩展 hypothesis class；VoI 最大化选择下一实验；用部分观测 summary statistics 做干预预测。生物例子为 single-neuron electrophysiology NeuronBench，另有物理/化学 benchmark。 | 已占据“Agent 提议/审查模型 + 预测失败触发扩展 + 后验/VoI 选实验”的通用方法模式。 | 没有药物筛选、代理药效与独立功能端点的实证；没有证明直接功能测量和局部虚拟状态更新之间的药筛收益。把 MDA 外壳加在当前管线不会自动产生新机制。 |
| **CellQ/PACE**, *Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation*, bioRxiv v1, 2026-08-11, DOI `10.64898/2026.08.04.742916` | **报告（选读原文片段）**：CellQ 将单细胞转录组 RVQ 压成 8 个 token，并预测药物诱导的模块变化；PACE 用 10 个带方向的 cell-type modules；约 5,000 个候选缩到 110 个 PBMC 化合物；Analyzer--Planner--Auditor 读取反馈后把 `(D+U)/2` 改成 `min(D,U)`，另以 13 个化合物的 T-cell flow/senescence/cytokine 读出关联验证。 | 最接近“虚拟细胞状态 + 外部功能 + Agent/规则更新”的同一项目组合。 | 这是 preprint，完整 supplement、代码/权重/agent logs 未核实。OMIX017117 官方快照标为 controlled-access，1.69 GB h5ad 当前不可下载；未见等预算、独立新药物/背景 holdout 的“直接测功能 vs 只更新状态”比较。`min` 规则是聚合评分更新，不等于局部 response model 的可识别更新。 |
| **MultiVCDiff**, *Cell Reports Methods* 2026, DOI `10.1016/j.crmeth.2026.101459` | **报告（原文 p0305/p0310/p0165）**：CPgenes 将每个 perturbagen/target 的 L1000 表达做 perturbation-level 平均，再赋给对应 morphology 样本；静态端点（示例 24 h），无连续 dose/时间动力学。 | 是近期 multimodal virtual-cell 方向，说明 RNA/形态联合生成可作为代理表示。 | **推断**：perturbation identity join 不保证同一 cell×drug×dose×time×preparation×replicate 的 RNA--功能协方差，不能直接作为独立功能反馈资源；没有 Agent 选测或药效终点收益。 |
| **系统比较**, *Science Advances* 2026, DOI `10.1126/sciadv.aed3414` | **报告（选读原文）**：分解 basal/shared/perturbation/non-additive/context-specific residual，讨论 conserved vs rewired response；指出 batch/protocol、matched controls/replicates、perturbation efficiency、破坏性 scRNA 与稀疏时间点限制运输。 | 已覆盖许多“局部残差/上下文迁移”诊断概念。 | 不是药物 Agent 选测，也不提供独立功能终点闭环；重命名 residual 或加自然语言 Agent 不构成新能力。 |
| **Active learning + mechanistic logic-ODE**, *Signal Transduction and Targeted Therapy* 2026, DOI `10.1038/s44320-026-00221-w` | **报告（方法）**：两条 PDAC 细胞系、细胞因子/抑制剂、24 h CXCL9 bead-FACS；logic-ODE 与 greedy/uncertainty/GU acquisition 联动；两次独立 screen、技术重复，作者注明 n=2 biological replicates 且统计偏定性。 | 近邻的“功能终点 + mechanistic model + uncertainty acquisition”，是当前候选应击败的普通强基线。 | 不是 virtual-cell Agent 的独立端点闭环，也没有证明跨背景/跨药物的 Agent 优势；CXCL9 是分泌功能而非肿瘤杀伤。 |

## Perturb-seq、PRISM 与多模态/多保真反例

### Perturb-seq / scRNA 与功能拼接

- **报告**：当前库中的 PerturbArena/scPerturbBench 等公开对象主要是固定条件的单细胞转录组 perturbation（例如 1 μM、3--4 d 或 4 d 处理）；部分样本做 donor pooling，公开子集还按 TRADE 等响应排序选取强/弱条件。
- **推断**：把其 RNA 与 PRISM/GDSC viability 按 drug、cell line 名称连接，不能得到独立功能配对；缺少匹配 dose、exposure time、培养/板准备、vehicle、独立生物重复和同一 readout 语义。identity join 只能支持探索性相关或基线，不支持层级错误归因或 assay-saving claim。
- **未知**：具体数据版本是否保留所有 donor/replicate 的逐行关系，需要逐对象 schema 审计；不能把文件名或细胞数当作独立生物重复。

### PRISM/GDSC 多模态与多保真

- **报告**：PRISM 19Q4 primary 本地为 DMSO 相对、ComBat 后、重复折叠的 log2 response；primary 矩阵约 41 MB，secondary 合并矩阵约 92 MB。PRISM 24Q2 官方 Figshare 元数据声称 1,514 compounds、906 cancer cell lines、2.5 μM、5-day、triplicate，但完整响应文件很大；当前 MAESTRO 只亲核了元数据/README，未将其当盲态确认集。
- **推断**：primary/secondary 是同类 viability assay 的不同 screen/重复层，不是“便宜代理→独立功能”两种保真度；重复折叠和不同屏幕处理不能替代独立 endpoint。把 L1000/Perturb-seq 作为低保真、PRISM 作为高保真时，必须逐行证明同一 drug/dose/time/background/preparation，否则多保真校准会把 assay bias 当 biology。
- **报告**：BATCHIE 可直接使用公开 ALMANAC/GDSC2/MERCK viability 资源，并在 prospective viability 上验证；这证明资源可用于不确定性选测，但不提供 RNA/功能双终点。
- **未知**：本轮没有发现一个 2025--2026 原始方法已公开、可逐行下载且同时含 RNA/cheap proxy、独立功能终点、重复/准备字段和 Agent 选测日志的通用药筛矩阵。该“未发现”仅限本次有界材料与日期，不是全领域否定。

### 其他近邻资源

- **CAF/LPC screen**, *Cancer & Metabolism* 2025, DOI `10.1186/s40170-025-00389-z`：**报告** 3,336-compound cytotoxicity 与 LPC-crosstalk inhibition 两臂，寻找不直接细胞毒但阻断 fibroblast-associated lipid rescue 的 hit；**推断** 这已占据“便宜 cytotoxicity + 独立环境/功能标准”的两 assay criterion；**未知** MOESM5 workbook 未完整取得，故没有合格的逐行 paired resource。
- **ChemScreener**, DOI `10.1186/s13321-026-01204-7`：**报告** 多轮单剂量 WDR5 HTRF 主动筛选并做 dose/counter follow-up；**推断** 是便宜迭代 hit discovery 的直接竞争基线，但 target-protein HTRF 不是 cell functional endpoint。
- **CPgenes / MultiVCDiff** 的公开 Zenodo 元数据显示 h5ad 与图像压缩包均为 GB 级；元数据称 paired trimodal，但未证明 matched biological unit。下载/开放许可不等于可经济训练或可用于独立功能评估。

## 对当前候选与数据资源的影响

### 当前候选的最小改写

将候选从“Agent 发现了一个新闭环”改成可证伪的决策问题：

> 在 cheap proxy 与独立 function 均按同一条件 ID 配对时，Agent 能否在不确定性足够高时选择一次直接功能测量，在不确定性足够低时仅更新局部状态，并在证据不足时 abstain/quarantine；其 equal-budget held-out function utility 是否超过层级测量误差 + 标准 VoI？

必须预先冻结三类动作：`measure_function`、`update_local_state`、`abstain/quarantine`，并记录每次动作的成本、预测分布、触发阈值和失败替代方案。仅改变 LLM 角色名、均值改最小值、或把 uncertainty score 变成文字解释都不算机制。

### 资源准入排序

| 资源 | 当前可用性 | 能否支撑本候选 |
|---|---|---|
| PRISM 19Q4 / 24Q2 | 便宜、公开/本地已有 viability；19Q4 已暴露开发，24Q2 仅元数据/README 亲核 | **不能单独支撑** proxy/function 层归因；可做 viability-only baseline 或 action-cost 设计。 |
| Perturb-seq/scPerturbBench | 公开 RNA perturbation，部分为固定剂量/时间并有 pooled/响应选择问题 | **不能直接支撑** 独立功能闭环；需要同条件 viability/功能和独立重复。 |
| BATCHIE ALMANAC/GDSC2/MERCK | 原文与数据入口清楚，适合复现 Bayesian adaptive viability selection | **可做强普通基线**，不是独立功能资源。 |
| CellQ/PACE OMIX017117 | 论文报告了虚拟细胞与功能流程，但官方入口当前 controlled-access，h5ad 约 1.69 GB | **不能作为当前可复现实验资源**；可借用方向性 panel、revision ledger 和接口定义。 |
| DrugReflector campaign | 原文报告了 paired scRNA/phenotype 与闭环命中率，但本地只读选定 PDF 片段，补充配对表未核 | **可作最接近生物先例**，不能直接当可下载验证集。 |
| CAF/LPC | 两 assay criterion 与当前“独立功能”概念高度相关，但 workbook 恢复失败/不完整 | **只能作先例**，不能作逐行重分析资源。 |

因此，当前最现实的实验入口仍是：先把 PRISM 或类似 viability 仅作为便宜代理，另找同一 drug/dose/time/background/preparation 的独立功能矩阵；在没有第二终点前，任何“局部错误源定位”“功能测量节省”都应标为不可识别/未验证。

## 必要反例与验收门槛

1. **普通模型反例**：层级 `proxy_response` + `proxy_to_function` 测量误差模型，含 drug/background random effects、batch/time effects、潜在 error-source indicator、posterior predictive check 与标准 cost-aware VoI。若其与 Agent 相同，撤回算法新颖性。
2. **不可识别反例**：24 h proxy 与 72 h function 的时间映射变化可同时解释“response model 错”和“proxy→function map 错”；若所有合法观察在两世界下 likelihood 相同，正确动作是保留等价类并 abstain，不能强行局部更新。
3. **数据门槛**：每行必须有 drug、dose、time、cell/background、donor/plate/preparation、vehicle、独立生物重复、cheap proxy、viability 与独立 function；训练/校准/测试按整药物并至少整背景或整批次隔离。技术 well 不能冒充独立生物重复。
4. **公平比较**：同一初始数据与总 assay budget，对比 random/fixed panel、直接 function、完整重拟合、uncertainty/standard-VOI、层级测量误差模型和 Agent；主终点为 held-out function utility 或 fixed-threshold simple regret，次终点为校准的定位/隔离/abstention。

## 证据边界与检索记录

- 本轮复用了本地已保存的 DrugReflector 原始 PDF、BATCHIE 原始 Europe PMC XML、MDA 原始 arXiv HTML/摘录、CellQ/PACE 选定原文片段、MultiVCDiff 与 Science Advances 原文段落，以及 PRISM/Perturb-seq 资源审计。
- 没有重复受限目标论文的 403/429 路径；没有读取 OMIX 封存响应值、PRISM 24Q2 响应值、BATCHIE source data 数值或作者代码；没有执行实验，也没有改 `src/`、`tools/`。
- 这是 2026-10-30 的定向审查，未覆盖所有 2025--2026 后续引用。CellQ/PACE 的后续论文、DrugReflector 的完整补充配对表、以及任何未进入本地资料库的多保真药筛工作均为 **未知**，不能从未命中推出不存在。

**当前决定：** broad operation = **已有先例**；exact package = **本次有界核查未见同篇明确实现，不能称首次**；当前候选 = **parked/conditional**，等待合格 paired proxy/function resource 与 ordinary-model challenge。
