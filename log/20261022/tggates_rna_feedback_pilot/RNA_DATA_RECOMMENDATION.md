# RNA身份与下载路线结论

2026-10-22。仅metadata工作，按root要求至此封存，不再探索processed来源。旧headroom与全部旧phase只读。后续须先固定数值protocol，才能下载/处理RNA；当前未下载或解析任何CEL/表达值。

**原始CEL路线已够具体，可直接进入下载/处理冻结。** RNA_IDENTITY_MANIFEST.json逐行认证172个合法CEL：source24药各Middle2+High2+control2，共144；development7药各Middle2+control2，共28。全为HG-U133_Plus_2，2h，原始individual1/2；EXP/GROUP/individual、BARCODE、药名/COMPOUND_NO、剂量/单位与旧safeidentity精确一致。172barcode和samplekey均唯一。排除所有later、Low、非2h和developmentHighRNA。不能把两个individual称独立donor。

官方compoundlist的FTP链接经README HTTPS镜像规则转换，31个archive basename全部在官方Human/in_vitro目录找到；31次HEAD均200且提供Content-Length，总3,658,321,111bytes（约3.66GB/3.41GiB）。HEAD的Accept-Ranges元数据见RNA_DATA_METADATA_SUMMARY.json。所有HEADbody下载0；压缩包内部真实member清单、172member单独compressed/uncompressed成本尚未检查，不能把估计说成实测。

最快可复现方案是下载这31个已认证官方ZIP到log内缓存，先只读ZIP member目录，按172basename白名单抽取并处理；其他member不解压、不读CELheader/intensity。整包下载会bytecontact同31药的Low、devHigh和其他time压缩payload，必须在下一数值protocol中明确授权并披露；不会接触later14药的archive。若希望减少网络和排除payload接触，可利用已报Accept-Ranges进行centraldirectory/memberRange获取，但必须验证实际206/Content-Range/ETag，拒绝server忽略Range时意外完整body。HEAD支持并不证明实际Range工作。无需为此无限延后研究；wholearchive路线的3.66GB预算已具体可审。

预处理候选由机制方另审。此处推荐source-only可控制的单array处理或冻结参考法，避免把所有172一起jointRMA后再声称组外预测。source代理组outerfold的HighRNA不得进入该fold的dictionary/featureselection/normalizer fit；development只给Middle+controls。RNA归一化和probe→gene注释成本属于真实程序预算；控制使用均须与strongdirect/fulljoint相同。

## 已找到的实际processed替代及其限制

一手发布metadata已认证Zenodo20204514及其作者标注HF镜像中的rma_human.tsv：340,322,060bytes，MD5a185c33e41060996df5138570cfccd58；HF-LFS SHA256347d19a244a4d3fa15731a3aa2a5a089f5021af97f81119db92ec032fcf46920。metadata声明20,414genes×2,397barcodes、log2RMA、Entrez行与barcode列。没有取matrixheader或任何gene值，所以172覆盖未认证；它与官方2,605CEL数量不同。

该发布是2026-05-15第三方复现数据，并非原始TG试剂/物料认证。作者repo树SHA dfd7390f7573cca12c4d98dc8148095e102c3733、固定normalizationblob6ec26ee1eb3eceb2f2178a9c43d039c0323b9e2f的代码调用`justRMA(filenames=cel_files)`，cel_files来自输入目录全部CEL。因此现成矩阵的已发布预处理没有source-fold隔离保证，按允许column筛取不能撤销既成联合归一化。它可作将来单独声明的transductive/exposed参考，当前strictsource-onlyRNA试验优先rawCEL；不为此继续追coverage或取数值。

另有TXG-MAPr原文明确全PHHjointRMA，并按941实验筛gene/WGCNA/normalizescores；其现成模块也不能免费当source-only特征。BioStudies E-MTAB-798 metadata认证humaninvitro，但顶层当前仅列attribute/IDF/SDRF三个metadata文件，并未认证一个可直接取的processed数值矩阵或逐CELasset列表。没有把文件枚举器0CEL当作全球没有CEL。

## 可审证据与成本

官方入口：[compoundlist](https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/open_tggates_main.zip)、[Human/in_vitro目录](https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/Human/in_vitro/)、[README](https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/README_e.html)。处理替代：[Zenodo原发布](https://zenodo.org/records/20204514)、[固定作者处理代码](https://github.com/Ajay1989Kumar/eastman-pande-2019-repro/blob/dfd7390f7573cca12c4d98dc8148095e102c3733/41a_rma_brainarray.R)。TXG方法：[原始论文](https://doi.org/10.1007/s00204-021-03141-w)。精确31URL、样本身份、原responsebody/headers/SHA均本phase保存。

直接HTTP共10GET+31HEAD，全部200；GET都是metadata/原论文/作者sourcecode，共1,097,121bodybytes，HEAD RNA-body0。两次websearch工具调用共4query，工具不报告bodybytes，不混入上述可计量总量。无API模型调用、rawCEL/表达下载、GPU、RNA预处理、模型fit或新增生物观测。两个exec session43772与16969均已poll确认terminalexit0，无背景下载。一次apply_patch格式错误在请求发出前终止；修补后只执行一次followup获取，没有HTTP重试或重复sourcebody覆盖。root已要求本role结束，后续metadata/下载监控可交Luna、关键method交Astra。
