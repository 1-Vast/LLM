$ErrorActionPreference='Stop'
$buildDir='D:\MAESTRO\.build-1009\revision\depth'
$target='C:\Users\59964\Desktop\24计算机科学与技术2\郑淼\生物信息\1009.pptx'
$before=Join-Path $buildDir '1009-before-depth.pptx'
if(!(Test-Path -LiteralPath $before)){Copy-Item -LiteralPath $target -Destination $before}
$draft=Join-Path $buildDir '1009-depth-draft.pptx'
$app=New-Object -ComObject PowerPoint.Application
for($i=$app.Presentations.Count;$i -ge 1;$i--){$p=$app.Presentations.Item($i);if($p.FullName -eq $draft -or $p.FullName -eq $before){$p.Saved=-1;$p.Close()}}
$deck=$app.Presentations.Open($before,-1,0,0)
$palette=@{ink=0x26383D;muted=0x617079;green=0x527C71;blue=0x637F94;line=0xDCE4E4;white=0xFFFFFF}
function RGB([int]$hex){[int](($hex -shr 16 -band 255) -bor (($hex -shr 8 -band 255) -shl 8) -bor (($hex -band 255) -shl 16))}
function Txt($s,[string]$t,[double]$x,[double]$y,[double]$w,[double]$h,[double]$size,[string]$color='ink',[bool]$bold=$false){
 $sh=$s.Shapes.AddTextbox(1,$x,$y,$w,$h);$sh.Line.Visible=0;$sh.Fill.Visible=0
 $sh.TextFrame.MarginLeft=0;$sh.TextFrame.MarginRight=0;$sh.TextFrame.MarginTop=0;$sh.TextFrame.MarginBottom=0
 $sh.TextFrame.WordWrap=-1;$sh.TextFrame.AutoSize=0;$sh.TextFrame2.AutoSize=0
 $r=$sh.TextFrame.TextRange;$r.Text=$t;$r.Font.Name='Microsoft YaHei';$r.Font.NameFarEast='Microsoft YaHei';$r.Font.Size=$size
 $r.Font.Color.RGB=(RGB $palette[$color]);$r.Font.Bold=[int][bool]$bold;$r.ParagraphFormat.SpaceAfter=3;$sh.Height=$h
}
function Rule($s,[double]$x,[double]$y,[double]$w){$sh=$s.Shapes.AddLine($x,$y,($x+$w),$y);$sh.Line.ForeColor.RGB=(RGB $palette.line);$sh.Line.Weight=1}
$spec=Get-Content -LiteralPath (Join-Path $buildDir 'slides.json') -Raw | ConvertFrom-Json
foreach($item in $spec){
 $s=$deck.Slides.Item([int]$item.slide)
 for($j=$s.Shapes.Count;$j -ge 1;$j--){$s.Shapes.Item($j).Delete()}
 Txt $s $item.section 48 23 864 20 11 green $true
 Txt $s $item.title 48 57 864 43 27 ink $true
 Txt $s $item.subtitle 48 106 864 31 14 muted
 Rule $s 48 501 864
 Txt $s $item.source 48 514 814 16 9 muted
 Txt $s ('{0:D2}' -f $item.slide) 888 512 30 18 11 green
 foreach($o in $item.objects){switch($o.type){
  'text' {Txt $s $o.text $o.x $o.y $o.w $o.h $o.size $o.color $o.bold}
  'line' {Rule $s $o.x $o.y $o.w}
  'bar' {$sh=$s.Shapes.AddShape(1,$o.x,$o.y,$o.w,$o.h);$sh.Line.Visible=0;$sh.Fill.ForeColor.RGB=(RGB $palette[$o.color])}
  'picture' {$sh=$s.Shapes.AddPicture($o.path,0,-1,$o.x,$o.y,-1,-1);$r=[Math]::Min($o.w/$sh.Width,$o.h/$sh.Height);$nw=$sh.Width*$r;$nh=$sh.Height*$r;$sh.LockAspectRatio=0;$sh.Width=$nw;$sh.Height=$nh;$sh.Left=$o.x+($o.w-$nw)/2;$sh.Top=$o.y+($o.h-$nh)/2}
 }}
}
$deck.SaveAs($draft)
$deck.SaveAs((Join-Path $buildDir 'preview.pdf'),32)
$fit=@()
foreach($s in $deck.Slides){foreach($sh in $s.Shapes){if($sh.HasTextFrame -and $sh.TextFrame.HasText){$fit+=[pscustomobject]@{slide=$s.SlideIndex;text=$sh.TextFrame.TextRange.Text;height=$sh.Height;bound=$sh.TextFrame.TextRange.BoundHeight;top=$sh.Top}}}}
$fit|ConvertTo-Json -Depth 3|Set-Content -LiteralPath (Join-Path $buildDir 'fit.json') -Encoding utf8
$deck.Close();$app.Quit()
Write-Output $draft
