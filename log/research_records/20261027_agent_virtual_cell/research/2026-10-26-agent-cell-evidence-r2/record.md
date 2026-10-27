# 第二轮：从合格动作到确定更新

2026-10-26。继承[第一轮](../2026-10-26-agent-cell-evidence/record.md)，总目标不缩小，ACTIVE / NOT_ACHIEVED。前一目标turn为progress：产生原始资格计数、原始来源证据、15重叠键与独立复算；没有获得算法收益。

用户继续目标且补充允许API测试。本轮为授权延续，新增至多3个有界pass：①已点名BATCHIE来源/板和重复映射＋可执行机制替代；②仅对决定能否实验的缺口定向核验；③冻结后的独立查新与执行审查。继承已用3pass/17query，累计上限6pass；不因agent/新候选重置。I001已用一次实质修订，本轮最多再一次；新方向也共享预算。现有参考库verify通过，9条来源中4原始HTML＋外置BATCHIE XML；旧阴性、暴露史不变。

本轮主要决定：BATCHIE原始板/药库位置是否解释15个标签重叠；重复与random stage能否提供真正分离的功能评分；是否能固定一个一次反馈更新并给出区别于普通层级更新的跨任务预测。机制识别仍需要匹配正交参照，但不能因此永久阻止有清晰功能界限的算法实验。不得把同源组合补全替代原目标的未见细胞/药物和跨任务迁移。

资源：所有代码/测试在D:/anaconda/envs/maestro/python.exe；CPU小实验优先，无需安装或改src/tools。外部API授权已收到；尚未决定需要付费模型调用，不主动输出或读取密钥值。若API测试有必要，先固定用途/上限/记录费用，输出只能当提案，不能作机制真值。独立审查仍由实际子agent执行。

Git开始状态与第一轮末一致：原有两个tracked修改和旧untracked/sealed均保留；本轮只写新research目录及引用索引，补充公开来源入既有reference须协调者负责。

## 最终状态与实际用量

ROUND_CLOSED_WITH_OPERATOR_STOP_AND_BASELINE_EVIDENCE；总目标ACTIVE / NOT_ACHIEVED。[报告](report.md)。本轮3pass：已指名来源/算子侦察（worker各2 query），原始时间/动作/终点设计的定向检查（0新query），独立审查（0新query，仅打开已指名原文）。新增4 query，累计6pass/21 query；没有为下载、agent或改名重置预算。I001.v1→v2→v3已用2次实质修订，停止该算子创新主张。

## 观察与科学决定

- I001.v3 observed数学：下闭有限支持＋硬一致性＋偏好大支持先验下，上锥删除=普通层级MAP；开发者9点20下闭集45相容反馈验证，独立者19,683三值标注中4,032相容情况验证。不等于所有共同学习无效；也不补足潜在真实支持标签的生物测量误差。
- E002B observed：source1—10轮36,257聚合条件，10旧cell；5个时间新背景；后期54重复板动作中目标30动作。每动作2板766导出记录，终点309/314/315/315/314条件。所有方法同source、预算和共享轨迹，source-only描述412 drug-dose，没有RNA/engagement。6更新器×30=180指标，4策略×6×5=120汇总。最终64树source与64树重训练；核参数固定，不做terminal调参。
- 效用GP随机−静态=-0.086300688，探索CI[-0.161527613,-0.024358632]；KG−随机(GP)=0.001884158，CI[-0.081111610,0.063593123]。静态剩余oracle regret仅0.004342537。当前低存活菜单近floor，不能据此追求漂亮活性分数或宣称全领域负面。
- endpoint support observed metadata：random中5EWS与BJ/RPE同药同剂量交集全0；ews-hit stage中五EWS＋BJ/RPE有1449共同键，每条件2文件，其中source剂量支持的0.1＋0.1子集23键。后者未用于本轮模型/策略/数值效果。它是被作者选择的hit panel、同源暴露资料，不是新独立确认集。
- 独立复核澄清23与5：23仅表示双剂量落在source取值内；要求相同药物对和双方剂量均已在source1—10轮实际测过，则交集仅5。不能把dose-level support写成已测pair支持；报告和helper已明确两种口径。
- 第14轮Axitinib库位点与random不同数字plate有相同原始药名/剂量，原文确认4药重复扩成210槽；仍无stock、盐型与细胞别名字典，不能提升为完整实体认证。独立培养/engagement未齐，但纯功能研究不要求先有机制真值。

## 纠错与独立性

asrun_v0完整保留，不能使用：代码在acquisition前用terminal QC过滤设计池；5目标实际QC全有效，故潜在通路不导致当前数值变化，不能声称观察到泄漏收益。纠错同时把36树重训统一64树，未按结果选参。最终code feb99d274a575bcfab285b10f5356fdb1bf984cc2f9692f2561578ec0141bbb6，protocol d46ff1abe0bac0c23e3c1cf8904b1211f3d2d06585bc6bfef8a2912df6484f68，结果a800c7fa4d3353a2664c8138bd2f0ab5069e0c490aeba2061b0bc5a1830b8b4f。复算摘要曾暂时指向首版result，当前固定版完成后已复跑review_recompute.py，所有版本hash一致；不把中途快照当最终独立认证。

requested角色配置继承：primary_evidence gpt-6.1-sol/medium；principle_scout转开发 gpt-6.1-sol/high，不再作挑战者；新r2_review gpt-6-astra/high、fresh minimal context，先保存初评再接收协调者后续。effective均unknown。审查者未代写候选。

所有测试用maestro，数学、元数据、GP/static每动作独立读数、120汇总及30预算复算通过；source森林实现复用，只独立核412描述条目和GP条件化/评分，未全量独立重拟合其余更新器。baseline最终174秒，不声称等实际计算预算。初版exec handle失效后检查进程缺失＋最终产物确认terminal，没有仅因poll超时重启。

资料库新增2篇原始arXiv HTML（2605.02611、2506.15893），P级范围在operator_development.md。最终11条、6HTML、4restricted、1pending外置XML，代码9 not_verified＋2 not_yet_checked，0 snapshots，verify0 errors/0 warnings。没有付费模型API调用，没有密钥值输出。

## 完成审计（不能据此标记总目标完成）

| 原始要求 | 证据状态 |
|---|---|
| 审计规则/Git/最新阴性，2025—2026一手差异 | 已有两轮可追溯记录，覆盖仍有受限来源，不宣称穷尽 |
| 药×细胞、正交参照、独立终点/重复 | 功能设计与库位映射推进；条件级engagement/独立培养未齐 |
| 新且明确的共同学习算法 | I001最后修订被同先验层级MAP精确解释，未建立主贡献 |
| 同信息预算强预测/重训/层级/随机/GP/决策学习 | E002B执行有界普通基线；未跑原BATCHIE或强分子VC，不能说所有最强方法均已覆盖 |
| 独立药物决策收益 | 本轮同源活性回放无候选收益，配对选择性资源待新协议 |
| 未见细胞与药物、跨任务迁移 | 时间新cell已做基线；新药实体/独立来源未做 |
| 元学习/RSI、等预算程序搜索 | 条件未达，尚不准入；没有用有限选择冒充RSI |
| 验证通过后晋升 | 未晋升，遵守门槛 |
