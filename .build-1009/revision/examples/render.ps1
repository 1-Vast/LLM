$ErrorActionPreference='Stop'
$a=New-Object -ComObject PowerPoint.Application
foreach($name in @('组会十二','组会十（讲解）')) {
$p=$a.Presentations.Open(('C:\Users\59964\Desktop\24计算机科学与技术2\郑淼\生物信息\组会\'+$name+'.pptx'),-1,0,0)
foreach($i in $(if($name -eq '组会十二'){@(3,4,5,6,7,10,11,12)}else{@(3,6,7,14,16)})) {
$p.Slides.Item($i).Export(('D:\MAESTRO\.build-1009\revision\examples\'+$name+'-'+$i+'.png'),'PNG',1440,810)
}
$p.Close()
}
$a.Quit()
