$s=Base 8 '论文二   Robin / 系统创新与方法流程' '检索形成可测试候选，执行分析推动下一轮更新' '创新在工作衔接：有来源的假设、可运行的数据分析与真实实验反馈共同构成发现过程。' 'Ghareeb et al., 2026, Fig. 1 / Methods: Robin and Finch implementation'
Node $s 'Crow：先选研究方向' '机制与实验模型报告' 48 154 193 94
Node $s 'Falcon：审查候选' '药理证据、引用与局限' 271 154 193 94
Node $s '研究者：执行实验' '选药、协议与湿实验' 494 154 194 94
Node $s 'Finch：分析新数据' 'FCS / RNA 与 notebook' 718 154 194 94
Link $s 241 201 271 201
Link $s 464 201 494 201
Link $s 688 201 718 201
Link $s 815 248 815 275
Link $s 815 275 366 275 $palette.green $false
Link $s 366 275 366 248
Txt $s 'Robin 协调器综合新观察，调整候选与后续实验' 48 269 638 26 15 $palette.muted
Block $s '如何把大量文献转成待测清单？' '10 个机制／实验报告 → 成对比较选读数 → 30 个药物假设 → Falcon 深入评估 → 研究者选择实际测试对象。' 48 314 410 88
Txt $s 'BTL：P(i 胜 j) = sᵢ / (sᵢ + sⱼ)' 48 448 410 27 18 $palette.blue $true
Block $s '如何从原始数据形成可复核结论？' 'Finch 用 edit_cell 编写并执行代码，8 条独立分析轨迹后综合结论；保留 notebook，使 QC、统计与结果可以追查。' 508 314 404 88
Txt $s '名次衡量文献依据；药效由实验检验。8 条分析轨迹检查分析一致性，不能当作 8 个生物学重复。' 508 448 404 46 15 $palette.muted
Notes $s "Crow和Falcon采用PaperQA2检索文献，也访问临床试验及OpenTargets。Crow快速回答疾病、机制、测量方法，Falcon对候选深入评价药理依据与局限。Robin协调器基于o4-mini，成对裁判为ClaudeSonnet3.7。先形成10份机制/实验报告，再排序选择实验方向、生成30个假设，以Falcon报告评估，研究者审核选择并执行实验。最多25项时比较所有配对，否则随机300对；BTL把成对偏好拟合为相对强度s，概率为s_i/(s_i+s_j)，排序不表示实测效应。Finch接受原始FCS或RNA数据，在Jupyter用edit_cell修改并执行代码，以submit_answer提交结论。8条独立分析轨迹的共识有助于发现分析一致性，却受相同模型、提示和数据的共同偏差约束，不能代替独立培养或供者。新观察返回协调器构成下一轮输入。图中人类湿实验环节不可省略。论文创新是把这些环节在真实案例中接起来，代理数量本身不是科学发现有效性的证明。\n$robincite"
