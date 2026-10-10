$ErrorActionPreference='Stop'
$buildDir='D:\MAESTRO\.build-1009\revision\compact'
$source='C:\Users\59964\Desktop\24计算机科学与技术2\郑淼\生物信息\1009.pptx'
$draft=Join-Path $buildDir '1009-compact-draft.pptx'
Copy-Item -LiteralPath $source -Destination (Join-Path $buildDir '1009-before-compression.pptx') -Force
$app=New-Object -ComObject PowerPoint.Application
$deck=$app.Presentations.Open($source,-1,0,0)
$deck.SaveAs((Join-Path $buildDir 'before-preview.pdf'),32)
$deck.SaveAs($draft)
$palette=@{ink=0x26383D;muted=0x617079;green=0x527C71;blue=0x637F94;line=0xDCE4E4}
function RGB([int]$hex){[int](($hex -shr 16 -band 255) -bor (($hex -shr 8 -band 255) -shl 8) -bor (($hex -band 255) -shl 16))}
function Txt($slide,[string]$text,[double]$x,[double]$y,[double]$w,[double]$h,[double]$size=17,[int]$color=$palette.ink,[bool]$bold=$false){
 $shape=$slide.Shapes.AddTextbox(1,$x,$y,$w,$h)
 $shape.Line.Visible=0;$shape.Fill.Visible=0
 $shape.TextFrame.MarginLeft=0;$shape.TextFrame.MarginRight=0;$shape.TextFrame.MarginTop=0;$shape.TextFrame.MarginBottom=0
 $shape.TextFrame.WordWrap=-1;$shape.TextFrame.AutoSize=0;$shape.TextFrame2.AutoSize=0
 $range=$shape.TextFrame.TextRange;$range.Text=$text
 $range.Font.Name='Microsoft YaHei';$range.Font.NameFarEast='Microsoft YaHei';$range.Font.Size=$size
 $range.Font.Color.RGB=(RGB $color);$range.Font.Bold=[int]$bold;$range.ParagraphFormat.SpaceAfter=4
 $shape.Height=$h
}
function Rule($s,$x,$y,$w){$sh=$s.Shapes.AddLine($x,$y,($x+$w),$y);$sh.Line.ForeColor.RGB=(RGB $palette.line);$sh.Line.Weight=1}
function Reset($s,$section,$title,$subtitle,$sourceText){
 for($i=$s.Shapes.Count;$i -ge 1;$i--){$s.Shapes.Item($i).Delete()}
 Txt $s $section 48 23 850 20 11 $palette.green $true
 Txt $s $title 48 57 864 43 29 $palette.ink $true
 Txt $s $subtitle 48 105 864 35 15 $palette.muted
 Rule $s 48 499 864
 Txt $s $sourceText 48 511 814 17 9.5 $palette.muted
 Txt $s '00' 888 510 30 18 11 $palette.green
}

$mapNotes=$deck.Slides.Item(3).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text+"`n`n"+$deck.Slides.Item(4).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text
$appNotes=$deck.Slides.Item(14).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text+"`n`n"+$deck.Slides.Item(15).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text

$s=$deck.Slides.Item(3)
Reset $s '论文一   MAP / 背景、问题与总体思路' '未测药物响应预测：已有进展与机制知识的作用' '任务：给定对照细胞、药物结构与剂量，预测给药后的基因表达变化，辅助候选筛选。' 'Feng et al., 2026, Introduction / Fig. 1 / Methods'
Txt $s '已有进展：分子与细胞表示逐步增强' 48 155 410 27 19 $palette.green $true
Txt $s "实测扰动图谱提供响应样本，但组合覆盖稀疏。`nchemCPA 等用结构编码新分子，缓解药物类别 ID 的限制。`nSTATE 等提供细胞与基因表征，增强细胞背景建模。" 48 201 410 155 17
Txt $s '具体缺口：结构尚未显式约束作用关系' 508 155 404 27 19 $palette.blue $true
Txt $s '新分子能被编码，仍不等于响应可被准确预测。仅靠稀疏响应监督，难以补齐靶点、抑制／激活方向与基因功能关系。' 508 201 404 88 17
Txt $s 'MAP：先学知识表示，再学条件响应' 508 307 404 27 19 $palette.green $true
Txt $s '公共属性与有向关系补充扰动监督，为药物结构和蛋白序列提供机制相关先验。' 508 345 404 49 17
Rule $s 48 398 864
Txt $s '知识预训练：属性＋关系  →  响应训练：细胞＋药物＋剂量  →  给药后表达' 48 411 864 28 18 $palette.green $true
Txt $s '组合外推：药物已在其他背景测过，留出目标细胞–药物配对。' 48 449 410 47 17
Txt $s '药物外推：整药响应留出，并去除知识预训练中的实体、别名与关联边。' 508 449 404 47 17
$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=$mapNotes

$s=$deck.Slides.Item(14)
Reset $s '方法应用   通用药物发现智能体 / 设计与评测' '两篇论文对药物发现智能体的启发与验证' 'MAP 提供机制相关的条件表征；Robin 提供可追溯的实验反馈流程。以下为设计建议。' '拟议方案，依据 MAP 与 Robin；固定条件、候选菜单、工具权限与预算'
Txt $s '借鉴 MAP：以机制知识支持外推' 48 155 410 27 19 $palette.green $true
Txt $s '候选记录结构、抑制／激活关系和细胞／剂量／时间，预测转录变化；保留来源与不确定性，避免把知识关联当成因果。' 48 198 410 94 17
Txt $s '借鉴 Robin：让实测结果更新假设' 508 155 404 27 19 $palette.blue $true
Txt $s '先选疾病相关功能读数，再执行实验与代码分析；保存原始数据、QC、效应区间与失败结果，明确下一轮为何保留或淘汰候选。' 508 198 404 94 17
Txt $s '机制证据与响应预测  →  功能／毒性实验  →  分析与更新  →  下一轮候选' 48 311 864 29 19 $palette.green $true
Rule $s 48 355 864
Txt $s '必须分别检验的增益' 48 369 220 27 19 $palette.ink $true
Txt $s '对照设计与判断依据' 292 369 620 27 19 $palette.ink $true
Txt $s '知识是否帮助外推？' 48 411 228 25 17 $palette.green $true
Txt $s '结构／完整知识／打乱关系；严格留药，比较响应与方向。' 292 411 620 25 17
Txt $s '预测是否帮助选药？' 48 442 228 25 17 $palette.green $true
Txt $s '廉价先验／预测响应／实测上限；比较功能命中与效应。' 292 442 620 25 17
Txt $s '智能体是否改善决策？' 48 473 228 25 17 $palette.green $true
Txt $s '确定性／LLM／无更新策略；同预算比较最终效用与成本。' 292 473 620 25 17
$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=$appNotes

# Delete the two slides whose material was merged, in descending order.
$deck.Slides.Item(15).Delete()
$deck.Slides.Item(4).Delete()

foreach($s in $deck.Slides){
 foreach($sh in $s.Shapes){
  if($sh.HasTextFrame -and $sh.TextFrame.HasText -and $sh.Left -gt 880 -and $sh.Top -gt 500 -and $sh.Width -lt 50){
   if($sh.TextFrame.TextRange.Text -match '^\d{2}$'){$sh.TextFrame.TextRange.Text=('{0:D2}' -f $s.SlideIndex)}
  }
 }
}
$deck.Slides.Item(1).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text="本次汇报共15页，包含两张论文来源封面。MAP用背景与总体思路、知识预训练、条件响应预测、实验结果四页讲解；Robin保留背景、流程、两轮实验、系统评价五页。应用设计集中一页，MAESTRO单独两页。资料截至2026-10-10。"
$deck.Slides.Item(2).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text='用户提供的论文来源封面，保留原始图片。Feng et al., A knowledge-driven framework for predicting single-cell responses for unprofiled drugs. Nature Machine Intelligence (2026). DOI: 10.1038/s42256-026-01286-w'
$deck.Slides.Item(7).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text='用户提供的论文来源封面，保留原始图片。Ghareeb et al., A multi-agent system for automating scientific discovery. Nature (2026). DOI: 10.1038/s41586-026-10652-y'
$deck.SaveAs($draft)
$deck.SaveAs((Join-Path $buildDir 'compact-preview.pdf'),32)
$fit=@()
foreach($s in $deck.Slides){foreach($sh in $s.Shapes){if($sh.HasTextFrame -and $sh.TextFrame.HasText){$fit+=[pscustomobject]@{slide=$s.SlideIndex;text=$sh.TextFrame.TextRange.Text;height=$sh.Height;bound=$sh.TextFrame.TextRange.BoundHeight;top=$sh.Top}}}}
$fit|ConvertTo-Json -Depth 3|Set-Content -LiteralPath (Join-Path $buildDir 'fit.json') -Encoding utf8
$deck.Close();$app.Quit()
Write-Output $draft
