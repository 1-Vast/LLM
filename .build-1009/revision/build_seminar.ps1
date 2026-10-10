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
Txt $s 'MAP 与 Robin：研究问题、方法推导和证据分析' 60 300 835 36 22 $palette.muted
Rule $s 60 379 840
Txt $s "01  MAP：知识预训练与新药物响应预测`n02  Robin：文献假设、数据分析与两轮实验`n03  通用方法设计与 MAESTRO 阶段总结" 60 405 820 91 17
Notes $s "汇报日期沿用1009，项目资料截至2026-10-10。两篇论文各用5页解释问题、方法、实验、结果与边界。方法启发2页与MAESTRO2页相互独立。所有应用设计标注为建议。`n$mapcite`n$robincite"

# 02: task explained before architectures
$s=Base 2 '论文一   MAP / 问题与任务' 'MAP 的任务：从细胞与药物结构预测转录响应' '单细胞 RNA 测序给出每个细胞的基因表达。药物响应谱描述给药后哪些基因变化、变化多少。' 'Feng et al., 2026, Introduction / Fig. 1–3 / Methods'
Node $s '基础细胞' '未给药的表达向量 x' 48 160 249 89
Node $s '待测分子' 'SMILES 结构 + 剂量 δ' 48 269 249 94
Node $s '条件预测 f(x, p, δ)' '输出给药后的表达 x̂⁽ᵖ⁾，再计算相对对照的转录变化' 394 181 518 138
Link $s 297 206 394 233
Link $s 297 316 394 272
Txt $s '药物 ID 难以表示新分子。结构近邻也难以刻画靶点、作用方向和目标细胞状态。' 394 337 518 59 17 $palette.muted
Rule $s 48 389 864
Block $s '组合外推：药物已测，配对未测' '药物在其他背景出现过，留出目标背景的响应。每个背景留出 5% 配对。' 48 405 406 54
Block $s '药物外推：整个药物未测' '留出药物全部响应，以及知识预训练中的实体、别名和关联边，阻断信息泄漏。' 508 405 404 54
Notes $s "药物发现中大量候选没有目标背景下的响应谱。scRNAseq以破坏性测量得到细胞群体，给药前后通常不是同一细胞的配对。MAP从对照细胞状态及药物结构/剂量预测给药后的表达。以群体平均与真实处理群体比较，两种外推任务要分开。组合外推允许药物在其他背景被测过，各背景5%留出集合不重叠。未测药物移除其全部响应与MAP-KG中的实体、别名、关联边，推断时只使用可用结构与属性。药物ID不能自然生成新分子表示，结构编码可外推但缺乏机制约束。MAP的核心创新是让机制知识先参与表示训练，再用于响应预测。`n$mapcite"

# 03: two distinct alignment objectives, formulas and biological meaning
$s=Base 3 '论文一   MAP / 知识预训练' '跨模态属性对齐与有向关系对齐' 'MAP-KG 整合 14 个资源：187,089 个药物、22,924 个基因、694,246 条关系。' 'Feng et al., 2026, Fig. 1a–b / Methods, equations 2–5'
Picture $s 'map_knowledge.png' 45 151 406 221
Txt $s '跨模态编码器' 48 390 402 25 18 $palette.green $true
Txt $s "名称与注释：BioBERT`n结构：MoleculeSTM；蛋白序列：ESM-2`n后两者冻结，训练 4 层 MLP 适配器。" 48 420 402 71 17
Block $s '① 节点内：同一个实体的属性对齐' '以名称文本 zᵢ 为规范表示，拉近结构、蛋白序列和功能描述。同一实体是正例，批内其他实体是负例。' 493 158 419 78
Block $s '② 节点间：关系条件化的邻居对齐' '先编码“抑制”等关系 r，再用有序拼接区分源实体与目标实体，让表示保留作用方向。' 493 283 419 66
Txt $s "zᵢ→ⱼ = MLP([zᵢ, zᵣ])`nzⱼ←ᵢ = MLP([zᵣ, zⱼ])" 493 390 419 65 20 $palette.blue $true
Txt $s '双向 InfoNCE 拉近正确配对。机制相近的分子形成邻域，支持已测响应向新分子迁移。' 493 456 419 38 15.5 $palette.muted
Notes $s "第一阶段知识预训练不需要细胞扰动响应。MAP-KG有428,192条药物–基因边与266,054条基因–基因边。节点规范嵌入来自实体名称文本BioBERT。MoleculeSTM与ESM-2冻结，4层MLP适配。节点内正例为该实体结构、序列或描述，节点间正例为其关系条件化邻居表示。关系编码z_r=BioBERT(r)，MLP的拼接顺序保留头/尾角色。双向InfoNCE对一批配对(z_i,z'_i)优化：L=-mean_i{log[exp(sim(z_i,z'_i)/tau)/sum_k exp(sim(z_i,z'_k)/tau)] + log[exp(sim(z_i,z'_i)/tau)/sum_k exp(sim(z_k,z'_i)/tau)]}。直观解释是识别正确的实体属性/关系配对，形成跨模态且机制相关的几何邻域。关系角色的编码构成归纳偏置，不能把图谱中的关联自动升级为因果证据。图来自论文Fig.1a–b。`n$mapcite"

# 04: exact token flow and population supervision
$s=Base 4 '论文一   MAP / 条件响应预测' '融合细胞状态、蛋白知识与药物剂量' '第二阶段用已测药物的对照与处理群体训练预测器，推断时输入新分子的结构。' 'Feng et al., 2026, Fig. 1c / Methods, equations 6–12'
Picture $s 'map_predictor.png' 48 151 290 273
Block $s '① 细胞状态提供上下文' 'STATE SE-600M 编码 x，得到全局细胞 token h 与基因 token T。MLP 融合 T 和对应蛋白知识。' 378 154 534 65
Block $s '② 药物与剂量决定扰动条件' '分子编码得到 zₘₒₗ，按对数剂量 δ 缩放。4 层 Transformer 处理 [δzₘₒₗ, h, T融合]。' 378 264 534 64
Block $s '③ 扰动细胞 token 解码为表达' 'MLP 把 ĥ⁽ᵖ⁾ 解码为表达 x̂⁽ᵖ⁾。同时匹配处理群体的平均表达和平均细胞嵌入。' 378 362 534 57
Txt $s 'L = ‖mean(ĥ) − mean(h)‖² / d + λ · ‖mean(x̂) − mean(x)‖² / G' 48 461 864 29 18 $palette.green $true
Notes $s "T,h=STATE(x)，h来自SPECIAL token。T_fuse=MLP([T,Z_seq])，对应基因序列/知识按身份对齐。药物结构z_mol乘以施加剂量的log变换δ，Transformer输入[δ z_mol,h,T_fuse]，取细胞位置输出h_hat，再由MLP解码表达x_hat。表达预处理限定19,790人类蛋白编码基因、总UMI归一化到10,000再log1p，STATE输入为每细胞高表达的2,048基因token，并采用软分箱。双损失匹配真实处理群体均值：嵌入误差除以d，表达误差除以G，λ权衡。真实扰动群体先由STATE编码形成嵌入监督。群体均值损失可减少噪声，却不保证完整单细胞分布或每个细胞的真实轨迹。模型输入药物是SMILES，因而对新分子可以计算嵌入，无须药物类别ID。图来自Fig.1c。`n$mapcite"

# 05: experimental meaning, delta metric and comparison scope
$s=Base 5 '论文一   MAP / 实验设计与评价指标' '泛化评测检查“药物引起的变化”是否预测正确' '各数据集内部训练与留出，分别评测两类外推。结果不能直接解释为跨数据集迁移。' 'Feng et al., 2026, Fig. 2–3 / Methods'
Table $s @(
 @('实验数据','论文实际使用的背景','药物覆盖'),
 @('Tahoe-100M','6 条选定癌细胞系','原始图谱 379 种药物'),
 @('OP3','6 种免疫细胞类型','144 种化合物'),
 @('SciPlex3','A549 / MCF7 / K562','187 种化合物')
) 48 155 @(195,410,259) @(35,43,43,43)
Block $s '表达变化的一致性' 'Δx = 处理群体均值 − 对照群体均值。Pearson Δ 比较预测 Δx 与实测 Δx，避免基础表达主导相关性。' 48 342 408 66
Block $s '方向、区分度与误差' '方向准确率检查上调/下调。区分度检查不同药物的响应差别。MSE、Wasserstein 补充幅度和分布评价。' 508 342 404 66
Txt $s '评价基因：top-50 差异表达基因与 top-2000 高变基因。比较 trainMean、chemCPA、CRISP、PRnet、XPert。' 48 447 864 43 16.5 $palette.muted
Notes $s "Tahoe原始图谱含50细胞系379药物，论文概念验证仅用A172、A498、A549、HepG2/C3A、PANC1、SKMEL2六条，不能宣称在全图谱训练。OP3有6免疫类型、144化合物；SciPlex3有3癌系187化合物。每数据集独立采用留出策略。评测常以pseudobulk群体均值构成响应，Pearson delta=correlation(mu_pred-mu_ctrl,mu_obs-mu_ctrl)，衡量相对对照的变化模式，它对整体尺度误差并不充分敏感，所以需MSE等指标。差异表达方向与药物间可区分性回答其他问题。top2000HVG依据数据集变异计算，DEG选择依据论文差异分析；测试DEG评测回答已知真实响应基因上的恢复质量，不等同于可无监督选定真实DEG。比较包含经验均值与分子条件化模型。STATE仅可比较组合任务，因类别药物ID无法自然用于未测药物。`n$mapcite"

# 06: result chart, causally bounded ablation interpretation
$s=Base 6 '论文一   MAP / 主结果、消融与应用' '未测药物泛化改善，知识边提供可定位的贡献' '主结果为 top-50 DEG Pearson Δ 相对最强基线的提升，百分比表示相对增益。' 'Feng et al., 2026, Fig. 2–5 / A549 computational screen'
Txt $s '未测药物的相对提升（%）' 48 157 431 25 19 $palette.green $true
$bars=@(@{name='Tahoe';value=11.8;y=216},@{name='OP3';value=19.8;y=283},@{name='SciPlex3';value=10.4;y=350})
foreach($b in $bars){Txt $s $b.name 48 $b.y 130 28 18;Bar $s 182 ($b.y+1) ($b.value*12.5) 28 $palette.green;Txt $s ('+'+[string]$b.value+'%') (194+$b.value*12.5) $b.y 87 28 18 $palette.green $true}
Link $s 182 204 182 394 $palette.line $false
Txt $s '未见组合：Tahoe +12.3%，SciPlex3 +6.6%' 48 422 480 52 17 $palette.blue $true
Block $s '消融：哪些知识有效？' 'MAP-KG 相对 PrimeKG 的 PDCorr 再提升 11.4%。去掉药物–基因边下降最大，支持靶点关系的贡献。' 576 158 336 85
Block $s '应用：如何从响应得到药物排序？' '对 A549 预测表达做 GSEA 通路富集。58 个留出候选中，4/5 个已批准 NSCLC 药物进入前 15。' 576 302 336 80
Txt $s '证据支持转录响应与计算候选排序。A549 分析没有开展新的药效湿实验，靶点因果和临床有效性仍需验证。' 48 469 864 29 15 $palette.muted
Notes $s "相对增益=(MAP指标-最强基线指标)/最强基线指标，不能读作百分点。未测药物Tahoe11.8%、OP319.8%、SciPlex310.4%，组合外推Tahoe12.3%、SciPlex36.6%。MAP未测药物SciPlex3与OP3 top50DEG平均相关系数分别0.827、0.861。MAP-KG相对PrimeKG报告方向准确率+7.2%、PDCorr+11.4%、区分度+4.3%，去掉药物–基因边影响最大；比较不能直接将所有增益归因为知识质量，也包含规模影响。A549应用基于预测响应做GSEA、疾病相关通路排序与文献一致性，58候选中4/5已批准NSCLC药在前15，adagrasib第2，afatinib第4。该计算筛选不等价于新湿实验，也不能证明药物靶点结合或临床效益。讨论可提出同规模图谱对照与机制更严格的留出，进一步区分知识量、结构与特定关系贡献。`n$mapcite"

# 07: scientific problem and the measurable assay
$s=Base 7 '论文二   Robin / 疾病目标与实验读数' 'Robin 的任务：寻找增强 RPE 吞噬的再利用药物' 'dAMD 指干性年龄相关性黄斑变性。RPE 是视网膜色素上皮，负责清理光感受器外节。' 'Ghareeb et al., 2026, Introduction / Fig. 2a–b'
Block $s '疾病目标如何转成实验目标？' '论文选择 RPE 吞噬功能下降这一疾病相关机制，以“药物是否增强吞噬”为功能读数，寻找已知药物的新用途。' 48 155 410 91
Block $s '为什么需要发现闭环？' '文献能提供候选，但不能决定它是否有效。实验给出效应，原始数据分析再提出机制线索与下一轮候选。' 48 301 410 77
Picture $s 'robin_assay.png' 507 157 405 115
Txt $s '功能实验的时间和测量' 508 295 404 29 19 $palette.green $true
Txt $s "给药 1 h，再加入 pHrodo 底物 3 h。`n底物进入酸性溶酶体后发荧光。`n流式检测活细胞中的平均荧光强度（MFI），以 DMSO 对照归一化。" 508 340 404 116 17
Txt $s '疾病相关功能读数使候选可以检验。细胞吞噬增强与患者获益之间仍需要疾病模型和临床证据。' 48 464 864 35 16 $palette.muted
Notes $s "Robin探索dAMD药物再利用。RPE吞噬清理光感受器外节的过程与视网膜健康有关，吞噬不足在老化和AMD中出现。论文把宽泛疾病目标转成增强RPE吞噬的可测方向。初筛使用ARPE19与pHrodo微球，后续用原代RPE-SC与牛光感受器外节ROS。pHrodo在酸性环境发荧光，因此流式MFI构成实验读数。给药1h，再共孵育底物3h，不宜将它直接描述为24h存活实验。归一化MFI反映底物进入酸性环境后的信号，可能受其他细胞/荧光因素影响，QC与替代解释需检查。图来自Fig.2b，由论文作者使用BioRender制作。`n$robincite"

# 08: explicit role contracts and ranking method
$s=Base 8 '论文二   Robin / 假设生成与候选排序' '智能体分工：检索、候选排序与实验数据分析' 'Robin 协调分工。Crow 与 Falcon 基于 PaperQA2，Finch 在 Jupyter 中执行数据分析代码。' 'Ghareeb et al., 2026, Fig. 1 / Methods: Robin and Finch implementation'
Node $s 'Crow：疾病与实验检索' '疾病问题、机制和模型' 48 156 259 95
Node $s 'Falcon：候选证据评估' '药理依据、引用和局限' 350 156 259 95
Node $s 'Finch：数据分析执行' '实验后 FCS / RNA 计数' 653 156 259 95
Link $s 307 204 350 204
Link $s 609 204 653 204
Txt $s "人工`n实验" 615 161 35 36 11 $palette.muted
Txt $s '10 个机制 / 实验报告' 48 273 259 27 19 $palette.green $true
Txt $s '成对比较后选定实验，再生成 30 个药物假设。研究者审核并选择实际测试对象。' 48 317 259 116 17
Txt $s '两两裁判 + BTL 排序' 350 273 259 27 19 $palette.green $true
Txt $s '≤25 项比较所有配对，更多候选随机比较 300 对。BTL 拟合相对强度，形成候选名次。' 350 317 259 116 17
Txt $s '8 条分析轨迹 + 共识' 653 273 259 27 19 $palette.green $true
Txt $s 'edit_cell 修改并执行代码，submit_answer 提交结论。保留 notebook，汇总路径一致性。' 653 317 259 116 17
Txt $s 'BTL：P(i 胜 j) = sᵢ / (sᵢ + sⱼ)，s 表示相对偏好强度。该排序评价科学依据，实际药效由实验检验。' 48 416 864 37 16 $palette.blue $true
Txt $s '新实验数据返回协调器，更新假设。8 条轨迹是分析路径重复，独立生物重复取决于实验样本。' 48 462 864 35 16 $palette.muted
Notes $s "Robin以Aviary框架实现，o4mini综合文献并生成假设，ClaudeSonnet3.7担任成对裁判。Crow快速总结，Falcon提供详细文献报告，资源包括临床试验与OpenTargets。先提出通用问题，再10机制对应模型报告，排序选定功能读数，生成30候选及Falcon报告。BTL模型拟合P(i胜j)=s_i/(s_i+s_j)，不超过25假设比较所有配对，超过25随机采300配对。优先根据科学依据、药理和文献方法学判断，排序仍不是实验药效。人类选择候选并制定执行协议。Finch使用edit_cell与submit_answer工具，8独立轨迹执行相同数据的不同分析，元分析形成共识。分析轨迹探索参数敏感性，不能代替独立生物重复。图示按实际流程简化，Falcon到Finch之间存在人类湿实验。作者观察协调工具顺序几乎固定，后续简化为notebook，说明核心价值在角色与工具流程，不能仅据多代理数量认定自主规划优势。`n$robincite"

# 09: first experimental round and mechanism generation
$s=Base 9 '论文二   Robin / 第一轮实验与原始数据分析' '第一轮结果：ROCK 命中与 ABCA1 转录线索' '初筛从排序中测试前 5 个候选，MFGE8 作为已知吞噬促进的阳性参照。' 'Ghareeb et al., 2026, Fig. 2c–f / Fig. 3 / RPE phagocytosis assay'
Picture $s 'robin_volcano.png' 48 157 374 266
Txt $s '横轴为 log₂FC，纵轴为 −log₁₀P。红色表示上调，蓝色表示下调。' 48 440 374 54 16 $palette.muted
Block $s '① 流式确认功能命中' 'Finch 去除碎片、双细胞和 DAPI 阳性死细胞，比较 MFI 与 DMSO。Y-27632 的吞噬增强由人工复分析确认。' 471 155 441 72
Block $s '② 命中推动后续 RNA-seq' '既有机制是 ROCK 抑制调节肌动蛋白。新数据发现 ABCA1 约 3 倍上调，并富集肌动蛋白、小 GTP 酶和自噬相关程序。' 471 282 441 77
Block $s '③ 分析生成下一步假设' 'ABCA1 编码脂质外排泵，连接脂质稳态与 RPE 功能。它提供可检验机制线索，尚需干预实验建立因果。' 471 407 441 55
Notes $s "第一轮前五候选为exendin4、fingolimod、MFGE8、Y27632、AICAR与TUDCA组合，MFGE8有既有吞噬增强证据作为阳性参照。系统最初建议ROS与原代/干细胞分化RPE，但人类选择更易获得微球和ARPE19加速验证。FCS通过FSC/SSC排碎片，FSC-A/H选单细胞，DAPI排死细胞，再比较归一化MFI。n3孔，Dunnett检验对DMSO。Y27632命中、人类同数据分析支持后，Robin提出RNAseq。Finch差异与GO分析显示细胞骨架、小GTP酶和自噬相关转录变化；8路径中超过50%识别相同显著DEG。ABCA1约3倍上调，调整P=2.13e-83，编码脂质外排泵，可能连接吞噬后的脂质处理与RPE健康。火山图来自Fig.3b。批量RNA结果是机制关联，应通过敲低/救援及功能复测检验ABCA1必要/充分性，此类实验是建议而非论文已完成。`n$robincite"

# 10: second round includes primary cells and orthogonal limits
$s=Base 10 '论文二   Robin / 第二轮候选与验证' '实验反馈把 ROCK 命中推进到 ripasudil 再利用' 'ripasudil 是已获批治疗青光眼的 ROCK 抑制剂。研究者测试第二轮 10 种候选，再用原代细胞复核。' 'Ghareeb et al., 2026, Fig. 4 / RPE-SC validation'
Picture $s 'robin_evidence.png' 48 158 513 186
Txt $s 'ARPE-19：ripasudil 的 MFI 为对照 1.89 倍' 48 363 513 31 19 $palette.green $true
Txt $s '剂量响应曲线支持更高效力。人工复分析为 1.75 倍，均为相对 DMSO 的倍数。' 48 411 513 64 17
Block $s '模型升级：原代 RPE-SC + ROS' '从 1 位 >60 岁供者获得细胞，以牛光感受器外节替代微球。ripasudil 与 Y-27632 再次命中（n=4 孔）。' 607 157 305 92
Block $s '跨领域线索：KL001 也命中' '昼夜节律调控启发候选。KL001 稳定 CRY 蛋白，抑制其泛素依赖降解。ABCA1 上调也在原代细胞复现。' 607 315 305 92
Txt $s '证据推进到细胞模型、底物和剂量复核。单供者的孔重复不足以证明人群泛化，ABCA1 因果与临床疗效仍待验证。' 48 471 864 29 15 $palette.muted
Notes $s "第二轮十药由实验反馈与文献综合提出，ripasudil是在日本批准用于青光眼的ROCK抑制剂，相比研究分子Y27632有再利用背景。ARPE19读数为1.89×vehicle，人类分析1.75×，不能读成净增加189%。原代RPE-SC来自>60岁单供者，牛ROS替代微球，n4孔筛选/剂量响应支持ripasudil和Y27632。上清LDH补充毒性读数，Y27632剂量与LDH无相关，ripasudil为负相关。KL001通过防止CRY蛋白泛素依赖降解稳定蛋白，依据RPE吞噬昼夜节律联系成为候选并命中。原代有/无ROS条件下ripasudil均引起ABCA1上调，扩展机制一致性但尚未验证ABCA1因果。展示图来自Fig.4b–c。生物实验单位包括培养/供者，单供者多个孔不能扩大成人群证据。`n$robincite"

# 11: meaningful architectural critique
$s=Base 11 '论文二   Robin / 系统评测与方法评价' '系统评测：引用可靠性、分析收益与自主性边界' '组件消融、外部任务和生物实验回答不同问题，需要分别解读。' 'Ghareeb et al., 2026, Extended Data Fig. 4–6 / Methods / Discussion'
Txt $s 'BixBench 正确率（%，170 题，3 次运行）' 48 155 495 31 19 $palette.green $true
Txt $s 'Finch' 48 217 116 28 18 $palette.ink $true
Bar $s 179 214 (22.8*12) 29 $palette.green
Txt $s '22.8 ± 1.7' 304 215 155 28 18 $palette.white $true
Txt $s "Sonnet 3.7`n无工具" 48 278 122 53 17
Bar $s 179 283 (1.6*12) 29 $palette.blue
Txt $s '1.6 ± 1.2' 211 284 181 28 18 $palette.blue $true
Txt $s '生物统计 47.9%，生物信息 15.3%' 48 344 481 28 18 $palette.green $true
Txt $s '多步流程与参数敏感性仍是弱项。此比较同时改变工具和流程，不能单独归因于“多智能体”。' 48 389 485 88 17
Block $s '文献检索确实减少虚构引用' 'o4-mini 的实验方案虚构引用率为 44.5% ± 6.37%。Crow 检查的 15 份方案未见虚构。' 584 156 328 84
Block $s '组会需要讨论的两个边界' '调用顺序几乎固定，作者后续精简为 notebook。8 条分析轨迹能检查路径敏感性，无法保证共同偏差消失。' 584 301 328 88
Txt $s '创新在于文献假设与可执行分析、真实湿实验反馈的衔接。临床验证、专家协议和独立供者仍必要。' 48 470 864 30 15.5 $palette.muted
Notes $s "BixBench均值±标准误，n3运行，选定170问题；Finch总体22.8±1.7%，Sonnet3.7无agent框架1.6±1.2%，生物统计47.9±1.5%、生物信息15.3±2.0%。这是系统工具流程比较而非相同工具多智能体数量的干净消融。任务特定专家rubric RNAseq86%、flow100%也只是遵从评分，不代表所有真实任务准确率。文献检查Crow15方案零虚构，o4mini44.5±6.37%虚构，支持源证据检索。候选质量消融由LLM评审，仍有评审偏差。Robin调用顺序几乎固定，后续作者精简为notebook，不能宣称自由自主规划已建立。8路径共识不能消除相同数据、相同提示、相同模型的共同错误。时间收益为作者估计，551论文约30min，359–424人工h与<2认知h没有受控时间benchmark。单任务DeepResearch候选17独特无命中也无法普遍证明系统优势。主要科学贡献为有文献依据的跨领域候选和湿实验反馈更新。`n$robincite"

# 12: concrete transferable design, no MAESTRO references
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

# 13: falsifiable plan with ranking objective and controls
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

# 14: compressed, quantitative project progress
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

# 15: achieved benefit, hypothesis and gated sequence in one page
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

$candidate=Join-Path $assetDir '1009-seminar-draft.pptx'
$deck.SaveAs($candidate)
$deck.SaveAs((Join-Path $assetDir '1009-seminar-preview.pdf'),32)
$fit=@()
foreach($slide in $deck.Slides){foreach($shape in $slide.Shapes){
 if($shape.HasTextFrame -and $shape.TextFrame.HasText){$fit+=[pscustomobject]@{slide=$slide.SlideIndex;text=$shape.TextFrame.TextRange.Text;height=$shape.Height;bound=$shape.TextFrame.TextRange.BoundHeight;top=$shape.Top}}
 if($shape.HasTable){for($i=1;$i -le $shape.Table.Rows.Count;$i++){for($j=1;$j -le $shape.Table.Columns.Count;$j++){$cs=$shape.Table.Cell($i,$j).Shape;$fit+=[pscustomobject]@{slide=$slide.SlideIndex;text=$cs.TextFrame.TextRange.Text;height=$cs.Height-12;bound=$cs.TextFrame.TextRange.BoundHeight;top=$cs.Top}}}}
}}
$fit|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $assetDir 'seminar-fit.json') -Encoding utf8
$deck.Close();$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck)|Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)|Out-Null
Write-Output $candidate
