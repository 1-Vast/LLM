# Data/feedback-unit innovation proposal request

你是本项目的数据与可执行研究机会探索者。请提出一个最强、简洁、能执行的创新机会；不要只给数据来源名单、泛泛架构或不断提高门槛。本次是独立API提案，输出不是证据。允许明确说创新尚未建立，但应提出下一项会改变行动的最低成本检验。

总目标：虚拟细胞干预state/function世界模型支持药物发现的研究智能体；通过真实反馈改进模型更新/研究程序，把有效能力迁移到后续任务；进一步测旧/新improver在同一later-solver/history/budget下谁能让改进更有效(C4)。静态action-conditioned world、RNA代理和有限离线任务均合法，但不能把RNA说成疗效，把clone/cell说成独立研究任务。

本地真实证据与约束（以这些为准，不需要假装联网）：

1. TG-GATEs人原代肝细胞持续暴露：身份/缺失已认证，但本候选未开真实RNA或功能值。2h->24h有156个LDH身份可用条件/52药标签；要求DNA与LDH均有则144条件/48药；进一步每药Low/Middle/High三种不同正剂量且正常单位后47药。8h->24h有385LDH条件/152标签，但不是385个已认证正剂量动作，完整双assay三剂量菜单未认证。功能记录2606条；DNA602 missing/LDH2 missing。不能擅自补值。
2. 官方把DNA(%)和LDH(%)都定义为relative survival，不能把LDH%当原始泄漏量或拆birth/death。高剂量来自80-90% relative-survival预筛或溶解度限制，预筛时间/lot关系未知，不能用高剂量设置猜新药真实毒性。无sample->donor/lot/同培养映射，不做donor或同细胞轨迹结论。条件对齐的assay均值预测仍合法。
3. 已停止的TG候选：单eta时间warp操作属于普通system identification，且未限制曲线族时钟不能识别。尚无任何TG真实数值模型试验，不应说已失败所有RNA或动力学。
4. 上一轮skeptic提案但未执行：按干预后早RNA响应几何传播少量功能残差，预测未买高剂量；必须比chemical/dose direct、辅助RNA direct、普通offset/refit/state-kernel/4gene stress signature。不要简单重述此提案并改名创新。
5. Watermelon Nature2021 DOI10.1038/s41586-021-03796-6，GSE150949：PC9 300nM osimertinib，day0/3/7/14，56419cells/11samples，共享day0、两culture day3/day7及day14 cycling/medium/noncycling三sort gate。H2B-mCherry dilution真实proliferation history，但捕获gate比例不是自然population probability。无已认证逐replicate sampling weight。单30nt barcode day3+两culture day14共享482个，固定309/84/89 source/dev/test；>=2cells则206(134/35/37)。两culture不能说482研究任务或宽泛C4。全部RNA/clone_size/per-gate lineage target尚未打开。可做独立合同下conditional sampled-gate prediction。
6. 已构造反例：初始state、endpoint state×division-history、endpoint total、global division/death全相同，origin->late state transport不同；普通conditional mixture精确重现观察。故不从这些summary主张识别selection vs transition；并不否认实际lineage信息或预测价值。
7. DRUG-seq paper433compound×8dose×triplicate，但GSE120222真实仅72bulkRNA samples，DMSO+6codedcompounds×3dose12h，实际大型matchedgrowth panel未认证。历史MIX-seq24h->PRISM5day/STATE确认停止，不能重开。
8. 项目真实负结果：ppODE不如strong direct、STACK额外history有3.5%但未过预定实用门、AZpaid-reference effect coordinate不如full direct、PRISM固定两pool大panel覆盖失败、generic program编辑未胜ordinaryrefit/search。不能用旧exposed failedtest调门槛或打开AZ413 reserve。
9. 最新已留存fullprimary：LCD-CLIPR PNAS2026-10-08 DOI10.1073/pnas.2602630123，stationarysnapshot、causaldiffusion、噪声分解、线性drift识别；SciAdv2026-09-09 DOI10.1126/sciadv.aed3414，13methods/25datasets/24metrics，压缩方差和synergy低估、celltype泛化不足。不能把世界模型/LLMloop本身作为新意。

任务：优先从已认证TG真实feedback与compound later-tasks，或其他上列可执行资产中，提出1个不是上一轮residual-kernel改名的窄创新研究机会。应基于具体生物结构/可重复统计现象/改进策略，而非必须发明新方程。选择可以经验否证的主张；说明最近普通解释、为什么仍值得一测。不要未经来源核验编造新数据可得性或文献。

必须输出：
- 具体drug-discovery决策、exact allowed source fields、真实可付feedback bundle和later task单位；不夸大独立性。
- 一个主张和<=12行操作；world到底预测什么，如何从实际反馈改进。
- 最便宜可执行kill（可以metadata/replay/普通reproduction，但若是synthetic不可称生物证据）；如果数值pilot，应说在开值前需冻结哪些东西、主终点/实用成功与停条件。
- 与strong direct（同辅助RNA）、普通重训、CL、AL、简单mixture、等预算program-search公平比较；模型继承和策略继承如何分开；C4需要哪些task数量和common-start对照。不能凭小N承诺效能。
- 把不确定的创新性、必要模块、真实预算/失败cost、最强反对解释说清楚。

答复请简洁而具体，避免把验证协议本身包装成核心创新。不执行任何代码。
