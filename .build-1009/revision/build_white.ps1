$ErrorActionPreference = 'Stop'
$outDir = 'D:\MAESTRO\output-1009'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$assetDir = 'D:\MAESTRO\.build-1009\revision'
$app = New-Object -ComObject PowerPoint.Application
$app.Visible = -1
$deck = $app.Presentations.Add()
$deck.PageSetup.SlideWidth = 960
$deck.PageSetup.SlideHeight = 540
$palette = @{ ink=0x26383D; muted=0x617079; green=0x527C71; blue=0x637F94; line=0xDCE4E4; pale=0xF4F7F6; white=0xFFFFFF }
$font = 'Microsoft YaHei'
function RGB([int]$hex) { [int](($hex -shr 16 -band 255) -bor (($hex -shr 8 -band 255) -shl 8) -bor (($hex -band 255) -shl 16)) }
function Txt($slide,[string]$text,[double]$x,[double]$y,[double]$w,[double]$h,[double]$size=17,[int]$color=$palette.ink,[bool]$bold=$false) {
 $shape=$slide.Shapes.AddTextbox(1,$x,$y,$w,$h)
 $shape.Line.Visible=0; $shape.Fill.Visible=0
 $shape.TextFrame.MarginLeft=0; $shape.TextFrame.MarginRight=0; $shape.TextFrame.MarginTop=0; $shape.TextFrame.MarginBottom=0
 $shape.TextFrame.WordWrap=-1; $shape.TextFrame.AutoSize=0; $shape.TextFrame2.AutoSize=0
 $range=$shape.TextFrame.TextRange; $range.Text=$text
 $range.Font.Name=$font; $range.Font.NameFarEast=$font; $range.Font.Size=$size
 $range.Font.Color.RGB=(RGB $color); $range.Font.Bold=[int]$bold
 $range.ParagraphFormat.SpaceAfter=4
 $shape.Height=$h
}
function Rule($slide,$x,$y,$w) { $shape=$slide.Shapes.AddLine($x,$y,($x+$w),$y); $shape.Line.ForeColor.RGB=(RGB $palette.line); $shape.Line.Weight=1 }
function Base([int]$n,[string]$section,[string]$title,[string]$sub,[string]$source) {
 $slide=$deck.Slides.Add($n,12)
 $slide.FollowMasterBackground=0; $slide.Background.Fill.Solid(); $slide.Background.Fill.ForeColor.RGB=(RGB $palette.white)
 Txt $slide $section 48 23 850 20 11 $palette.green $true
 Txt $slide $title 48 57 864 43 29 $palette.ink $true
 Txt $slide $sub 48 105 864 35 15 $palette.muted
 Rule $slide 48 499 864
 Txt $slide $source 48 511 814 17 9.5 $palette.muted
 Txt $slide ('{0:D2}' -f $n) 888 510 30 18 11 $palette.green
 return $slide
}
function Notes($slide,[string]$text) { $slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=$text }
function Picture($slide,[string]$file,$x,$y,$w,$h) {
 $shape=$slide.Shapes.AddPicture((Join-Path $assetDir $file),0,-1,$x,$y,-1,-1)
 $ratio=[Math]::Min($w/$shape.Width,$h/$shape.Height)
 $newWidth=$shape.Width*$ratio; $newHeight=$shape.Height*$ratio
 $shape.LockAspectRatio=0; $shape.Width=$newWidth; $shape.Height=$newHeight
 $shape.Left=$x+($w-$shape.Width)/2; $shape.Top=$y+($h-$shape.Height)/2
}
function Block($slide,[string]$head,[string]$body,$x,$y,$w,$h) {
 Txt $slide $head $x $y $w 28 18 $palette.green $true
 Txt $slide $body $x ($y+37) $w $h 17 $palette.ink
}
function Table($slide,$rows,$x,$y,$widths,$rowHeights) {
 $n=$rows.Count; $cols=$widths.Count; $w=($widths|Measure-Object -Sum).Sum; $h=($rowHeights|Measure-Object -Sum).Sum
 $shape=$slide.Shapes.AddTable($n,$cols,$x,$y,$w,$h); $tbl=$shape.Table
 for($j=1;$j -le $cols;$j++) { $tbl.Columns.Item($j).Width=$widths[$j-1] }
 for($i=1;$i -le $n;$i++) {
  $tbl.Rows.Item($i).Height=$rowHeights[$i-1]
  for($j=1;$j -le $cols;$j++) {
   $cell=$tbl.Cell($i,$j); $cs=$cell.Shape; $cs.Fill.Solid(); $cs.Fill.ForeColor.RGB=(RGB $(if($i -eq 1){$palette.pale}else{$palette.white}))
   $tf=$cs.TextFrame; $tf.MarginLeft=10; $tf.MarginRight=8; $tf.MarginTop=7; $tf.MarginBottom=5
   $tf.TextRange.Text=[string]$rows[$i-1][$j-1]; $tf.TextRange.Font.Name=$font; $tf.TextRange.Font.NameFarEast=$font
   $tf.TextRange.Font.Size=17; $tf.TextRange.Font.Bold=[int]($i -eq 1); $tf.TextRange.Font.Color.RGB=(RGB $palette.ink)
   foreach($edge in 1..4) { $cell.Borders.Item($edge).ForeColor.RGB=(RGB $palette.line); $cell.Borders.Item($edge).Weight=0.6 }
  }
 }
}
$mapcite='Feng et al., Nature Machine Intelligence (2026). DOI: 10.1038/s42256-026-01286-w'
$robincite='Ghareeb et al., Nature 655, 497–505 (2026). DOI: 10.1038/s41586-026-10652-y'

# 01
$s=$deck.Slides.Add(1,12)
$s.FollowMasterBackground=0; $s.Background.Fill.Solid(); $s.Background.Fill.ForeColor.RGB=(RGB $palette.white)
Txt $s '1009   研究组会' 62 55 600 24 14 $palette.green $true
Txt $s "知识驱动的药物发现`n与科学发现智能体" 62 157 835 130 42 $palette.ink $true
Txt $s '两篇论文精读、方法启发与阶段进展' 64 310 835 35 23 $palette.muted
Rule $s 64 394 830
Txt $s "01  MAP 与 Robin 论文解读`n02  药物发现智能体的设计思路`n03  MAESTRO 最新进展与后续工作" 64 414 675 82 17 $palette.ink
Txt $s "2026.10.09`n修订资料截至 10.10" 745 440 170 45 12 $palette.muted
Notes $s "本次汇报分为三个独立部分。第一部分精读MAP与Robin，第二部分讨论对一般药物发现智能体的启发，第三部分单独总结MAESTRO。资料包括两篇论文、0927汇报和截至2026年10月10日的项目研究记录。附加研究任务文本作为方向参考，不代表本次执行的新实验。`n$mapcite`n$robincite"

# 02 MAP background
$s=Base 2 '论文一   MAP / 研究问题' '未测药物的单细胞响应预测' '核心问题：没有药物扰动谱时，如何预测它在目标细胞中的转录变化？' 'Feng et al., 2026, Fig. 1–3 / Methods'
Block $s '现有表示的不足' '药物 ID 只能记住已测分子。单独使用化学结构，也难以表达靶点、作用方向和细胞背景之间的关系。' 48 157 399 115
Block $s '研究任务' "输入：基础细胞状态、药物结构和剂量。`n输出：给药后的基因表达，以及相对基础状态的变化。" 503 157 409 115
Table $s @(
 @('评测任务','测试时缺少什么','留出与防泄漏'),
 @('未见细胞–药物组合','目标背景中的响应谱','每个背景留出 5% 配对，药物在其他背景出现'),
 @('未测药物','该药物的全部扰动谱','留出 5% 药物，同时移除图谱内实体、别名及相关边')
) 48 321 @(215,262,387) @(38,61,61)
Notes $s "MAP区分两种难度不同的泛化任务。组合外推允许训练集包含该药物在其他背景中的响应；未测药物外推移除该药物的全部响应，以及MAP-KG预训练中的相关实体、别名和边。推断时仍可使用药物结构与可用属性。模型学习f(x,p)，药物剂量也是输入。各数据集内部切分分别评测，不能把结果解释为跨数据集迁移。Tahoe评测使用选定的6条细胞系，而非全50条。OP3含6种免疫细胞和144种化合物，SciPlex3含3条癌细胞系和187种化合物。`n$mapcite"

# 03 MAP innovation
$s=Base 3 '论文一   MAP / 创新与知识预训练' '把机制关系写入药物和蛋白表示' '文本提供共同语义空间，对齐结构、蛋白序列、功能注释和有向关系。' 'Feng et al., 2026, Fig. 1a–b / Methods'
Picture $s 'map_knowledge.png' 40 154 520 283
Block $s '节点内部对齐' '以名称文本为基准，拉近分子结构、蛋白序列与功能描述，形成跨模态实体表示。' 590 156 322 87
Block $s '节点之间对齐' '将头实体、关系与尾实体按方向编码，用对比学习区分正确配对与批内负例。' 590 299 322 87
Txt $s '14 个公共资源     187,089 个药物     22,924 个基因     694,246 条关系' 48 456 864 28 17 $palette.green $true
Notes $s "MAP-KG整合13个数据库加PrimeKG，共14个公共资源。文本编码器是BioBERT，分子和蛋白编码器分别为MoleculeSTM与ESM-2。冻结后两者，并训练4层MLP适配器。节点规范表示来自名称文本。节点内对齐使名称嵌入接近结构/序列/属性文本。节点间对齐使用z_i→j=MLP([z_i,z_relation])与z_j←i=MLP([z_relation,z_j])，输入顺序保留方向和角色，采用对称InfoNCE，批内其他配对作为负例。这些关系提供机制相关归纳偏置，本身不证明药物因果机制。图来自论文Fig.1a–b。`n$mapcite"

# 04 MAP predictor
$s=Base 4 '论文一   MAP / 响应预测器' '知识表示与细胞状态共同预测转录响应' '知识预训练先提供分子与基因先验，监督训练再学习剂量和细胞背景下的响应。' 'Feng et al., 2026, Fig. 1c / Methods'
Picture $s 'map_predictor.png' 48 153 291 285
Block $s '输入融合' 'STATE SE-600M 提供细胞 token 与基因 token。基因 token 融合蛋白知识，药物嵌入按对数剂量缩放。' 387 156 525 81
Block $s '条件响应建模' '4 层自注意力 Transformer 联合处理药物、细胞和基因 token，再由 MLP 解码基因表达。' 387 272 525 70
Block $s '两层监督信号' '同时约束群体平均的扰动细胞嵌入与基因表达，减少“表示接近但表达错误”的情况。' 387 378 525 65
Txt $s 'L = MSE(扰动嵌入) + λ · MSE(基因表达)' 48 461 864 26 18 $palette.green $true
Notes $s "STATE SE-600M给出基因级token T和全局细胞token h。知识增强的蛋白嵌入与对应基因token融合。分子嵌入乘以经对数变换的剂量δ，得到剂量条件化表示。四层Transformer预测给药后的细胞嵌入，MLP解码到基因表达。损失分别计算预测/真实扰动嵌入的均方误差，以及预测/真实表达的均方误差，第二项有λ权重。两项监督建立在群体平均上，不能仅凭这些评测推断每个单细胞的完整分布都恢复准确。大量基因token还带来显存和计算成本。图来自论文Fig.1c。`n$mapcite"

# 05 MAP evidence
$s=Base 5 '论文一   MAP / 效果与证据边界' '未测药物预测的收益来自机制知识' '主要数字为 top-50 差异表达基因 Pearson Δ correlation，相对最强基线的提升。' 'Feng et al., 2026, Fig. 2–3, 5 / A549 ranking analysis'
Table $s @(
 @('数据集','未见组合','未测药物'),
 @('Tahoe（6 条细胞系）','+12.3%','+11.8%'),
 @('SciPlex3','+6.6%','+10.4%'),
 @('OP3','—','+19.8%')
) 48 163 @(251,126,143) @(40,56,50,50)
Block $s '消融支持知识贡献' 'MAP-KG 相对 PrimeKG 的 PDCorr 提高 11.4%。移除药物–基因关系造成最大下降。' 604 165 308 86
Block $s '计算筛选的可用性' 'A549 的 58 个留出候选中，5 个已批准 NSCLC 药物有 4 个进入前 15。' 604 305 308 78
Rule $s 48 414 864
Txt $s '转录响应与通路排序支持候选优先级。该 A549 分析属于计算筛选，后续仍需功能与药效实验。' 48 436 864 52 17 $palette.muted
Notes $s "所有百分比均为相对提升，不是百分点。实验同时评测top-2000高变基因、top-50差异表达基因、方向准确率、PDCorr、药物区分能力、MSE和Wasserstein。比较包括trainMean、chemCPA、CRISP、PRnet和XPert；STATE以药物类别ID表示，因而未纳入未测药物比较。MAP-KG相对PrimeKG带来PDCorr+11.4%、方向准确率+7.2%、区分能力+4.3%的报告收益。消融中药物–基因边最关键。A549分析基于预测转录谱、GSEA和文献作计算排序，58个留出候选中4/5个已批准NSCLC药物在前15，adagrasib第2、afatinib第4。这不是新湿实验验证。结果支持转录/通路候选筛选，不等价于靶点结合、因果机制或临床药效。`n$mapcite"

# 06 Robin background
$s=Base 6 '论文二   Robin / 研究问题' '科学发现需要连接假设、实验和新数据' '核心问题：智能体能否依据文献提出可检验假设，并用真实实验结果修正下一轮候选？' 'Ghareeb et al., 2026, Introduction / dAMD case study'
Block $s '已有系统的缺口' '文献问答和假设生成已有进展，但从原始数据分析到假设更新的衔接较弱。药物再利用还需要跨领域整合证据。' 48 170 405 119
Block $s '论文选择的疾病场景' '干性年龄相关性黄斑变性（dAMD）。视网膜色素上皮（RPE）功能下降，研究以增强吞噬功能为可测的干预方向。' 507 170 405 119
Rule $s 48 328 864
Txt $s '疾病目标需要先转换成一个实验可以回答的问题' 48 351 864 33 23 $palette.green $true
Txt $s '采用什么细胞模型和吞噬底物？怎样区分有效候选与测量背景？新数据支持保留还是修改机制假设？' 48 410 864 60 19 $palette.ink
Notes $s "Robin论文针对科学发现中假设生成、实验设计、执行后数据解读和后续假设更新的断点。干性AMD病例以RPE吞噬功能为干预策略：RPE清理光感受器外节与视网膜健康相关。选择这个读数使疾病目标转化为可检验的实验任务，但细胞吞噬增强并不证明改善患者疾病。Robin探索药物再利用，已知分子作用和跨领域文献为新候选提供根据。系统仍依赖专家提示、人类实验设计与执行，属于半自主发现流程。`n$robincite"

# 07 Robin architecture
$s=Base 7 '论文二   Robin / 多智能体分工' '检索智能体提出假设，分析智能体处理原始数据' '协调器管理任务，工具执行和可追溯证据承担关键工作。' 'Ghareeb et al., 2026, Fig. 1 / Agent architecture'
Picture $s 'robin_architecture.png' 42 151 388 332
Block $s 'Crow 与 Falcon：证据到候选' 'Crow 快速总结机制与实验读数。Falcon 深入分析候选、证据和局限，排序后交由研究者选择。' 474 157 438 86
Block $s 'Finch：原始数据到结论' '在 Jupyter 中执行流式和 RNA 分析。8 条独立分析轨迹保留代码与结果，再形成共识。' 474 280 438 81
Block $s '实验反馈推动下一轮' '研究者执行湿实验，系统据结果重审机制并提出下一批药物。8 条轨迹属于分析重复。' 474 403 438 66
Notes $s "Robin协调Crow、Falcon、Finch。Crow/Falcon基于PaperQA2，访问文献、临床试验和OpenTargets等资源。最初形成10个机制/实验报告，通过两两LLM比较选择实验，生成30个候选假设，再由Falcon评价并进行锦标赛式排序，人类选择并执行实验。Finch处理FCS与RNA计数，执行过滤、流式门控、统计、富集等操作。8条独立分析轨迹产生notebook并形成共识，属于对分析路径的重复，不是8个独立生物学重复。原始数据QC、门控和模型选择仍影响结论，共识降低路径波动但不能保证正确。图来自论文Fig.1。`n$robincite"

# 08 Robin biological evidence
$s=Base 8 '论文二   Robin / 生物学验证' '从 ROCK 抑制命中到 ripasudil 再利用假设' '第一轮实验结果和 RNA 分析共同推动第二轮候选更新。' 'Ghareeb et al., 2026, Fig. 3–4 / Human wet-lab validation'
Block $s '第一轮：建立实验和机制线索' 'ARPE-19 吞噬筛选命中 Y-27632。RNA 分析发现 ABCA1 约 3 倍上调，提示进一步考察 ROCK 相关机制。' 48 153 418 95
Block $s '第二轮：检验新候选' 'ripasudil 的吞噬读数为对照的 1.89 倍。原代 RPE-SC 配合牛视网膜外节验证，另有 KL001 命中。' 510 153 402 95
Picture $s 'robin_evidence.png' 48 283 602 184
Txt $s "验证层级`n细胞系筛选`n原代细胞复核`n剂量响应分析" 699 288 213 128 18 $palette.green $true
Txt $s '原代样本来自 1 位供者，孔重复不能代替供者重复。机制因果与临床效益仍待验证。' 699 416 213 74 15 $palette.muted
Notes $s "第一轮ARPE-19以pHrodo微球作底物，给药1h再吞噬3h，FCS分析排除碎片、双细胞、死细胞和背景。Y-27632为ROCK抑制剂命中。RNAseq中ABCA1约3倍上调，调整P=2.13e-83。反馈后提出已批准用于青光眼的ripasudil，ARPE-19吞噬读数1.89×vehicle，人类复分析为1.75×，均为相对对照的倍数。原代RPE-SC来自一位60岁以上供者，以牛光感受器外节（ROS）作更生理相关底物，n=4孔及剂量响应验证。KL001通过抑制CRY的泛素依赖降解稳定其蛋白，体现昼夜节律跨领域线索。ripasudil在RPE-SC有/无ROS条件下复制ABCA1变化，但尚未证明ABCA1对吞噬的必要性或充分性。图来自Fig.4b–c。`n$robincite"

# 09 Robin architectural evidence
$s=Base 9 '论文二   Robin / 系统效果与局限' '证据检索与代码执行带来可测的改进' '生物学案例之外，论文还对智能体组件进行消融和任务评测。' 'Ghareeb et al., 2026, Fig. 5 / Extended Data / BixBench'
Table $s @(
 @('评测','报告结果','能够支持的结论'),
 @('文献引用消融','o4-mini 虚构引用 44.5%\nCrow 检查样本未见虚构','检索和溯源提高引用可靠性'),
 @('BixBench，170 题','Finch 22.8%\n无工具 Sonnet 3.7 为 1.6%','代码工具和分析流程有增益'),
 @('发现过程时间','551 篇论文，约 30 分钟\n认知工作 <2 小时','作者估计节省人力时间')
) 48 157 @(209,309,346) @(39,72,72,72)
Txt $s '可复用贡献：把引用、notebook 和实验反馈留在证据链中。' 48 433 864 29 20 $palette.green $true
Txt $s '主要局限：专家提示与人工实验仍必要。单一疾病案例和任务子集，不能证明通用自主发现能力。' 48 472 864 25 15 $palette.muted
Notes $s "o4-mini替代检索代理时，实验方案的虚构引用率44.5±6.37%；Crow在检查的15份方案中未见虚构引用。该结果限于检查样本。Finch在BixBench选定170个相关问题、3次运行上为22.8±1.7%，无工具Sonnet3.7为1.6±1.2%；生物信息子任务15.3%、生物统计47.9%，绝对水平仍有限。论文自定义RNAseq/流式rubric为86%和100%，n=3，并不代表所有数据分析准确率。551篇文献约30分钟、人工359–424小时与智能体认知工作小于2小时属于作者估计，未进行受控时间基准。系统仍欠缺完整可执行实验协议，专家输入、人类湿实验和后续因果/临床验证不可缺。`n$robincite"

# 10 generic MAP idea
$s=Base 10 '方法启发   药物发现智能体 / 知识表示' '机制知识可以约束候选生成与模型外推' '可采纳的设计思路：让每个候选携带结构化机制证据，再进入预测和筛选。' '设计建议，依据 MAP；尚需独立评测'
Table $s @(
 @('知识对象','智能体如何使用','进入系统的条件'),
 @('分子结构与已知作用','检索近邻、补充候选解释\n支持新分子的响应预测','统一实体与别名，记录来源'),
 @('有方向的药物–靶点关系','区分抑制和激活\n形成可反驳的机制假设','保留作用方向、条件与证据等级'),
 @('基因功能与细胞背景','判断靶点是否在目标背景有效\n选择预期变化的通路或读数','绑定细胞、剂量、时间和测量类型')
) 48 159 @(220,345,299) @(39,70,70,70)
Txt $s '知识表示解决“如何外推”，检索证据支持“为何提出该候选”。两者可共用来源，但需要分别评测。' 48 438 864 52 18 $palette.green $true
Notes $s "本页为面向一般药物发现智能体的设计建议，与任何特定项目实现无关。MAP启发在于机制知识可进入表征学习，也可供智能体查询，但不能把知识嵌入的训练收益直接当作LLM推理收益。可采用带实体、关系方向、物种/细胞背景、剂量时间、证据等级及原始引用的记录，避免把‘与某疾病相关’直接升级成药物机制。候选输出同时包含预测效应、支持证据和可能反例。检索到已知靶点只证明信息检索能力；新药物外推需从图谱与响应数据中同时留出候选及相关信息，验证避免泄漏。`n$mapcite"

# 11 generic Robin idea
$s=Base 11 '方法启发   药物发现智能体 / 实验闭环' '功能读数驱动的候选更新' '可采纳的设计思路：沿用 Robin 的角色分工，用可执行工具把假设接到实验。' '设计建议，依据 Robin；实验执行与审核仍需研究者'
Table $s @(
 @('阶段','交付内容','接受或退回的标准'),
 @('疾病与读数检索','疾病机制证据，适用的实验模型','读数与疾病目标相关，条件明确'),
 @('候选与实验设计','有引用的机制假设、阳性/阴性对照','候选可检验，区分竞争解释'),
 @('实验数据分析','原始数据、QC、代码、效应与区间','分析可复现，实验单位统计正确'),
 @('下一轮候选更新','保留、淘汰或修改的具体理由','更新来自新证据，记录失败结果')
) 48 160 @(217,337,310) @(39,57,57,57,57)
Txt $s '例：预测某药提高吞噬功能，同时检验细胞死亡、荧光背景与独立供者，排除“读数升高”的替代解释。' 48 449 864 45 17 $palette.green $true
Notes $s "本页是一般系统方案。Robin提示不能以文献报告作为闭环终点。先把疾病目标操作化为适当的功能读数，再以检索、候选评价、实验执行和可复现分析相接。分析角色需要代码执行、版本化原始数据和明确QC，而非单纯对结果表进行语言总结。流式吞噬例子需排除存活、背景荧光等混杂，生物学重复以独立培养/供者为单位。可重复运行不同分析路径以发现敏感性，但共识不能替代外部验证。下一轮每次更新都应指明导致更新的新观察和竞争假设。`n$robincite"

# 12 generic integration
$s=Base 12 '方法启发   药物发现智能体 / 联合评测' '预测收益、知识收益与决策收益分别验证' '两篇论文可组合成“知识预测 + 实验反馈”方案，效果需要通过有归因的比较建立。' '拟议评测方案；方法依据 MAP 与 Robin'
Table $s @(
 @('需要回答的问题','比较设计','主要读数'),
 @('机制知识是否帮助外推？','结构模型、完整知识、打乱关系\n严格留出药物与关联图谱信息','响应误差与方向准确率'),
 @('转录预测是否帮助选药？','实测响应上限、廉价先验、预测响应\n在匹配的功能实验中比较','候选命中率、效应与区间'),
 @('智能体是否值得引入？','同数据、工具、候选菜单和预算\nLLM 与确定性策略比较','有效命中、错误行动及总成本')
) 48 162 @(233,373,258) @(39,74,74,74)
Txt $s '进入实验前的输出：候选、预期效应、证据来源、反证条件、成本和停止规则。' 48 449 864 34 19 $palette.green $true
Notes $s "本页是独立的通用药物发现智能体评测建议。完整链路可以以MAP类型表征产生响应与不确定性，以Robin类型代理生成可检验实验并分析反馈。评测需分离：知识是否提供超出结构/近邻的信号，转录预测是否提供超出廉价先验的功能读数收益，LLM策略是否超出确定性同工具策略。首先用真实响应作为预测上限，判断在该端点下转录信息是否存在足够收益，再投入复杂模型。使用相同数据、工具权限和预算，计入无效实验、错误筛选、工具失败、延迟与成本。实验重复与独立生物学单位需分清，停止规则提前约定。`n$mapcite`n$robincite"

# 13 MAESTRO progress
$s=Base 13 '阶段总结   MAESTRO / 0927 之后的进展' '运行闭环、数据坐标和采购效率已有实质推进' '0927 的主要限制是选择优势与有效独立样本不足。后续先补齐可执行和可复核的基础。' '项目记录：research/REPORT.md；EVIDENCE.md；log/20261010/P05R_EXTENSION.json'
Table $s @(
 @('推进方向','截至 10.10 的结果','形成的能力'),
 @('运行闭环','验证两轮工具与测量反馈\n支持持久化、预算、重试和重启','真实调用链可追踪和复现'),
 @('端点坐标认证','c44、c45 均唯一匹配 39/39 基因\n对照全部 62,710 个源基因','指定文件中的端点身份明确'),
 @('采集与采购效率','c45 新增 133,564 表达字节，减少 60.7%\nV3 预采购停止：129 次减少至 35 次','更少数据完成认证\n减少不会使用的购买')
) 48 160 @(182,425,257) @(39,70,70,86)
Txt $s '坐标结果属于文件内身份认证，采购节省来自匹配动作保持一致的模拟。二者为后续评测降低成本。' 48 454 864 41 16 $palette.muted
Notes $s "独立MAESTRO部分从0927进度出发。0927中76–82%的L1000案例在动作菜单下难以区分，+2百分点检出所需独立单位345–813，现有42–256或外部38，未形成稳定决策优势。当前运行合同覆盖agent–decision–virtual-cell实际路由、两轮测量反馈、持久化、预算、重试、幂等与重启，证明工程能力。P0.5R扩展在c44/c45对全部62,710源基因完成39/39唯一坐标匹配，容差1e-5，最大差1.4416e-7/1.4611e-7。c44复用252已暴露细胞，新增RNA字节为0；c45获取11个区分细胞、133,564新表达字节，相对旧340,068字节方案减少60.7%。独立逻辑切片/块状算术复核一致。这不认证完整2000基因轴或模型解码轴。V3预采购停止把A购买129降到35，减少94次即72.9%，匹配动作不变；总模拟profiles774降到680，无更新为645，不能据此声称净决策优势。"

# 14 MAESTRO phenotype
$s=Base 14 '阶段总结   MAESTRO / 10.10 表型读数研究' 'G1 组成读数出现可量化的预测信号' '同一球状培养单元的 24 h RNA 与表型读数，覆盖 5 个 checkpoint 留出背景、379 种药物。' '项目记录：research/astra/phenotype_anchor_20261010/RESULTS.json 与 PROTOCOL.md'
Txt $s '+0.254 r' 48 160 388 62 42 $palette.green $true
Txt $s '预测细胞 G1 组成 vs 基础相似性方法' 48 235 422 30 18 $palette.ink $true
Txt $s "平均相关系数 0.350 vs 0.096`n95% CI [0.156, 0.367]，4/5 背景更好`n这是由 RNA 推导的细胞周期组成。" 48 282 422 103 17 $palette.ink
Txt $s '+0.558 log₂' 515 160 397 62 42 $palette.blue $true
Txt $s '基础相似性迁移的生存选择效用' 515 235 397 30 18 $palette.ink $true
Txt $s "top-10 相对通用药物强度排序的提升`n95% CI [0.235, 0.819]，5/5 背景更好`n支持利用廉价先验改善该任务的排序。" 515 282 397 103 17 $palette.ink
Rule $s 48 416 864
Txt $s '按端点决定模型准入：生存选择性主分析中 STATE 较基础方法 Δr = −0.226，当前未准入。' 48 434 864 28 17 $palette.muted
Txt $s '已有背景暴露与先验重叠，当前结果仍属于开发研究；G1 信号尚未建立独立生物确认或总体决策收益。' 48 470 864 24 14.5 $palette.muted
Notes $s "10月10日研究在Tahoe相同球状培养单元中连接24h RNA与obs推导相对细胞系份额/相位。40个合格参考背景，5个checkpoint留出背景Hs766T、PANC1、C32、HepG2/C3A、HOP62，药物菜单379。E2中S_cells（预测细胞的G1组成）平均r=0.3495417，基础相似性B为0.0959951，差0.2535466，CI[0.1564786,0.3672753]，4/5更好。它是RNA推导的周期组成，与独立存活率或凋亡确认不同。E1中基础相似性迁移的top10平均效用相对通用强度排序+0.5580816 log2，CI[0.235,0.819]，5/5更好。主要STATE核读数平均r=0.0722125，B为0.2984267，差−0.2262142，0/5更好。参考真实RNA上限相对基础方法仅+0.0029597 r，低于预定0.05最小有用收益，因此门控拒绝STATE进入该端点。目标背景先前已暴露，参考背景与预训练重叠。本研究提升了端点桥接和模型准入规则的清晰度，未确立知识反馈或LLM决策优势。"

# 15 MAESTRO next
$s=Base 15 '阶段总结   MAESTRO / 后续工作' '观测可靠性与知识反馈的下一阶段评测' '39 个端点坐标的认证，为下一阶段观测可靠性研究补齐了指定文件的前置条件。' '下一阶段为拟议工作；P0.6 尚未放行执行，P2 仍关闭'
Table $s @(
 @('后续任务','具体工作','验收依据'),
 @('新冻结 P0.6 协议','固定源版本、端点、排除规则\n处理/对照、真实样本数与共享对照','重复来源的误差估计与精确采集成本'),
 @('借鉴 MAP 的知识先验','按关系类型选择有效知识\n比较结构、完整知识和打乱知识','在同条件留出任务上有增益'),
 @('借鉴 Robin 的证据反馈','检索保留引用，分析保留代码\n从功能读数生成可反驳的下一轮假设','相同工具和预算下减少错误选择')
) 48 161 @(214,365,285) @(39,76,76,76)
Txt $s '优先级：可靠观测与端点资格在前，预测和策略评测随后。论文方法的实际收益仍需分别验证。' 48 449 864 43 18 $palette.green $true
Notes $s "未来可以在MAESTRO中选择性借鉴论文，但这是待实施/待评测方向。当前合格任务是重新冻结P0.6观测可靠性协议：绑定精确源修订、端点坐标、排除、处理/对照行、实际组大小、参考权重、共享对照的不确定性、来源重复估计对象与确切采集成本，之后才读取表达。24个细胞系/板分层实际是12个pooled样本，不能当24个独立培养。全局24h暴露有记录，但逐样本时间与第三确认源缺失。c44/c45身份认证不解锁旧c40/c44计划，不认证完整2000基因轴，P0.6执行未放行、P2仍关闭。MAP方向宜先考察特定关系类型和端点是否有效，当前泛化融合/反馈比较未证明稳定优势。Robin方向宜保留引用、可执行分析和负结果，以同信息、同工具、同预算确定性策略为比较，未来在未触碰合格生物单位上评测终局选择、损害和成本。当前证据支持工程和测量基础推进，独立知识反馈与LLM科学决策收益尚未建立。"

# Convert intentional table line breaks.
foreach($slide in $deck.Slides) {
 foreach($shape in $slide.Shapes) {
  if($shape.HasTable) {
   for($i=1;$i -le $shape.Table.Rows.Count;$i++) { for($j=1;$j -le $shape.Table.Columns.Count;$j++) {
    $range=$shape.Table.Cell($i,$j).Shape.TextFrame.TextRange; $range.Text=$range.Text.Replace('\n',"`n")
   } }
  }
 }
}
$deck.SaveAs((Join-Path $outDir '1009.pptx'))
$deck.SaveAs((Join-Path $assetDir '1009-white-preview.pdf'),32)
$fit=@()
foreach($slide in $deck.Slides) { foreach($shape in $slide.Shapes) {
 if($shape.HasTextFrame -and $shape.TextFrame.HasText) {
  $fit+= [pscustomobject]@{slide=$slide.SlideIndex; text=$shape.TextFrame.TextRange.Text; height=$shape.Height; bound=$shape.TextFrame.TextRange.BoundHeight; top=$shape.Top}
 }
 if($shape.HasTable) { for($i=1;$i -le $shape.Table.Rows.Count;$i++) { for($j=1;$j -le $shape.Table.Columns.Count;$j++) {
  $cellshape=$shape.Table.Cell($i,$j).Shape
  $fit+= [pscustomobject]@{slide=$slide.SlideIndex;text=$cellshape.TextFrame.TextRange.Text;height=$cellshape.Height-12;bound=$cellshape.TextFrame.TextRange.BoundHeight;top=$cellshape.Top}
 } } }
} }
$fit|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $assetDir 'fit.json') -Encoding utf8
$deck.Close(); $app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck)|Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)|Out-Null
Write-Output (Join-Path $outDir '1009.pptx')
