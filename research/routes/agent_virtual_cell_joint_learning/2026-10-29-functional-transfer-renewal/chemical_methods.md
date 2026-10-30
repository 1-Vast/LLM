# 化学方法原文恢复：2023 attachment-context 规则

2026-10-29。本件只补方法原文，不开发候选，不裁决E.v1或总体新颖性。**实际获得并核读1篇合法OA正式论文JATS全文（P）；补充文件未下载/未读（F=0）。** 第一优先源已足以回答本次attachment context方法字段，停止公开访问，未访问第二优先DOI 10.1021/acs.jcim.0c00583。该2020论文仍只有前批摘要证据，不能借本篇补齐其方法。

## 身份、版本与原件

Lou等，*Chemical rules for optimization of chemical mutagenicity via matched molecular pairs analysis and machine learning methods*，Journal of Cheminformatics，2023-03-20，15:35，DOI **10.1186/s13321-023-00707-x**，PMID36941726，PMC10029263。PubMed精确DOI搜索及其正式记录，与EuropePMC返回JATS `front/article-meta/article-id`、题名、日期/卷/页一致。正文为正式期刊OA存档JATS；未将摘要或作者稿冒充正式全文。`front/article-meta/permissions/license`明载CC BY4.0。未访问此前拒绝的Springer/PMC/RSC正文；EuropePMC本次是已确认PMCID的正式OA fullTextXML endpoint，与前批失败的主题query不同，无代理、认证跳转或自动redirect。

原始字节：`sources/chemical_methods/fulltext2023.body`，134308B，SHA256 `d6e499b367b0fb5acbe52fc22ded1f9f96614ae7ec90d9e4e14a0baaffba8c06`。`fulltext2023_reading.txt`是离线派生阅读副本，节点前整数为ElementTree前序迭代序号，仅作定位，**不伪称原件或原生行号**。所有以下段号均为原JATS的`p/@id`，公式为`disp-formula/@id`。实际已读：Materials and methods全部Par29–40，Results Par41–55与相关表，Discussion/Conclusions Par56–61、data availability和补充文件的正文说明；补充实体、图像位图、GitHub代码未下载/执行。

## 指定字段的原文核读

| 字段 | 实际方法与定位 | 限度 |
|---|---|---|
| MMP变量片段、常量 | Par27将MMP定义为single structural change的相似分子对。Par31使用Hussain–Rea/mmpdb，变化片段2–15重原子且不超过分子一半；单/双/三切分别产生side chain/linker/scaffold，切键保留手性；只从Ames阳性→阴性提取规则并编码SMIRKS。 | 变化片段与共同剩余结构的操作来自切割，但正文没有另行给出constant fragment的严格形式化/对称性处理算法；未知细节不可补写为mmpdb默认实现。一个MMP可提多规则，一个规则可源自多个MMP（Par31）。 |
| attachment context | Par31记录attachment points半径0–5圆形指纹的SHA256；Par53应用规则时可设最小半径，以确保attachment局部环境相同；芳香→脂肪环境的泛化问题有明确例子。 | 这是明确的预设结构环境匹配与分层统计。不是凭“有局部环境”就推断存在反馈学习/后验拆分。 |
| 统计/规则评估 | Par39–40、Equ2：对Ames阳性施规则生成分子，固定训练好的consensus模型预测；只把在模型适用域内的生成分子纳入统计；`Svalidity=Nneg/Ntotal`，Nneg是**预测**Ames阴性的生成分子数。Par51以>0.5定义high-quality，又过滤在两个优化数据集使用<10次的规则。Par53/Table4比较不同半径下预测转阴比例，Par54比较频数分组。 | 未描述对新付费实验观测进行增量/贝叶斯/序贯更新；这些比例不是新分子实测成功率，也没有在本次核读中获得置信区间或成本等价实验。 |
| 模型与适用域 | Par33–35：六最佳base classifier概率经LR stacking，离线训练。Par37–38、Equ1：ECFP/Tanimoto，`DT=γbar+zσ`；新分子K个最近邻的相似度**全部超过**DT才为ID。Par46用test set在保留化学空间与预测性能间搜K,z，最终K=5、z=4、DT=0.338。 | 结构attachment半径与预测模型AD是两种不同限制。阈值由test set设定这一事实必须保留，不将其误称完全独立于测试的预先固定门限。 |
| 主动付费query/反馈修订 | Par39、49、59实际过程是离线生成→模型评分；Par59平台免费，两个药物case也是预测生成物。Par60说未来继续更新数据集并借expert systems优化规则。 | 原文已读范围内未描述主动实验选择效用、单位query价格、付费查询预算、观测触发规则拆分/修订或闭环验收。上述算法细节均记**unknown / not described**；“未来更新”不算已实现闭环，平台免费也不证明实验免费。 |
| endpoint与重复 | Par29：Salmonella bacterial reverse-mutation/Ames，S9存在或缺失；至少一菌株显著诱发revertant colony growth即阳性，所有reported strains均不诱发才阴性。Par30重复化合物记录re-analyzed并重新赋标签；Par41集合8576、4643阳性/3933阴性，外部664强阳性+805批准药作为阴性。 | 这是binary Ames集合，不是已确认的双细胞相同物理dose/time连续功能差；重复化合物不等于技术/生物重复。菌株逐项、S9逐项、剂量、时长、重复次数/原始误差模型未在所读主文方法给出，均unknown。批准药物阴性中还包括“无证据证明致突变”（Par29），不应一律表述为实验确认阴性。 |
| 公开数据 | 主文Availability of data and materials段（派生节点863）声称全部数据在附加文件，相关数据/预测代码在 `http://github.com/Louchaofeng/Ames-mutagenicity-optimization`。MOESM1说明表S1/S3–5；MOESM2说明规则表S2、评估表S6–9。 | 这是作者公开性声明和明确链接；本次未下载补充/仓库，不认证其当前可用性、完整性或可重放字段。Pipeline Pilot是作者购得授权的商业预处理软件；它不是主动付费query。 |

Par43直接报告7485 MMP、6107规则，其中85.08%只出现一次；可作为**该论文数据**的支持稀疏性描述，不迁移成当前项目的结构支持统计。Par54还报告高频规则未优于中频规则，作者将频数视为受既有研究化学空间影响的extrinsic property；不以“次数多”替代迁移成立。Par53/Table4半径增大时预测转阴率上升同时覆盖量变化，不能只引用最高比例为实测泛化成功。主文Par41的阳性总数4643，与Table3/Hansen-ISSSTY行的4670不一致；本次保留原值，不自行调和。

## 动作、限额与交接

| 本worker动作 | 精确请求tag | HTTP | 原body字节 | 角色 |
|---|---|---:|---:|---|
| 1 | pubmed_exact2023 | 200 | 212 | 精确DOI身份定位，不是主题query或全文 |
| 2 | pubmed_record2023 | 200 | 29656 | PubMed身份/题录，不是方法全文 |
| 3 | fulltext2023 | 200 | 134308 | 合法OA JATS全文，P |

实际3/6逻辑HTTP动作、0主题query、0失败、0重试、0自动redirect；每件timeout30s、单件cap8388608B，成功body总164176/12582912B，剩余12418736B；最大134308B。worker剩余3动作**未用**，父12动作中实际占3，父其他动作由root汇总。`retrieval.jsonl`逐件保存请求URL、UTC、HTTP、响应头、hash、bytes、耗时与限额；离线复核见`verification.json`。同host动作由串行请求与1.1s前置间隔保证≥1s。离线提取/读XML的第一次命令因引号语法失败，无HTTP、未记为研究来源动作；随后本地脚本完成读取。

不因成功取得这篇而声称2020/2021方法已核，也不作E.v1重叠最终判断。已通知root合法全文可进入其library登记流程；本worker未改共享reference清单。进一步问题若只依赖本篇已写方法，不应为耗满额度追加访问；只有缺失的2020统计Transform等具体方法确实会改变下一判断时，再由root决定剩余动作用途。
