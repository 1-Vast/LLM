# 阶段综合的后续内容核对

2026-10-29。审阅对象为本目录Terra综合report.md。本角色已完成M.v0独立科学挑战；现在已经暴露report、source_evidence、mechanism_development和DQ1结果，**这是后续内容审阅，不是第二次盲审，不增加pass、科学修订或科学性能运行。** requested Sol/high；effective model、effort、usage/费用无运行metadata，unknown。只新增本文件，不改冻结候选、初判、独立挑战或report。

**结论：综合准确保留主裁决、负结果和数据边界；发现的一处明确字节类型错误现已更正，源码分支与主文采样规则的区别在下文补充留痕。更正不改变M.v0尚不完整、0科学性能run、ACTIVE_NOT_ACHIEVED的主裁决。** 该状态是根本算法与价值证据未决，不应为获得“通过”反复增加审稿或默认修补M.v0。

## 已核对的材料及真实读取范围

本次全文阅读report.md、source_evidence.md、mechanism_development.md、budget_usage.json、library_verify.json、p6_code_receipt.json、dq1_result.json、dq1_independent_review.md、continuation_receipt.json、retrieval.jsonl、P6 source navigation，以及DS023的main_review.md、usage.json和receipt.json。对dq1_independent_result.json仅抽取summary/rules/qualification/timing等非packet字段；对support_qualification.json读取非pairs字段并检查pairs长度171，不声称独立重算171对或科学响应。未重执行任何DQ脚本。

首次把DQ1结果、review、support全文合并输出时被截断；后独立读完整review并以JSON抽取非长列表字段恢复所用部分。未依据未显示的中段作结论。此前独立挑战的P4/P5/P6阅读范围与截断恢复仍以independent_challenge.md为准；本次没有把先前阅读升级成全篇/全代码审查。

重要争点回到原件/代码：

- 直接读取P5原JATS Sec23所含PCHIP、归一化浓度和派生终点文字，确认预测插值不是新增实验；该段LaTeX有冗余，但本次所需PCHIP等句可见。P5/P6电子发表年份已在前次独立挑战直接核front，分别2024-09-20和2024-06-03；P4本地HTML第352行明确arXiv v1 2026-10-16。正式会议录用未证。
- P6原JATS custom-meta[@id='data-availability']直接给出YChH/StructureLearning官方URL。主文sec013/015的具体算法此前已独立全文读过，本次未仅依赖root的P6摘要。
- 直接从保存的AL02-Final.ipynb文本定位并逐个JSON解码113个`source`字符串数组，未解析outputs为证据、未运行notebook：source-array12第9–15行；array52第1–44、55–119行；array60、77只查看含排序、decision_function、Comparison、round3等关键词的行。数组索引是0起算，数组内行号1起算。其他数组及完整实验分支未核。
- 直接读取本目录保存的旧R源码：gdscmatrixanalyser/R/classes.R:313–350、402–410；R/matrix_well_stats.R:48–66；gdscIC50/R/nlme_fit_prep.R:779–824。未执行R，未认证这些缓存版本就是实际ZIP生成版本。

0网络/API/实验/新代理/安装；未打开ZIP、科学响应成员或其他响应；未访问PRISM24Q2、CTRP、sealed/confirmation或.env。仅在已有允许结果中读取汇总字段，不从原响应重新挑样。

## 具体更正及影响

### 已更正：5,059,873 B不是全部论文正文

首次收到的report预算段写“成功获取正文5,059,873 B”。retrieval.jsonl的六条成功获取记录逐项相加为：

| 类型 | 记录 | 成功body字节 |
|---|---|---:|
| 论文正文 | P4 HTML 746,403；P5 XML 523,653；P6 XML 256,339 | 1,526,395 |
| metadata | P4 Atom 3,266；P6 GitHub commit JSON 8,543 | 11,809 |
| 作者代码压缩档 | P6 code ZIP | 3,521,669 |
| 总和 | 六个成功HTTP body | 5,059,873 |

我将此错误回报root后，再次直接读取当前report第35行与budget：report已改成“成功获取HTTP body共5,059,873 B”及上述三分类；budget同步增加paper_fulltext_body_bytes=1526395、metadata_body_bytes=11809、code_archive_body_bytes=3521669，并留存旧草稿错误记录。该更正已核，不需再改。budget原字段名successful_fetch_body_bytes本身准确。9/10逻辑动作=3个主题查询+6个获取；3/3查询、非穷尽、底层HTTP请求数unknown继续保留，不能把逻辑动作称为已认证网络请求总数。当前report也将“121篇/106文件”校正为“121个唯一来源/106个论文文件”，避免把登记来源全等同已获论文。

**影响：原为来源/预算措辞错误，现已修正；不影响论文方法判断、DQ资格、pass额度或科学主裁决。** 报告已准确承认代码archive含数据字节；此次更正使预算段与该边界一致。

### 建议补清：P6主文“各10”不等于保存源码所有分支都如此

source_evidence.md第47行的“再各取10个正/负近边界点”忠实概括P6主文sec015；首次审阅时report.md第29行只写“再选近边界实验并反馈更新”，没有“各取10”细节。源码局部分支更具体：AL02-Final.ipynb array52第38行要求comparisonList[topIndex]>0.3；第68/78行先各取最近20个候选，第81行并集，第88行从并集中random.sample(allNew,n)，n=20；第91–115行合并旧训练数据并调用ComparisonMultipleRun。该分支最终不保证恰好正负各10。array60/77也出现近边界排序和round3.xlsx调用；本次未审全分支，不能用这一分支改写整篇论文统一算法。

source_evidence.md已记录“>0.3、排序后再抽样”的限定，report也链接精确证据，故建议在report P6源码段加一句：“主文各10为方法叙述；保存源码所读一分支从每侧前20候选并集再随机取20，未据此认定全论文规则。”

收口更正记录：本审阅初版误将source_evidence.md第47行的“各取10”归于report，root指出后本角色定点回读并纠正文件归属。该细节是可选方法粒度补充，不是report原有错误；后续report即使补入主文/源码范围句，也不倒证历史report已有“各10”。本次仅维护此审阅文件，未新增科学重审、来源读取、数据或运行。

**影响：提高方法粒度与复现边界准确性；不影响P6已有结构学习/主动测量/反馈闭环先例的裁定，也不证明M.v0等价或P6结果错误。** round3.xlsx缺失、LICENSE unknown、只提取四notebook、未运行/不使用outputs已正确保留。8个数据成员未打开/提取是既有receipt声明；本审未打开archive重新验证其完整清单，因此不将该声明升级成独立字节审计。

## 核对通过的关键边界

1. **身份与执行。** report将自身标为已暴露综合，未冒称fresh挑战；与本次审阅角色一致。requested Terra/high只能证明请求，effective/usage/cost仍unknown，不能因产物存在反推实际模型身份。独立DQ脚本原作者失去句柄且没留结果，与后来执行者实际exit0的履历分开；脚本执行复算不是作者身份或科学模型验证。旧401和本次新native交付分开记载；本次核对没有读取旧401原日志或新native调度metadata，所以仅确认report未混用，未额外独立认证旧失败/实际模型。budget.team和status仍写synthesis_pending/content_review_pending，属于最终维护状态待更新，不能把这些旧状态反当本次没有产物。
2. **响应单位与处理。** dq1_result与独立summary一致支持前20000行、40000出现、5924唯一键、5923重复键、零冲突/非有限/越界等当前结果。support汇总与report19cell/11drug/204组/876ref、772×7和104×5、146多ref组、171对分布一致。这里只是核对既有结果，未复算原始数据。以ref及其映射确定drug，不把重复join副本当新观测；跨查询/评分不能拆同键。固定前缀已开发暴露，不能新划分为确认集。
3. **源码语义。** R原件classes.R:320、402–406给出归一化并trim；nlme_fit_prep.R:810、813–815把normalized_intensity转y、以BARCODE+lib_drug组标识并取1−y。matrix_well_stats.R:57–66按libN_dose标签join前移除单药POSITION/CL。report的“按剂量连接”是概括，严格说是排序后赋dose标签再join，不应外推为已核实逐个原始物理浓度/源well一一对应。实际生成版本缺口、fluorescence与72h CTG2来源冲突仍未解决；未因缺RNA自动否决有限同筛预测，也未把有限预测资格扩成机制证据。
4. **数学限定。** report固定eta高斯条件化和平方风险下降与独立挑战一致；均值位移期望平方不能再加到同一下降。w=0反例保留仅经B的平滑依赖、可分离ridge、混合块及可逆条件，也说明任意混合H不适用和非零初始化可避；没有把系数交叉项等同eta H。先前错误r=0反例及自行更正保留。N1的“完整三节点”没有被包装成连续精确oracle。当前核心缺件仍是完整风险/eta不确定性/有效协方差运算，而非数据资格审核未通过。
5. **先例与等价。** P4的实际CTMI+hardness→k-center、另用PCGrad；P5剂量输出/相关参数学习/PCHIP；P6结构→选点→反馈均与读过原件相符。反平行不必未加权和为0的手推正确，但不替代P4经验复现。report没有以通用Bayes可表示候选或逐字克隆N1当优先权证据，也未把这三篇不足以判等价倒置成已证明新颖。
6. **预算、DS023和数据字节。** continuation与budget一致：历史23、新实际2、累计25/26，旧未用额度不结转；pass3未启，候选0/2实质修订。Harness14+1=15/15；DS023 receipt/usage记录exit0、4.36s、1final/1step_end，1594input/503output/256cache-read、reported total2353。它仅核注入16键固定算术，不是全源独立核查。旧241MB归档未重下与P6代码archive附带468164未压缩数据字节是两件事；report没有声称整体获取data-free。计费/底层请求/实际模型unknown没有填造。
7. **负结果与nextstate。** dataqualification已有真实执行和复算，故“0运行”若无定语会错；report准确写0科学性能运行，并单列DQ执行。没有用资格通过、reference库校验errors=[]、DS格式/算术通过或源代码下载认定创新。0经验H、0晋升、算法/药筛收益未立、ACTIVE_NOT_ACHIEVED及不启pass3均保留。先核普通支持中跨未查询drug的关系复用及预定筛选决策，是提出下一问题，不是本轮已获得其正结果。

## 最终审阅意见

HTTP body类型更正已直接核实；P6主文/代码分支差异已在本文件和source_evidence记录，report未声称源码所有分支完全等于主文，故不把可选补充升级为阻断。后续将pending状态更新为本次实际审阅完成并保留此记录即可。**不需要为了“内容检查通过”重做科学审判或提高M.v0完成度。** 本次审阅未改变独立科学裁决：当前候选缺完整定义，计算贡献尚无结果，实际功能决策价值与具体最近先例未闭合；内容核对通过不使这些缺件消失。
