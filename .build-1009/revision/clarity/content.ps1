$oldNotes=@{}
for($i=1;$i -le 15;$i++){$oldNotes[$i]=$deck.Slides.Item($i).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text}
$deck.Slides.Add(4,12)|Out-Null
function Note($s,$text){$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=$text}
function Pic($s,$name,$x,$y,$w,$h){
 $sh=$s.Shapes.AddPicture((Join-Path $buildDir $name),0,-1,$x,$y,-1,-1)
 $r=[Math]::Min($w/$sh.Width,$h/$sh.Height);$nw=$sh.Width*$r;$nh=$sh.Height*$r
 $sh.LockAspectRatio=0;$sh.Width=$nw;$sh.Height=$nh;$sh.Left=$x+($w-$nw)/2;$sh.Top=$y+($h-$nh)/2
}
function Step($s,$n,$head,$text,$y){
 Txt $s $n 48 $y 40 28 19 $palette.blue $true
 Txt $s $head 104 $y 155 32 20 $palette.green $true
 Txt $s $text 280 $y 632 68 18
}
function Block($s,$head,$text,$x,$y,$w,$h){Txt $s $head $x $y $w 29 20 $palette.green $true;Txt $s $text $x ($y+40) $w $h 18}
function Arrow($s,$x1,$y1,$x2,$y2){$sh=$s.Shapes.AddLine($x1,$y1,$x2,$y2);$sh.Line.ForeColor.RGB=(RGB $palette.green);$sh.Line.Weight=1.5;$sh.Line.EndArrowheadStyle=3}

$s=$deck.Slides.Item(3)
Reset $s '论文一   MAP / 为什么做这项研究' 'MAP：用机制知识改善未测药物的响应预测' '研究目标：在没有目标药物响应数据时，预测它会让细胞中的哪些基因发生变化。' 'Feng et al., 2026, Introduction / Fig. 1 / Methods'
Step $s '01' '研究需求' '大量候选药物尚未在目标细胞中测量。逐一实验成本高，需要从有限的已测响应推断未测药物的效应。' 163
Rule $s 280 241 632
Step $s '02' '已有进展' 'chemCPA 等用分子结构表示新药物；STATE 等提供细胞与基因表征。模型已能利用化学特征和细胞背景。' 255
Rule $s 280 333 632
Step $s '03' '关键缺口' '结构表示没有显式约束靶点、抑制／激活方向和基因功能。稀疏的响应数据难以完整补齐这些作用关系。' 347
Rule $s 280 425 632
Step $s '04' 'MAP 的思路' '先用公共属性和有向关系学习机制相关表示，再联合药物、剂量与细胞状态，预测给药后的表达。' 439
Note $s $oldNotes[3]

$s=$deck.Slides.Item(4)
Reset $s '论文一   MAP / 整体流程' 'MAP 的两阶段训练与预测任务' '知识预训练补充作用关系；响应训练学习这些信息在具体细胞条件下怎样影响表达。' 'Feng et al., 2026, Fig. 1 / Methods'
Block $s '第一阶段：学机制相关表示' '名称、分子结构、蛋白序列和功能描述，与药物–基因、基因–基因关系共同参与对比学习。' 48 158 402 83
Block $s '第二阶段：学条件响应' '输入对照细胞、药物表示与剂量，用已测处理群体训练模型，输出给药后的基因表达。' 510 158 402 83
Arrow $s 453 218 499 218
Rule $s 48 306 864
Txt $s '预测时：对照细胞 ＋ 新药物结构 ＋ 剂量  →  给药后表达  →  相对对照的变化' 48 328 864 57 21 $palette.green $true
Block $s '评测一：未见细胞–药物组合' '药物在其他背景出现过；留出目标细胞与该药物的配对响应，检查组合泛化。' 48 398 402 58
Block $s '评测二：整种药物未测' '留出该药全部响应，知识预训练也移除其实体、别名与关联边，检查新分子外推。' 510 398 402 58
Note $s $oldNotes[3]

$s=$deck.Slides.Item(5)
Reset $s '论文一   MAP / 方法一：知识预训练' '知识预训练：对齐实体属性，保留作用关系' 'MAP-KG 整合 14 个资源，包含 187,089 个药物、22,924 个基因与 694,246 条关系。' 'Feng et al., 2026, Fig. 1a–b / Methods'
Pic $s 'figure-4.png' 48 162 414 225
Txt $s '图中两类信息：实体的不同属性，以及实体之间的有向关系。' 48 400 414 50 16 $palette.muted
Txt $s 'BioBERT 编码文字；MoleculeSTM 编码分子；ESM-2 编码蛋白，适配器负责对齐。' 48 457 414 39 15 $palette.muted
Block $s '① 同一实体：对齐不同来源的信息' '以名称文字为共同参照，把同一药物的结构、同一蛋白的序列与功能描述拉近；其他实体作为负例。' 510 163 402 84
Block $s '② 相连实体：保留作用类型与方向' '例如“二甲双胍抑制 MT-ND1”。有序编码区分源药物、关系与目标基因，再对齐正确的关系配对。' 510 315 402 84
Txt $s '输出：带机制相关先验的药物与蛋白表示，供下一阶段预测器使用。' 510 454 402 44 17 $palette.green $true
Note $s $oldNotes[4]

$s=$deck.Slides.Item(6)
Reset $s '论文一   MAP / 方法二：条件响应预测' '预测器怎样结合细胞背景、药物与剂量' '同一药物在不同细胞中可能产生不同响应，因此预测必须同时依赖分子和细胞条件。' 'Feng et al., 2026, Fig. 1c / Methods'
Pic $s 'figure-5.png' 48 161 290 280
Block $s '① 细胞分支：提供状态与基因功能' 'STATE 提供细胞和基因 token；对应蛋白知识与基因 token 融合，给模型提供细胞背景。' 386 163 526 61
Block $s '② 药物分支：提供扰动条件' '分子表示按对数剂量缩放，与细胞及基因 token 一起进入 4 层 Transformer，建模条件间的影响。' 386 271 526 65
Block $s '③ 输出分支：预测给药后的表达' 'MLP 将预测细胞 token 解码为基因表达；训练同时匹配处理群体的平均表达和平均细胞嵌入。' 386 387 526 63
Txt $s '监督作用于群体均值。均值预测准确，仍不能直接证明每个单细胞的分布或轨迹准确。' 48 472 864 26 16 $palette.muted
Note $s $oldNotes[5]

$s=$deck.Slides.Item(7)
Reset $s '论文一   MAP / 实验验证' '机制知识是否真正改善未测药物的预测？' '整药留出实验比较预测与实测响应；另外用消融和 A549 计算筛选检查知识贡献与应用价值。' 'Feng et al., 2026, Fig. 2–5 / Methods；主结果按论文数字重绘'
Txt $s '主结果：未测药物的响应预测' 48 157 470 27 20 $palette.green $true
Txt $s '50 个差异表达基因的 Pearson Δ，相对最强基线的提升。' 48 201 470 44 17
$bars=@(@{name='Tahoe';v=11.8;y=273},@{name='OP3';v=19.8;y=334},@{name='SciPlex3';v=10.4;y=395})
foreach($b in $bars){Txt $s $b.name 48 $b.y 112 27 18;Bar $s 165 ($b.y+1) ($b.v*11) 25 $palette.green;Txt $s ('+'+$b.v+'%') (177+$b.v*11) $b.y 98 27 18 $palette.green $true}
Txt $s 'Pearson Δ 先减去对照表达，再比较变化方向与模式，避免基础表达主导相关性。' 48 450 470 43 16 $palette.muted
Block $s '消融：哪类知识起作用？' '去掉药物–基因边下降最大；MAP-KG 比 PrimeKG 的 Pearson Δ 高 11.4%，支持靶点关系的贡献。' 576 157 336 85
Block $s '应用：预测能否帮助排序？' 'A549 的 58 个留出候选中，5 个已批准非小细胞肺癌药物有 4 个进入前 15。' 576 309 336 74
Txt $s '各数据集内部留出。A549 为计算筛选，尚未开展新的药效湿实验。' 576 451 336 45 16 $palette.muted
Note $s $oldNotes[6]

$s=$deck.Slides.Item(9)
Reset $s '论文二   Robin / 为什么做这项研究' 'Robin：把文献假设接到真实实验反馈' '案例目标：寻找能增强视网膜色素上皮（RPE）吞噬功能的再利用药物。' 'Ghareeb et al., 2026, Introduction / Fig. 1–2 / Discussion'
Step $s '01' '疾病需求' '干性年龄相关性黄斑变性与 RPE 功能下降相关。RPE 负责清理光感受器外节，论文选择增强吞噬作为可测目标。' 163
Rule $s 280 241 632
Step $s '02' '已有进展' '文献智能体能整合跨领域证据、提出药物候选；代码工具使大模型能够执行科学数据分析。' 255
Rule $s 280 333 632
Step $s '03' '研究缺口' '文献支持不等于药物有效。原始数据分析、机制解释与下一轮候选更新常被分开，缺少真实实验串联验证。' 347
Rule $s 280 425 632
Step $s '04' 'Robin 的做法' '检索和分析智能体分工协作，把实验新观察返回假设生成过程。研究者制定并执行湿实验协议。' 439
Note $s $oldNotes[8]

$s=$deck.Slides.Item(10)
Reset $s '论文二   Robin / 方法流程' 'Robin 如何组织检索、选药、实验与分析' 'Robin 协调器综合各阶段输出；实验后形成的新观察用于调整下一轮假设和候选。' 'Ghareeb et al., 2026, Fig. 1 / Methods'
$xs=@(48,271,494,718)
$heads=@('Crow：机制检索','Falcon：候选评估','研究者：湿实验','Finch：数据分析')
$bodies=@('回答疾病、机制和实验模型问题。','检查药理依据、引用与局限。','选择测试对象，制定并执行协议。','执行代码，分析原始流式与 RNA 数据。')
for($i=0;$i -lt 4;$i++){
 Txt $s $heads[$i] $xs[$i] 167 194 53 19 $palette.green $true
 Txt $s $bodies[$i] $xs[$i] 231 194 77 18
 if($i -lt 3){Arrow $s ($xs[$i]+195) 194 ($xs[$i]+218) 194}
}
Txt $s '实验新观察  →  Robin 综合解释  →  更新候选和后续实验' 48 323 864 30 20 $palette.blue $true
Rule $s 48 371 864
Block $s '候选怎样排出优先级？' '10 个机制／实验报告确定读数，30 个药物假设接受深入评估；成对评审与 BTL 模型形成排序。' 48 390 402 62
Block $s '分析结果怎样留下证据？' 'Finch 保存代码与 notebook。8 条分析轨迹检查一致性，不能替代独立生物样本。' 510 390 402 62
Note $s $oldNotes[9]

$s=$deck.Slides.Item(11)
Reset $s '论文二   Robin / 第一轮实验' '第一轮：吞噬命中怎样推动机制研究' '初筛用 ARPE-19 与 pHrodo 微球；平均荧光强度反映吞噬后酸性环境信号，以溶剂对照归一化。' 'Ghareeb et al., 2026, Fig. 2–3 / RPE phagocytosis assay'
Pic $s 'figure-10.png' 48 164 374 263
Txt $s 'RNA-seq 火山图：横轴为表达倍数变化，纵轴为显著性。ABCA1 位于上调基因一侧。' 48 449 374 49 16 $palette.muted
Block $s '① 功能实验找到 Y-27632' '流式分析去除碎片、双细胞与死细胞后，ROCK 抑制剂 Y-27632 显示吞噬增强；人工复分析支持。' 471 164 441 66
Block $s '② RNA-seq 检查命中伴随的变化' 'ROCK 抑制影响肌动蛋白。新数据富集细胞骨架、小 GTP 酶与自噬相关程序，ABCA1 约 3 倍上调。' 471 285 441 66
Block $s '③ ABCA1 成为下一步机制线索' 'ABCA1 编码脂质外排泵，提示吞噬与脂质稳态可能相关；仍需靶点干预实验检验因果。' 471 406 441 56
Note $s $oldNotes[10]

$s=$deck.Slides.Item(12)
Reset $s '论文二   Robin / 第二轮实验与功能复核' '第二轮：ripasudil 命中，并接受更接近生理的复核' '第一轮 ROCK 线索推动第二轮 10 种候选测试；ripasudil 是已获批的青光眼 ROCK 抑制剂。' 'Ghareeb et al., 2026, Fig. 4 / RPE-SC validation'
Pic $s 'figure-11.png' 48 164 513 188
Txt $s 'ripasudil：ARPE-19 吞噬信号为对照 1.89 倍' 48 376 513 57 20 $palette.green $true
Txt $s '人工复分析为 1.75 倍；剂量曲线进一步检查效力。倍数均相对于 DMSO。' 48 432 513 43 17
Block $s '复核一：改变细胞模型与底物' '用 1 位 >60 岁供者的原代 RPE-SC，以及牛光感受器外节。ripasudil 与 Y-27632 再次命中（4 孔重复）。' 607 164 305 113
Block $s '复核二：检查机制线索' 'ABCA1 上调在原代细胞复现；昼夜节律候选 KL001 也命中，为后续实验提供另一条线索。' 607 344 305 80
Txt $s '单供者孔重复仍不足以证明人群泛化；ABCA1 因果机制及临床疗效尚待验证。' 48 479 864 20 14 $palette.muted
Note $s $oldNotes[11]

$s=$deck.Slides.Item(13)
Reset $s '论文二   Robin / 系统评价' '哪些环节有收益，自动化到什么程度？' '文献检索和代码执行的作用分别评估；真实实验案例提供流程证据，自主规划仍需进一步验证。' 'Ghareeb et al., 2026, Extended Data Fig. 4–6 / Methods / Discussion'
Txt $s '代码执行：BixBench 正确率' 48 157 475 28 20 $palette.green $true
Txt $s '170 题，3 次运行，均值 ± 标准误' 48 202 475 24 16 $palette.muted
Txt $s 'Finch' 48 251 118 27 18
Bar $s 180 252 273.6 27 $palette.green
Txt $s '22.8 ± 1.7%' 279 251 186 28 18 0xFFFFFF $true
Txt $s "Sonnet 3.7`n无工具" 48 309 124 55 17
Bar $s 180 319 19.2 27 $palette.blue
Txt $s '1.6 ± 1.2%' 217 318 230 28 18 $palette.blue $true
Txt $s '工具流程改善了表现，总体正确率仍有限；工具和流程同时变化，无法单独归因于代理数量。' 48 400 475 88 18
Block $s '文献检索：减少虚构引用' 'o4-mini 方案虚构引用率 44.5% ± 6.37%；Crow 检查的 15 份方案未见虚构。' 576 157 336 76
Block $s '自动化边界：角色衔接已完成' '两轮实验实现候选更新与功能复核。湿实验由人执行，调用次序几乎固定；自主规划收益尚不明确。' 576 310 336 94
Txt $s '本篇的推进：把可追溯文献、可执行分析与真实实验反馈接成连续研究过程。' 48 479 864 20 14 $palette.muted
Note $s $oldNotes[12]

$s=$deck.Slides.Item(14)
Reset $s '方法应用   药物发现智能体 / 可迁移的想法' '可迁移的两点：机制条件化与可追溯实验反馈' '以下为独立的系统设计建议；实际收益需要在同数据、同工具和同预算下验证。' '设计建议，依据 MAP 与 Robin；知识关联和预测结果需接受功能实验检验'
Block $s '借鉴 MAP：候选要带机制与条件' '记录药物结构、抑制／激活关系、细胞、剂量和时间，形成机制相关的条件响应预测。' 48 159 402 77
Block $s '借鉴 Robin：更新要有新证据' '用疾病相关功能读数检验候选，保存原始数据、QC、代码和效应区间，并说明新观察怎样改变下一轮。' 510 159 402 77
Txt $s '机制证据／预测  →  功能与毒性实验  →  可复核分析  →  候选更新' 48 308 864 32 21 $palette.green $true
Rule $s 48 361 864
Txt $s '验证知识' 48 380 170 27 19 $palette.green $true
Txt $s '结构、完整知识、打乱关系比较：是否改善严格留药的响应预测？' 254 380 658 44 18
Txt $s '验证策略' 48 440 170 27 19 $palette.green $true
Txt $s '确定性、LLM 与无更新比较：是否改善预算内命中、效应与成本？' 254 440 658 44 18
Note $s $oldNotes[13]

$s=$deck.Slides.Item(15)
Reset $s '阶段总结   MAESTRO / 最重要的新发现，更新至 10.11' '转录迁移出现确认收益，LLM 增益仍未成立' '421 种封存确认药物，101 种满足杀伤标准；目标是预测对 578 条癌细胞系的选择性杀伤。' '项目来源：mechanism_routing_20261011 / PROTOCOL、RESULTS 与核验记录'
Txt $s '实测 L1000 响应  →  5 个转录近邻  →  加权迁移 PRISM 杀伤谱' 48 155 864 31 21 $palette.green $true
Rule $s 48 210 864
Txt $s '确认了什么？' 48 233 402 28 21 $palette.green $true
Txt $s '+0.116 r' 48 283 402 46 33 $palette.green $true
Txt $s '未见机制类别中超过靶点近邻。' 48 343 402 29 19 $palette.ink $true
Txt $s "多重比较校正区间 [0.053, 0.181]。`n独立复筛增益 +0.103 r。`n补充 160 系部分筛选增益 +0.049 r。" 48 389 402 101 18
Txt $s '尚未确认什么？' 510 233 402 28 21 $palette.blue $true
Txt $s 'LLM 的四种角色均未增加收益' 510 283 402 57 23 $palette.ink $true
Txt $s '文献预测、近邻审查、筛后解释、信任判断。其中审查使 Δr 下降 0.052，文献预测融合下降 0.025。' 510 356 402 77 18
Txt $s '下一步保留跨机制近邻，先验证错误淘汰和最终选择收益，再引入更强的实验反馈。' 510 444 402 51 17 $palette.muted
Note $s ($oldNotes[14]+"`n`n"+$oldNotes[15])
$deck.Slides.Item(16).Delete()

foreach($s in $deck.Slides){foreach($sh in $s.Shapes){if($sh.HasTextFrame -and $sh.TextFrame.HasText -and $sh.Left -gt 880 -and $sh.Top -gt 500 -and $sh.Width -lt 50){if($sh.TextFrame.TextRange.Text -match '^\d{2}$'){$sh.TextFrame.TextRange.Text=('{0:D2}' -f $s.SlideIndex)}}}}
Note $deck.Slides.Item(1) '本次汇报共15页，两张论文来源封面保留。两篇论文按背景问题、总体或系统流程、方法与实验结果展开。方法应用与MAESTRO均压缩为一页。项目资料截至2026-10-11，当前确认的是实测转录近邻迁移的收益，LLM独立增益尚未成立。'
