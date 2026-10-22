# Watermelon 设计结果执行审查

2026-10-22，`mechanism_advocate`。只读保存的 WATERMELON_HEADER_RESULT.json 与 WATERMELON_DESIGN_RESULT.json；结合此前已读官方正文。无 HTTP、表达/lineage/clone_size 数值读取、拟合或生物数值实验。既有 INDEPENDENT/CROSS 不改。

**裁决：存在可定义的 conditional state/fate pilot 切入点；尚无新 core、真实 agent acquisition 菜单或 C4 任务资格。** 根已接受不把 clone 当 query、无权重不称 mass，本审查不重复将它们变成普遍禁令。

## 保存结果究竟认证了什么

| 部分 | 已有正证据 | 尚不能推得 |
|---|---|---|
| PC9 | 56419设计行；day0一个共同sample；day3/7各rep1、rep2；day14 high/med/low各rep1、rep2；header有lineage_barcode/clone_size | lineage实际可用率、early—late overlap、逐culture fate、clone_size含义/权重、barcodes是否future-defined；这些字段尚未获准解析 |
| pooled | 50735设计行；有cell_line、sample_pool、experiment、cycling/non-cycling标签 | header无lineage_barcode，不能直接宣称跨模型谱系转移；样本标签不是已认证物理培养/独立later-task |
| 发布链 | README、LFS object SHA/size、GEO两个metadata压缩文件确有header | LFS pointer不是已下载RDS；header不认证所有payload/schema或数值可用性 |

有三项影响任务定义的具体不齐，不能靠过滤隐藏：

- 实际 pooled label 为 `COLO829_SKIN`，此前官方正文为 COLO858。先解析身份；不能静默视为同一个 cell model。
- Ex2 的 PC9 只有 naive/non-cycling tuple，没有 cycling tuple；HCC827 在当前结果只有 Ex3 cycling/non-cycling，无 naive tuple。缺 tuple 是采样结果，不是药物把该群完全消灭的证据。
- A375/HT29 在 Ex2 与 Ex3 都有两个终点 gate，可作为跨experiment的条件表型分类候选；其他极少 captured rows 的组合不能自动构成有效独立任务。设计行数不是power或bioN。

## 最窄可验证的 world 与 agent 切入点

**PC9 的候选任务：** 若另行允许并认证 lineage addresses，冻结 day3（或day7）合法早期RNA，预测同一barcode在另一个culture的day14 raw gate倾向。逐culture定义 target，禁用合并replicates的majority fate、未来clone_size、按未来结果挑选的gene。若same barcode在训练/测试两culture出现，明确是共同founder条件下的跨culture预测；若要newlineage泛化，需按barcode共组留出。单个day0不能伪装成两culture各有独立baseline。

这可定义一个有意义的状态—功能预测问题，功能指H2B-mCherry报告的proliferative history/gate。若进一步比较 day3→day7→day14 的状态条件分布预测，应把未来RNA与gate单独计分，不以终点class准确率代替transition准确率。不能从缺失barcode直接生成death label。

**pooled 的候选任务：** 仅在已认证的同cell model/experiment内，学习RNA与报告gate的条件关系，并对另一experiment保留测试；当前没有逐lineage ancestry，也没有把一个naive单cell配到一个未来单cell的证据。day10 RNA→day10 gate 是同期表型预测；不是早期命运预测。A375/HT29是设计上可讨论的窄起点，不是预先选择的获胜子组，任何未来使用须数值前另合同并报告完整缺失设计。

**agent：当前没有已认证的实验选择动作。** 读取一个culture/time/gate的完整assay bundle可定义离线信息揭示成本；每个clone label单独当湿实验购买不成立。若只做计算性improver比较，可以把读取权限/计算动作定义清楚，但必须标注offline catalog、保护audit，不能把任意行揭示称新实验。仅两个PC9文化replicate、少数pooled experiments不自动有足够独立source/development/later任务；gene/cell/clone分行不能补足它。

## 为什么 raw gate 可重建仍是 ordinary fate classification

raw gate 是作者实际FACS采样provenance的监督标签，真实性使任务更可靠，不赋予算法新颖性。给定早期RNA/lineage/history后预测 `P(gate14 | early,H,culture)`，可由常规logistic/树模型、cell-cycle与已知stress signatures、hierarchical clone effect、多实例分类、label-shift校准完成。若先预测futureRNA再映射gate，最近替代是同辅助RNA监督的ordinaryfactorized方法；完全同构版本应合并，不能要求world击败自身复制品。

这些比较仍能检验明确结构偏置/状态监督的有限反馈价值；分类有效不等于已学到选择与状态转换的分离规律。gateconditional校准/排序不直接给母体cycling prevalence；按gene/cell表面的高准确度也不代表跨culture可迁移或可指导药物选择。原文已报告NRF2/ROS/FAO与persistercycling关系，重现这些关联不是新发现。

能改变决定的额外可测结构应是：**同一可重复的干预状态更新规律，对未参与拟合的真实时长/干预/起始群体给出超过gate classifier的限制和可检验预测。** 例如用独立division/death/absolute-count或已校准reporter约束selection，再测试状态转移规律是否跨culture/初始混合比例保持；或预先随机的机制干预使其对futurestate与functional gate的联合预测被验证/推翻。额外测量必须真的存在，不能从scRNA capturedcount代入。

这类生物结构不因可写成ordinary constrainedlearning就自动无价值；但标准birth-death/state-transition、unbalancedtransport、同信息hierarchicalclassification/ordinaryrefit须为最近比较。只多一个massbalance恒等式、sign constraint、选gate顺序或一条特例成功不足以清newcore。当前未发现满足上述条件的新操作/证据，不为Watermelon编造创新。

## 下一份 selection/transport 反例的独立数学复核准备

根的下一反例尚未到达；本稿不预判其PASS。将逐项独立核对：

1. 明确 latent population、state坐标、时点、clone及samplinggate；区分真实零与未捕获零。
2. 每个候选 transition 的非负/行和、selection的允许范围与normalization，以及对应观测核。
3. 是否两种机制在**所有现有观测**下相同，而不只是totalRNA均值相同；若观测含reporter/lineage，反例也须匹配它们。
4. 若 `p1_j ∝ Σ_i p0_i w_i T_ij`，只有marginals时，fullsupport允许 `T=I,w_i∝p1_i/p0_i` 的selection解释，也允许 `w=1,T_ij=p1_j` 的transport解释。这只说明该观测/模型类的非识别性；限制w、谱系配对或加入真实event约束后须重检，不能推广成一切模型不可能。
5. 观察到的gate分布是 `r_j ∝ q_j π_j`，未知sampling概率π可再造成等价。若反例只证latent相同，却忽略已知π或lineage条件，论证不完整；反之，missingπ不能被擅自设1。
6. 若新增计数、mCherry或lineage足以打破所构造等价，明确指出打破的是哪个观测条件，仍不自动证明唯一分子机制或新算法。

以上是符号级审查标准，没有执行任何生物数值。结论应局限为selection/transport的给定可识别性，不能把数学反例升级为predictive utility、world/agent/RSI的性能阴性。
