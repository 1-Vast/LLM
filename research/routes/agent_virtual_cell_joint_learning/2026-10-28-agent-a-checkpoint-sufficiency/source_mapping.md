# 2015 来源资格：代码、剂量 token、条件映射与导出语义

2026-10-28。任务 A；effective_model/effort unknown。仅核来源，不审阅 A1 或本轮候选创新性。未读 B 输出；本 Agent 网络请求 0，未打开/解析 `data.txt`、`pert.txt` 或其本地响应/活动量副本，未运行科学模型。

**已完成的是88条现存源条件到作者索引标签的可追溯、一致映射；完整89行源契约仍不成立。** 剂量的逐药 token 对应可以复核，但混合单位的作者规则仍未找到。论文说明支持相对对照的 log₂ 响应图；没有足够原始导出说明，把下载文件的每一列、每个聚合数直接认证成该语义。机器可读逐行证据见本 episode 的 `mapping.json`。

## 1. 直接来源与读取边界

本次逐条用到的原件及定位如下；每个实际读取原件的 SHA256、字节数另存 `mapping.json/source_registry`。哈希仅固定版本，下面结论来自表格/正文/代码内容核读。

| ID | 本地原件 | 内容定位与用途 |
|---|---|---|
| S1 | `D:/MAESTRO/research/2026-10-28-agent-a-matched-signal-function/sources/q1_elife_supp1.docx` | ZIP 内 `word/document.xml`：零基第0表为 S1A，第2表为 S1C。直接提取 A/C；未用 D/E/F 的功能预测数值 |
| S2 | `D:/MAESTRO/research/2026-10-28-agent-a-matched-signal-function/sources/q1_pertbio_exp_index.txt` | 全部89个原始条件标签；保留行后两个整数为未解释字段 |
| S3 | `D:/MAESTRO/research/2026-10-28-agent-a-matched-signal-function/sources/q1_pertbio_node_index.txt` | 节点标签及末列分组；不读取对应响应或活动值 |
| S4 | `D:/MAESTRO/research/2026-10-28-agent-a-matched-signal-function/sources/q1_pmc4539601_jats.xml` | Fig2；s2-1-2；s4-1-2；s4-1-4；s4-2-1/2/3/4；fig6s2；作者回复中 triplicates 一句。方法、图注和代码来源说明，未分析图中功能数值 |
| S5 | `D:/MAESTRO/research/2026-10-28-agent-a-matched-signal-function/sources/q1_elife_article.html` | 官网 Fig2 和 RPPA 方法段，与 JATS 的相对对照/log 与重复说明交叉核对 |
| S6 | `D:/MAESTRO/research/2026-10-28-agent-a-matched-signal-function/sources/q1_pertbio_project.html` | 约第274–324行 `download_template`；保留数据、索引和原模型代码链接及 TODO 描述 |
| S7 | `D:/MAESTRO/research/2026-10-28-agent-a-checkpoint-sufficiency/source_code/DataModel.js` | 父协调本轮下载、只读未执行；矩阵/网络 REST 路径，无导出转换说明 |
| S8 | `D:/MAESTRO/research/2026-10-28-agent-a-checkpoint-sufficiency/source_code/MatrixParser.js` | 父协调本轮下载、只读未执行；空白分词、可选表头、可选裁尾零行，无物理单位或归一化运算 |

S1–S6 的原请求 URL/时间保留在旧 episode 的同名前缀 `.fetch.json`；本次已核读相应收据。S7/S8 的 URL/时间在新 episode `source_code/fetch_receipts.json`。其中官网主文为 `https://elifesciences.org/articles/04640`，JATS 为 `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4539601/fullTextXML`，作者项目为 `http://projects.sanderlab.org/pertbio/`。没有为本任务发起这些请求。

## 2. 代码、名称与剂量 token

下表“比值”仅表示 S1C 数字与作者标签数字的经验对应，不认证作者标签为 µM/nM；更不是全局单位转换。S1C 比较时只把逗号作为千位分隔符，并保留所有原文。S1A 的 `5.000/10.000` 不静默改写。

| S1C 标签 | 作者代码 | S1A 药名原文 | S1C 单药剂量原文 | 作者单药 dose token | 经验数字比值 |
|---|---|---|---|---|---:|
| AKTi | AK | AKTi 1/2 | 5,000 / 10,000 | 5 / 10 | 1000 |
| HDACi | HN | HNHA | 6,000 / 12,000 | 6 / 12 | 1000 |
| MDM2i | NT | Nutlin | 3,000 / 6,000 | 3 / 6 | 1000 |
| PKCi | RO | RO-31-7549 | 3500 / 7000 | 3.5 / 7 | 1000 |
| CDK4i | RY | RY | 2,000 | 2 | 1000 |
| SRCi | SR | SR | 2,400 / 4,800 | 2.4 / 4.8 | 1000 |
| STAT3i | ST | Stattic | 600 / 1200 | 0.6 / 1.2 | 1000 |
| PI3Ki | ZS | ZSTK474 | 600 / 1,200 | 0.6 / 1.2 | 1000 |
| MEKi | 901 | PD0325901 | 1.5 / 3 | 1.5 / 3 | 1 |
| JAKi | P6 | P6 | 20 / 40 | 20 / 40 | 1 |
| BRAFi | PLX | PLX4720 | 60 / 120 | 60 / 120 | 1 |
| mTORi | Tm | Temsirolimus | 0.3 / 0.6 | 0.3 / 0.6 | 1 |

代码不是凭缩写认定：先将23条单药 S1C 条件的 source_index 与作者索引同序行作为**显式锚定前提**，得到12个一对一代码及23个剂量 token 对应；随后仅用这些单药锚，生成其余65条配对条件的无序 `(code,dose_token)` 集合，在全部89个作者标签中搜索。65条配对均各有唯一匹配，且匹配作者行号均等于 S1C source_index。名称部分另按 S1A 的 target 注释对应 S1C 的操作标签；不把这一注释对应当成分子靶点占据或化学结构认证。

该方法有实质限制：若没有上述行序锚，只按剂量范围，STAT3i 与 PI3Ki 都是600/1200，无法由剂量区分 ST 与 ZS。官网也未提供更高层的作者代码/单位图例。所以“唯一”是对所声明锚及全部标签一致性的条件性结论，不是独立于锚的化学鉴定。

名称只保留 S1A 给出的精度：RY、SR、P6、Nutlin、AKTi 1/2 不扩写成未经原件核定的 CAS/完整化合物名称。PLX 的训练条件对应 S1A 的 **PLX4720**；s4-2-1 另称验证实验使用 PLX4032，不能因二者都以 PLX 开头而混为一药。

### 为什么 AK|5、HN|6 与 MEKi1.5 缩放不同

可以确证的是表中逐药数字对应模式：8种代码比值1000，4种比值1。其模式与混用 µM 和 nM 的标签编码相容，**但未找到作者明确的单位声明或导出规则，不能把相容解释升级为事实**。S1A/C 列标题统一写 nM；S1A 又把 AKTi 写成 `5.000/10.000`，而 S1C 同时存在 `5,000` 和 `5000`，这进一步要求保留原始标点而不做静默更正。

S6 下载区各文件下是 `TODO description`；S7/S8 没有单位换算。旧2013方法或未缓存的原始预处理/导出代码可能有解释，本任务0网络请求未取得它们。不能全局乘1000；如需物理剂量、µM、药代/AUC或跨剂量机制分析，这项资格仍关闭。若预先限定为作者原始 token 条件的分组/预测标识，可以原样使用 token，不声称知道单位。

## 3. 88条源行与89个作者标签

直接读原DOCX，S1C 的44个数据表行每行含左右两组条件：左块 index=1–44，右块 index=46–89。**原件没有45**。不是先前 JSON 解析漏掉了这一条。直接 XML 提取的五个字段与旧 `q1_condition_manifest_from_S1C.json` 的88条记录逐项一致。

- 现存 S1C：88条，无重复 source_index；23单药、65配对。
- 作者索引：89条原始标签；23单药、66配对。
- 以上单药锚与独立配对匹配给出88个唯一作者行，全部同序；每条原文、XML表/行/左右块、作者行与原始标签存于 `mapping.json/condition_mapping`。
- 唯一未匹配作者标签是第45行 `PLX|60,HN|6`。按已派生代码，它指向 BRAFi/HDACi 的候选条件，但 **S1C_source_index 保持 null**，不补造“原件第45条”及剂量认证。

因此能够交付可查的88条现存源映射与1条未匹配索引标签；不能交付不存在的完整89条原件一一契约。另一个独立限制是：S6/S7/S8 没有说明 `files/data.txt` 导出矩阵与 exp/node 索引的精确行列契约；S7 访问的是 `data/matrix/<name>`，不是直接解释该下载文件。本文没有用响应值猜矩阵方向、重排或标签对齐。将作者行视为实际矩阵行仍需父协调冻结协议时单独注明其证据等级，不能称已由原导出代码认证。

## 4. 数值归一化、重复与聚合：已知和未决

| 问题 | 原始依据 | 本轮可认定范围 |
|---|---|---|
| 响应图的尺度 | S4 Fig2、S5同图注：“relative to a no drug control”，`log2(perturbed/unperturbed)` | 论文 Fig2 响应图说明明确；不能单由此证明每个下载文件的每一列都无额外变换 |
| 蛋白预处理 | S4 s4-2-2 / S5：Bradford调整总蛋白、标准RPPA总蛋白归一化；对相应 untreated 做 log normalization；低重复性抗体/读出剔除；s4-2-3再筛响应蛋白 | 可认定论文的RPPA流程，不能重建每个公开聚合数的全部变换链 |
| RPPA重复 | S4 s4-2-2：“Three biological replicates are spotted for each sample”；fig6s2称每个c-Myc图点是3个RPPA重复的平均 | 有该重复描述与该图的均值描述；不证明所有82×89值均按相同公式聚合，或每条无缺失重复 |
| 功能预处理 | S4 s4-2-4：resazurin荧光由细胞数标准曲线转为细胞数；流式由DNA含量分相 | 未说明公开5个功能节点逐值采用的聚合/再缩放公式；不把代谢荧光直接叫细胞死亡率 |
| 功能重复 | S4作者回复：“Cell cycle arrest experiments (flow cytometry) were run in triplicates.” | 该实验存在三重复说明；不证明每个导出功能值都有可恢复的独立三重复或相同对照批次 |
| 数据导出的精确尺度 | S6各下载文件无描述；S7/S8不含导出转换 | 未决：是否直接log₂比值、是否再缩放/截断/中心化、每类节点是否统一、活动节点如何接入 |
| 重复聚合运算 | 已读原件无完整导出公式 | 未决：均值的对数 vs 对数的均值、算术/几何聚合、对照如何共享/平均、各条件重复覆盖、分层/批次信息 |

RPPA方法中的“spotted”与“biological replicates”按原文同时保留，不自行重写为独立培养或仅技术点样。即使按论文接受生物重复描述，索引仍没有分离的重复轴；S2两个无表头整数未当作重复、批次或训练/测试标签。S3末列的82/5/12分组也不提供独立重复值。

S4 s4-2-4 内部对细胞周期时间先写24h、后写72h；resazurin则明确72h。因此不把所有五个功能节点一律叫72h，也不依据这一段生成时间轨迹。S4 s4-1-4把活动节点的量化转引到 Molinelli 等2013；本轮没有该完整原始量化链，不将活动值当独立测得的靶点占据。

S8只把输入按行/空白分成字符串，可选表头；默认 `trimData:true` 会裁尾部全零行。它没有 log、剂量转换或重复聚合，所以“浏览器未再归一化”不能推出“下载文件从未归一化”。本次未执行该代码，也不沿用其默认裁行行为。

## 5. 资格结论与具体未决

可用于下一阶段协议的内容：原样作者 token 作为条件标识；88条有原件的条件映射；第45作者标签单独待定；S1A明确列出的药物名精度与注释；论文响应图的相对对照/log₂说明。若任务只限定为固定 token 面板预测，不能假装物理单位问题已解决，也不必为分组 key 强行解释 µM。

未认证的部分：完整89条源行契约；下载矩阵对 exp/node 索引的原导出代码契约；逐药混合单位产生原因；所有节点的导出数值变换链；逐值重复聚合与独立误差；某些药名的完整化学身份。这些未决均保存在 `mapping.json`，不能以响应结果是否好看来反向选择解释。

若计划涉及物理剂量、机制幅度、百分比抑制/阈值、跨剂量迁移或生物置信区间，应先停在对应资格门。最直接缺证是 S6 已列但未缓存的 `common.bp2`、`common.main`、`decima_pp.f`、`input.txt` 或作者预处理/导出说明，以及必要的重复级原件；它们不是本任务已读内容，也不保证其中一定有答案。本 Agent 没有越过0请求边界取得它们。

本次仅新增本文件与 `mapping.json`，没有改旧原件、索引、冻结候选、其他 Agent 文件或全局记忆。
