# 原始来源核读与迁移边界

2026-10-29 Asia/Shanghai。围绕用户新提出的CV/NLP多尺度/多模态来源做2pass有界探索，保留便宜常见功能数据主线。确切URL/时间/哈希/错误见retrieval.jsonl；不是最新全领域穷尽查新。三篇均为arXiv原文，正式会议/期刊身份未核，不称顶会录用。

## 三篇原文实际提供什么

| 来源 | 首次公开，取得版本 | 实际核读 | 可支持的原则及不能直接移植的假设 |
|---|---|---|---|
| Dynamic Chunking for End-to-End Hierarchical Sequence Modeling（H-Net） | 2025-07-10，2507.07955v2；564,655B，SHA e918a695230b7a44194c06343f9f627c5d996e04c2236b43ff325c1cef69232a | root读§2.1–2.2方法段落/行内公式，独立scout核同段原HTML math alttext及§4；未审全实验/附录/源码 | 根据相邻编码上下文学习chunk边界，用ratio loss约束压缩，粗主网与细残差同时保留。完整细序列先经encoder；少处理内层token没有减少原始输入测量数 |
| DC-DiT: Adaptive Compute and Elastic Inference for Visual Generation via Dynamic Chunking | 2026-03-06，2603.06351v2；248,674B，SHA39c0abc33c0792ac3e33201b4ba4294d126ef5b93c102aefcab3f7a34fcfdfcd | root§3.1–3.5段落和A.2/A.3；scout§3.1/3.3/3.5和A.2/A.3原文/公式；未核全部独立公式/实验 | 全latent grid编码后按局部不可预测性路由，边界概率排名tail drop，多预算训练随机采样同一tail-drop路径。A.2统计TFLOPs/img含encoder/router/decoder、250采样步及CFG分支；A.3按总训练FLOPs匹配而非固定相同步数。不是药筛新测点选择证据 |
| SimMLM: A Simple Framework for Multi-modal Learning with Missing Modality | 2025-07-25，2507.19264v2；343,213B，SHA54f1377f6522b79d641fcc913d5cd9192dd02d7676f652bfe9f1a39eb125b985 | root§3.1–3.4、Eq3/4 alttext、§5/6；scout§3.1/3.4/4.1–4.2/5/6及部分3.2/3.3；未读SI/源码 | 完整训练模态集合、模态专家/门控、训练随机dropout；MoFe=max(0,loss_more−loss_fewer)作为逐样本训练偏置。不能当“每次新实验都必降低损失”的定理，也不能把选择性药筛缺失当同分布随机dropout |

DC-DiT的HTML title标签只有“1Introduction”；root实际核body p2.1完整题名、p3.1/p3.2作者，并与q2原Atom的标题/作者/固定id核对，未把泛标题当论文身份。H-Net/SimMLM正文题名和原Atom一致。首发日期来自published，不用作v2更新时间或正式接受日期。

H-Net与SimMLM原文分别指向https://github.com/goombalab/hnet 和 https://github.com/LezJ/SimMLM，已登记official链接但未取commit/许可/源码，不称代码齐备。DC-DiT未核作者代码链接，不等于代码不公开。三件原HTML已通过reference_library.py --file/--html入库，未改原字节/执行下载代码。

## 领域先例与普通数据条件

复用DeepSynBa2026 DOI10.1093/bioinformatics/btag416的现有原HTML，root本轮实际读Methods2.1、2.2、2.3及Discussion段落（独立公式未核）；不是其全算法复现。原文已有dose-response完整曲面和potency/efficacy分解，故不能将“别只预测IC50/一个分数”认作首次。其DeepSynBa输出是点参数；Discussion把概率参数/不确定性列为未来方向，不能误写为当前已经做了Bayesian不确定性实验设计。所读段落是预测/训练，不足以宣称整篇或领域没有主动曲线设计。

DeepSynBa Methods2.2提供具体资格提醒：NCI-ALMANAC矩阵边缘含单药，O’Neil矩阵非零组合格没有内嵌单药边缘；同一组合/细胞/剂量重复被中位数聚合。前者不是自动满足任意8剂量网格，后者不能从矩阵边缘虚构单药。其神经模型因缺表达/结构过滤一些细胞/药物，不意味着普通功能分析必须接受该组学门槛。本轮没有取得这些资源原始重复/处理时长/费用或证明S1覆盖。

原有GDSC2 20.36MB文件是拟合摘要；本轮只进一步读GDSC007 matrix_results的CSV表头，见组合、拟合IC50/MaxE和时间零相关摘要列，未读任何响应数值。不能由这些摘要反推出原始逐剂量孔和独立重复。原始matrix_well_stats ZIP只被列为文件线索，未开功能内容；24Q2/CTRP确认均未开。本轮新功能数据下载/实验/训练/安装=0。

## 获取预算与检索缺口

当前7/10获取动作，4/4主题query（含失败），成功6件原响应共1,230,957B，其中三篇原HTML1,156,542B；≤20MB保存与8MB/件cap，0自动重试。query1返回total500而仅取最新12条；query2 total18取relevance前8；query3 total517取前10；其余未遍历，不称全部相关论文。

query4为Europe PMC“drug screening/drug response × multi-fidelity/multi-scale/multimodal，2025-01-01到2026-10-29”，实际HTTP503，无结果体、未重试。此缺口不能被三篇源领域论文或旧库补成“最近药筛尚无先例”；S1的level-set、shape-constrained、goal-oriented/robust design、multi-fidelity先例核查仍未闭合。剩3个获取动作不是额外主题query额度，不在本轮另开新检索枝。

起初尝试bs4抽取时发现maestro未安装该包，未安装，改用标准库HTMLParser生成reading_extracts.json辅助定位；单独公式后来从math alttext补读。这个衍生文本不替原HTML和哈希。一次工具输出中DC-DiT tail-drop段被裁剪，已单独重取S3.SS3.p4.1完整文本，不冒称截断文本已读。

DS016按固定三行packet做版本/日期/输入范围/成本单位编目，原事件/正文/usage与root审核在research/deepseek/tasks/DS016。对H-Net返回“same computational budget”不作为真实单位采纳，规范单位null；Sim的完整训练模态条件与随机dropout同时保留。真实headless session-cdae8773-28bb-4fda-9a00-38678e37ca98、5.094s、2023input/702output/cache-read256、stdin7093B、一次final。累计8/8调用封账，实际backend/实付/底层请求数unknown。此辅助未选科学方法或机制，root逐源核后才有限采纳。

指定Terra上阶段尝试实际401失败，本阶段没有重复该失败调用或伪称Terra整理。协调者按organize-files保存来源、分支、候选和停止边界，重要科学文字另交独立内容审阅。
