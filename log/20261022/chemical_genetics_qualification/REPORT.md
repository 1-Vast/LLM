# Chemical genetics / evolution source qualification

2026-10-22。范围：仅资格核验，不做新机制或性能结论。论文为 *Systematic mapping of antibiotic cross-resistance and collateral sensitivity with chemical genetics*，DOI `10.1038/s41564-024-01857-w`，PMC11726442，PMID39623067。

## Decision

**SOURCE_AVAILABLE; EXPERIMENTAL_IDENTITIES_PARTLY_QUALIFIED; EXACT_STATE_FUNCTION_JOIN_NOT_YET_QUALIFIED.** 真实单基因删除株功能screen、抗生素进化与时间分层WGS均有一手方法依据。不能据此把静态screen写成细胞状态转移，也不能把某一四环素WGS子集外推为23药或70pair全部有纵向状态。无架构或核心创新获准；不运行数值实验。

## Acquisition and exposure

- 预登记 `PROTOCOL.md` 的2 GET / 2,000,000bytes内完成。Europe PMC exact fullTextXML HTTP200、242,880bytes；论文明确引用的Zenodo record HTTP200、13,785bytes；合计 **2 GET / 256,665bytes**。逐请求URL、UTC、status、SHA256与body保存在 `sources/NETWORK.json` 和原始文件。没有重试或alternate mirror。
- 只投影Methods、Data availability、参考数据源身份及补充文件manifest。完整XML保存于本地但未投影Results、图、响应表或摘要；Methods本身含作者已发表的训练计数、特征选择与threshold，此项明确算 **literature/design-exposed**，不能声称未见任何已发表数值或把原文作者标签当项目heldout检验。
- 没有下载FASTQ、XLSX、图片、响应矩阵或Shiny内容。Zenodo原始metadata中不必要的description未投影；仅论文题名/作者/DOI/许可、关联标识、文件名/大小/checksum/links。
- `METHODS_AVAILABILITY.json` 初次只匹配sec，因此遗漏notes中的声明；已由 `AVAILABILITY_SOURCE_MANIFEST.json` 修正。遗漏不是数据不可用证据。未发现独立Code availability note也不等于无代码。

## Authenticated layers

### Static genotype × drug functional screen

Methods / Data sources and preprocessing 明确来源为Nichols et al., *Phenotypic landscape of a bacterial cell*, Cell2011，DOI `10.1016/j.cell.2010.11.052`，PMC3060659，ref31。原始实验包含3,979非必需单基因删除株及必需基因hypomorph、324conditions / 114stresses和drugs。s-score为相对该mutant跨所有conditions的median colony size的modified t-statistic。

本论文筛除hypomorph、≥10missing值mutant、非抗生素/组合等条件及无极端s-score的7药后，保留 **3,904mutants × 40antibiotics**；多浓度时取最高浓度。40drug名称/浓度指向Supplementary Table1。此数据能表示已知遗传干预在药物下的功能响应，但不是时间轨迹，也不是未经选择的完整动作空间。原始跨条件标准化与本文全数据筛选已暴露条件信息，后续严格外推不能仅切分最终矩阵后声称全部预处理无泄漏。

### Functional assay and evolution protocol

Methods / Bacterial strains and growth conditions 指定E.coli BW25113或该背景single-gene knockouts，LB Lennox、37°C、850rpm。MIC (IC90) determination 给出8个二倍稀释浓度、2技术重复、24h每30min OD600，AUC除以no-drug control并计算IC90，以及no-cell/no-drug/no-cell+drug对照。

Methods / Experimental evolution and XR/CS measurements 指定WT经 **23antibiotics、12lineages、5daily passages/~50generations**，每日从OD600>0.3的最高生长浓度转移。此为响应依赖的适应性选择，不能把每天不同浓度当随机分配或独立反事实。

文中真实反馈菜单为 **70 of 634 predicted interactions**，不是所有预测pair完整测量，也不是随机无选择抽样。文字给出12lineages ×140combinations(70unique drugpairs) ×2technical replicates，并明确Source Data Fig3c–e；具体有向药对、重复/lineage键与排除规则尚未读取。14pair另延长5passages；azithromycin–tetracycline有跨代药敏追踪，但不能把此methods文字当已认证逐样本join。

Methods / Experimental evolution against antibiotic combinations 另有8single drugs、7combinations、7lineages、7days的实验。其动作浓度/组合依赖先前IC90，公平比较必须共享同样的IC90先验与实验反馈成本。尚未认证其源表粒度和完整反馈菜单。

### Genome state manifest

Methods / Whole-genome sequencing and analysis 给出WTclone和12lineages在day3/5/7测序、single-end122bp、Breseq、参考基因组 `GCF_000750555.1`，并去除WT相对reference的变异。

Data availability notes明确“Raw reads of sequenced samples (file names describe samples)”位于 **10.5281/zenodo.10572857**。第二GET正式record的题名与论文一致，作者Nazgul Sakenova、EMBL，access open、CC-BY4.0。manifest共 **37FASTQ / 15,995,466,405bytes**，未下载：

- `Tetracycline_lineage{1..12}_day{3,5,7}.fastq`：36个不同identity，文件名笛卡尔积完整、无重复。
- `WT.fastq`：1个。文件名不能进一步认证clone/亚群、founder或同一管实验身份。

这将WGS覆盖范围收窄到明确 **Tetracycline** 文件名子集，不支持23药或全部70pair都有WGS。文件名足以索引待核验lineage/day，尚不足证明同号lineage在药敏源表中必然为同一生物样本。

## Official availability / minimum next objects

官方声明补表1–3、所有数据Shiny `https://shiny-portal.embl.de/shinyapps/app/21_xrcs`、Source Data随论文提供。XML给出以下精确文件身份，没有下载：

- `41564_2024_1857_MOESM3_ESM.xlsx`，Supplementary Table1；最低成本核对drug名/浓度身份。
- `41564_2024_1857_MOESM7_ESM.xlsx`，Source Data Fig3；Methods直接指向70pair和lineage susceptibility反馈，应优先仅审sheet/header与drug/lineage/day/ancestor/replicate身份，不开响应列。
- MOESM4/5为Supplementary Table2/3，MOESM6为Fig2，MOESM8/9/10为Fig4/5/6，MOESM11–15为ED1/2/3/4/6。除标签外不猜内容；如需纵向TET状态–功能join，应先由方法/身份schema明确对应文件再开。

当前2GET额度已用完；上述只是具体后续最低成本metadata对象，不自动执行新GET。无需FASTQ下载、alignment或新模型便能决定是否存在合法schema。

## What can and cannot be replayed

有真实功能反馈的跨实验query→update→heldout-transfer可成为research-agent评估任务；不要求相同colony具备所有continuation branch。仍必须先认证：(1)动作/反馈的真实drug身份与可获得范围；(2)query单位和技术/生物重复聚合；(3)谱系、founder、day及对照的exact join；(4)不同任务的独立单位与不可共享未来反馈。

World-model的状态转移贡献还需可观察状态与后续干预/功能对应。静态删除株screen或遗传相似性预测本身不证明该贡献。若只有固定终点菜单，可研究实验选择/模型更新，但对直接预测、普通重训练、持续学习、主动学习和简单混合必须给同样输入/反馈。若只有单药12lineages的3个状态时间点，其任务数/独立性可能不足继承或RSI；不能拆技术重复成研究任务。

后续若只认证有向end-point矩阵而没有可用state–function join，应明确降为功能预测/研究反馈source，而非直接取消跨实验智能体可行性。若状态join不能建立，停止此source的world-state实验；不以昂贵下载代替身份依据。是否继续应由根代理与独立审核根据实际schema决定。

## Claim limits

本阶段没有项目模型、预测误差、统计显著性、继承收益、联合收益或RSI实验。论文已发表的预测/验证结果不作本项目性能。来源资格不解决新颖性：chemical-genetics-derived cross-resistance本身已有明确基线，任何后续创新需说明与该原论文及普通重训练/程序搜索的实质差异。
