# 原始方法证据与生物数据资格：PASS1

核查日期：2026-10-28。职责仅为原始证据核读与数据条件分解，不发展或裁决本轮候选。未读sealed/confirmation或项目未授权功能值，未运行实验、模型API、作者代码或子代理。

## 对当前决策最有影响的事实

1. **DrugReflector（Science 2025）已实现功能反馈改写下一轮选药所用的表达signature**。它并非仅用表达重建分数训练：20个药物的表达time course与Day7流式功能表型配对，基因—表型关联形成learned signature，与原signature插值，再前瞻筛此前未测药物。此事实直接约束“反馈更新生物信息对象用于新干预决策”的泛化新意表述。原始PDF pp5–6，Fig4A–F；本文所述更新对象是输入signature，未据此推定主MLP也在线更新。
2. **BATCHIE（Nature Communications 2025）既有真实功能闭环，也有决策相关距离先例**。原始JATS Sec14定义posterior diameter的主动选plate；Sec16末段在MSD之外明确定义TI-aware distance（TID），topK=20。不能把它概括为只降参数不确定性或只拟合表达。真实prospective运行不能与本文retrospective TID实验混为同一验证。
3. **Punzi 2025支持治疗时程/撤药状态的生物需求，但不自动提供广泛药物×细胞×历史的学习任务**。研究有真实持续给药、两周persister及五周drug holiday，有遗传PINK1/HNF4A参照与功能终点；表达、条形码、scGET不是对同一活细胞连续无损测量。历史状态的存在与可从当前表达识别全部历史的可辨识性是两件事。
4. **新命中的virtual yeast 2026需严格降级**。Nature原站认证跳转受阻；EPMC原始题录标注Review和Journal Article，完整摘要是8功能模块、LLM协调和主动实验的提案/平台描述。Fig3“closed-loop”仅见搜索片段，没有读到方法或真实结果，不能当成已完成实验的算法先例。
5. **State 2026本次取得正式题录/摘要与官方README；其功能闭环仍unknown**。摘要支持跨细胞背景表达扰动预测，README支持ST/SE训练接口和zeroshot/fewshot划分，不能升级为真实功能endpoint反馈、治疗历史或功能优化的证据。

## 一手来源及实际阅读层级

| 标识 | 一手来源、身份与日期 | 本次实际收到/阅读 | 明确边界 |
|---|---|---|---|
| P1 DrugReflector | DeMeo等，*Active learning framework leveraging transcriptomics identifies modulators of disease phenotypes*；[10.1126/science.adi8577](https://doi.org/10.1126/science.adi8577)；PDF末页记2025-10-23 online。作者[原PDF](https://cellarity.com/wp-content/uploads/science.adi8577.pdf)已经在库，本次无重下载 | **P**：独立从库内20页PDF提取并核pp2–6、12；pp11参考文献作来源导航。生成的选页extract在sources/drugreflector_verified_page_*.txt；未读全部SI | 不是完整复现；PDF结果为作者报告，不是项目效果分析。GEO metadata复用既有官方原文收据；未新抓h5ad或表型数值 |
| P2 BATCHIE | *A Bayesian active learning platform for scalable combination drug screens*；[10.1038/s41467-024-55287-7](https://doi.org/10.1038/s41467-024-55287-7)；正式发表2025-01-02，DOI后缀2024不是发表日期；[原始PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11696745/) | **P**：复用research/2026-10-26-agent-cell-evidence/sources/PMC11696745.xml，核Sec5–8、Sec12、14–18、26、32及data/code availability；cell viability protocol原段 | 未核全部证明/SI；没有读取项目replay或随机验证功能值；不裁定项目现行split是否合格 |
| P3 Punzi | *Early tolerance and late persistence as alternative drug responses in cancer*；[10.1038/s41467-024-54728-7](https://www.nature.com/articles/s41467-024-54728-7)；原页2025-02-03 | **P**：库内正式HTML，实际核Results Sec6、7、8，Methods Sec12、28、33、44，data/code availability及Fig4/5/6 caption。对应选节extract在sources/punzi_*.txt | 本次未读整个补充DOCX或Source Data ZIP，不把文件目录存在等同于数值可配对；未分析效果值 |
| P4 State | *Predicting cellular responses to perturbation across diverse contexts with State*；[10.1016/j.cell.2026.07.052](https://doi.org/10.1016/j.cell.2026.07.052)；EPMC electronic/first publication2026-08-31；PubMed卷期2026-09-17 | 正式论文 **A**：EPMC完整摘要/题录保存在sources/state_epmc.json。[官方GitHub](https://github.com/ArcInstitute/state) README **P**：训练/推断、TOML split、Licenses（原工具行214–225、250–331、425–431） | 正式全文未取得；bioRxiv v2原页403停止。README当前main分支不是冻结正式论文代码快照；未检查全部源码与许可证正文 |
| P5 virtual yeast | Qian等，*Towards the construction of a virtual yeast*；[10.1038/s41586-026-10574-9](https://doi.org/10.1038/s41586-026-10574-9)；EPMC2026-07-01，PMID42387167 | **A**：EPMC完整摘要、PubType与公开性元数据保存在sources/virtual_yeast_epmc.json；Nature Fig3标题仅 **R** | Nature跳转idp认证；无PMCID，EPMC标非OA/Subscription required。PubType含Review，不把摘要架构蓝图写成已做过主动实验；方法、实验单元、源码、配对数据和实际feedback均unknown |

R=题录/检索片段，A=完整摘要，P=相关原始方法或选节；本次没有F级全方法及必要补充全部核读来源。

## 数据逐项资格表

这些维度分别服务不同主张，不要求一个数据集满足全部主张。unknown表示未核实，不表示没有。

| 资源/用途 | 药物×细胞交叉 | dose/time及历史 | target/genetic参照 | 独立功能endpoint | replicate/nesting | 独立验证 | 许可、访问与尚缺内容 |
|---|---|---|---|---|---|---|---|
| BATCHIE prospective（功能主动screen） | 原文Sec5：206药、16细胞背景（包含两非癌control），drug-dose pair交叉稀疏；15轮约54K unique cell×drug-dose-pair，约全空间4% | 每药0.1/1µM，pair有4剂量组合；加药72h后加Alamar Blue再24h；不是持续跟踪的治疗历史任务 | drug target/MOA覆盖；Sec32 DepMap表达与CRISPR knockout用于解释，不是同井同细胞轨迹配对输入 | Alamar Blue fluorescence-derived viability，TI来自癌/非癌反应差；不是表达proxy | 实验单元是well，plate与cell line有层级；Sec26 r1–10每plate一次，r11–15独立duplicate，viability差>0.5 flagged；不能把整份数据称全程生物重复 | 随机未观测plate验证、top-hit细剂量矩阵；另2个EWS患者来源ex vivo模型（原文Sec7）；本文报告与本项目内部重放分开 | prospective [Zenodo 13871987](https://doi.org/10.5281/zenodo.13871987)；论文明确MIT源码[batchie](https://github.com/tansey-lab/batchie)。患者来源测序未获同意识别性健康数据公开。数据许可细则本次未核 |
| DrugReflector Cellarity benchmark（表达泛化） | p3：88 CMap药×10 cell types，6 immortalized+4 primary；1,737样本约1.26M cells；不能推定每格完整且全为有效样本 | 此处完整dose/time布局unknown；不要借下一行20药time course来填本行 | 本次未核同条件CRISPR/target反事实 | 主要用于表达signature→compound recall；不能当独立功能score | 原文称duplicate；同一细胞的读数不是新的独立药物/供体重复 | 含训练外primary背景；它验证的是表达→药物检索泛化 | GEO [GSE306429](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE306429)为论文声明；本次未取数据文件/许可 |
| DrugReflector signature反馈（功能选药） | 12hit+8nonhit的CD34+HSPC分化系统；不是20药×10细胞完整交叉 | p5–6：Day1/2/5/7 scRNA，Day7配对流式；复用GSE305979官方metadata：single donor，1µM，Day0/2/5给药；是重复施药时程，不等同连续跟踪同一cell | 有药物作用类解释，但本次未核独立遗传功能干预；不能由signature关联称因果靶点 | 流式Mk lineage induction独立于表达测量；hit定义含viability/cell-count QC；新旧signature据真实功能命中率评估 | GEO原metadata称每药biological duplicate分置libraries；同一个供体，12 CMO样本混pool/libraries。单细胞数量不能替代供体数；paired是condition level，非同cell longitudinal | 初始Mk hit在另2donor复验；反馈后96个此前未screen药，85过QC、22hit（p6作者报告）；不能把这个验证说成新cell-type迁移。输入signature选择利用了同20药的功能监督 | [GSE305979](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE305979)、signature [16921906](https://doi.org/10.5281/zenodo.16921906)、code [16921928](https://doi.org/10.5281/zenodo.16921928)。本次Zenodo原API核到open/frozen源码包29,067 bytes，未下载/运行；API未给明确license。数字化Day7流式表型怎样逐well关联GEO仍待SI/table核查 |
| Punzi cancer history（生物状态/干预参照） | 多癌模型/患者PDO按各自标准治疗；HCT116/HT29等、5mCRC PDO、乳癌及卵巢模型；不是统一广药物cross-cell格网 | Sec12明确0/16/24/48/72/120h dose-response；两周持续药物（每4天更新）后五周DH；方法中的急性、persister、clonogenic剂量不同，不能合成同一dose轨迹 | Sec28 PINK1/ATG2A/ATG5/ATG12 shRNA、HNF4A esiRNA/过表达，含scrambled/LUC对照；genetic与drug背景的范围要按具体实验区分 | crystal-violet survival、clonogenic、drug-holiday recovery、mitophagic flux等，独立于表达；Fig6g PDO17的PINK1干预+FOLFOX/FOLFIRI+DH是功能证据 | Fig4a scRNA两experimental replicas；Fig6a三个replicates；Fig6g三个experimental repeats；Sec12 PDO triplicate、OC viability quadruplicate、clonogenic triplicate；25 TEM fields不是25个患者。多层级不能池化为独立drug×cell样本 | 多模型/患者来源验证生物机制；某个结论是否跨供体验证须逐图限定，不能统称独立外部训练/测试数据 | 原文ArrayExpress E-MTAB-12946/48/47/52/53，scRNA/barcode12949/50/51，CUT&Tag13597；Source Data公开声明。库已存正式HTML和SI-DOCX，本次未抓数字表。遗传/表达/功能逐condition无歧义join、轨迹raw availability与license本次unknown |
| State（表达扰动预测） | 正式摘要支持遗传/signaling/chemical perturbations与跨context；该正式版本完整组合数本次unknown | 未核完整dose/time标签；“cell state”不能被换写为治疗历史/记忆 | 包含genetic perturbation输入，非等同药物target engagement与功能机制参照 | 本次没有取得独立功能endpoint反馈证据；unknown | 生物replicate、donor/study nesting本次unknown；README downsample group含celltype/perturbation/batch | 摘要支持新细胞context表达效应/DE评估；README支持zeroshot holdout whole celltype、fewshot holdout perturbations；不是已核真实功能前瞻验证 | 官方README声明代码CC BY-NC-SA4.0，模型weights/output另受State Non-Commercial License及AUP；EPMC论文元数据cc by与非OA标记并存，不能以此给代码/模型统一许可；未下载模型/数据 |

## 关键方法定位与有限解释

**P1原始PDF pp2、5–6 / Fig4**：DrugReflector为3个MLP ensemble，训练任务是signature到instigating compound分类。反馈时，研究者用每个perturbation的pseudobulk表达与Day7功能结果计算基因关联，得到learned signature，再与旧signature插值。本文把整个过程称ARL；仅凭这种称呼不能证明policy gradient、online model learning或多轮agent共同优化。作者遍历cell types×readout days×步长0:0.05:1，用AP选择Day1 HSPC、0.7；选择阶段受到功能label监督，随后新药screen是另一层证据。分子反馈与真实功能反馈的区别在此已经有可执行先例。

**P2 JATS Sec12、14、16、26**：hierarchical Bayesian tensor factorization用drug-dose与cell embedding拟合logit viability；主动选plate最小化近似posterior average-diameter scoring，距离可以按预测viability（MSD）或TI决策损失（TID）设定。Sec16的TID是原文retrospective方法细节，不据此说15轮prospective已使用TID。Sec26真实实验引入new cell lines与可用性限制，模型再更新；仅重新命名成agent或world model不能产生算法区别。

**P3 HTML #Sec6/#Sec12/#Sec28，Fig4、Fig6g**：历史实验包含真实withdrawal和重新敏感性，不能仅凭观察时间长短把snapshot数据称memory。Fig4是不同时间群体scRNA与scGET整合；不含同活细胞baseline→postRNA配对。Methods acute exposure与persister exposure用药浓度不同，因此8/16h与两周的差异不自动隔离time/history的独立效应。该资源有机制参照优势，但跨药/跨细胞自由外推与可重复状态估计仍需单独资格审查。

**P4正式摘要 + GitHub README**：论文支持表达扰动预测增益；README提供训练命令不构成本次复现成功。前述缺失的functional feedback不能写成全文证明不存在。

**P5 EPMC record**：full abstract提出将mechanistic knowledge、subcellular architecture和dynamic states三类数据，整合为8个function-centered模块与LLM orchestration；本次尚无方法/结果原文定位，故仅列概念/架构近邻。根任务可继续核公开作者稿；本worker不据检索片段填实验表。

## 本pass检索、访问和停止边界

4/4初始精确query，均2026-10-28以web__run真实执行：

1. `"Active learning framework leveraging transcriptomics identifies modulators of disease phenotypes" 2025 2026`
2. `"virtual cell" "active learning" functional 2026 drug`
3. `"Early tolerance and late persistence as alternative drug responses in cancer"`
4. `"Predicting cellular responses to perturbation across diverse contexts with State" functional`

初始合并查询工具收据在本会话，但未逐条完整持久化原始返回；不报告完整召回数，也不以搜索片段当全文。共8/8后续一手/官方来源访问尝试（含失败）：

| 次序 | URL/动作 | 实际结果 |
|---|---|---|
| 1 | Nature virtual yeast正式HTML | non-retryable cookie authorization redirect；停止该受保护页 |
| 2 | bioRxiv State2025 v2 full HTML | 403；停止该页 |
| 3–4 | web open EPMC DOI metadata query（yeast、State各一次） | 工具称URL不可访问/提取失败；不是源站鉴权拒绝，不推定论文不存在 |
| 5–6 | requests到独立公开EPMC REST，DOI query/resultType=core | 两者HTTP200，JSON实际存盘；无PMCID/Subscription required；没有重取受保护Nature/bioRxiv |
| 7 | [Zenodo code metadata](https://zenodo.org/api/records/16921928) | HTTP200，metadata与files列表实际存盘；open source deposit，未取archive或模型权重 |
| 8 | [State官方仓库README](https://github.com/ArcInstitute/state) | 原工具返回训练/split/许可段；未安装、克隆或运行 |

定向任务不重下全库。只新增两份题录JSON、1份Zenodo元数据及本地原件选节extract；没有新增论文全文下载或源码快照，未改变共享papers.tsv/repositories.tsv。sources/primary_source_file_hashes.json记录本worker生成的来源文件大小与SHA。原web失败与README工具返回另持久化为primary_web_receipts.json。

运行技能reference_library.py verify核现有库，收到快照：82 unique论文，69 files，downloaded_html56、downloaded_pdf8、abstract_only1、pending10、restricted7；5官方代码快照，changed=[]；63.5MB论文/12.4MB代码，errors=[]、warnings=[]。这是并发工作期间的文件清单完整性快照，不认证方法正确、数据资格或重现。来源变化由协调者统一登记。

本pass未完成OpenAlex结构化全域检索、PubMed/EuropePMC主题全面覆盖、arXiv/OpenReview独立主题检索、引用链/作者组跟踪、所有补充文件和冻结源码审计。不是2025–2026全面查新，不写首次或无近邻；对virtual yeast的正文限制保留。Dryad/SequenTx由协调者另核，本worker未重复调用或据转述填结论。
