# 新一手方法改变了哪一个决定

2026-10-29。root实际核读，不是只定位题名。两个新原件均已按reference_library.py入库；正式PDF/预印本、局部阅读/未读证明、作者报告/本项目观察分开。原生web出现前原库verify为127来源/111文件；结束为129/113，校验只证文件清单完整。

## L2M：不完整历史的原理已有具体运算

[Learning-To-Measure: In-Context Active Feature Acquisition](https://proceedings.mlr.press/v306/kobayashi26a.html)，ICML2026，PMLR306:59720–59752。官方PDF原body1,672,184B，33页，来自PMLR条目给出的mlresearch原件URL；身份与五作者核首面。root读PDF p3 §3部分、p4–5假设3.1–3.3/定理3.4/§4.1–4.2，p6图后Gumbel、MonteCarlo、架构和训练开头。附录证明、p7后实验/实现未核；p25只提取作者repo链接元数据，不能算读了附录方法。

§3目标是对静态feature、统一获取成本、给定baseline与fixed budget，在新任务用有标签context为未标query选下一feature。p4明确R_j=1为已观测；MAR、No Direct Effect、Positivity三条件下，作者给出参考分布CMI从已观测数据识别的定理。它要求具体缺失/条件支持，不能从“missingness arbitrary”的摘要措辞推成任何MNAR药筛都可识别。原文证明未读，不认证其定理最弱条件。

§4.1–4.2以Transformer条件预测和序列context、一步后预测loss代理CMI；训练blocked policy不选该样本历史缺失feature。Theorem4.2陈述理想联合极小值的Bayes/CMI性质；不是任意拟合网络保证。p6用straight-through Gumbel–Softmax与MonteCarlo近似，先训predictor再固定它训policy；多步扩展指向未读A.5，不能认定仅有短视或代码已完成最优规划。原文报告in-context能力，未在本项目复现。

对本轮的作用：不把“共享关系未知”“在部分历史上学习策略/预测器”单独认领新增算法；须指出与该具体摊销估计/动作代理的差别。该文没有在已读范围替本项目认证：并行drug assay的No Direct Effect、同细胞跨孔/批次依赖、两个目标直接测量动作、真实孔价与关系审计成本。已读流程的有标签context不可免费送给药筛候选；是否采取该模型尚无决定，0训练/权重/作者代码执行。

## AFA-ITD：缺失记录可改变训练动作问题，不只是预测输入

[Active Feature Acquisition With Incomplete Training Data](https://arxiv.org/html/2609.32325v1)，arXiv2609.32325v1，原头26Sep2026、CC BY4.0；formal venue未核，其他更早公开版本未搜。五作者核原HTML。body544,485B。root完整读§3.3–3.4及§4.1–4.3；证明、实验、作者代码未核。HTML非well-formed XML，ElementTree失败后用标准HTMLParser按section提取，非网络重试；MathML保留、重复annotation删去用于阅读，原body不动。

m_i=1在本篇表示缺失，正好与L2M的R_i=1已观测相反。§3.4区分历史样本可用动作与部署可购买动作，前者是后者子集。§4.1 Proposition1在MCAR、同状态和共同可用动作等条件下给值函数偏小及一步Q相等的结论；这是受限动作Bellman问题，不是“MCAR下所有信息价值不变”。shortcut思想例展示需要后续动作时的损失，不把图中accuracy=1+Q误当Q本身或本项目结果。

§4.2给三种具体方案：忽略mask混合不同可用动作的aliasing；按mask分层的filtering；学p(x_a|s)与停止值、补恢复缺失转移的generative restoration。前者可在无限数据仍学错部署动作值，后两者在所列条件下能恢复目标递推。§4.3 Theorem1是离散feature、K有界、固定且独立于训练样本的predictor、bounded loss、各feature独立MCAR、unit以上cost和整数budget下的统计界；filtering含(1−p)^−d，restoration含(1−p)^−b。它们还含K^b，不能简写成不受维度/预算影响的通用高效算法。正面算法与条件都有，不能借这篇只写信息不可能。

对本轮的作用：先区分“某条训练记录没有某项动作”和“部署真的不能买该测量”；没有完整11列不必直接丢掉所有cell，也不能无条件生成缺失值作真标签。药筛是否MCAR/支持是否正、共享培养噪声和目标观测是否可得仍须数据资格。该文的恢复运算已有，不能把“补齐训练可选动作”当新。它没有从边际创造不可识别联合分布，也没有替733个ID认证生物独立性。

## 2025 contrastive原件的追加核读

复用arXiv2506.15893v1、SHA2569f8ea8bdd91581c60bc1b64bf04bbe8e841432ae9fe9ecd440ce7dc697d63be0。root从库提取后读取§2起始到最小距离模型前的原文（派生文本字符6852–16952）；涵盖oracle回答query标签及额外带标签contrast、已知contrast-set映射、版本空间还按oracle规则排除相容标签假设、Definition1/Proposition2及无限制映射可编码概念的说明。未读后续复杂度证明/全文。普通功能孔不返回免费的对照反例；这份理论合同不能直接用一次孔数换一次oracle复杂度。它也是有限V删除的最近原理，不把版本空间名字当新算法。

## 实际访问与局限

原生web4条query，精确文字见record.md和sources/web_search_1.json、2。正式paper条目/摘要在结果里收到，不对未收到的截断结果作覆盖声明；返回含代理镜像/聚合站，不采用其方法事实。随后两个原件直接HTTP动作，共6/12逻辑动作、4/4主题。可测量成功body合计2,216,669B，0重试/redirect；native搜索底层响应字节unknown，故20MB全网络硬cap不能宣称已验证。所有direct请求逐条URL/UTC/status/bytes/SHA在sources/retrieval.jsonl；预留6动作未为用满额度访问。

两新论文official repo链接均只登记not_verified，0新代码快照/commit/许可认证，0作者代码执行。最终library75HTML/18PDF/25pending/8restricted/3abstract_only，129唯一来源/113文件；代码10快照关联9论文，70not_verified/50not_yet_checked。搜索覆盖不是穷尽2025–2026/CV/NLP，也没有由新论文存在推出本项目阳性。
