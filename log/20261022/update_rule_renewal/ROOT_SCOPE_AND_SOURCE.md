# 本轮范围、来源与新颖性判断修正

2026-10-22。上一轮是PROGRESS：新S4实验、独立复现及冻结停止条件改变了实际研究动作。本轮重新阅读全文目标、HEAD与当前continuation，不重跑旧数值、不重开保护响应。三个native代理分别独立完成具体机制/筛选规则审查，再交叉。

## 不能把同代码别名当作已有工作

root主动质疑frontier稿：将一个新候选逐行复制并起名ordinary，不足以证明它早已发表。一个local target的代数展开等于synthetic-gradient step，能否定“写成target本身新增操作”，却不能自动证明该teacher的参数化、外层训练目标和有限成本性质已被具体先例覆盖。skeptic提出的成本保真标准也保留：相同理想argmin不等于相同计算精度/内存/时间，不能给普通对手免费的全局求解器。

root因此做两次针对性的官方primary请求而非泛泛再搜：一次arXiv metadata query检索synthetic gradient与meta/learning-to-learn，随后获取精确2009.09675v1全文，全部原响应与receipt在root_prior。该2020机器人论文是较早技术近邻，不算2025–26新作。全文3.2明确静态SGM根据activation+target提供各层gradient，并用真实gradient监督；3.3在MAML预训练阶段训练SGM，再冻结到未见物体。它证明跨任务元训练/冻结localSGM并非新概念，**不证明**与本次通过heldout功能queryloss外训teacher的步骤逐项相同。query还返回2004.12696、2011.05438与Guided ES metadata，未获取它们全文，不能凭摘要宣布完整目标已覆盖。

读取范围为上述全文abstract、intro、method3.1–3.3及实验4.2训练方式和相关段落，不声称复现作者效果。HTML转文本可保留脚本；关键方法原句已实际读到。一次对单行DeltaTTT文本使用rg导致过量输出，随后改为分行已提取材料。没有基于截断输出宣布全篇已读。

## API与明确执行的证伪

第一次DeepSeek调用实际reported14544tokens（546prompt/13998completion），finishlength，正文只有1341字符的ESG开头，保留为INCOMPLETE_RESPONSE_RETAINED；第二次将原提示与partial发送，关闭thinking以完成同一候选，reported2740tokens（1259prompt/1481completion），finishstop。没有执行模型生成代码；独立数学检查人工编写。两个逻辑调用成本分别83.016秒/7.203秒，transportattempts及美元计价不可得，不能把第一调用当成功完整答案或免费抹去。

ESG声称同药/同状态并集差分取消状态偏差、Bin门控制chance一致性。root先写ROOT_ESG_PROTOCOL，再执行exact_esg.py，在iid continuous vertex noise下枚举全部720orderings：原有向边接受169/720，善意去重后49/720，均高于名义.05。单节点结果独立不等于共享端点边独立；这是一项精确null校准检查，不是生物错误率。另给纯状态主效应且真实药效0的反例，门仍把状态偏差写入冻结base之外的g。它否定普遍取消主张，不证明总预测一定变差。相同pairwise L1负方向导数解释其S，统计gate作为独特部分却尚无有效论据。两独立API稿在读root结果前封存，随后实际cross。

## 不变边界

已有S4/CDK组成、ALMANAC、decryptE、净增长、Lie bracket、投影、DR等限定STOP保留。本轮无新生物值、权重或数据下载；原native任务三方来源请求上限仅各自工作分配，不是需用户批准的全局限制。所有记录log/，代码research/；src/tools、旧dirty导航不改。局部绑定不修复历史来源漂移。完整WM/agent/继承/联合/改进策略自身进步仍未完成。
