$ErrorActionPreference = 'Stop'
$outPath = 'D:\MAESTRO\output-1009\1009.pptx'
$sourceDir = 'D:\MAESTRO'
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = -1
$pres = $ppt.Presentations.Add()
$pres.PageSetup.SlideWidth = 960
$pres.PageSetup.SlideHeight = 540

$C = @{
  bg = 0xF6F8F5; ink = 0x1E3432; muted = 0x5B6B67; green = 0x28745B
  mint = 0xDDEDE5; lime = 0xA7C93A; orange = 0xD8814B; paleOrange = 0xF7E7DA
  blue = 0x4A7886; paleBlue = 0xE2ECEF; white = 0xFFFFFF; line = 0xD5DED9
  dark = 0x183D37; yellow = 0xE7BD55; paleYellow = 0xF5EFCF; red = 0xB45748
}
$font = 'Microsoft YaHei'

function To-ColorRef([int]$hex) {
  $r = ($hex -shr 16) -band 255
  $g = ($hex -shr 8) -band 255
  $b = $hex -band 255
  [int]($r -bor ($g -shl 8) -bor ($b -shl 16))
}

function Add-Text($s, [string]$text, [double]$x, [double]$y, [double]$w, [double]$h, [double]$size=18, [int]$color=$C.ink, [bool]$bold=$false, [string]$align='left') {
  $sh = $s.Shapes.AddTextbox(1, $x, $y, $w, $h)
  $sh.Fill.Visible = 0
  $sh.Line.Visible = 0
  $sh.TextFrame.MarginLeft = 0
  $sh.TextFrame.MarginRight = 0
  $sh.TextFrame.MarginTop = 1
  $sh.TextFrame.MarginBottom = 1
  $sh.TextFrame.WordWrap = -1
  $sh.TextFrame.AutoSize = 0
  $tr = $sh.TextFrame.TextRange
  $tr.Text = $text
  $tr.Font.Name = $font
  $tr.Font.NameFarEast = $font
  $tr.Font.Size = $size
  $tr.Font.Bold = [int]$bold
  $tr.Font.Color.RGB = (To-ColorRef $color)
  $tr.ParagraphFormat.Alignment = $(if ($align -eq 'center') { 2 } elseif ($align -eq 'right') { 3 } else { 1 })
  $sh
}

function Add-Rect($s, [double]$x, [double]$y, [double]$w, [double]$h, [int]$fill, [int]$stroke=-1, [double]$radius=0) {
  $kind = $(if ($radius -gt 0) { 5 } else { 1 })
  $sh = $s.Shapes.AddShape($kind, $x, $y, $w, $h)
  $sh.Fill.ForeColor.RGB = (To-ColorRef $fill)
  if ($stroke -lt 0) { $sh.Line.Visible = 0 } else { $sh.Line.ForeColor.RGB = (To-ColorRef $stroke); $sh.Line.Weight = 1 }
  $sh
}

function Add-Line($s, [double]$x1, [double]$y1, [double]$x2, [double]$y2, [int]$color=$C.line, [double]$weight=1.5) {
  $ln = $s.Shapes.AddLine($x1, $y1, $x2, $y2)
  $ln.Line.ForeColor.RGB = (To-ColorRef $color)
  $ln.Line.Weight = $weight
  $ln
}

function Add-Base($n, [string]$title, [string]$subtitle='', [string]$source='') {
  $s = $pres.Slides.Add($n, 12)
  Add-Rect $s 0 0 960 540 $C.bg | Out-Null
  Add-Rect $s 36 28 5 29 $C.green | Out-Null
  Add-Text $s $title 54 24 866 40 26 $C.ink $true | Out-Null
  if ($subtitle) { Add-Text $s $subtitle 54 66 858 28 12 $C.muted $false | Out-Null }
  Add-Line $s 36 503 924 503 $C.line 1 | Out-Null
  Add-Text $s $source 38 510 800 18 8 $C.muted $false | Out-Null
  Add-Text $s ('{0:D2}' -f $n) 889 510 32 18 9 $C.green $true 'right' | Out-Null
  $s
}

function Add-Picture($s, [string]$path, [double]$x, [double]$y, [double]$w, [double]$h) {
  $s.Shapes.AddPicture($path, 0, -1, $x, $y, $w, $h) | Out-Null
}

function Add-Notes($s, [string]$text) {
  try {
    $notes = $s.NotesPage.Shapes.Placeholders(2)
    $notes.TextFrame.TextRange.Text = $text
    $notes.TextFrame.TextRange.Font.Name = $font
    $notes.TextFrame.TextRange.Font.NameFarEast = $font
  } catch { }
}

# 1 Cover
$s = $pres.Slides.Add(1, 12)
Add-Rect $s 0 0 960 540 $C.dark | Out-Null
Add-Rect $s 0 0 960 10 $C.lime | Out-Null
Add-Text $s 'MAESTRO  /  1009' 60 44 820 24 12 $C.lime $true | Out-Null
Add-Text $s '知识驱动的药物发现智能体' 60 137 820 66 34 $C.white $true | Out-Null
Add-Text $s '从单细胞扰动预测，到多智能体实验闭环，再到当前工作的证据边界' 60 218 805 52 19 0xDDE8E2 $false | Out-Null
Add-Line $s 60 317 900 317 0x4B6C62 1 | Out-Null
Add-Text $s '两篇论文的互补思想  /  面向药物发现的系统设计  /  10 月 9 日进展总结' 60 345 805 30 13 0xC2D4CB $false | Out-Null
Add-Text $s '研究组会汇报     2026-10-09' 60 461 600 22 11 $C.lime $true | Out-Null
Add-Notes $s '依据：Feng et al., Nature Machine Intelligence (2026), doi:10.1038/s42256-026-01286-w；Ghareeb et al., Nature 655, 497-505 (2026), doi:10.1038/s41586-026-10652-y；MAESTRO 当前代码与 2026-10-09 研究记录。'

# 2 Problem framing
$s = Add-Base 2 '药物发现的瓶颈：证据稀疏，决策仍需实验' '两篇论文分别补上“未测药物如何预测”和“如何把知识转成可检验假设”' 'Feng 2026; Ghareeb 2026'
$rows2 = @(
  @{y=148; n='01'; label='未测药物'; body='缺少目标细胞背景下的单细胞响应谱'; color=$C.blue},
  @{y=235; n='02'; label='知识分散'; body='靶点、机制、通路与实验结论跨多个资源'; color=$C.green},
  @{y=322; n='03'; label='验证昂贵'; body='候选排序最终仍需匹配的模型和可解释读数'; color=$C.orange}
)
foreach($r2 in $rows2) {
  Add-Text $s $r2.n 64 $r2.y 59 34 21 $r2.color $true | Out-Null
  Add-Text $s $r2.label 140 ($r2.y+1) 183 30 17 $C.ink $true | Out-Null
  Add-Text $s $r2.body 352 ($r2.y+3) 530 29 14 $C.muted $false | Out-Null
  Add-Line $s 140 ($r2.y+49) 888 ($r2.y+49) $C.line 1 | Out-Null
}
Add-Text $s 'MAP' 142 414 72 26 15 $C.green $true | Out-Null
Add-Text $s '以机制知识增强未测药物响应预测' 215 414 278 26 13 $C.ink $false | Out-Null
Add-Text $s 'Robin' 535 414 74 26 15 $C.orange $true | Out-Null
Add-Text $s '把文献假设与实验结果接成迭代流程' 611 414 281 26 13 $C.ink $false | Out-Null
Add-Notes $s '这里对比的是两篇工作的研究目标：MAP预测单细胞转录响应；Robin自动化假设生成与数据分析并由人类执行实验，属于半自主发现流程。'

# 3 MAP question
$s = Add-Base 3 'MAP 聚焦的任务：两种逐级更难的零样本外推' '把“模型没见过什么”定义清楚，才能解释泛化结果' 'Feng et al., 2026, Fig. 1-3'
Add-Text $s '训练中见过药物？' 64 146 285 30 20 $C.ink $true 'center' | Out-Null
Add-Text $s '见过' 137 204 120 24 16 $C.green $true 'center' | Out-Null
Add-Text $s '未见' 594 204 120 24 16 $C.orange $true 'center' | Out-Null
Add-Line $s 208 184 208 202 $C.line 2 | Out-Null
Add-Line $s 665 184 665 202 $C.line 2 | Out-Null
Add-Rect $s 58 242 390 145 $C.paleBlue | Out-Null
Add-Rect $s 510 242 390 145 $C.paleOrange | Out-Null
Add-Text $s '未见细胞–药物组合' 82 258 340 28 17 $C.blue $true | Out-Null
Add-Text $s '药物在其他背景出现过；测试背景中的配对被留出。' 82 299 340 45 13 $C.ink $false | Out-Null
Add-Text $s '回答：已知药物能否迁移到新细胞背景？' 82 354 340 21 11 $C.blue $true | Out-Null
Add-Text $s '未测药物' 534 258 340 28 17 $C.orange $true | Out-Null
Add-Text $s '移除测试药物全部扰动谱，并从 MAP-KG 移除相关实体与边。' 534 299 340 45 13 $C.ink $false | Out-Null
Add-Text $s '回答：只靠结构与可用注释能否外推？' 534 354 340 21 11 $C.orange $true | Out-Null
Add-Text $s '切分时同时防止图谱泄漏，未测药物推断才是真正的零样本。' 68 426 826 28 13 $C.muted $false 'center' | Out-Null
Add-Notes $s 'MAP评测：组合外推在每种细胞背景留出5%药物，并保证不同细胞背景留出的集合互不重叠。未测药物外推移除测试药物全部扰动谱，并移除MAP-KG内对应实体及相关边。'

# 4 MAP architecture
$s = Add-Base 4 'MAP：把异构生物知识对齐为机制感知药物表征' '知识图谱不是检索附件，而是药物和基因表示的训练信号' 'Feng et al., 2026, Fig. 1'
Add-Picture $s 'D:\MAESTRO\.build-1009\map_fig1.png' 44 132 601 363
Add-Text $s '证据规模' 679 164 200 19 11 $C.green $true | Out-Null
Add-Text $s '14' 674 195 110 65 42 $C.ink $true | Out-Null
Add-Text $s '个公开资源' 747 220 138 26 15 $C.muted $false | Out-Null
Add-Line $s 675 278 896 278 $C.line 1 | Out-Null
Add-Text $s '187,089' 674 293 204 41 25 $C.blue $true | Out-Null
Add-Text $s '药物实体' 677 334 204 21 12 $C.muted $false | Out-Null
Add-Text $s '694,246' 674 369 204 41 25 $C.orange $true | Out-Null
Add-Text $s '机制关系' 677 409 204 21 12 $C.muted $false | Out-Null
Add-Text $s '结构 × 序列 × 机制文本' 675 449 222 20 11 $C.ink $true | Out-Null
Add-Notes $s 'Feng et al. 构建 MAP-KG，论文摘要称整合14个公共资源；图1说明为13个数据库加PrimeKG。知识编码器包含分子、蛋白序列和文本模态；对比预训练包括属性级与关系级对齐。预测器将知识表征与STATE细胞状态模型联合使用。'

# 5 MAP results
$s = Add-Base 5 'MAP 的零样本收益：未见组合与未测药物都优于基线' '论文报告的是 top-50 DEG Pearson Δ correlation 相对最强基线提升' 'Feng et al., 2026, Fig. 2-3'
Add-Text $s '相对提升（%）' 65 142 200 20 11 $C.muted $true | Out-Null
Add-Line $s 281 181 281 391 $C.line 1 | Out-Null
Add-Line $s 281 391 876 391 $C.line 1 | Out-Null
$bars = @(
 @{y=205; label="未见细胞–药物组合`nTahoe-100M"; value=12.3; color=$C.blue},
 @{y=276; label="未测药物`nTahoe-100M"; value=11.8; color=$C.green},
 @{y=347; label="未测药物`nOP3"; value=19.8; color=$C.orange}
)
foreach($b in $bars) {
  Add-Text $s $b.label 65 ($b.y-4) 204 43 12 $C.ink $false | Out-Null
  $bw = $b.value * 22
  Add-Rect $s 290 $b.y $bw 31 $b.color | Out-Null
  Add-Text $s ('+' + $b.value + '%') (300+$bw) ($b.y+2) 90 25 16 $b.color $true | Out-Null
}
Add-Rect $s 65 416 824 53 $C.paleYellow | Out-Null
Add-Text $s 'Tahoe / SciPlex3 / OP3；伪整体评测。跨背景表现不等于跨组织或体内疗效。' 82 431 790 20 12 $C.ink $false 'center' | Out-Null
Add-Notes $s '摘要中MAP在三项基准中 top-50 DEGs Pearson delta correlation 相比最强基线提升：未见细胞-药物组合最多+12.3%，未测药物三个数据集分别达到Tahoe-100M +11.8%、OP3 +19.8%、SciPlex3 +10.4%。图中挑选代表值，不能误读为百分点。'

# 6 MAP screen evidence / limits
$s = Add-Base 6 'MAP 的筛选证据仍停留在转录与通路层' '预测排序有价值，但后续决策需要更近端、更直接的表型验证' 'Feng et al., 2026, Fig. 4; Discussion'
Add-Text $s '基因变化' 69 160 182 24 15 $C.blue $true 'center' | Out-Null
Add-Text $s '通路一致性' 387 160 182 24 15 $C.green $true 'center' | Out-Null
Add-Text $s '实验优先级' 704 160 182 24 15 $C.orange $true 'center' | Out-Null
Add-Line $s 150 238 810 238 $C.line 2 | Out-Null
Add-Rect $s 92 220 18 36 $C.blue | Out-Null
Add-Rect $s 469 220 18 36 $C.green | Out-Null
Add-Rect $s 786 220 18 36 $C.orange | Out-Null
Add-Text $s 'DEG / GSEA' 67 280 185 25 13 $C.ink $true 'center' | Out-Null
Add-Text $s "A-549：58 个留出候选中，`n5 种已批准抗癌药有 4 种进入前 15" 331 280 290 54 13 $C.ink $true 'center' | Out-Null
Add-Text $s "体外筛选候选排序`n仍需表型与机制验证" 674 280 243 48 13 $C.ink $true 'center' | Out-Null
Add-Rect $s 72 373 816 79 $C.paleOrange | Out-Null
Add-Text $s '边界' 92 389 72 20 12 $C.red $true | Out-Null
Add-Text $s '模型预测转录响应，不直接证明靶点占用、功能抑制、细胞存活或临床疗效。论文也指出基因级 token 造成计算与内存开销。' 170 385 692 52 12 $C.ink $false | Out-Null
Add-Notes $s 'MAP论文使用GSEA评估功能程序一致性，并在A-549中进行in vitro筛选排序；摘要报告58个留出化合物中5种已批准抗癌药的4种被排到前15。该证据并非药物疗效确证。作者讨论计算与内存成本，主要来自细粒度基因级交互建模。'

# 7 Robin architecture
$s = Add-Base 7 'Robin：检索、候选评估、实验分析由专长代理分工' '协调器让证据生成、实验读数与下一轮假设形成反馈链' 'Ghareeb et al., Nature 655 (2026), Fig. 1'
Add-Picture $s 'D:\MAESTRO\.build-1009\robin_fig1.png' 42 135 448 367
Add-Text $s '一次 dAMD 发现流程' 529 153 360 25 14 $C.orange $true | Out-Null
Add-Text $s '551' 527 195 143 69 43 $C.ink $true | Out-Null
Add-Text $s '篇论文' 670 226 131 24 14 $C.muted $false | Out-Null
Add-Text $s '约 30 分钟' 529 267 340 27 16 $C.green $true | Out-Null
Add-Line $s 529 309 889 309 $C.line 1 | Out-Null
Add-Text $s '75 次代理调用' 529 327 340 24 15 $C.ink $true | Out-Null
Add-Text $s "45 × Crow`n30 × Falcon" 529 359 136 47 12 $C.muted $false | Out-Null
Add-Text $s '估算运行成本' 682 359 132 18 10 $C.muted $false | Out-Null
Add-Text $s '$10.76' 681 381 133 32 19 $C.orange $true | Out-Null
Add-Text $s '节省的是知识综合时间；实验仍由研究者执行。' 529 436 355 35 11 $C.ink $true | Out-Null
Add-Notes $s 'Robin的Crow与Falcon基于PaperQA2做简明与深入检索；Finch执行RNA-seq、流式细胞术等数据分析，8条独立轨迹后进行元分析。论文的时间比较是估算，并明确湿实验由人类执行；Robin为半自主系统。'

# 8 Robin case
$s = Add-Base 8 'Robin 案例：dAMD 的 RPE 吞噬作用药物再定位' '模型提出可测假设，体外数据触发候选更新，后续实验检验外推' 'Ghareeb et al., 2026, Fig. 2-4'
Add-Picture $s 'D:\MAESTRO\.build-1009\robin_fig2.png' 47 141 560 357
Add-Text $s '筛选结果' 636 155 243 21 11 $C.orange $true | Out-Null
Add-Text $s '1.89×' 630 185 260 70 42 $C.ink $true | Out-Null
Add-Text $s 'ripasudil 对吞噬读数的提升' 635 258 255 39 12 $C.muted $false | Out-Null
Add-Line $s 635 310 893 310 $C.line 1 | Out-Null
Add-Text $s '人源复验' 635 327 100 20 11 $C.green $true | Out-Null
Add-Text $s "RPE-SC 中重测`nripasudil 与 Y-27632 均为命中" 635 353 260 50 12 $C.ink $false | Out-Null
Add-Text $s '机制线索' 635 413 100 20 11 $C.blue $true | Out-Null
Add-Text $s 'ABCA1 RNA 上调约 3 倍；仍待因果验证。' 635 439 263 25 11 $C.ink $false | Out-Null
Add-Notes $s '论文报告ripasudil在ARPE-19吞噬测定约1.89倍vehicle，后续使用来源于一名老年供体的人源RPE-SC重复验证；KL001也被筛为体外命中。Y-27632处理后的RNA-seq分析中ABCA1表达约上调3倍，作者将潜在自噬联系明确为待验证。'

# 9 comparison
$s = Add-Base 9 '两篇论文互补，但回答的问题不同' 'MAP 增强未测药物的响应预测；Robin 把知识变成迭代实验决策' 'Feng 2026; Ghareeb 2026'
Add-Text $s '比较维度' 62 143 166 24 12 $C.muted $true | Out-Null
Add-Text $s 'MAP' 313 143 254 24 16 $C.green $true 'center' | Out-Null
Add-Text $s 'Robin' 640 143 254 24 16 $C.orange $true 'center' | Out-Null
$rows = @(
 @('核心难题','未测药物的单细胞响应外推','假设、实验设计与数据解释的衔接'),
 @('知识位置','以结构/靶点/关系训练机制表示','以文献证据支持机制与候选排序'),
 @('主要输出','条件化的转录响应预测','实验候选与分析后的下一轮问题'),
 @('验证方式','零样本基准、通路排序、体外筛选','实际体外筛选及RNA-seq分析'),
 @('关键边界','转录预测不等于功能疗效','湿实验仍由研究者执行')
)
$yy=183
foreach($row in $rows) {
  Add-Line $s 59 ($yy+39) 900 ($yy+39) $C.line 1 | Out-Null
  Add-Text $s $row[0] 62 $yy 160 30 12 $C.ink $true | Out-Null
  Add-Text $s $row[1] 253 $yy 353 31 12 $C.ink $false | Out-Null
  Add-Text $s $row[2] 620 $yy 274 31 12 $C.ink $false | Out-Null
  $yy += 52
}
Add-Notes $s '两篇论文可以组合成一个药物发现框架，但不要把MAP的转录预测准确度与Robin的实验闭环当成同一种证据。MAP的验证以计算基准和体外排序为主；Robin实验由人类研究者执行。'

# 10 integrated architecture
$s = Add-Base 10 '面向药物发现智能体：知识、预测与实验决策各守边界' '推荐把两篇论文当作可组合模块，按来源与决策权限接入' '设计综合：MAP + Robin + MAESTRO task.md'
$blocks = @(
 @{x=48; w=184; title='知识与文献'; body="靶点、通路、机制`n来源与证据等级"; color=$C.blue; tint=$C.paleBlue},
 @{x=274; w=184; title='候选响应'; body="结构 / 靶点 / 细胞背景`n预测转录响应与适用域"; color=$C.green; tint=$C.mint},
 @{x=500; w=184; title='实验选择'; body="确定候选差异`n计算测量价值与成本"; color=$C.orange; tint=$C.paleYellow},
 @{x=726; w=184; title='实验分析'; body="读数质控与统计`n更新结论与后续问题"; color=$C.red; tint=$C.paleOrange}
)
foreach($b in $blocks) {
  Add-Rect $s $b.x 194 $b.w 139 $b.tint | Out-Null
  Add-Text $s $b.title ($b.x+10) 211 ($b.w-20) 23 14 $b.color $true 'center' | Out-Null
  Add-Text $s $b.body ($b.x+10) 258 ($b.w-20) 55 12 $C.ink $false 'center' | Out-Null
}
foreach($x in @(232,458,684)) { Add-Line $s $x 263 ($x+36) 263 $C.green 2 | Out-Null }
Add-Line $s 817 334 817 387 $C.orange 2 | Out-Null
Add-Line $s 817 387 141 387 $C.orange 2 | Out-Null
Add-Line $s 141 387 141 336 $C.orange 2 | Out-Null
Add-Text $s '实验结果回流，下一轮根据剩余不确定性决定是否继续' 266 371 424 27 12 $C.orange $true 'center' | Out-Null
Add-Text $s '共同记录：候选身份  /  细胞背景  /  剂量与时间  /  读数类型  /  来源  /  置信与拒答原因' 74 438 811 24 11 $C.muted $false 'center' | Out-Null
Add-Notes $s '这是基于两篇论文和MAESTRO现有任务契约的设计综合，不是论文已实现或已验证的结论。预测通道用于计划，不得把RNA预测转写成靶点活动或药效证据。'

# 11 decision gates
$s = Add-Base 11 '智能体决策要看“哪项测量会改变选择”' '预测更准不自动带来更好候选；需要把候选比较损失和测量成本纳入评测' 'MAESTRO task.md; research/REPORT.md'
Add-Text $s '候选与机制解释' 62 157 192 25 14 $C.ink $true 'center' | Out-Null
Add-Line $s 255 171 301 171 $C.green 2 | Out-Null
Add-Text $s '条件预测' 303 157 132 25 14 $C.green $true 'center' | Out-Null
Add-Line $s 436 171 479 171 $C.green 2 | Out-Null
Add-Text $s '信息价值' 482 157 138 25 14 $C.orange $true 'center' | Out-Null
Add-Line $s 622 171 666 171 $C.orange 2 | Out-Null
Add-Text $s '行动门控' 669 157 126 25 14 $C.red $true 'center' | Out-Null
Add-Line $s 798 171 840 171 $C.orange 2 | Out-Null
Add-Text $s '测量 / 停止' 840 157 87 25 13 $C.ink $true 'center' | Out-Null
Add-Rect $s 69 218 823 91 $C.paleBlue | Out-Null
Add-Text $s '预测资格检查' 89 237 143 22 12 $C.blue $true | Out-Null
Add-Text $s '背景、化合物、剂量、时间、读数和模型版本是否匹配？不匹配则拒答或回退。' 247 234 615 43 12 $C.ink $false | Out-Null
Add-Rect $s 69 326 823 91 $C.mint | Out-Null
Add-Text $s '证据资格检查' 89 345 143 22 12 $C.green $true | Out-Null
Add-Text $s '模型预测、文献推断、真实观测分别保留来源；只有合格观测可以支持对应科学更新。' 247 342 615 43 12 $C.ink $false | Out-Null
Add-Text $s '停止准则需要独立校准的模型风险、成本、失败与延迟参数；缺项时不要把“零购买”解释成价值为零。' 73 445 817 31 12 $C.red $true 'center' | Out-Null
Add-Notes $s 'MAESTRO当前操作契约强调预测条件匹配，拒答边界，实测证据与模型预测来源分离。最新决策价值研究中，失败/延迟和真实成本效用换算没有注册，严格EVSI因此拒绝行动，而不是断言测量没有价值。'

# 12 Sep27 baseline
$s = Add-Base 12 '0927 汇报的阶段：双核心架构已成形，核心优势待验证' '0927.pptx 是 9 月 27 日快照；当时的主要瓶颈是任务可区分性、样本数与风险校准' '0927.pptx; log/20260927/0927'
Add-Text $s '76%–82%' 61 153 250 65 36 $C.red $true | Out-Null
Add-Text $s 'L1000 案例无法由现有行动区分机制' 63 222 247 45 12 $C.muted $false | Out-Null
Add-Line $s 336 151 336 337 $C.line 1 | Out-Null
Add-Text $s '功效估算：正确率提升 2 个百分点' 374 151 506 24 14 $C.ink $true | Out-Null
Add-Text $s '当前样本' 375 203 113 22 11 $C.muted $false | Out-Null
Add-Rect $s 494 207 174 16 $C.blue | Out-Null
Add-Text $s '42–256' 685 199 115 26 14 $C.blue $true | Out-Null
Add-Text $s '所需样本' 375 265 113 22 11 $C.muted $false | Out-Null
Add-Rect $s 494 268 299 16 $C.orange | Out-Null
Add-Text $s '345–813' 801 260 93 26 14 $C.orange $true | Out-Null
Add-Text $s 'GSE70138 外部单元只有 38' 375 312 512 23 11 $C.red $true | Out-Null
Add-Line $s 60 368 898 368 $C.line 1 | Out-Null
Add-Text $s '已建立' 67 390 94 22 13 $C.green $true | Out-Null
Add-Text $s '智能体定位解释缺口并组织补测；虚拟细胞按条件预测读数。' 165 388 713 28 13 $C.ink $false | Out-Null
Add-Text $s '待证明' 67 431 94 22 13 $C.orange $true | Out-Null
Add-Text $s '世界模型是否提高决策价值，智能体是否胜过同信息强基线。' 165 429 713 28 13 $C.ink $false | Out-Null
Add-Notes $s '0927.pptx第8页报告protocol-v2 development screen：20 tasks，12,428 episodes；76%-82% L1000案例无法经行动集合区分。其功效分析估算345-813独立单元以检测正确率提升2个百分点，现有分层为42-256，外部GSE70138为38。该页当时已表明样本量限制。'

# 13 timeline current updates
$s = Add-Base 13 '9 月 27 日之后：实现更完整，科学结论也更克制' '10 月 9 日研究记录把预测、反馈解释与行动价值拆开检查' 'research/REPORT.md; log/20261009/README.md'
Add-Line $s 92 197 864 197 $C.line 3 | Out-Null
$events = @(
 @{x=112; date='10/07'; title='公开数据与闭环'; body='两轮真实工具与测量回流的工程链路打通。'; color=$C.blue},
 @{x=340; date='10/08'; title='MAP 启发试点'; body='知识表示对齐改善；响应修正未通过验证，决策与 M2 相同。'; color=$C.green},
 @{x=568; date='10/08'; title='原权重探测'; body='公开前向存在输入映射、剂量与输出顺序问题；未证实原生 MAP 响应。'; color=$C.orange},
 @{x=796; date='10/09'; title='读数与反馈'; body='小型预测候选通过开发门槛；决策优势仍不稳定。'; color=$C.red}
)
foreach($e in $events) {
  Add-Rect $s $e.x 186 15 22 $e.color | Out-Null
  Add-Text $s $e.date ($e.x-38) 143 92 22 12 $e.color $true 'center' | Out-Null
  Add-Text $s $e.title ($e.x-53) 231 136 27 13 $C.ink $true 'center' | Out-Null
  Add-Text $s $e.body ($e.x-66) 269 166 78 11 $C.muted $false 'center' | Out-Null
}
Add-Rect $s 67 388 824 66 $C.paleYellow | Out-Null
Add-Text $s '重要更新：10/09 清理未晋升的 MAP runtime repair；代码与临时产物已移除，历史验证仍保留在记录中。' 84 405 790 41 12 $C.ink $true 'center' | Out-Null
Add-Notes $s '来源：research/REPORT.md对10/7-10/9研究的综合；log/20261009/README.md记录MAP runtime repair删除，研究结论维持“工程检查通过但科学收益未证实”。'

# 14 latest evidence
$s = Add-Base 14 '10 月 9 日最新结果：预测信号存在，稳定决策优势未建立' '对照从旧更新器扩展到 no-screen 后，收益解释发生变化' 'research/EVIDENCE.md, 10/09 studies'
Add-Text $s '读数校准' 62 142 232 22 13 $C.green $true | Out-Null
Add-Text $s "MSE 参考折 -2.17%`n5 个已暴露背景 -7.84%" 62 175 235 53 18 $C.ink $true | Out-Null
Add-Text $s '最终 equal-budget 候选集与 M2 完全相同' 62 238 280 37 12 $C.muted $false | Out-Null
Add-Line $s 335 142 335 318 $C.line 1 | Out-Null
Add-Text $s '联合反馈开发集' 364 142 248 22 13 $C.blue $true | Out-Null
Add-Text $s "43 个参考背景`n比旧反馈 KG +6.55%" 364 175 232 53 18 $C.ink $true | Out-Null
Add-Text $s "5 个已暴露目标背景`n比旧反馈 KG -0.87%" 364 241 232 53 14 $C.red $true | Out-Null
Add-Line $s 633 142 633 318 $C.line 1 | Out-Null
Add-Text $s '严格 LOO（39-gene RNA score）' 662 142 239 22 11 $C.orange $true | Out-Null
Add-Text $s "联合 KG vs no-screen`n+0.000054" 662 175 239 53 17 $C.ink $true | Out-Null
Add-Text $s "多用 8 个测量单位`n筛选成本与效用未能认证" 662 241 239 51 13 $C.red $true | Out-Null
Add-Rect $s 60 353 840 97 $C.dark | Out-Null
Add-Text $s '解释' 82 371 70 20 12 $C.lime $true | Out-Null
Add-Text $s '10/09 联合反馈在完整参考背景上通过开发门槛，但 5 个已暴露目标上的结果不稳。最新严格 LOO 中，no-screen 是必要主基线，联合 KG 的增益几乎为零。' 159 367 713 53 12 $C.white $false | Out-Null
Add-Notes $s '读数校准：参考外层MSE相对固定M2下降2.17%，5个已暴露目标背景下降7.84%；只在一个背景产生初始B集合替换，终点与M2相同。联合反馈开发实验相对旧反馈KG在43个参考背景+6.55%，5个已暴露目标-0.87%，但曝光目标非独立确认。最新严格完整背景LOO：joint KG均值终端RNA分数0.1620356，no-screen 0.1619812，差0.0000544；二者A测量分别8和0。单位成本/效用转换和失败/延迟参数未注册。'

# 15 next steps and references
$s = Add-Base 15 '下一阶段：用独立证据验证候选比较与测量价值' '研究主张聚焦在“相同信息与资源下，是否能以更少观测做出更好的候选决策”' 'Feng 2026; Ghareeb 2026; MAESTRO research'
$items = @(
 @('1','外部转移','筛出未参与训练且来源合格的细胞背景与观测单位；锁定完整候选菜单。'),
 @('2','同预算比较','对照 no-screen、现有 KG、固定筛选和反馈策略；预先锁定成本、失败与停止规则。'),
 @('3','表型桥接','把 RNA 响应与目标结合/功能抑制、细胞存活或目标表型分开测量，验证前不互相替代。'),
 @('4','智能体归因','同一数据、工具与预算比较 LLM 与确定性策略；计入错误行动、延迟和调用成本。')
)
$yy=143
foreach($it in $items) {
  Add-Text $s $it[0] 64 $yy 37 25 17 $C.green $true 'center' | Out-Null
  Add-Text $s $it[1] 115 $yy 146 25 13 $C.ink $true | Out-Null
  Add-Text $s $it[2] 269 $yy 617 39 11 $C.muted $false | Out-Null
  Add-Line $s 63 ($yy+43) 899 ($yy+43) $C.line 1 | Out-Null
  $yy += 61
}
Add-Text $s '参考文献' 63 398 91 20 10 $C.orange $true | Out-Null
Add-Text $s 'Feng et al. “A knowledge-driven framework for predicting single-cell responses for unprofiled drugs.” Nature Machine Intelligence (2026). doi:10.1038/s42256-026-01286-w.' 157 394 730 25 8 $C.ink $false | Out-Null
Add-Text $s 'Ghareeb et al. “A multi-agent system for automating scientific discovery.” Nature 655, 497–505 (2026). doi:10.1038/s41586-026-10652-y.' 157 423 730 25 8 $C.ink $false | Out-Null
Add-Notes $s '建议实验顺序：先解决独立背景与完整候选菜单来源资格，再确认同信息同预算下的候选集合效用，之后验证RNA到功能表型的桥接，最后单独评测LLM是否真正贡献选择价值。'

$pres.SaveAs($outPath)
$pres.Close()
$ppt.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
Write-Output $outPath
