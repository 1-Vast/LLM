# 新来源实际核读与研究条件

2026-10-29，Asia/Shanghai。原URL/时间/响应/hash见retrieval.jsonl；定向lit-survey，不是全领域查新。arXiv仅最新20条，PubMed74命中仅最新30元数据/原记录。四新增原文已入reference，均P级选读、0作者代码/数据执行；两个主文JATS借generic supplement技术槽，非科学SI，主PDF/HTML仍缺。

| 一手来源与日期/版本 | root实际阅读 | 对研究的约束 |
|---|---|---|
| Learning to Explore Hidden Kinematics for Articulated Object Manipulation，2609.36553v1，首发2026-09-29 | p4原HTML S3段落：粒子先验/滤波、后验运动field、信息奖励、privileged expert及蒸馏；独立显示公式未全核，未复现数值 | 模型后验转成每点运动场、每种关节场按该部分平均幅度归一，再后验加权向量和。PPO用熵差奖励，训练先特权状态expert，再蒸馏/继续RL。不是药筛已有真物理结构/无损连续交互；归一化若搬到药效可能删掉重要幅度；后验均值场不自动保留全部不确定性。此为原理/失配，不是本项目算法证据 |
| PhysCaP，2608.21031v2，首发2026-08-21 | p7原HTML S3.1–3.3及内联质量/刚度公式，未全读附录/提示/实验/代码 | 标准机器人硬件经空载/负载扭矩差估质量，夹爪力/位移拟合刚度；刚度测五次、多数级别。Planner决定何时探索/停止，Prioritizer视觉启发过滤排序。测到物理量再修订计划已有实现，但未由此学细胞作用模型；机器人可直接测物理量/反复操纵同物体的条件不能免费搬到培养/破坏性终点 |
| BCheM，10.3389/fbinf.2026.1838904，PMC13226526，原JATS pub2026-05-19，更早公开未知 | p5 s3-1 Materials、s3-2 Method；未核结果/切分/代码 | 395疾病、1391药、3261耐药/敏感关联（作者报告）来自DRESIS；GPT疾病描述、BioBERT/ChemBERTa与关联图卷积。**behavioral不是原始逐剂量功能谱**，不认证cell×drug×dose×time或培养重复。初看标题时的功能谱联想经方法核读更正；普通功能谱近邻应归DRP2026，不能误归该文 |
| RegFormer，Nature Communications2026，10.1038/s41467-026-72198-x，PMC13376892；原JATS epub2026-05-05，更早公开未知 | p6 Sec15–18模型、拓扑序、双embedding/Mamba，Sec29 drug-response；未全核消融/源码/全部结果 | 输入序由预定GRN的DAG拓扑决定；给固定表达embedding替换DeepCDR表达分支，其他变异/甲基化仍存在，方法写LODO。不是由普通功能反馈学层级/免费增加模态。拓扑顺序的“causal directionality/biologically valid paths”是作者措辞，不等于本项目确认因果识别或所有隐连接受GRN硬约束 |

两arXiv来源正式venue未核，不称顶会录用或代码复现。BCheM与RegFormer主文分别链接https://github.com/Yuu088/BCheM 与 https://github.com/BGIResearch/RegFormer；commit/许可/源码未取得，不能说代码已齐。两机器人论文原HTML项目页不等于已核官方repo，页面中的arXiv/LaTeXML反馈repo不当作者代码。

## 旧基础原文的新增定向核查

root实际回读2013原文 *A simple high-content cell cycle assay reveals frequent discrepancies between cell number and ATP and MTS proliferation assays*，10.1371/journal.pone.0063583，本地原HTML P20、62、107、115（以p/h2/h3块计）：同一信号→细胞数解释需每细胞分析物不变；48h、20点二倍稀释、四格式用replicate plates；ATP/MTS可表现不同Emax、potency shift、双相。本文提供测量语义与单曲线形状混淆的直接事实，不是本项目新机制；破坏性格式在不同板，不是同一培养的连续观测。仅由ATP曲线不能区分cell number与ATP/cell，不把额外计数作为普通ATP终点预测的通用门槛。本轮不读其响应表、图片数值或下载SI。

中性scout独立选读该文、DeepSynBa2026、PIMOGP2024与Active Learning of Model Discrepancy2025的指定方法/限制段，准确范围在neutral_scout.md。DeepSynBa已分解potency/efficacy并拟合剂量面；PIMOGP已有多输出/缺测/同时组合的交换核（不推广成顺序交换）；discrepancy工作已有BED→物理参数MAP→NN误差更新，且承认参数与误差设计的冲突/解释掉结构的边界。不能把它们的旧元件重新认领新意；本轮未复现其效果。

## 普通数据与主张边界

拟合IC50/AUC表可用于其原指标，但不能恢复被强制曲线模型删除的局部转折。曲线坐标/幅度规律须原始多剂量点、单位、time、endpoint/控制及可解释重复，并有多个药物/背景让共享规律对未查询药物产生可证伪预测。不需要完整cell×drug矩阵或昂贵模态。若只得同endpoint的曲线，可以研究该endpoint规律，不能由此推靶点、细胞数量或持久状态。

本轮未读取新功能响应/数据集，旧开发暴露保留；PRISM24Q2、CTRP、sealed/confirmation和.env不读。2013论文与旧AZ raw字段/重复审计不是本轮数据资格：旧ZIP有字段/结构不能自动认证时间、培养独立性或新候选覆盖。未取得并冻结合格动作/评定小包，不能称新H ready，也不把普通实验常产生这些字段写成公开下载必然保留。

## 真实辅助交付与完整性

DS021新隔离headless真实4.375s、exit0、1final/1step_end，8150B stdin；2618input/772output/512cache-read、reported total3902；effective/底层请求数/实付unknown。root逐项核八条PubMed主ID与locator，均匹配；八quote字面匹配，但一条81>80被拒收、canonical用root从原题名取60字符并注明。首次格式assert触发是工程验收事件，非科学负结果；原final/events/usage不改，0重试/后端替换，累计13/13封账。见../deepseek/tasks/DS021/main_review.md。

library_verify.json实际核114唯一来源、100件论文文件；唯一主行70 HTML、13 PDF、21 pending、8 restricted、2 abstract_only。代码仍8快照关联7篇，58 not_verified、49 not_yet_checked；论文89.0MB/代码12.6MB，errors/warnings/changed空，仅证文件/清单一致，不证明读全、数据可得、方法成立或新颖。
