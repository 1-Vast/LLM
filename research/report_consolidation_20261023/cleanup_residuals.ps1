$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath('D:\MAESTRO')
$taskResearch = Join-Path $taskRoot 'research'
$taskOut = Join-Path $taskRoot 'log\20261023\report_consolidation'
$taskPlan = Get-Content -LiteralPath (Join-Path $taskOut 'APPROVED_DELETIONS.json') -Raw | ConvertFrom-Json
$taskReceiptPath = Join-Path $taskOut 'RESIDUAL_CLEANUP_RECEIPT.json'
if (Test-Path -LiteralPath $taskReceiptPath) { throw 'Residual receipt already exists' }
$taskEntries = @()
foreach ($taskRelativeOwner in $taskPlan.directories) {
    $taskOwner = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskRelativeOwner))
    if (-not $taskOwner.StartsWith($taskResearch + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Owner outside research' }
    if (-not (Test-Path -LiteralPath $taskOwner)) { continue }
    foreach ($taskFile in Get-ChildItem -LiteralPath $taskOwner -Recurse -File) {
        $taskCache = $taskFile.Extension.ToLowerInvariant() -in @('.pyc','.pyo')
        $taskSourceDocument = $taskFile.Extension.ToLowerInvariant() -in @('.rmd','.md','.txt') -or $taskFile.Name -eq 'LICENSE'
        if (-not ($taskCache -or $taskSourceDocument)) { throw ('Unreviewed remaining file: ' + $taskFile.FullName) }
        $taskRelative = $taskFile.FullName.Substring($taskRoot.Length + 1).Replace([char]92,[char]47)
        $taskEntries += [PSCustomObject]@{ path=$taskRelative; full_path=$taskFile.FullName; bytes=$taskFile.Length; sha256=(Get-FileHash -LiteralPath $taskFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); cache=$taskCache }
    }
}
$taskDone = [System.Collections.Generic.List[object]]::new()
foreach ($taskEntry in $taskEntries) {
    $taskDataRelative = $null
    $taskOldLog = $null
    if (-not $taskEntry.cache) {
        $taskTail = $taskEntry.path.Substring('research/'.Length)
        $taskDataRelative = 'data/external/retired_research_sources/' + $taskTail
        $taskTarget = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskDataRelative))
        if (-not $taskTarget.StartsWith((Join-Path $taskRoot 'data') + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'External source destination outside data' }
        [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($taskTarget)) | Out-Null
        if (-not (Test-Path -LiteralPath $taskTarget)) { Copy-Item -LiteralPath $taskEntry.full_path -Destination $taskTarget }
        if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'External source copy changed' }
        $taskOldLog = 'log/research_records/' + $taskTail
        $taskOldLogFull = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskOldLog))
        if (Test-Path -LiteralPath $taskOldLogFull) {
            if ((Get-FileHash -LiteralPath $taskOldLogFull -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'Archive source mismatch' }
            Remove-Item -LiteralPath $taskOldLogFull -Force
        } else { $taskOldLog = $null }
    }
    if ((Get-FileHash -LiteralPath $taskEntry.full_path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'Remaining source changed' }
    Remove-Item -LiteralPath $taskEntry.full_path -Force
    $taskDone.Add([PSCustomObject]@{ old_path=$taskEntry.path; old_log_path=$taskOldLog; data_path=$taskDataRelative; bytes=$taskEntry.bytes; sha256=$taskEntry.sha256; cache=$taskEntry.cache })
}
foreach ($taskRelativeOwner in $taskPlan.directories) {
    $taskOwner = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskRelativeOwner))
    if (-not (Test-Path -LiteralPath $taskOwner)) { continue }
    $taskFolders = @((Get-ChildItem -LiteralPath $taskOwner -Directory -Recurse).FullName) + @($taskOwner)
    foreach ($taskFolder in ($taskFolders | Sort-Object Length -Descending)) {
        $taskChecked = [System.IO.Path]::GetFullPath($taskFolder)
        if (-not $taskChecked.StartsWith($taskResearch + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Directory outside research' }
        if (-not (Get-ChildItem -LiteralPath $taskChecked -Force | Select-Object -First 1)) { [System.IO.Directory]::Delete($taskChecked, $false) }
    }
}
[ordered]@{ status='COMPLETE'; files=$taskDone; file_count=$taskDone.Count; bytes=($taskDone | Measure-Object bytes -Sum).Sum; utc=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $taskReceiptPath -Encoding UTF8
[PSCustomObject]@{ status='COMPLETE'; removed_residual_files=$taskDone.Count } | ConvertTo-Json
