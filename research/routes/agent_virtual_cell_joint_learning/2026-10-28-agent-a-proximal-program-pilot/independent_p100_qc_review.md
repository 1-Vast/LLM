# P100 P0 独立审查

审查日期：2026-10-28。审查角色：`/root/p100_qc_review_resume`，继承父配置，effective_model=unknown。任务是核查冻结的数据资格实验，不以正结论或一致意见为目标。

**判断：可保留三张固定板上“同药批内谱平均比异药谱更相似”的描述性结果。它支持继续核定测量接口，不构成 CL1 的程序语义、跨药复用、独立功能预测或决策收益证据。当前资料不足以把后续 CL1 功能分支标为数据已具备资格；这不是 CL1 被证伪。**

我先读 BRIEF、协议、执行代码和来源，独立形成上述范围判断，再向协调者索取 PSP 已存源码路径。未读取协调者拟定的研究结论或其他 Agent 的审查报告。协调者随后提示检查 DMSO 缺失和负药物差值；下述数字由我直接核对原件或已存逐药结果。没有重新计算 Spearman、bootstrap 或任何科学模型；没有训练、下载、API 调用或打开 PRISM 效果矩阵。仅写本报告。

## 1. 原件、排除与统计口径

三件输入的当前字节数、SHA256 均与 `p100_download_receipts.json` 一致；协议和只读 sealed ID 文件的当前 hash 均与 `p100_qc.json` 一致。GCT 行数、列数、元数据宽度、唯一探针 ID 和样本列 ID 均核对成立。三件各有96列，共288列。

| 固定层 | 原件探针×列 | manual TRUE | 原件有限值 | 原件0值 | 原件缺失 |
|---|---:|---:|---:|---:|---:|
| A375 / P-0028 / PRM | 95×96 | 86 | 9047 | 102 | 73 |
| MCF7 / P-0029 / DIA | 96×96 | 85 | 9063 | 0 | 153 |
| YAPC / P-0032 / PRM | 96×96 | 91 | 9066 | 215 | 150 |

原件均无负数。这里的“原件”计数覆盖所有探针和列，与输出 JSON 在选 ID、选探针后的计数不同。

`p100_qc.py:22` 保留 vehicle，及满足完整 BRD core 格式且不在 sealed ID 集合的列。我仅读取 sealed 文件的 `core` 列用于排除和文件 hash，未读取旧效果或 confirmation。每板恰好排除3个 sealed 处理列；未发现其他无效非对照 ID。每板最后93列，即90个处理列与3个 DMSO 列。

三件共同且各自 manual suitability=TRUE 的探针为78条，独立计数与输出一致；选择没有使用本轮响应强弱。每板30个处理 ID 各有3个不同孔、3个不同 MS 原文件，内部重复标签为1、2、3；同一 ID 内的细胞、板、剂量、剂量单位、时间、时间单位和 vehicle 一致。

**30个处理 ID 包含 staurosporine、vorinostat 两个资源阳性对照。** `p100_qc.py` 将它们作为 `trt_cp` 纳入面板平均值，这是当前 P0 协议允许的口径。另一个元数据资格结果报告28个候选药，是因为另行排除了这两个阳性对照。两处不能混称“30个独立候选药”。DMSO 只承担基线，不进入同药/异药处理谱相关。

## 2. L2X 与预处理是否可解释

三件配套 CFG 字节 hash 均与来源回执一致，且都在第34行定义 `log_transform_prov_code_entry = L2X`。**L2X 表示记录过对数变换，不代表 Level 2、z-score、row-median 归一化或靶点参与。** 当前 GCT 的统一 provenance 分别为 `PR1`、`DIA1`、`PR1`，没有 L2X。

已存官方 PSP 快照 `dry.py:251` 的 `log_transform_if_needed` 在不存在该标记时先拒绝负值，然后调用 log2；`dry.py:285` 的 `log_transform` 将0换为 NaN。`p100_qc.py:59` 的当前原件处理与这个约定一致：非负未标 L2X 的数据 log2，不加 pseudocount，然后每探针减去该板 DMSO 的 log2 均值。没有误把缺失当0，也没有从已按板内所有样本 row-median 处理的 Level4 文件起步。

来源仍有一个须保留的语义边界：2021原论文 Data processing 文字把 Level2 描述为 light/heavy 的 log2 ratio；同文 Fig.1 图注又写 Skyline 产生 L/H ratio 后经 PSP 处理。因此，不能只按“Level2”这个名称判断具体原件已经取过 log。当前 provenance、配套 CFG 和 PSP 行为使本轮转换有可审计依据，但当前 PSP 快照不证明2015–2020原始导出所用历史版本。没有发现必须因负数而触发本协议 `source_semantics_unresolved` 的原件。

2018资源论文在本地只有元数据和摘要，全文回执明确为 HTTP500；本审查没有把摘要当成该文方法全文。有关3小时处理、triplicate、处理层级和资源 reproducibility 的方法判断取自已存且 hash 核对一致的2021全文和具体 GCT。

## 3. 缺失与实际可用探针必须补充说明

输出 JSON 的 `finite/missing/zero` 是转换前、已选78探针×93列的计数，不能当作最终响应矩阵的缺失量。独立核对为：

| 板 | 已选原数值缺失 | 0转缺失 | log后缺失 | DMSO有效数为0/2/3的探针数 | 最终响应缺失 / 7254 |
|---|---:|---:|---:|---|---:|
| A375 | 0 | 17 | 17 | 0 / 1 / 77 | 17 |
| MCF7 | 75 | 0 | 75 | 0 / 0 / 78 | 75 |
| YAPC | 51 | 79 | 130 | 2 / 1 / 75 | 279 |

YAPC 下列两条探针在三份 DMSO 中全部不可用，`nanmean` 无基线，使它们在该板所有列的响应都不可用：

- `8115_LRWD1_S212_ANS[+80]PEKPPEAGAAHKPR`
- `8380_HSPC075_S353_TQLWASEPGT[+80]PPLPTSLPSQNPILK`

因此78是共同入选探针数，YAPC 响应阶段最多可用76条。每个处理谱的有限探针数最低分别为75、69、53；缺失并未使该板没有可比较的谱。A375 和 YAPC 各有一条探针的基线实际来自两份有限 DMSO；协议中的“三份 DMSO 均值”在有缺失时应解释为三列中的可用均值。

这属于应补报的有效维度和缺失口径，不表明当前代码偷偷插补或改变协议。不能把 `missing=0` 的 A375 输出读成“log后完全无缺失”，也不能把 YAPC 写成78条完整响应探针。不得据此事后更换探针阈值或归一化来追求更大差值。

## 4. 已存结果支持多强的判断

下表抄录已存结果，逐药差值的算术平均与保存的板均值一致；没有重新计算相关或重采样。

| 固定板 | 同药相关均值 | 异药相关均值 | 平均差 | 化合物重采样2.5–97.5%区间 |
|---|---:|---:|---:|---|
| A375 | 0.7197 | 0.2630 | 0.4567 | [0.3884, 0.5154] |
| MCF7 | 0.7180 | 0.4484 | 0.2696 | [0.2181, 0.3184] |
| YAPC | 0.5822 | 0.2654 | 0.3168 | [0.2616, 0.3658] |

每板均有一个负差值，且都是 Tofacitinib (`BRD-K31283835`)：A375为−0.0950858、MCF7为−0.1786672、YAPC为−0.0943963。故可报告面板平均差为正，不能报告“所有药物都可区分”或“每药均通过复现”。P0也没有执行药物身份分类或原论文的单药 permutation/q-value 检验。

区间的准确含义比“化合物 bootstrap CI”更窄：代码先计算每药固定的 `within - between`，再1000次对这30个固定差值有放回抽样。每药的异药参照仍来自原整板其他药；抽样没有重建新面板的异药参照，也没有重采 DMSO、孔、批次或探针。不同药的差值共享异药相关对、同一个基线及板效应，因此并非独立观测。该区间只能视为**固定板、固定参照下，对药物权重的重采样敏感性范围**，不应称为化合物总体或独立生物学的95%置信区间。JSON 将 `biological_CI` 留空是合适的。

重复单位也有限：原文说 treatment in triplicates，元数据确认批内不同孔/原文件；没有独立培养起始、培养日期或独立处理批次的证据。因此不能武断说三份样品只是重复上机，也不能把它们升级为三次独立培养。每个细胞只有一张本轮 P0 板，细胞、板及 PRM/DIA 部分混杂，三层不宜合并或用于证明细胞背景效应。

还有一个未被此设计排除的解释：三件原件各32个条件组，全部都是同一行连续3孔，DMSO固定在 A1–A3。同药相似性可能同时受处理效应、局部板位或采集顺序影响。没有随机布局或独立批次证据，不能把相关差的全部来源归为药理过程。所有处理减同一估计 DMSO 基线也带来共享误差，而当前重采样未传播该误差。这些限制不抹去同药与异药谱的已观察差异，但限制其因果和可迁移解释。

## 5. 原始3件与扩展20件须分开

`p100_qc.py:39` 仅加载 `p100_download_receipts.json` 的3件；以上相关数值及78探针集合只属于这3件。扩展回执自身也明确写“metadata coverage only; P0 remains frozen to original three files”。20件包含原3件，不是额外20件或23件，也没有20件都完成同一数值 QC 的证据。

我独立检查扩展20件的 hash、字节数、GCT头及列元数据：全部匹配，5种癌细胞各4件，共1901列；按已声明的对照、sealed、ID和单位规则计出111个候选药、555个条件，与已存元数据结果一致。条件重复键分布为540组有3个、12组有2个、3组有1个；扩展范围不能沿用“三份重复全部齐全”。重复键也不是独立培养数。

扩展文件中保存的名义 ID/细胞/剂量连接为30条件、6药，覆盖 afuresertib、vemurafenib、belinostat、BIX-01294、tacrolimus、decitabine。它们的现存 target 注释没有同细胞内两个药共享的标记；即使拆开逗号分隔的基因注释也没有共享组。这说明这条**已匹配功能候选子集**还没有名义上重复实现同一程序的两种化学工具，不能推成整个P100库都不存在可复用程序。

这30条件的 PRISM 连接在本审查中只核对了保存的元数据输出与其代码范围，没有重做跨库连接或读取响应。扩展检查代码比较 BRD core、精确名义剂量及细胞/筛选支持，未核结构身份、响应非缺失、培养独立性或完整暴露；它不等于药物批次、盐型、细胞内暴露或靶点占据相等。原3件的另一份资格输出只连接到2药/6条件，也不能与扩展6药/30条件混用。P100为3h；现存 PRISM 时间元数据未核定为同暴露，已知部分文件名为120H。早期信号预测晚期功能可以是另行声明的任务，但不能叫同步条件等价。

## 6. 对下一步 CL1 的影响

可以继续使用这些原件设计一个范围明确的测量接口或程序语义必要性检验。开展前须冻结“程序”所指的实测对象、至少两种可比化学实现、暴露与观测条件、留药/留批规则，以及能反驳程序复用的简单解释。单凭目标注释相同、谱相似或本轮平均差，不足以完成这些核定。

CL1 的功能分支目前仍缺：条件明确且有非缺失独立功能端点的连接、同一程序可比的多种化学实现、可承担所声明不确定性的独立单位，以及普通程序网络、自由潜码+相同辅助标签、充分重训练和层级/GP等同信息强基线。P0没有训练预测器，也没有运行这些比较。没有依据由 P0 自动启动功能模型或宣称机制、迁移、决策收益成立。

因此建议记录为：**P0固定板描述性测量检查已完成并保留；YAPC有效探针和最终缺失需补充报告；CL1下一阶段资格尚未核定，功能分支保持 data_not_qualified。** 最能改变当前判断的下一项证据是找到并核定一个预先定义的近端程序在同一细胞和可比暴露下的两种化学实现，同时明确它能连接的独立功能端点与重复单位。若找不到，应如实保留资源缺口，不靠归一化调整或扩大模型把它改写成阳性结果。

## 7. 复核与来源定位

现存 `p100_qc_parse_error.json` 保留了首次 `#N/A` 解析失败，并写明未计算效果指标；这与修复缺失解析后的当前代码相符。可称一次完成的冻结科学统计，不能删去失败记录并暗示总共只启动过一次进程。源 hash 匹配证明当前文件一致，不独自证明协议保存先于首次分析的时间顺序；本审查未取得不可变时间戳或完整执行日志来独立核实该时间顺序。

已存运行记录为 wall 3.8704s、CPU 3.7344s、峰值工作集103481344字节、0模型训练，符合该协议资源上限；本审查没有重跑计时或独立监视历史进程。

- [BRIEF.md](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/BRIEF.md:5)、[PROTOCOL_P0_P100.md](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/PROTOCOL_P0_P100.md:7)：假设、范围、区间解释、停止条件。
- [p100_qc.py](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/p100_qc.py:15)、[p100_qc.json](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/p100_qc.json)：解析、探针选择、DMSO基线、逐药结果和固定差值重采样。
- [原始下载回执](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/p100_download_receipts.json)、[扩展下载回执](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/p100_expanded_download_receipts.json)、[扩展元数据结果](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/expanded_metadata_check.json)、[扩展元数据代码](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/check_expanded_inputs.py:25)。
- [三件配套CFG示例](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/sources/plate28_processing.cfg:33) 与各自 `_receipt.json`；三件CFG的共同 SHA256 为 `3a13bb7bdead8a1eb54ce64031612f481fc5ec7c26f2bc5147ce58c4d86ba19f`。
- [PSP已存官方源码](D:/MAESTRO/reference/code/psp-official/9389e9d86424/broadinstitute_psp/dry/dry.py:251)；本次文件 SHA256 为 `a97dde38ea45ecf32088e953181acba491329a6f8c98bf50c697ef4d7faea869`。目录标记不能替代历史执行版本证明。
- 2021原论文：[Proteomic profiling dataset of chemical perturbations in multiple biological backgrounds](https://doi.org/10.1038/s41597-021-01008-4)，已存[XML](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/sources/p100_2021.xml)及[分节文本](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/sources/p100_2021_sections.json)，核读 Cell treatment、Data processing、Technical Validation 和相关 Fig.1/3 段落。XML SHA256 为 `51b0467b640bd883b718630656950d1b4cc60ee5425fa98481c276fce6b78b15`。
- 2018原始资源论文：[A Library of Phosphoproteomic and Chromatin Signatures for Characterizing Cellular Responses to Drug Perturbations](https://doi.org/10.1016/j.cels.2018.03.012)，本地仅[元数据](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/sources/p100_2018_metadata.json)，[全文失败回执](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/sources/p100_2018_receipt.json)。

本审查时关键文件 SHA256：协议 `4c2c81925625bcde9b72d304b1baf023c079224ad2229a6cbf4888fb3c425b32`；执行代码 `7dccff7b60cd8b6d255306583bdc807a74ee0c1d1fc02e58feee2ae9907e80e6`；结果 `715355ea3c213ddf6cb1fc5bdddd8214794677b40c366a0bdb8ec82f24dfd4e8`；扩展元数据结果 `52212b942b76da6980209ed81a8c5efdf68d36aaf65629cd1a8b6c887a9bc89c`。
