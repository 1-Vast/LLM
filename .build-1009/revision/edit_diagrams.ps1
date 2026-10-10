$ErrorActionPreference='Stop'
$assetDir='D:\MAESTRO\.build-1009\revision'
$destination='C:\Users\59964\Desktop\24计算机科学与技术2\郑淼\生物信息\1009.pptx'
$app=New-Object -ComObject PowerPoint.Application
$app.Visible=-1
$deck=$app.Presentations.Open('D:\MAESTRO\output-1009\1009.pptx',0,0,-1)
$p=@{ink=0x26383D;muted=0x617079;green=0x527C71;blue=0x637F94;line=0xDCE4E4;pale=0xF4F7F6;white=0xFFFFFF}
function RGB([int]$hex){[int](($hex -shr 16 -band 255) -bor (($hex -shr 8 -band 255) -shl 8) -bor (($hex -band 255) -shl 16))}
function Txt($s,[string]$t,[double]$x,[double]$y,[double]$w,[double]$h,[double]$size=17,[int]$color=$p.ink,[bool]$bold=$false,[bool]$center=$false){
 $sh=$s.Shapes.AddTextbox(1,$x,$y,$w,$h);$sh.Line.Visible=0;$sh.Fill.Visible=0
 $tf=$sh.TextFrame;$tf.MarginLeft=0;$tf.MarginRight=0;$tf.MarginTop=0;$tf.MarginBottom=0;$tf.WordWrap=-1;$tf.AutoSize=0;$sh.TextFrame2.AutoSize=0
 $r=$tf.TextRange;$r.Text=$t;$r.Font.Name='Microsoft YaHei';$r.Font.NameFarEast='Microsoft YaHei';$r.Font.Size=$size;$r.Font.Color.RGB=(RGB $color);$r.Font.Bold=[int]$bold
 if($center){$r.ParagraphFormat.Alignment=2};$r.ParagraphFormat.SpaceAfter=4;$sh.Height=$h
}
function Line($s,$x1,$y1,$x2,$y2,$color=$p.line,$arrow=$false,$weight=1.2){
 $sh=$s.Shapes.AddLine($x1,$y1,$x2,$y2);$sh.Line.ForeColor.RGB=(RGB $color);$sh.Line.Weight=$weight
 if($arrow){$sh.Line.EndArrowheadStyle=3}
}
function Box($s,$title,$body,$x,$y,$w,$h,$tint=$p.pale){
 $sh=$s.Shapes.AddShape(1,$x,$y,$w,$h);$sh.Fill.ForeColor.RGB=(RGB $tint);$sh.Line.ForeColor.RGB=(RGB $p.line);$sh.Line.Weight=1
 Txt $s $title ($x+14) ($y+12) ($w-28) 28 19 $p.green $true
 Txt $s $body ($x+14) ($y+49) ($w-28) ($h-54) 17
}
function Bar($s,$x,$y,$w,$h,$color){$sh=$s.Shapes.AddShape(1,$x,$y,$w,$h);$sh.Line.Visible=0;$sh.Fill.ForeColor.RGB=(RGB $color)}
function Reset($s,$section,$title,$sub,$source){
 for($i=$s.Shapes.Count;$i -ge 1;$i--){$s.Shapes.Item($i).Delete()}
 Txt $s $section 48 23 864 20 11 $p.green $true
 Txt $s $title 48 57 864 43 29 $p.ink $true
 Txt $s $sub 48 105 864 35 15 $p.muted
 Line $s 48 499 912 499
 Txt $s $source 48 511 814 17 9.5 $p.muted
 Txt $s ('{0:D2}' -f $s.SlideIndex) 888 510 30 18 11 $p.green
}

# 09: editable quantitative chart and evidence annotations
$s=$deck.Slides.Item(9)
Reset $s '论文二   Robin / 系统效果与局限' '证据检索与代码执行带来可测的改进' '组件消融与任务评测，分别检验引用可靠性和原始数据分析能力。' 'Ghareeb et al., 2026, Fig. 5 / Extended Data / BixBench'
Txt $s 'BixBench 正确率（%）' 48 158 464 29 20 $p.green $true
Txt $s '170 个相关问题，3 次运行' 48 197 464 24 15 $p.muted
Line $s 189 251 189 367 $p.line
Line $s 189 367 518 367 $p.line
foreach($v in @(0,10,20,25)){$xx=189+$v*12;Line $s $xx 367 $xx 373;Txt $s ([string]$v) ($xx-12) 380 32 23 13 $p.muted $false $true}
Txt $s 'Finch' 48 258 132 30 18 $p.ink $true
Bar $s 189 254 (22.8*12) 30 $p.green
Txt $s '22.8 ± 1.7' 319 254 184 30 18 $p.white $true
Txt $s "Sonnet 3.7`n无工具" 48 309 132 49 17
Bar $s 189 316 (1.6*12) 30 $p.blue
Txt $s '1.6 ± 1.2' 219 316 182 30 18 $p.blue $true
Txt $s '工具和分析流程有增益，绝对表现仍有限。' 48 416 479 46 17 $p.muted
Line $s 563 159 563 453
Txt $s '检索提高引用可靠性' 602 158 310 29 20 $p.green $true
Txt $s '44.5% ± 6.37%' 602 206 310 40 29 $p.blue $true
Txt $s "o4-mini 实验方案中的虚构引用率`nCrow 检查的 15 份方案未见虚构引用" 602 257 310 64 17
Txt $s '时间收益属于作者估计' 602 348 310 28 18 $p.green $true
Txt $s '约 30 分钟处理 551 篇文献，认知工作 <2 小时。人工实验与专家提示仍必要。' 602 391 310 71 17
Txt $s '证据范围：一个疾病案例与选定任务子集。尚未建立通用自主发现能力。' 48 470 864 24 15 $p.muted

# 10: editable directed evidence/data-flow diagram
$s=$deck.Slides.Item(10)
Reset $s '方法启发   药物发现智能体 / 知识表示' '机制知识如何进入预测与候选解释' '可采纳的设计思路：结构与机制证据共用实体记录，再服务于不同任务。' '设计建议，依据 MAP；尚需独立评测'
Box $s '分子结构' '结构相似性与化学先验' 48 165 210 98
Box $s '机制文献' '药物作用、靶点与基因功能' 48 311 210 112
Box $s '有方向的知识记录' "药物抑制 / 激活靶点`n靶点关联通路与读数`n`n细胞、剂量、时间`n原始来源与证据等级" 342 183 266 234
Box $s '响应预测' '帮助未测分子外推，预测转录变化与方向' 692 165 220 111
Box $s '候选解释' '说明证据依据，列出可检验机制与反例' 692 311 220 112
Line $s 258 214 342 252 $p.green $true 1.6
Line $s 258 367 342 348 $p.green $true 1.6
Line $s 608 252 692 221 $p.green $true 1.6
Line $s 608 348 692 367 $p.green $true 1.6
Txt $s '统一实体与别名' 259 168 94 59 13 $p.muted $false $true
Txt $s '保留条件与引用' 259 399 94 56 13 $p.muted $false $true
Txt $s '候选交付：预测效应 + 支持证据 + 反证条件。知识嵌入与证据检索的收益分别评测。' 48 453 864 39 18 $p.green $true

# 11: editable experimental loop with explicit human execution
$s=$deck.Slides.Item(11)
Reset $s '方法启发   药物发现智能体 / 实验闭环' '功能读数驱动的候选更新' '可采纳的设计思路：沿用 Robin 分工，让真实实验反馈进入下一轮假设。' '设计建议，依据 Robin；实验执行与审核仍需研究者'
Box $s '01  疾病与功能读数' '机制证据、细胞模型和实验条件，定义可测的疾病目标' 48 159 342 112
Box $s '02  候选与实验设计' '有引用的机制假设，阳性与阴性对照，区分竞争解释' 570 159 342 112
Box $s '04  假设与候选更新' '保留、淘汰或修改的理由，来自新观察并记录失败结果' 48 345 342 112
Box $s '03  原始数据分析' 'QC、代码、效应与区间，统计正确的独立实验单位' 570 345 342 112
Line $s 390 215 570 215 $p.green $true 1.8
Line $s 741 271 741 345 $p.green $true 1.8
Line $s 570 401 390 401 $p.green $true 1.8
Line $s 219 345 219 271 $p.green $true 1.8
Txt $s '提出可检验候选' 399 181 162 27 14 $p.muted $false $true
Txt $s '研究者执行湿实验' 759 291 153 44 14 $p.muted
Txt $s '证据支持或反驳假设' 397 369 171 26 14 $p.muted $false $true
Txt $s '调整读数与条件' 49 292 154 26 14 $p.muted $false $true
Txt $s '例：吞噬读数升高时，检查死亡与荧光背景，并用独立供者复核。' 48 471 864 25 16 $p.green $true

# 12: editable nested evaluation diagram, distinct hypotheses and comparators
$s=$deck.Slides.Item(12)
Reset $s '方法启发   药物发现智能体 / 联合评测' '知识、预测与智能体策略的分层评测' '两篇论文可组成“知识预测 + 实验反馈”方案，各层贡献需要独立验证。' '拟议评测方案；方法依据 MAP 与 Robin'
Txt $s '候选生成' 48 164 154 30 19 $p.green $true
Txt $s '机制知识是否有用？' 48 204 184 53 17
Txt $s '功能读数' 48 282 154 30 19 $p.green $true
Txt $s '转录预测能否选药？' 48 322 184 53 17
Txt $s '实验决策' 48 400 154 30 19 $p.green $true
Txt $s '智能体是否值得引入？' 48 440 184 50 17
Line $s 210 196 260 196 $p.green $true 1.5
Line $s 210 314 260 314 $p.green $true 1.5
Line $s 210 432 260 432 $p.green $true 1.5
Box $s '知识归因比较' '结构模型 / 完整知识 / 打乱关系' 260 154 393 85
Box $s '预测价值比较' '廉价先验 / 预测响应 / 实测响应上限' 260 272 393 85
Box $s '策略价值比较' '确定性策略 / LLM，同工具和预算' 260 390 393 85
Line $s 456 239 456 272 $p.blue $true 1.4
Line $s 456 357 456 390 $p.blue $true 1.4
Line $s 653 196 704 196 $p.green $true 1.5
Line $s 653 314 704 314 $p.green $true 1.5
Line $s 653 432 704 432 $p.green $true 1.5
Txt $s '严格留出药物与图谱' 708 159 204 26 16 $p.muted
Txt $s '响应误差与方向准确率' 708 199 204 44 18 $p.green $true
Txt $s '匹配条件的功能实验' 708 277 204 26 16 $p.muted
Txt $s '命中率、效应与区间' 708 317 204 44 18 $p.green $true
Txt $s '相同菜单、数据与权限' 708 395 204 26 16 $p.muted
Txt $s '有效命中、损害与成本' 708 435 204 44 18 $p.green $true

$draft=Join-Path $assetDir '1009-diagrams-draft.pptx'
$deck.SaveAs($draft)
$deck.SaveAs((Join-Path $assetDir '1009-diagrams-preview.pdf'),32)
$fit=@()
foreach($n in 9..12){$s=$deck.Slides.Item($n);foreach($sh in $s.Shapes){if($sh.HasTextFrame -and $sh.TextFrame.HasText){$fit+=[pscustomobject]@{slide=$n;text=$sh.TextFrame.TextRange.Text;height=$sh.Height;bound=$sh.TextFrame.TextRange.BoundHeight}}}}
$fit|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $assetDir 'diagram-fit.json') -Encoding utf8
$deck.Close();$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck)|Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)|Out-Null
Write-Output $draft
