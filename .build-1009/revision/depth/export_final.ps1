$ErrorActionPreference='Stop'
$buildDir='D:\MAESTRO\.build-1009\revision\depth'
$word=New-Object -ComObject Word.Application
$word.Visible=$false
$word.DisplayAlerts=0
$doc=$word.Documents.Open((Join-Path $buildDir '1009-逐页讲解稿.docx'),$false,$true)
$doc.ExportAsFixedFormat((Join-Path $buildDir 'notes-preview.pdf'),17)
$doc.Close(0)
$word.Quit()
$ppt=New-Object -ComObject PowerPoint.Application
$deck=$ppt.Presentations.Open((Join-Path $buildDir '1009-with-notes.pptx'),-1,0,0)
$deck.SaveAs((Join-Path $buildDir 'final-preview.pdf'),32)
$deck.Close()
$ppt.Quit()
Write-Output 'Word and PowerPoint previews exported.'
