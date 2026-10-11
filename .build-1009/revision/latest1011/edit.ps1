$ErrorActionPreference='Stop'
$buildDir='D:\MAESTRO\.build-1009\revision\latest1011'
$source='C:\Users\59964\Desktop\24计算机科学与技术2\郑淼\生物信息\1009.pptx'
$draft=Join-Path $buildDir '1009-latest1011-draft.pptx'
Copy-Item -LiteralPath $source -Destination (Join-Path $buildDir '1009-before-progress-update.pptx') -Force
$app=New-Object -ComObject PowerPoint.Application
$deck=$app.Presentations.Open($source,-1,0,0)
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


function Bar($s,$x,$y,$w,$h,$color){$sh=$s.Shapes.AddShape(1,$x,$y,$w,$h);$sh.Line.Visible=0;$sh.Fill.ForeColor.RGB=(RGB $color)}
$s=$deck.Slides.Item(14)
Reset $s '阶段总结   MAESTRO / 10.11 确认实验' '转录近邻迁移验证了选择性杀伤预测的增益' '任务：预测药物对 578 条癌细胞系的杀伤分布。421 种封存确认药物中，101 种满足杀伤标准。' '项目证据截至 2026-10-11：mechanism_routing / PROTOCOL、RESULTS、核验记录'
Txt $s '实测 L1000 响应  →  选择 5 个转录近邻药物  →  加权迁移其 PRISM 杀伤谱' 48 153 864 30 20 $palette.green $true
Txt $s '9 条细胞系 × 6/24 h，10 μM；按共享条件的余弦相似度选邻居。PRISM 目标读数为 2.5 μM。' 48 195 864 24 15 $palette.muted
Rule $s 48 235 864
Txt $s '未见机制类别：平均选择性 r' 48 250 440 28 19 $palette.ink $true
Txt $s '靶点近邻' 48 301 118 28 17
Bar $s 174 303 (0.037491619402148575*1800) 23 $palette.blue
Txt $s '0.038' 258 301 80 27 17 $palette.blue $true
Txt $s '化学近邻' 48 351 118 28 17
Bar $s 174 353 (0.05292952033024978*1800) 23 $palette.blue
Txt $s '0.053' 285 351 80 27 17 $palette.blue $true
Txt $s '转录近邻' 48 401 118 28 17 $palette.green $true
Bar $s 174 403 (0.15322475179118863*1800) 23 $palette.green
Txt $s '0.153' 464 401 84 27 17 $palette.green $true
Txt $s '同机制参考药物全部移除。选择性 r 去除通用杀伤谱，检查“哪些细胞更敏感”的预测。' 48 441 482 34 14 $palette.muted
Txt $s '+0.116 r' 576 249 186 38 26 $palette.green $true
Txt $s '超过靶点近邻：校正区间 [0.053, 0.181]' 576 291 336 26 16
Txt $s '+0.049 r' 576 327 186 38 26 $palette.green $true
Txt $s '补充本药 160 系部分筛选：[0.004, 0.097]' 576 369 336 26 16
Txt $s '+0.103 r' 576 405 186 38 26 $palette.green $true
Txt $s '独立复筛再次优于靶点：[0.049, 0.160]' 576 447 336 26 16
Txt $s '已纳入转录迁移模块；证据来自公共实测响应与筛选数据，尚需跨条件和新实验验证。' 48 481 864 17 12.5 $palette.muted
$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=@'
最新进展来自2026-10-11 Block N（mechanism_routing），替换此前仅突出坐标认证和G1开发信号的总结。问题是：利用药物的L1000响应，能否预测它对哪些癌细胞系产生更强杀伤，以及LLM是否有额外价值？这次“虚拟细胞”实现是实测转录近邻迁移，输入不是STATE或MAP生成的RNA。L1000来自GSE92742，978 landmark genes，9条细胞系的6/24h、10μM处理；目标是PRISM19Q4 primary的578系、2.5μM杀伤谱。两种数据的条件不相同，经验结果支持本次映射任务，不能声称已建立同培养单元的因果或时间桥接。

1403药物按机制类内划分：701参考、281开发、421确认；确认值在方案冻结之前封存。确认时982参考加开发药物作为参考池。101确认药物至少在5%细胞系产生log fold change<-1，组成预测效果评价人群；信任排序使用全部421药物。未见机制类别设置移除每个查询药物的同类参考药物及智能体的同类词汇。近邻按共享细胞×时间条件的平均余弦相似度选择5个，正相似度作权重，迁移实测PRISM谱。

选择性r先从预测和观测中分别回归去除通用杀伤谱G，再对细胞系求Pearson相关，评价敏感性分布。101活性确认药物的均值为：转录迁移0.15322475，靶点kNN0.03749162，Morgan化学kNN0.05292952。转录vs靶点Δr=0.11573313，机制类聚类bootstrap4000次、VC八个对比Bonferroni校正（99.375%）区间[0.05344536,0.18149802]，PASS；vs化学Δr=0.10029523，区间[0.03007173,0.17746861]。V6添加到160系部分筛选的ridge上，在独立281测试系评价：0.19370605 vs0.14478771，Δr=0.04891834，区间[0.00367681,0.09718775]。V7在独立secondary复筛的89活性药物上，L=0.14756211、T=0.04475845，Δr=0.10280366，区间[0.04879022,0.16032215]。确认条件下这些增益通过注册规则；绝对相关仍较低，secondary实测primary的一致性上限约0.320。

模块transfer_profile、signature_similarity、selective_r及top similarity信任分数已纳入src/virtual_cell/transcriptional_transfer.py，保留条件适用范围与具名拒绝。缺失参考值规则的推广实现改为跳过缺失值，记录事后影响均值不超过0.001。没有LLM角色被推广。没有购买新湿实验样本。当前支持公开数据中实测转录信息的预测收益，不等价于发现新药、临床疗效或完整双核决策优势。

核验：8/9冻结检查通过；recomputed_contrasts_match因CSV精度使A3一个描述性负差变平局而失败。后冻结补充核验保留原失败记录，注册估计与区间差异≤8.3e-17，全部判定不变。结果置换负对照的八个VC对比均不支持。

来源：D:/MAESTRO/research/astra/mechanism_routing_20261011/PROTOCOL.md、RESULTS.json、VERIFIED.json、VERIFIED_SUPPLEMENT.json、DEVIATIONS.json；D:/MAESTRO/log/20261011/MECHANISM_ROUTING.json；D:/MAESTRO/src/virtual_cell/transcriptional_transfer.py。
'@

$s=$deck.Slides.Item(15)
Reset $s '阶段总结   MAESTRO / 智能体边界与后续工作' '明确智能体的增益边界，再验证可靠协作' '文献预测、近邻审查、筛后解释、信任判断四种角色均未显示额外收益；两项对比出现显著损害。' '最新证据：mechanism_routing（10.11）；kinetic_horizon、mechanism_falsification（10.10）'
Txt $s 'LLM 加入后的效果差（Δr）' 48 155 440 28 19 $palette.green $true
Txt $s '近邻审查替代转录迁移' 48 201 437 25 17
Txt $s '−0.052' 48 237 170 41 29 $palette.blue $true
Txt $s '校正区间 [−0.091, −0.017]' 230 246 258 24 16
Txt $s '文献预测与转录迁移融合' 48 300 437 25 17
Txt $s '−0.025' 48 336 170 41 29 $palette.blue $true
Txt $s '校正区间 [−0.051, −0.003]' 230 345 258 24 16
Txt $s '事后诊断：约 63% 的活性药物被审查器拒绝所有近邻。按已知机制排斥跨机制相似性，可能丢失有效表型信号。' 48 394 437 77 17
Txt $s '近期实验形成的使用边界' 530 155 382 28 19 $palette.ink $true
Txt $s '跨平台与时间：STATE 加入先验后 Δr = −0.091；早期状态不能默认替代后期药效测量。' 530 198 382 71 17
Txt $s '机制证伪：502 药物的真实机制保留率为 89.2%，强活性组仅 77.6%；自动淘汰机制尚未通过门槛。' 530 278 382 71 17
Txt $s '下一步：已有方法作为基线，角色逐项准入' 530 365 382 28 18 $palette.green $true
Txt $s '保留跨机制近邻，比较软权重与硬淘汰；先验证错误拒绝率，再接入真实实验反馈。' 530 405 382 66 17
Txt $s '后续设计尚待验证；当前转录迁移尚未证明可替代 40 系部分筛选，也未建立完整双核决策优势。' 48 479 864 20 13 $palette.muted
$s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=@'
Block N把LLM职责拆为四种并逐项与强非LLM对照比较，采用deepseek-flash、thinking off与冻结提示词。预测者从文献路由机制类；审查者保留或删除十个转录近邻；解释者看到40发现系中的最高和最低20系并提出基因组特征；信任判断合并保留数量、预测杀伤与VC相似度。四种角色的七项注册对比均未PASS。A4审查者vs转录迁移Δr=-0.05180801，agent七对比Bonferroni校正（约99.29%）区间[-0.09115363,-0.01681211]，HARM；A2文献预测加入VC=-0.02492064，区间[-0.05107673,-0.00309378]，HARM。其余NOT_SUPPORTED不代表已证明所有LLM永远无效，只限定当前任务、模型、提示与对照。

事后错误诊断中，审查者平均只保留1.1188/10近邻，64/101活性药物（约63.4%）被全部拒绝。近邻的有效信息可以跨已标注机制，硬性要求机制一致可能误删。这个原因解释属于事后诊断，下一步软权重或保留跨机制邻居是拟议实验，不是已验证的修复。开发阶段thinking/pro对预测与解释未改变结论，pro审查对14例可能有改善，但确认层未执行，不能推广“模型规模完全无效”。研究总记录支出7.4575美元，1044确认调用，无新实验购买。

10.10 Block K检验24h早期状态能否支持5天PRISM选择：48条MIX-Seq确认系、六药，实测早期状态对DepMap先验增量-0.021、95%CI[-0.109,0.078]；STATE预测增量-0.091、CI[-0.182,-0.005]，平台迁移受限。trametinib单药时间序列中只有48h测量显现超过先验的增益，不能推广所有药物的最佳时间。冻结评估存在非配对估计问题，独立算术检查失败；事后配对分析不改变判定。已加入基于区间下界且可弃权的plan_measure_or_predict契约。

10.10 Block M为424机制类、502封存L1000药物、每药四响应的校准证伪研究。总体真实机制保留覆盖0.8924，最强活性层49药仅0.7755，低于预定0.80底线。类别内容相比打乱标签减少约19个存活候选，但文献/批判/类比/主动设计没有成立的独立智能体贡献；自动淘汰机制未推广。类标签与四个单剂量响应不能证明分子因果。

下一阶段建议（尚未执行）：以转录迁移作为强基线，限制LLM硬淘汰，先比较原样迁移、柔性权重、明确机制冲突标记和确定性同工具策略。用误删有效邻居、最终选择效用、损害和全成本验收，先开发修复再冻结新确认层。验证不同剂量、平台和时间；功能命中后再进行机制干预。可借鉴MAP保留作用方向与条件，借鉴Robin保留引用、代码与实测反馈，二者本身不能补足本项目尚未成立的增益。

对0927以来的总结：运行闭环与两文件39/39坐标认证已经形成基础；G1预测是开发信号。10.11新增的是功能筛选目标上的、块内封存确认和独立复筛支持的转录信息收益。旧RNA观测路线P0.6未放行、P2仍关闭；新的Block N确认不解除旧门控。报告开头和SCIENTIFIC_STATUS仍标10.10，因此最新结论以日期更晚的冻结试验、RESULTS及receipt为准，不把旧汇总日期当成最新状态。

来源：D:/MAESTRO/research/astra/mechanism_routing_20261011/RESULTS.json、posthoc/agent_failure_modes.json、PROTOCOL.md、README.md；D:/MAESTRO/research/astra/kinetic_horizon_20261010/RESULTS.json、README.md；D:/MAESTRO/research/astra/mechanism_falsification_20261010/RESULTS.json、README.md；D:/MAESTRO/research/EVIDENCE.md；D:/MAESTRO/research/REPORT.md。
'@

foreach($s in $deck.Slides){foreach($sh in $s.Shapes){if($sh.HasTextFrame -and $sh.TextFrame.HasText -and $sh.Left -gt 880 -and $sh.Top -gt 500 -and $sh.Width -lt 50){if($sh.TextFrame.TextRange.Text -match '^\d{2}$'){$sh.TextFrame.TextRange.Text=('{0:D2}' -f $s.SlideIndex)}}}}
$coverNote=$deck.Slides.Item(1).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text
$coverNote=$coverNote.Replace('资料截至2026-10-10','项目资料更新截至2026-10-11')
$deck.Slides.Item(1).NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text=$coverNote
$deck.SaveAs($draft)
$deck.SaveAs((Join-Path $buildDir 'latest-preview.pdf'),32)
$fit=@()
foreach($s in $deck.Slides){foreach($sh in $s.Shapes){if($sh.HasTextFrame -and $sh.TextFrame.HasText){$fit+=[pscustomobject]@{slide=$s.SlideIndex;text=$sh.TextFrame.TextRange.Text;height=$sh.Height;bound=$sh.TextFrame.TextRange.BoundHeight;top=$sh.Top}}}}
$fit|ConvertTo-Json -Depth 3|Set-Content -LiteralPath (Join-Path $buildDir 'fit.json') -Encoding utf8
$deck.Close();$app.Quit()
Write-Output $draft
