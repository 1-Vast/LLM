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

function Link($s,$x1,$y1,$x2,$y2,$color=$palette.green,$arrow=$true){$sh=$s.Shapes.AddLine($x1,$y1,$x2,$y2);$sh.Line.ForeColor.RGB=(RGB $color);$sh.Line.Weight=1.5;if($arrow){$sh.Line.EndArrowheadStyle=3}}
function Node($s,$title,$body,$x,$y,$w,$h){
 $sh=$s.Shapes.AddShape(1,$x,$y,$w,$h);$sh.Fill.ForeColor.RGB=(RGB $palette.pale);$sh.Line.ForeColor.RGB=(RGB $palette.line)
 Txt $s $title ($x+12) ($y+10) ($w-24) 27 18 $palette.green $true
 Txt $s $body ($x+12) ($y+45) ($w-24) ($h-49) 17
}
function Bar($s,$x,$y,$w,$h,$color){$sh=$s.Shapes.AddShape(1,$x,$y,$w,$h);$sh.Line.Visible=0;$sh.Fill.ForeColor.RGB=(RGB $color)}

# 01
$s=$deck.Slides.Add(1,12);$s.FollowMasterBackground=0;$s.Background.Fill.Solid();$s.Background.Fill.ForeColor.RGB=(RGB $palette.white)
Txt $s '1009   组会论文汇报' 58 48 830 25 14 $palette.green $true
Txt $s "未测药物的响应预测`n与实验驱动的科学发现" 58 143 842 132 40 $palette.ink $true
Txt $s 'MAP 与 Robin：研究背景、已有进展、方法与实验验证' 60 300 835 36 22 $palette.muted
Rule $s 60 379 840
Txt $s "01  MAP：知识预训练与新药物响应预测`n02  Robin：文献假设、数据分析与两轮实验`n03  通用方法设计与 MAESTRO 阶段总结" 60 405 820 91 17
Notes $s "汇报日期沿用1009，项目资料截至2026-10-10。两篇论文各用5页解释背景与已有进展、具体缺口、方法、实验与本篇推进。方法启发2页与MAESTRO2页相互独立。所有应用设计标注为建议。`n$mapcite`n$robincite"


# 02
$s=Base 2 '论文一   MAP / 研究背景与已有进展' '响应预测已能利用分子结构，未测药物仍难外推' '研究对象：给定细胞背景、药物和剂量，预测给药后各基因的表达变化，为候选筛选提供信息。' 'Feng et al., 2026, Introduction / Methods；背景按论文相关工作概括'
Txt $s '已有研究逐步补齐了什么？' 48 157 408 27 20 $palette.green $true
Block $s '① 实测扰动图谱' '单细胞测序记录药物处理后的响应，提供细胞背景与药物效应的训练样本；但测量组合仍然稀疏。' 48 204 408 62
Block $s '② 分子条件化预测' 'chemCPA 等方法引入结构表示，使新分子可以被编码，缓解“药物只有类别 ID”的限制。' 48 313 408 62
Block $s '③ 单细胞基础表示' 'STATE 等模型提供细胞与基因表征，增强细胞状态建模；新药物的作用关系仍需额外信息。' 48 414 408 48
Txt $s '这些进展留下的关键缺口' 508 157 404 27 20 $palette.blue $true
Txt $s '新分子能被编码，响应为何仍难预测？' 508 210 404 58 21 $palette.ink $true
Txt $s '结构表示提供化学特征，但不显式约束它作用于哪些靶点、是抑制还是激活，以及与哪些基因功能相关。稀疏响应数据难以独自补齐这些关系。' 508 294 404 108 18
Rule $s 508 414 404
Txt $s 'MAP 的切入点：先用公共知识学习机制相关的药物／蛋白表示，再学习细胞条件下的响应。' 508 432 404 60 18 $palette.green $true
Notes $s "论文题目：A knowledge-driven framework for predicting single-cell responses for unprofiled drugs。`n本页先讲研究发展，再定位论文缺口，避免把任务定义当作创新。单细胞药物扰动图谱使研究者有数据学习药物对细胞的影响，但全药物×细胞×剂量空间不可能都被测量。只使用类别ID的方法依赖训练中见过的药物；分子条件化方法例如chemCPA通过结构编码让未测分子至少拥有表示，这是已有进展。另一方面，STATE类型基础模型提供细胞与基因上下文。两条路线分别加强分子和细胞表示，却没有自动建立药物–靶点作用类型与蛋白功能之间的关系。论文提出将这些公共关系用于知识预训练，使结构表示具有机制相关的归纳偏置。需要强调：结构模型并非完全没有生物信息，而是其仅靠响应监督难以系统约束机制。所谓最新进展在本次汇报中指这篇2026论文报告的推进，不代表实时检索后的领域排名。`n$mapcite"


# 03
$s=Base 3 '论文一   MAP / 核心思想与总体流程' '把机制知识先学进表示，再预测细胞响应' '核心思路：用大量公共实体与关系补充稀缺的扰动监督；知识预训练与响应训练承担不同任务。' 'Feng et al., 2026, Fig. 1 / Methods'
Node $s '阶段一：知识预训练' '名称、结构、蛋白序列、功能注释与有向关系' 48 160 260 118
Node $s '知识增强的实体表示' '同一实体的多模态对应；药物–基因作用关系' 355 160 259 118
Node $s '阶段二：响应训练' '融合细胞状态与剂量，用已测处理群体监督' 661 160 251 118
Link $s 308 217 355 217
Link $s 614 217 661 217
Txt $s '预测时：对照细胞 x + 新药物结构 + 剂量  →  给药后表达 x̂  →  相对对照的响应 Δx̂' 48 301 864 51 19 $palette.green $true
Rule $s 48 366 864
Block $s '未见组合：考察配对泛化' '药物在其他背景已测，目标细胞–药物配对留出；每个背景留出 5% 配对。' 48 387 410 64
Block $s '未测药物：考察分子外推' '整种药物的响应全部留出；知识预训练也移除其实体、别名和关联边，避免记住测试对象。' 508 387 404 64
Notes $s "第一阶段回答：不依赖目标药物的扰动实验，能否通过公共属性与关系学习对新分子可用的表示？第二阶段回答：已知细胞状态、剂量和机制相关分子表示后，如何把条件映射成转录响应？阶段一采用跨模态与关系对比学习，阶段二采用监督预测。预测输入的药物可以由结构编码，不要求存在训练药物的类别ID。scRNA-seq是破坏性测量，处理与对照通常为不同细胞群体，因此这里比较处理群体与预测群体，而非观测同一个细胞给药前后的真实轨迹。两类评测任务很关键：未见组合允许药物在其他背景出现；未测药物移除所有响应，并在MAP-KG预训练时去除实体、别名和关联边。二者难度与信息条件不同。各数据集内部训练/留出，并不是跨数据集直接迁移。知识表示提供归纳偏置，实际细胞响应仍需监督训练，不能将图谱关系当成细胞内已经验证的因果。`n$mapcite"


# 04
$s=Base 4 '论文一   MAP / 方法一：知识预训练' '如何把结构、功能与靶点关系学进同一表示' 'MAP-KG 整合 14 个资源：187,089 个药物、22,924 个基因、694,246 条关系。' 'Feng et al., 2026, Fig. 1a–b / Methods, equations 2–5'
Picture $s 'map_knowledge.png' 45 151 406 221
Txt $s '跨模态编码器' 48 390 402 25 18 $palette.green $true
Txt $s "名称与注释：BioBERT`n结构：MoleculeSTM；蛋白序列：ESM-2`n后两者冻结，训练 4 层 MLP 适配器。" 48 420 402 71 17
Block $s '① 节点内：同一个实体的属性对齐' '以名称文本 zᵢ 为规范表示，拉近结构、蛋白序列和功能描述。同一实体是正例，批内其他实体是负例。' 493 158 419 78
Block $s '② 节点间：关系条件化的邻居对齐' '先编码“抑制”等关系 r，再用有序拼接区分源实体与目标实体，让表示保留作用方向。' 493 283 419 66
Txt $s '例：二甲双胍 —抑制→ MT-ND1' 493 364 419 22 15 $palette.muted
Txt $s "zᵢ→ⱼ = MLP([zᵢ, zᵣ])`nzⱼ←ᵢ = MLP([zᵣ, zⱼ])" 493 390 419 65 20 $palette.blue $true
Txt $s '对比学习（InfoNCE）拉近正确配对、区分错误配对，为新分子响应预测提供机制相关先验。' 493 456 419 38 15.5 $palette.muted
Notes $s "第一阶段知识预训练不需要细胞扰动响应。MAP-KG有428,192条药物–基因边与266,054条基因–基因边。节点规范嵌入来自实体名称文本BioBERT。MoleculeSTM与ESM-2冻结，4层MLP适配。节点内正例为该实体结构、序列或描述，节点间正例为其关系条件化邻居表示。关系编码z_r=BioBERT(r)，MLP的拼接顺序保留头/尾角色。双向InfoNCE对一批配对(z_i,z'_i)优化：L=-mean_i{log[exp(sim(z_i,z'_i)/tau)/sum_k exp(sim(z_i,z'_k)/tau)] + log[exp(sim(z_i,z'_i)/tau)/sum_k exp(sim(z_k,z'_i)/tau)]}。直观解释是识别正确的实体属性/关系配对，形成跨模态且机制相关的几何邻域。关系角色的编码构成归纳偏置，不能把图谱中的关联自动升级为因果证据。图来自论文Fig.1a–b。`n$mapcite"


# 05
$s=Base 5 '论文一   MAP / 方法二：条件响应预测' '相同药物为何在不同细胞中产生不同响应？' '细胞提供背景，蛋白知识提供基因功能，药物与剂量提供扰动条件，模型联合学习它们的作用。' 'Feng et al., 2026, Fig. 1c / Methods, equations 6–12'
Picture $s 'map_predictor.png' 48 151 290 273
Block $s '① 输入：细胞状态与基因功能' 'STATE SE-600M 编码 x，得到全局细胞 token h 与基因 token T。MLP 融合 T 和对应蛋白知识。' 378 154 534 65
Block $s '② 建模：条件之间如何相互影响' '分子编码得到 zₘₒₗ，按对数剂量 δ 缩放。4 层 Transformer 联合处理 [δzₘₒₗ, h, T融合]。' 378 264 534 64
Block $s '③ 输出与监督：给药后的表达' 'MLP 把 ĥ⁽ᵖ⁾ 解码为表达 x̂⁽ᵖ⁾。同时匹配处理群体的平均表达和平均细胞嵌入。' 378 362 534 57
Txt $s 'L = ‖mean(ĥ) − mean(h)‖² / d + λ · ‖mean(x̂) − mean(x)‖² / G' 48 461 864 29 18 $palette.green $true
Notes $s "T,h=STATE(x)，h来自SPECIAL token。T_fuse=MLP([T,Z_seq])，对应基因序列/知识按身份对齐。药物结构z_mol乘以施加剂量的log变换δ，Transformer输入[δ z_mol,h,T_fuse]，取细胞位置输出h_hat，再由MLP解码表达x_hat。表达预处理限定19,790人类蛋白编码基因、总UMI归一化到10,000再log1p，STATE输入为每细胞高表达的2,048基因token，并采用软分箱。双损失匹配真实处理群体均值：嵌入误差除以d，表达误差除以G，λ权衡。真实扰动群体先由STATE编码形成嵌入监督。群体均值损失可减少噪声，却不保证完整单细胞分布或每个细胞的真实轨迹。模型输入药物是SMILES，因而对新分子可以计算嵌入，无须药物类别ID。图来自Fig.1c。`n$mapcite"


# 06
$s=Base 6 '论文一   MAP / 实验、结果与本篇进展' '严格留出新药物后，机制知识仍改善响应预测' '实验问题：未测分子的变化能否预测？哪些知识有贡献？预测响应是否有助于候选排序？' 'Feng et al., 2026, Fig. 2–5 / Methods；图表为论文数字重绘'
Txt $s '怎么验证“预测了药物效应”？' 48 152 470 26 19 $palette.green $true
Txt $s 'Pearson Δ = corr(预测均值−对照均值, 实测均值−对照均值)。先减对照，避免基础表达掩盖响应误差。' 48 193 470 67 17
Txt $s '相对最强基线的提升：50 个差异表达基因' 48 276 470 24 17 $palette.ink $true
$bars=@(@{name='Tahoe';value=11.8;y=317},@{name='OP3';value=19.8;y=367},@{name='SciPlex3';value=10.4;y=417})
foreach($b in $bars){Txt $s $b.name 48 $b.y 112 25 17;Bar $s 161 ($b.y+1) ($b.value*11) 23 $palette.green;Txt $s ('+'+[string]$b.value+'%') (174+$b.value*11) $b.y 86 26 17 $palette.green $true}
Txt $s 'Tahoe：6 条选定细胞系；OP3：6 种免疫细胞；SciPlex3：3 条癌细胞系。均为数据集内部留出。' 48 459 470 37 13.5 $palette.muted
Block $s '消融回答：机制关系有没有用？' 'MAP-KG 比 PrimeKG 的 Pearson Δ 高 11.4%；去掉药物–基因边下降最大，支持靶点关系的贡献。' 576 153 336 69
Block $s '应用回答：能否辅助候选排序？' 'A549：预测表达 → 通路富集 → 排序。58 个留出候选中，4/5 个已批准 NSCLC 药物进入前 15。' 576 269 336 76
Block $s '本篇推进与尚未解决的问题' '推进：机制知识增强未测分子的转录外推。边界：计算排序尚未经新药效实验验证；群体均值准确不保证单细胞分布准确。' 576 388 336 80
Notes $s "评测在Tahoe六条选定细胞系（原图谱50条、379药）、OP3六种免疫类型144化合物及SciPlex3三条癌系187化合物内部进行。比较trainMean、chemCPA、CRISP、PRnet、XPert，STATE的ID型表示不用于未测药物任务。Pearson delta比较相对对照的表达变化；还评估方向准确率、药物区分度、MSE与Wasserstein，基因集合有top50 DEG和top2000 HVG。三个未测药物相对最强基线提升分别11.8%、19.8%、10.4%，是相对百分比而非百分点。SciPlex3、OP3平均r分别0.827、0.861。组合外推Tahoe+12.3%、SciPlex3+6.6%。MAP-KG比PrimeKG PDCorr+11.4%，去掉药物–基因边最受损，支持关系贡献，但比较也可能受知识规模影响，若归因知识质量还需同规模对照。A549通过预测转录谱和GSEA进行计算筛选，58候选中4/5已批NSCLC药进入前15，adagrasib第2、afatinib第4。这是计算可用性证据，没有新的药效湿实验。论文推进的是新分子的转录响应外推，不是证明临床发现成功。`n$mapcite"


# 07
$s=Base 7 '论文二   Robin / 研究背景与已有进展' '科学智能体已能提出假设，实验结果如何改变假设？' '研究对象：药物再利用。论文以干性年龄相关性黄斑变性（dAMD）的 RPE 吞噬功能为案例。' 'Ghareeb et al., 2026, Introduction / Fig. 1–2 / Discussion'
Block $s '已有进展：从问答走向研究辅助' '文献智能体能检索、整合跨领域信息；假设生成系统能提出候选；代码工具使模型能够参与科学数据分析。' 48 156 410 89
Block $s '仍有断点：报告之后怎样继续？' '文献依据不足以判断候选是否有效。原始数据分析、机制解释与下一轮假设更新常被分开，缺少真实实验串联的验证。' 48 302 410 89
Txt $s 'Robin 的切入点：让检索与分析分工协作，围绕真实实验反馈连续推进候选。' 48 439 410 54 18 $palette.green $true
Txt $s '把疾病需求转成可检验的功能目标' 508 156 404 27 20 $palette.blue $true
Txt $s 'RPE：视网膜色素上皮，清理光感受器外节。论文选择增强其吞噬功能，寻找已有药物的新用途。' 508 204 404 76 18
Picture $s 'robin_assay.png' 508 294 404 113
Txt $s '给药 1 h，底物孵育 3 h。流式平均荧光强度（MFI）反映酸性溶酶体信号，按 DMSO 溶剂对照归一化。' 508 426 404 66 17
Notes $s "论文题目：A multi-agent system for automating scientific discovery。`n与MAP不同，本篇不训练药物响应预测器，而是组织科学发现的工作过程。已有文献问答、跨领域证据整合与假设生成系统扩展了模型在科研中的用途；代码执行又提供数据分析能力。论文关心的缺口是这些能力如何连接：候选必须接受实验检验，原始数据需要质量控制和可执行分析，新的观察应能推动下一轮假设。Robin不是只输出一份研究建议，而是在dAMD药物再利用中完成两轮实验反馈案例。RPE吞噬光感受器外节有助于维持视网膜健康，研究选择增强吞噬作为疾病相关、可测的目标，但功能改善不自动等同于患者获益。初筛人类选用ARPE19和pHrodo微球，给药1h、底物3h，底物进入酸性环境发光，流式MFI反映其信号。后面需要排除死细胞、背景和模型局限。研究者制定协议并执行湿实验，因此应描述为部分自动化、实验反馈驱动的发现过程。`n$robincite"

# 08
$s=Base 8 '论文二   Robin / 系统创新与方法流程' '检索形成可测试候选，执行分析推动下一轮更新' '创新在工作衔接：有来源的假设、可运行的数据分析与真实实验反馈共同构成发现过程。' 'Ghareeb et al., 2026, Fig. 1 / Methods: Robin and Finch implementation'
Node $s 'Crow：机制检索' '机制与实验模型报告' 48 154 193 94
Node $s 'Falcon：审查候选' '药理证据与局限' 271 154 193 94
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
Txt $s 'BTL：P(i 胜 j) = sᵢ / (sᵢ + sⱼ)' 48 442 410 27 18 $palette.blue $true
Txt $s 's：候选的相对偏好强度，由成对评审拟合' 48 477 410 20 13.5 $palette.muted
Block $s '如何从原始数据形成可复核结论？' 'Finch 用 edit_cell 编写并执行代码，8 条独立分析轨迹后综合结论；保留 notebook，使 QC、统计与结果可以追查。' 508 314 404 88
Txt $s '名次衡量文献依据；药效由实验检验。8 条分析轨迹检查分析一致性，不能当作 8 个生物学重复。' 508 448 404 46 15 $palette.muted
Notes $s "Crow和Falcon采用PaperQA2检索文献，也访问临床试验及OpenTargets。Crow快速回答疾病、机制、测量方法，Falcon对候选深入评价药理依据与局限。Robin协调器基于o4-mini，成对裁判为ClaudeSonnet3.7。先形成10份机制/实验报告，再排序选择实验方向、生成30个假设，以Falcon报告评估，研究者审核选择并执行实验。最多25项时比较所有配对，否则随机300对；BTL把成对偏好拟合为相对强度s，概率为s_i/(s_i+s_j)，排序不表示实测效应。Finch接受原始FCS或RNA数据，在Jupyter用edit_cell修改并执行代码，以submit_answer提交结论。8条独立分析轨迹的共识有助于发现分析一致性，却受相同模型、提示和数据的共同偏差约束，不能代替独立培养或供者。新观察返回协调器构成下一轮输入。图中人类湿实验环节不可省略。论文创新是把这些环节在真实案例中接起来，代理数量本身不是科学发现有效性的证明。`n$robincite"

# 09
$s=Base 9 '论文二   Robin / 第一轮实验与原始数据分析' '第一轮：功能命中如何变成下一步机制问题？' '初筛从排序中测试前 5 个候选，MFGE8 作为已知吞噬促进的阳性参照。' 'Ghareeb et al., 2026, Fig. 2c–f / Fig. 3 / RPE phagocytosis assay'
Picture $s 'robin_volcano.png' 48 157 374 266
Txt $s '横轴为 log₂FC，纵轴为 −log₁₀P。红色表示上调，蓝色表示下调。' 48 440 374 54 16 $palette.muted
Block $s '① 流式确认功能命中' 'Finch 去除碎片、双细胞和 DAPI 阳性死细胞，比较 MFI 与 DMSO。Y-27632 的吞噬增强由人工复分析确认。' 471 155 441 72
Block $s '② 命中推动后续 RNA-seq' '既有机制是 ROCK 抑制调节肌动蛋白。新数据发现 ABCA1 约 3 倍上调，并富集肌动蛋白、小 GTP 酶和自噬相关程序。' 471 282 441 77
Block $s '③ 分析生成下一步假设' 'ABCA1 编码脂质外排泵，连接脂质稳态与 RPE 功能。它提供可检验机制线索，尚需干预实验建立因果。' 471 407 441 55
Notes $s "第一轮前五候选为exendin4、fingolimod、MFGE8、Y27632、AICAR与TUDCA组合，MFGE8有既有吞噬增强证据作为阳性参照。系统最初建议ROS与原代/干细胞分化RPE，但人类选择更易获得微球和ARPE19加速验证。FCS通过FSC/SSC排碎片，FSC-A/H选单细胞，DAPI排死细胞，再比较归一化MFI。n3孔，Dunnett检验对DMSO。Y27632命中、人类同数据分析支持后，Robin提出RNAseq。Finch差异与GO分析显示细胞骨架、小GTP酶和自噬相关转录变化；8路径中超过50%识别相同显著DEG。ABCA1约3倍上调，调整P=2.13e-83，编码脂质外排泵，可能连接吞噬后的脂质处理与RPE健康。火山图来自Fig.3b。批量RNA结果是机制关联，应通过敲低/救援及功能复测检验ABCA1必要/充分性，此类实验是建议而非论文已完成。`n$robincite"


# 10
$s=Base 10 '论文二   Robin / 第二轮候选与验证' '第二轮：从研究化合物推进到获批药物再利用' 'ripasudil 是已获批治疗青光眼的 ROCK 抑制剂。研究者测试第二轮 10 种候选，再用原代细胞复核。' 'Ghareeb et al., 2026, Fig. 4 / RPE-SC validation'
Picture $s 'robin_evidence.png' 48 158 513 186
Txt $s 'ARPE-19：ripasudil 的 MFI 为对照 1.89 倍' 48 363 513 31 19 $palette.green $true
Txt $s '剂量响应曲线支持更高效力。人工复分析为 1.75 倍，均为相对 DMSO 的倍数。' 48 411 513 64 17
Block $s '模型升级：原代 RPE-SC + ROS' '从 1 位 >60 岁供者获得细胞，以牛光感受器外节替代微球。ripasudil 与 Y-27632 再次命中（n=4 孔）。' 607 157 305 92
Block $s '跨领域线索：KL001 也命中' '昼夜节律调控启发候选。KL001 稳定 CRY 蛋白，抑制其泛素依赖降解。ABCA1 上调也在原代细胞复现。' 607 315 305 92
Txt $s '证据推进到细胞模型、底物和剂量复核。单供者的孔重复不足以证明人群泛化，ABCA1 因果与临床疗效仍待验证。' 48 471 864 29 15 $palette.muted
Notes $s "第二轮十药由实验反馈与文献综合提出，ripasudil是在日本批准用于青光眼的ROCK抑制剂，相比研究分子Y27632有再利用背景。ARPE19读数为1.89×vehicle，人类分析1.75×，不能读成净增加189%。原代RPE-SC来自>60岁单供者，牛ROS替代微球，n4孔筛选/剂量响应支持ripasudil和Y27632。上清LDH补充毒性读数，Y27632剂量与LDH无相关，ripasudil为负相关。KL001通过防止CRY蛋白泛素依赖降解稳定蛋白，依据RPE吞噬昼夜节律联系成为候选并命中。原代有/无ROS条件下ripasudil均引起ABCA1上调，扩展机制一致性但尚未验证ABCA1因果。展示图来自Fig.4b–c。生物实验单位包括培养/供者，单供者多个孔不能扩大成人群证据。`n$robincite"


# 11
$s=Base 11 '论文二   Robin / 系统评测与方法评价' '本篇推进了实验反馈，也检验了组件能力' '组件消融、外部任务和生物实验回答不同问题，需要分别解读。' 'Ghareeb et al., 2026, Extended Data Fig. 4–6 / Methods / Discussion'
Txt $s 'BixBench 正确率（%，170 题，3 次运行）' 48 155 495 31 19 $palette.green $true
Txt $s 'Finch' 48 217 116 28 18 $palette.ink $true
Bar $s 179 214 (22.8*12) 29 $palette.green
Txt $s '22.8 ± 1.7' 304 215 155 28 18 $palette.white $true
Txt $s "Sonnet 3.7`n无工具" 48 278 122 53 17
Bar $s 179 283 (1.6*12) 29 $palette.blue
Txt $s '1.6 ± 1.2' 211 284 181 28 18 $palette.blue $true
Txt $s '生物统计 47.9%，生物信息 15.3%' 48 344 481 28 18 $palette.green $true
Txt $s '工具执行显著改善表现，但多步分析仍弱。比较同时改变工具和流程，尚不能单独归因于多智能体分工。' 48 389 485 88 17
Block $s '文献检索确实减少虚构引用' 'o4-mini 的实验方案虚构引用率为 44.5% ± 6.37%。Crow 检查的 15 份方案未见虚构。' 584 156 328 84
Block $s '结果留下的研究问题' '调用顺序几乎固定：自主规划增益尚不明确。分析轨迹共享数据与模型：共识之外仍需人工复核和独立实验。' 584 301 328 88
Txt $s '最新推进：在真实再利用案例中完成两轮反馈和功能复核。自主规划、独立供者及临床疗效仍需验证。' 48 470 864 30 15.5 $palette.muted
Notes $s "BixBench均值±标准误，n3运行，选定170问题；Finch总体22.8±1.7%，Sonnet3.7无agent框架1.6±1.2%，生物统计47.9±1.5%、生物信息15.3±2.0%。这是系统工具流程比较而非相同工具多智能体数量的干净消融。任务特定专家rubric RNAseq86%、flow100%也只是遵从评分，不代表所有真实任务准确率。文献检查Crow15方案零虚构，o4mini44.5±6.37%虚构，支持源证据检索。候选质量消融由LLM评审，仍有评审偏差。Robin调用顺序几乎固定，后续作者精简为notebook，不能宣称自由自主规划已建立。8路径共识不能消除相同数据、相同提示、相同模型的共同错误。时间收益为作者估计，551论文约30min，359–424人工h与<2认知h没有受控时间benchmark。单任务DeepResearch候选17独特无命中也无法普遍证明系统优势。主要科学贡献为有文献依据的跨领域候选和湿实验反馈更新。`n$robincite"


# 12
$s=Base 12 '方法应用   通用药物发现智能体 / 最小可执行方案' '通用方案：知识预测与实验反馈的组合' '候选携带条件记录、机制证据与反证标准，实验产生的新观察进入下一轮更新。' '以下为系统设计建议，依据 MAP 与 Robin，尚需验证'
Node $s '① 知识与细胞条件' '结构、有向靶点关系、细胞、剂量、时间' 48 156 251 119
Node $s '② 响应与实验假设' '预测转录变化，选择能区分机制的功能读数' 354 156 251 119
Node $s '③ 实验与代码分析' '实测功能与毒性，保留 QC、代码和效应区间' 661 156 251 119
Link $s 299 211 354 211
Link $s 605 211 661 211
Link $s 786 275 786 298
Link $s 786 298 174 298 $palette.green $false
Link $s 174 298 174 275
Txt $s '新观察更新机制证据、候选排序及停止条件' 272 304 417 27 15 $palette.muted
Block $s '候选记录至少包含什么？' '药物与引用，预测变化与不确定性，功能读数与对照，预期效应、反证条件、采集成本和停止规则。' 48 347 410 77
Block $s '例：假设某 ROCK 候选增强吞噬' '先看结构与靶点证据，再测 MFI、死细胞及荧光背景。功能命中后提出 RNA 或靶点干预，检验机制解释。' 508 347 404 77
Txt $s '采纳 MAP 的条件表征与方向关系，采纳 Robin 的引用、可执行分析和实验反馈。机制因果需要额外干预验证。' 48 471 864 29 15.5 $palette.muted
Notes $s "本页为独立通用方案，与任何特定项目当前实现无关。MAP提供用结构与机制相关关系生成条件响应的思路，Robin提供把文献、实验和可执行分析衔接的思路。最小数据契约包括统一药物/基因身份、作用方向、物种/细胞、剂量/时间、引用等级、预测/观察区分、原始数据版本、对照和单位、QC、效应与区间、成本及失败/停止理由。可用不确定性与机制分歧选择实验，但必须先确认不确定性经过校准。ROCK例子为设计演示，不声称新候选已有效。功能命中后RNA给出关联，再用抑制/敲低/救援区分机制因果。避免将预测转录恢复等同于真实功能改善。候选名单中的每条记录需支持第三方查回证据与重跑分析。`n$mapcite`n$robincite"


# 13
$s=Base 13 '方法应用   通用药物发现智能体 / 归因与效用评测' '分层评测：知识归因、功能预测与实验决策' '先固定细胞背景、剂量、时间、完整候选菜单和预算 B，再在独立实验单位上评价最终选择。' '拟议评测：相同数据、权限与预算；各层的增益不能互相替代'
Node $s '知识贡献' '结构表示 / 完整知识 / 打乱关系，留出药物及图谱边' 48 157 410 92
Node $s '响应与机制一致性' 'Pearson Δ、方向、候选区分度；同规模知识作为补充对照' 563 157 349 92
Node $s '预测贡献' '廉价先验 / 预测响应 / 实测响应上限，在匹配实验中比较' 48 269 410 92
Node $s '是否有功能信息收益？' '上限先超过廉价方法，再评测预测可否保留收益' 563 269 349 92
Node $s '智能体策略贡献' '确定性排序 / LLM 策略，允许相同工具和实验反馈' 48 381 410 92
Node $s '预算内的最终选择效用' '命中、效应、错误淘汰、总成本；包括停止与无更新策略' 563 381 349 92
Link $s 458 203 563 203
Link $s 458 315 563 315
Link $s 458 427 563 427
Notes $s "本页是可证伪的最小评测设计。知识比较应同时控制结构信息、图谱规模与关系置换，外推药物及相关边不进入预训练。预测比较先用真实RNA替代预测测上限，如果同条件真实RNA也不能提高功能决策，则复杂预测模型缺乏该端点的信息收益。策略比较应固定B、药物菜单、初始数据、工具、条件与动作，设置确定性、LLM、无更新/不追加实验及廉价先验。预算是所有采集与调用的成本，不能仅按轮数。终局效用可以定义为固定k入选的平均功能效应及预注册毒性约束，另报每总成本有效命中、假阳性和错误淘汰。独立性以供者/培养批次等真实单位定义，不能把细胞、孔或8分析轨迹扩大为生物学n。置信区间按背景/独立单位重采样，并预先声明最低有用效益与停止条件。功能读数与RNA需绑定同培养单元、剂量、时间和共享对照，避免跨实验的无证据桥接。`n$mapcite`n$robincite"


# 14
$s=Base 14 '阶段总结   MAESTRO / 最新实质进展' '39 基因坐标完成认证，G1 读数出现模型信号' '0927 尚未形成稳定选择优势。10.10 的新增证据推进了数据认证与同条件读数研究。' 'research/REPORT.md；EVIDENCE.md；P05R_EXTENSION.json；phenotype_anchor_20261010/RESULTS.json'
Txt $s '39 / 39' 48 153 415 53 34 $palette.green $true
Txt $s 'c44、c45 的端点坐标均唯一匹配' 48 217 416 29 19 $palette.ink $true
Txt $s "对照全部 62,710 个源基因。`n最大差约 1.46 × 10⁻⁷，容差 10⁻⁵。`nc44 复用 252 个细胞，新增 RNA 字节为 0。`nc45 用 11 个区分细胞取 133,564 字节，较旧方案少 60.7%。" 48 267 416 141 17
Txt $s '+0.254 r' 508 153 404 53 34 $palette.blue $true
Txt $s '预测细胞的 G1 组成读数出现信号' 508 217 404 29 19 $palette.ink $true
Txt $s "相对基础相似性：r 为 0.350 vs 0.096。`n95% CI [0.156, 0.367]，4/5 背景更好。`n同一球状培养单元的 24 h RNA 与读数，379 药物菜单，5 个 checkpoint 留出背景。" 508 267 404 141 17
Rule $s 48 427 864
Txt $s '端点准入带来更明确的使用范围：生存选择性主分析 STATE Δr = −0.226，真实 RNA 上限仅 +0.003，未准入。' 48 445 864 27 15.5 $palette.muted
Txt $s 'G1 来自 RNA 推导；坐标认证属于文件内身份；目标背景曾暴露。当前结果尚需独立生物确认。' 48 474 864 22 14.5 $palette.muted
Notes $s "MAESTRO独立部分。0927主要瓶颈为76–82%动作菜单难以区分，独立单位功效不足和选择优势未建立。当前已有可执行agent–decision–virtual-cell两轮反馈合同、持久化、预算、重试与重启。坐标扩展c44/c45唯一匹配39/39对全部62710基因，log1p(stored normalizedX)不变，容差1e-5，最大差1.4416e-7/1.4611e-7，独立块状算术复核一致。c44复用252暴露细胞0RNA字节，c45十一细胞133564表达字节，相对340068减少60.7%。认证只覆盖两个文件39端点，不能认证完整2000基因或checkpoint输出轴。表型研究40参考背景5checkpoint留出背景，G1的S_cells平均r.3495417，B为.0959951，差.2535466，CI[.1564786,.3672753]，4/5更好。E1 STATE kernel r.0722125 vsB.2984267，差-.2262142；真实RNA参考上限比B仅.0029597，低于预注册.05最低收益，门控拒绝。曾暴露背景和参考预训练重叠意味着开发证据，不是独立盲测。"


# 15
$s=Base 15 '阶段总结   MAESTRO / 效率收益与后续实验' '后续重点：可靠观测、有效端点与可归因的反馈' '运行闭环已验证两轮测量反馈及持久化、预算、重试和重启。下一步将工程能力转成可检验的研究。' '项目证据截至 2026-10-10；后续为拟议工作，P0.6 未放行，P2 仍关闭'
Txt $s '129 次 → 35 次' 48 158 421 49 31 $palette.green $true
Txt $s '预采购停止节省 94 次购买（72.9%）' 48 218 421 28 18 $palette.ink $true
Txt $s '匹配策略的最终动作保持一致。总模拟 profiles 为 774 → 680，无更新为 645，节省来自避免无效采集。' 48 263 421 83 17
Txt $s '+0.558 log₂' 530 158 382 49 31 $palette.blue $true
Txt $s '基础相似性迁移的生存 top-10 效用' 530 218 382 28 18 $palette.ink $true
Txt $s '相对通用药物强度排序，95% CI [0.235, 0.819]，5/5 更好。它构成后续复杂模型必须超过的廉价基线。' 530 263 382 83 17
Rule $s 48 361 864
Block $s '1. 冻结 P0.6 观测可靠性' '明确源版本、处理/对照、共享对照误差和采集成本。24 个分层实际为 12 个 pooled 样本。' 48 379 410 74
Block $s '2. 按端点评测知识与反馈' '借鉴 MAP 选择方向明确的有效关系，借鉴 Robin 保留引用和代码。用同工具预算比较，记录有益与有害更新。' 530 379 382 74
Notes $s "V3预购买停止从129降35，94次节省72.9%，最终匹配动作不变，total模拟profiles774至680，无更新645。不能据节省认定净实验信息价值或LLM优势。BvsZ top10生存选择性效用+.5580816log2，CI[.2352212,.8191470]，五背景均更好。B为基础相似性迁移，Z为通用药物强度排序，该改善来自廉价基线。P0.6需新冻结协议，绑定源版本、端点、排除、处理/对照行、实际组数、参考权重、共享对照误差、来源重复estimand和确切成本，24线/板分层为12pooledsamples。全局24h记录已有，逐样本时间/第三来源缺失，未解锁执行。未来MAP知识应用应分开关系方向与类型，控制结构/打乱知识；Robin反馈应用保留引用、代码、失败并预注册停止，以sameinformation/tool/budget确定性策略和无更新比较，终局效用、损害、成本和独立单位逐项验收。当前知识反馈和LLM独立科学决策收益未建立，未来方向不是现成整合成功。"

$candidate=Join-Path $assetDir '1009-flow-draft.pptx'
$deck.SaveAs($candidate)
$deck.SaveAs((Join-Path $assetDir '1009-flow-preview.pdf'),32)
$fit=@()
foreach($slide in $deck.Slides){foreach($shape in $slide.Shapes){
 if($shape.HasTextFrame -and $shape.TextFrame.HasText){$fit+=[pscustomobject]@{slide=$slide.SlideIndex;text=$shape.TextFrame.TextRange.Text;height=$shape.Height;bound=$shape.TextFrame.TextRange.BoundHeight;top=$shape.Top}}
 if($shape.HasTable){for($i=1;$i -le $shape.Table.Rows.Count;$i++){for($j=1;$j -le $shape.Table.Columns.Count;$j++){$cs=$shape.Table.Cell($i,$j).Shape;$fit+=[pscustomobject]@{slide=$slide.SlideIndex;text=$cs.TextFrame.TextRange.Text;height=$cs.Height-12;bound=$cs.TextFrame.TextRange.BoundHeight;top=$cs.Top}}}}
}}
$fit|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $assetDir 'flow-fit.json') -Encoding utf8
$deck.Close();$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck)|Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)|Out-Null
Write-Output $candidate
