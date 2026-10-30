# R3 第一 pass：配对功能需求与最近先例

2026-10-26。独立证据角色；只读R3 record、R2 report/terminal_support与既存P006原始XML，未读R3候选、开发或其他worker输出。requested `gpt-6.1-sol / medium`；effective unknown。本角色3条新query已耗尽，不新增候选，不运行模型或数据实验。

**配对正常对照、选择性目标和实验反馈重训均已有直接先例，不能据此主张新方法。** 可研究的剩余问题，是反馈是否改变可检验的条件功能预测及迁移边界，并在相同整板预算下改变独立选择。尚无证据证明这个剩余问题未被做过。

## 需求及资源边界

使用者是早期组合筛选研究团队。决策是优先验证哪些组合。仅按肿瘤低功能读数选药会混入对所有细胞均抑制的组合；BATCHIE明确用正常细胞研究这个问题，这是文献支持的需求。进一步希望少量反馈识别并更新“在哪些背景下差异仍成立”，是本研究提出的应用问题，不能宣称已有收益。

资源继承R2 terminal_support.json，本pass没有读取stage功能响应：ews-hit为5 EWS＋BJ/RPE共1,449个药物剂量键，每条件两个文件。23个低低组合仅表示剂量落入source取值，相同pair及双方dose在source1–10实际出现仅5个。作者筛出的面板及历史暴露公开归档只能支持面板条件下开发回放，不代表随机药物总体或全新确认。BJ/RPE为参照细胞，不是患者匹配正常组织。Alamar Blue是代谢功能代理，差值不是死亡率、临床安全或具体分子机制。

功能命题须产生未查询目标的预测，例如同一组合在肿瘤低读数时是否也在两个参照背景低读数，以及这种差异在另一未反馈肿瘤背景是否保留。若解释为具体靶点/通路因果机制，需匹配engagement/遗传参照；药物注释和功能排序不够。先定义竞争预测及失败条件，再揭示stage读数。

## 最近先例与方法定位

### P006 BATCHIE，Nature Communications 2025

DOI 10.1038/s41467-024-55287-7。[PMC原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11696745/)，既存原始文件 ../2026-10-26-agent-cell-evidence/sources/PMC11696745.xml。本pass实际读Introduction、Adaptive experimental design、Validation on existing datasets、prospective sarcoma、EWS validation、Bayesian tensor model、Study design、PDBAL distances、Therapeutic index、Code/Data availability相关段及Equ37/38；P级，未读完全部补充或复现理论。

- Therapeutic index：TI=正常组最小viability−肿瘤组中位viability。
- **PDBAL distances，Par85/Equ38**：先形成细胞间两两差值，在两个后验预测各自top-K集合上计算双向选择regret，取max；K=20。若t的topK为I，t'的topK为I'，则距离为 max(mean(t[I]−t[I']), mean(t'[I']−t'[I]))。它已连接选择性、后验分歧及实验设计，不只是最后报告TI。
- Validation on existing datasets：实际比较MSD与TID，报告无显著差异后保留MSD；不能扩大为所有TI设计无用。层级模型含细胞、药物剂量和交互嵌入；反馈更新，动作受整板/可用细胞约束。
- EWS validation：作者选10高TI组合和13负对照再测剂量矩阵，因此23组合有明确筛选过程。
- 可执行来源：[tansey-lab/batchie](https://github.com/tansey-lab/batchie)。论文明确MIT和教程；本pass未重跑或认证当前训练入口，既有仓库读数在R2 sources。

因此仅“用正常细胞竞争”“后验分歧选板”“选择性regret采样”均贴近已有PDBAL-TID。若说条件规则不同，须给出相同先验/反馈/目标下它与TID或层级模型不同的预测和能力，不能靠语言规则名称。

### 新来源：Orhobor等，2026-06-04预印本

*Iterative AI-guided optimisation of selective triple-drug combinations for breast cancer*，arXiv:2606.06562v1。[版本页](https://arxiv.org/abs/2606.06562)，[PDF](https://arxiv.org/pdf/2606.06562)。实际读Methods PDF页14–16、Discussion局限及Data/code availability；P级。

方法直接定义Δ=MCF10A−MCF7，随机初始组合后累计反馈重训Random Forest，按预测Δ完全exploitation选择后续组合并约束单药频率。正常对照选择性闭环已被覆盖；单肿瘤/单参照三药任务不同于本地多背景双药整板任务，差异本身不构成创新。本文未验证新细胞迁移，并承认机制因果需额外验证。

方法定位：PDF页14 Delta viability/Iterative workflow；页15–16 Modelling, prediction, and selection；页16 Data and code availability。作者[仓库](https://github.com/oghenejokpeme/multidrug-analysis)由GitHub connector实际打开root、README、analysis及experiments，后者有iteration_0–8及10,935字节code_templates.zip。仅内存读取小ZIP内notebook，未执行：2_generate_training_data.ipynb核对两细胞共同组合并算mcf10a−mcf7；3_model_and_predict.ipynb读取training.csv、调用sklearn RandomForestRegressor(n_estimators=200)、fit/predict。论文称R实现，公开模板却为Python，差异保留；不能认定所有轮次与论文一致。收据：sources/triple_code_read_receipt.json。此为实际训练/预测代码定位，尚非完整复现认证。

### 已知多输出GP对照（2024，不是近期新来源）

*Permutation invariant multi-output Gaussian Processes for drug combination prediction in cancer*，arXiv:2407.00175v1。[HTML](https://arxiv.org/html/2407.00175v1)。实际读Multi-output GPs、Permutation Invariance、Continuous representation、Prediction setting、Results/Conclusion，P级。LMC用共享潜函数线性组合和coregionalisation矩阵共享细胞信息，SVI处理缺失并给不确定性；细胞为输出，药物/剂量为输入。“共同细胞毒性＋背景特异残差”不天然区别于常规多输出GP。

实证为leave-triplet-out；新药/全新细胞属于展望，不能升级为已证迁移。正文定位到GPyTorch实现声明，没有核实官方可执行仓库。该2024来源只核已知基线，不冒充本轮2025–26发现，不追加科学query。

## 后续候选应满足的区别

1. 直接区分共同低功能与肿瘤相对参照低功能，并保留预设绝对活性要求；差值高也可能不满足研究用途，不得据终点调阈值。
2. 适用条件更新须改变未购买条件的数值预测、允许/拒绝外推或选择行动，并指明哪条反馈触发什么变化。普通重训、层级、GP、BATCHIE-TID得到相同信息。
3. 检验独立选择效用与预测校准，不能只检验规则可读性、拟合MSE或已购买条件事后解释。相同容量层级/多输出GP若能复制行为，不能以规则名称宣称不同原理。
4. 23组合可开发功能命题，不能同时证明新药、独立来源或正常组织转化；迁移门槛分别保留。

## 查询及访问限制

工具web.run，checked_at=2026-10-26。新query共3条，原样为：

1. `2025 2026 drug combination active learning selectivity healthy normal control cells Bayesian optimization therapeutic index multi output Gaussian process`
2. `2025 2026 active learning drug combination context transfer conditional rules cell line selectivity normal cells`
3. `"Iterative AI-guided optimisation of selective triple-drug combinations" "Gaussian" OR "GitHub" OR "methods"`

Q1/Q2同调用返回合并结果，不能把命中分派为各自完整召回。见到2606.06562、BATCHIE、2025 active-learning guide、MetaComb等。Q3返回bioRxiv目录噪声，不是零先例证据。近期新来源只有上述2026预印本完成相关方法阅读，未对其他命中升级方法结论。

原始来源打开不计新增query：2606.06562v1 HTML为404，官方PDF成功；2407.00175v2为404，v1 HTML成功；Nature发生idp重定向不可访问，未重试受限页，使用此前合法存储P006 XML。GitHub connector成功，小ZIP只内存读，无全仓库/数据下载。未安装、训练、读取sealed/reserve，未修改公共reference表。记忆快速搜索无相关命中，不据旧记忆推断事实。

这是3-query有界侦察，不是2025–2026完整系统检索。结论仅为已有选择性闭环和TI-aware设计直接先例；**条件规则迁移的新颖性未建立**。不能写“据检索未见同类”。
