# 独立预执行审查

2026-10-23。读取DIAGNOSTIC_PROTOCOL.md、diagnostic.py、test_diagnostic.py全文。未读取本轮其他角色审查，未执行prepare/run或synthetic tests；已告知根由其或critic执行一次测试即可。本报告仅静态代码审查，不能称测试已通过。

**REVISE（小范围对齐后GO）：数值主检验与隔离设计可执行；需解决一项明确协议/实现不一致。**

## 对齐项

源患者选择沿用旧fold哈希，患者最早字典序RNA context在读取marker/AUC之前确定，每患者最多一行。新discovery哈希按患者，replication不与discovery共享患者。prepare仅访问缓存groups/contexts/items/input_sha256成员，不加载压缩X/Y。raw表虽整行读入字符串，AUC在selected context且paper_inclusion TRUE且patient一致之后才float；CD14只转换selected source列。原始全文件哈希是字节访问，协议如实披露。没有调用旧loader的load/build，因而不意外物化开发Y/X。这修复了我初审指出的关键隔离风险。

moments的pairwise-complete矩阵运算正确：n_ij为共同有限数；sums_ij为该配对患者中Xi总和；var_ij为该配对集合Xi的中心平方和，cov_sum对称，slope_ij为Yj对Xi的斜率。权重bootstrap使用重复患者的等价计数，保留整行与pair依赖。test_pairwise_complete覆盖缺失与weighted moments，并对显式重复患者作对照；poison字符串测试确实检验非selected/非included行不数值解码。没有独立审查训练或结果的范围夸大。

T使用所有预先合格pair的delta_D*delta_R均值，未从discovery挑最大再偷看replication；与我原建议的选pair范式不同但不构成错误。missingness资格确实同时读两半可见mask，协议明确，不伪装完全未用replication设计信息。bootstrap固定eligibility、固定已观察CD14阈值及组别，不重采阈值；因此区间条件于这一次分组，不能代表完整median-learning程序的无条件不确定性。此限定建议写入最终解读，主screen可以保留。

## 必须对齐的描述性输出

协议第4项承诺“report reversal counts”，实现只保存contrast_direction_agreement=mean(delta_D*delta_R>0)。这不是相关正负反转计数：它表示两半contrast方向同号，不能命名为组内关联反转。请在run前选择：

- 增加low/high相关异号的discovery、replication及两半同时反转计数，作为无选择的描述性输出；或
- 删去协议的reversal counts承诺，明确只报告contrast方向一致率。

两者均不改变T或GO门，不需要探索结果作选择。PAIRS已有全部r，后续不能择例图宣称独立药理发现。

## 可接受限制与停止边界

相关常数判断实际为denominator<=1e-12，属于数值近常数约定，而不只是数学严格常数；代码明确计数且不剔除pair。建议协议补这个阈值，避免把近常数当真实零关联。bootstrap少数draw可能没有足够有效pair患者，moments仍会返回零并进入统计；当前最初每cell25覆盖减轻但不消除问题，不能宣称精确置信保证。

T下界>.01是预承诺诊断效应screen，并非有功效认证的临床/机制阈值；协议已经如实区分。相关差可以来自量程、共同敏感度、细胞组成、批次与选择缺失；即使过门也不证明全局条件预测有超额风险，不自动准许新结构更新器。未过门按规定停止CD14/当前分组依据，不换marker或新seed救分。现有CDK/一致性/顺序模型STOP均不被触碰。

对于目标，仅GO到这一源内条件关联screen，不是GO_BIOLOGICAL_METHOD_FIT，不是外部独立复现，也未比较world/agent/inheritance/joint/G1-G0。保留原目标未完成状态。

本审查0GET、0API、0拟合、0生物数值读取、0测试执行；没有改动协议/实现。
