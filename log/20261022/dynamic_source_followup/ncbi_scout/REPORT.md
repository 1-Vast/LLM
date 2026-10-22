# NCBI scout：一个真实纵向phenotype / timed-challenge lead

2026-10-22，Asia/Shanghai。**PRIMARY_LEAD_FOUND; PUBLIC_FILE_AND_EXACT_JOIN_NOT_YET_QUALIFIED**。本区块依预登记完成4 GET，totalbody **488,928bytes**；3个HTTP200，最后1个HTTP302、0body，未跟随/重试。每响应均<2MB。全部URL/status/UTC/SHA256/body与302 Location保留在`NETWORK.json`及原始文件。无FASTQ、工作簿、response matrix、外部联系或模型/API训练。本轮独立于Root的EuropePMC503；失败不说明没有研究。

## 一条具体lead

Jeff Maltas, Anh Huynh, Kevin B. Wood，**Dynamic collateral sensitivity profiles highlight opportunities and challenges for optimizing antibiotic treatments**，PLoS Biology，2025。PMID **39774800**；PMC **11709278**；DOI **10.1371/journal.pbio.3002970**。PubMed EFetch摘要与NCBI PMC EFetch fullXML均已取得，故以下设计并非只据abstract。

ESearch query183条，本轮仅默认relevance前10条原始abstract/metadata；不是穷尽搜索。明确排除LIST、Tripartite和chemicalgen既查PMID。10条中有colistinpreprint/正式稿同一研究duplicate、临床单背景及不相关工程论文，均不把它们当独立任务。PMID38607932的15drug RL是经验fitness landscape上的模拟，不作真实换药实验。本lead未在现有Markdown报告中检索到已查记录，此项不保证过去从无人看过它。

所有摘要、Methods、定向switch Results叙述/图注及补充文件说明均为**published/literature/design-exposed**，包括作者已发表数值与结果描述；不是本项目盲评或性能。未解析任何response table arrays。

## 真实实验设计和state范围

一手Methods认证所有谱系由 **E.faecalis V583** ancestor衍生，在BHI中培养。主实验 **5antibiotics ×4evolution replicates**，8days逐日serial passage；每天3个浓度中从最高仍可见生长孔转移，约1/200dilution。后续浓度以所选孔浓度的一半、2×和4×为典型值，故actualdose是依赖过去生长的动作，不能当随机drug dose。

IC50用6–14浓度dose–response、20hOD600/no-drug normalization与Hill-like fit，每曲线3或4technicalreplicates。主方法说冻存后plating并挑singlecolony做IC50；后续switch设计用population样本，两者需由文件身份明确，不能把clone与population混同。

Methods明确dynamic collateral profile在 **day2/4/6/8**测量；abstract说400strain–antibiotic combinations，设计上对应5选择drug、4lineages、4timepoints、5challenge drugs的组合，但**未读取实际行数/缺失/全部names/schema**，不能把该乘积当已验证完整400格。这里已认证的是phenotypic resistance profile state和later functional response线索，**没有认证纵向genome/transcriptome或独立分子state**。ancestor fully sequenced不等于各evolvedsample有WGS。

真实定时第二药实验见Results subsection及Fig4 caption：**20independent populations**在ceftriaxone (CRO)中选择14days；每日末取稀释样本，放入一系列doxycycline (DOX)浓度中培养24h，测OD dose–response、IC50及AUC sensitivity。该20replicate属于单独CRO/DOX实验，不与主实验4replicates混算。

**重要范围：这是同一CRO适应流程的每日sample→DOX功能挑战，不等于这些分支接受DOX后继续长期演化并多次切换。** 可支持“何时挑战第二药更有效”的实测设计；尚不支持全部5药/任意drug-switch多轮counterfactual菜单。也不能把日别/挑战浓度/technicalreplicate当新独立研究任务。

## 原作MDP已做与没被此来源证明的部分

原作Methods已明确：phenotypic resistance vector为state、antibiotic为action、action-dependent Markov transition、negative current resistance reward、value iteration求policy。dynamic版本使用day2/4/6/8的时间分段collateral profiles，逆时序把未来profile价值传回较早时段。作者已提出时间变化transition下的动态规划；不能把“显式动态世界模型+多药policy”重新命名为新贡献。

已取得的方法与设计没有证明：通过真实交互训练的任意adaptive multi-switch policy；已测所有startingstate×nextdrug的后续谱系；genotype-dependent足够state；跨strains/drugfamilies的程序继承；可编辑improver或RSI。MDP仿真transition来自collateral profiles不等于真实action-complete状态转移表；futureprofile在模拟规划中已知不等于研究agent在前瞻任务可免费知道未来。

可研究的最窄应用是：固定已测演化/挑战菜单中，早期phenotype/实际drug-dose历史能否改善稍后未查询药敏确认与实验分配。先给last-IC50/day/dose/history、direct multioutput、普通Markov、原作dynamicMDP、ordinaryrefit/continual、AL与等预算search相同信息/成本。当前只有sourcelead，无WM/Agent/继承/联合/RSI性能或新颖性结论。

## 公开位置和请求失败

官方DataAvailability（custom-meta及notes）明确：paper / Supporting information及 **10.5281/zenodo.14064963**。S1Data精确文件名 **`pbio.3002970.s001.xlsx`**、caption“Supplemental raw data”；S1Text `pbio.3002970.s002.pdf`是supplementarytext。不因文件名就宣称其含全部行或所需keys；均未下载。

最后GET `https://zenodo.org/api/records/14064963`返回 **HTTP302 → `/api/records/14064964`**，0body。no-redirect/no-retry使本原区块停止，未取version记录或文件。redirect是明确官方版本线索，不能当不存在/访问拒绝，也未视为已认证manifest。Root随后另授权一次versionmetadata GET，须另协议/账本，不能混入原4GET预算或偷偷follow。

## 具体join缺口与后续最小对象

先核对Zenodo versionmetadata的title/DOI/version关系和data/code file manifests；如文件为code，读取schema需要另授权，不能靠作者“data and code”文字猜函数输出。S1Data或registry数据若可取得，最小identity-only audit需锁定：

- selectiondrug、实际daily浓度与可见生长/转移记录、independentlineage/founder、day2/4/6/8与冻存/挑clone身份。
- challenge drug/concentration、OD/no-drug/ancestorcontrol、IC50/AUC拟合单位、technical vs biological replicate以及缺失/QC。
- 主5drug实验与20population CRO→DOX实验的不同sampleIDs；每日CRO母培养→DOX sampledbranch的exactjoin和是否存在postchallenge continuation。
- 任何state测量在决策cut前的真实可见性与assay bundle/query成本，完整attempt分母；若要分子state，还需实际evolvedgenomicsample与相同culture/lineage/time/function映射，现阶段未知。

这比先拿原始响应训练更便宜。若只有phenotype profile，则按phenotypic动态预测任务报告；若无完整lineage/day/branch link，则相应temporal/branch主张停止。没有足够source/后续任务，继承与RSI保持未测；没有分子state不自动禁止合法phenotype-world应用，但不虚称分子机制资格。
