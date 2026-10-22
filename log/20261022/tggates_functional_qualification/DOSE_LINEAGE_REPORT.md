# 剂量选择与测量方法血缘裁决

2026-10-22，Asia/Shanghai；方法审计，不开个体响应值。主文已取得且可复核，补充表及细化测量流程仍未认证。`DOSE_METHOD_EXCERPTS.json` 保留原文段落编号与原 XML SHA256。

原始论文 [Igarashi et al., 10.1093/nar/gku955](https://doi.org/10.1093/nar/gku955) 的 Dose setting 明确：in-vitro 最高浓度按产生 **80–90% relative survival** 的水平选择，难溶化合物例外按最大溶解度，原则上 low:middle:high=1:5:25。它没有在该段交代预筛具体 assay、时间、培养/lot 或与 released DNA/LDH 的独立性。因此可以认证“剂量菜单带有先前功能筛选信息”，不能认证其是独立24h DNA、LDH或其他测定，不能把各药High强制赋值为85%，也不能把预筛历史计作本智能体新获得的能力。

主文 Hepatocyte treatment 指六个人源 lot、两家供应商，并把 lot 信息及详细 viability 流程指向补充信息。当前没有取得 S2 或 sample→lot 映射；同药只有一个 EXP_ID、individual 1/2 仍不等于 donor。精确 sample key 将表达与功能联系到同一登记条件，未认证来自同一个物理孔、相同细胞或平行孔。各时间的破坏性采样不构成同细胞轨迹。

官方 [README §2.6](https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/README_e.html#2.6) 将 `DNA(%)` 定义为 DNA content 计算的 relative survival，将 `LDH(%)` 定义为培养上清泄漏 LDH activity 计算的 **relative survival**。后者不是已认证的原始泄漏量、死亡概率或OASIS LDH readout；在得到公式前，不能沿用别处“LDH越大损伤越强”的方向或阈值。登记百分数不证明裁剪至[0,100]，非缺失也不证明数值合法。

主文还提醒强细胞毒性可能使全局归一化后的mRNA fold-change偏离实际fold-change。后续若取表达，必须记录预处理、control范围及绝对/相对表达边界。文中关于十年间仪器/试剂变化的具体说明针对hematology/biochemistry，不能直接冒称已经证明本in-vitro表有相同批次偏移。

本轮方法访问按预登记执行六次请求，共 **12,795 HTTP body bytes**，全部未取得所需补充信息：旧PMC OA路径404，当前PMC OA403，OUP文章403，官方项目页TLS失败，Europe PMC网页403，BioStudies所查S-EPMC条目404。原返回及每次URL/status/hash/bytes/失败类型保留于 `dose_sources/NETWORK.json`；TLS失败没有响应体文件。未绕过访问限制，也没有把网页失败当作数据或机制的科学阴性。此前Europe PMC fullTextXML与官方README仍是有效已取一手来源，不重复下载。此次URL/条目推测不能认证相应资源不存在。

**允许的任务边界：** 可以另注册“已预筛持续暴露菜单内，已拥有早期状态时，少量后期功能反馈向未测条件传播”的条件任务；所有臂同获实际剂量、原始单位、dose level及可得预筛设计知识。绝不能称为无先验新药安全剂量发现、washout/rescue规划或跨donor继承。若声称早期RNA节省功能实验费用/时延，必须另证真实样本处理及返回成本；2h取样不等于2h获得表达，微阵列也不默认比24h DNA/LDH便宜。

该方法结论既不阻止合法条件预测试验，也不为新世界模型/Agent/RSI架构放行。数值开放仍须化学身份/分组、数值访问合同、功能单位及实际决策/损失先行冻结。当前跨lot身份、预筛独立性与具体测量公式继续 UNKNOWN；总目标尚未完成。

执行记录：主文摘录脚本在maestro成功运行。最初两次工作树只读检索分别使用不存在的LISTING.html及PowerShell未展开的rg路径通配符而失败，随后使用实际DIRECTORY.html及显式目录，未写入/改变任何旧证据。未做模型、API、GPU或生物实验。
