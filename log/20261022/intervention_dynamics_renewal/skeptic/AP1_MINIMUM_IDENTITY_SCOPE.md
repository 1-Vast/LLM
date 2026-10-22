# AP-1 workbook：最小 header/identity 范围与任务资格

2026-10-22。Root 新消息所述结构/代码IO基础上的独立意见。**本代理未读取该workbook/source cell values；本文件不把Root传来的结构或代码观察冒充本代理独立复核。** 没有新增请求；原6GET预算已结束。

## 已传入的具体对象与修正

Root取得repo `mainfigures_sourcedata(AutoRecovered).xlsx`，2,777,650bytes；gitblob `c4efab68e8dce4e517d45a8812e813f3ae571e6e`，SHA256 `6bcdbdd451e29246c5db16e9a67c43abf937e7cf3fb8796931d83096feaff42a`。这是作者repo的AutoRecovered版本，**尚未认证与publisherSourceData等价**。当前只知17sheets及以下usedranges：Fig2b A2:F16；2g B2:H21；3b A2:AE10868及summary；4c B4:AT78；4e A4:L102；5b A1:X241；5c A1:X226。Usedrange大小不认证measurement完整性或独立性。

Root/functional-auditor另已读作者代码IO并报告：`tram.Rmd`的7个文件包含T5224/JNK/control等不同处理，不能将“7files”解释成7个独立trametinibbiologicalruns；JNK `exp2536 hi2`无colony后人工补0；FISHfunction未作colonyjoin。本代理未重读源文件。原独立报告中n7/n6等来自**论文caption reported n**，应继续明确为reported，不把它们当workbook已验证run census。

人工补0必须有flag和理由：若完整被观察/计数的孔确实无colony，0可为合法生物结果；若只是文件缺失或未做实验，0不是缺失的合法替代。现在不预判其是哪一种，不自动删除或补正。

## 第一阶段：仅小范围 string headers

允许Root/auditor在上述七个目标sheet及对应summary中，只导出各usedrange起点附近前5行、前2列的非empty **string cells**，连同物理coordinates、merged-cell区域和sheet名。不导出numericcellbody，不以数值分布猜列义。少量headerstring可含drug/time/gene/clone/run等文字；这是设计身份暴露，不是outcome读取。

将字符串与论文caption和现有code读取/命名映射核对，建立fieldrole表：condition、drug/dose、phase/start/end、gene/reporter、clone、experiment/biologicalrun、well、cell/colony/track以及outcomecount/intensity/summary。如果前5行/前2列不足，只扩到**由已读header/code明确指向的下一header行/列**，逐项记录；不以“找ID”为由导出整页字符串/数据。

## 第二阶段：已确定字段后才开 identity columns

只允许导出角色已经明确的 run/sample/lineage/well/track/time身份字段。Numeric ID/day 可以是合法designmetadata，但必须先由header/authorcode证明字段角色；未知数字仍关闭。Count、spotnumber、intensity、ratio、mean、SEM、pvalue等响应/统计字段保持关闭。若outcome与identity同列混排，只取已定位header/identity行，不整列打开。

| Sheet/部分 | 最小必须核对的身份 | 不能以什么代替 |
|---|---|---|
| Fig2b | 实际experimentID、起始clone/passage、arm、dose/切换时刻、endpoint、count来源、各arm独立well；biological vs technical replicate | 7files、7columns、不同drugconditions或单细胞数 |
| Fig2g | 上项 + JNK/T5224处理阶段 + exp2536/hi2 manualzero flag/reason/attempt身份 | 手补0不带可解释observed-zero或missing区别 |
| Fig3b + summary | gene、condition、biologicalrun、cellID/ROI/field/well若存在；同run跨arm关联；summary→raw映射 | 10868rows、每个mRNAspot、summary作为新run |
| Fig4c/4e | integrationclone、independentexperiment/well、initialcell/trackID→descendantcolonyID、time、预选/排除track规则 | 46tracks当46independentcultures；只有起末scatter同图即认定逐celljoin |
| Fig5b/5c | cloneCC10等、experiment/well、phase、drugchange起止time、withdraw/washout、同一colony是否持续tracked、growth/fluorescence的同对象连接 | n1图的多个timepoint或多个colony当独立tasks；与Fig2/3同clone名即跨图join |

可顺带做**仅类型/存在性 census**：每已定位outcomecell是否blank/error/string/numeric以及missingflag数量，不导出值；但finite/validquantitation和manualzero的科学解释仍需后续单独决策。不要把类型为numeric当作已验证有效。

若字段没有biologicalrun/同样本连接，则该缺口就是结果。不要为凑transitiondataset继续扩大到FASTQ、全图像或所有outcomes。

## 可训练 world / agent / 继承 / RSI 的当前机会

**Endpointbiology / constraineddirectprediction：** 最现实的第一层是实际独立run内多arm的colony结果、DEX/withdrawal后的FISH或reporterbranch。有助于检验原论文主张或某个低维受约束预测器；但其公开aggregate及reportedn尚不足说明有held-out任务/新信息收益。只有phase/time明确、同对象前后连接和必要起始state后，才能把某个部分称为经验transitiontraining，而非不同端点的拼接。

**Worldmodel：** Fig2功能与Fig3/Fig5state若不能同run连接，不可用前者作后者的监督target。可以分别建phenotypicreporterdynamics或colony-response模型；state不必分子，function也可为明确的reporter输出。n1同对象timecourse可以是单trajectory机制stresscase，但不足以验证泛化、sampleefficiency或程序继承。没有必要为保留“virtualcell”名称强行配对。

**Researchagent：** 完整多arm菜单与真实assaybundle若可认证，可以预冻mask/reveal做archivequeryallocation；不需要作者历史的自适应查询顺序。每条query应对应独立可做的assaybundle，而不是单细胞/单spot；固定等logicalbudget可测信息分配，但不自动等于湿实验费用降低。缺完整菜单或只有n1对比时，不添加LLM、自修改或large-search来制造任务数。

**继承：** 同source中按细胞/colony随机拆分不能构成独立后继researchtask。需明确held-outrun、clone或干预背景及继承起点/顺序，与ordinarywarmstart/pooling/refit比较。Fig2n7不能替Fig5n1补transfer统计。当前未认证足够独立单位，不是已经证明不能继承。

**RSI：** 目前没有被编辑的improver对象，也没有一串独立后续improvementopportunities。AP-1细胞记忆是研究对象，不是智能体改进策略的继承。Sourceidentitypass即使通过，也不会自动给RSI资格。

## 实际资源决定

**只买上述一次小header/identitypass。** 若它确认某一单图内真实的same-runstate→action→laterreadout和多个独立单位，可以再选择一个最小、预注册的普通模型/功能资格pilot；不是现在开response。若它只得到跨图aggregate或n1branch，则保留为文献暴露的机制反例/stresssuite，停止把它扩为trainableworld-agent/RSIbenchmark。其他primarylead独立评估，不为保住AP1而补造joins或泛化能力。
