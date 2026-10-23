$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath('D:\MAESTRO')
$taskResearch = [System.IO.Path]::GetFullPath((Join-Path $taskRoot 'research'))
$taskLog = Join-Path $taskRoot 'log\20261023\report_consolidation'
$taskPlanPath = Join-Path $taskLog 'APPROVED_DELETIONS.json'
$taskReceiptPath = Join-Path $taskLog 'DELETION_RECEIPT.json'
if (Test-Path -LiteralPath $taskReceiptPath) { throw 'Deletion receipt already exists' }
$taskPlan = Get-Content -LiteralPath $taskPlanPath -Raw | ConvertFrom-Json
$taskHead = (git -C $taskRoot rev-parse HEAD).Trim()
if ($taskHead -ne $taskPlan.git_head) { throw 'HEAD changed after preparation' }
$taskResolved = @()
foreach ($taskEntry in $taskPlan.files) {
    $taskPath = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskEntry.path))
    if (-not $taskPath.StartsWith($taskResearch + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside research' }
    $taskOwner = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskEntry.owner))
    if (-not $taskPath.StartsWith($taskOwner + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside approved owner' }
    if (-not (Test-Path -LiteralPath $taskPath -PathType Leaf)) { throw ('Missing candidate: ' + $taskEntry.path) }
    $taskFile = Get-Item -LiteralPath $taskPath
    if ($taskFile.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Reparse point candidate' }
    if ((Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'Candidate changed' }
    $taskResolved += [PSCustomObject]@{ path=$taskEntry.path; full_path=$taskPath; bytes=$taskEntry.bytes; sha256=$taskEntry.sha256 }
}
$taskDeleted = [System.Collections.Generic.List[object]]::new()
$taskEmptyDirs = [System.Collections.Generic.List[string]]::new()
$taskReceipt = [ordered]@{ status='RUNNING'; git_head=$taskHead; started_utc=[DateTime]::UtcNow.ToString('o'); files=$taskDeleted; empty_directories=$taskEmptyDirs }
try {
    foreach ($taskEntry in $taskResolved) {
        Remove-Item -LiteralPath $taskEntry.full_path -Force
        $taskDeleted.Add([PSCustomObject]@{ path=$taskEntry.path; bytes=$taskEntry.bytes; sha256=$taskEntry.sha256 })
    }
    foreach ($taskOwnerRelative in $taskPlan.directories) {
        $taskOwnerPath = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskOwnerRelative))
        if (-not $taskOwnerPath.StartsWith($taskResearch + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid owner root' }
        $taskFolders = @((Get-ChildItem -LiteralPath $taskOwnerPath -Directory -Recurse).FullName) + @($taskOwnerPath)
        foreach ($taskFolder in ($taskFolders | Sort-Object Length -Descending)) {
            $taskChecked = [System.IO.Path]::GetFullPath($taskFolder)
            if (-not $taskChecked.StartsWith($taskResearch + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid directory scope' }
            if (Test-Path -LiteralPath $taskChecked -PathType Container) {
                if (-not (Get-ChildItem -LiteralPath $taskChecked -Force | Select-Object -First 1)) {
                    [System.IO.Directory]::Delete($taskChecked, $false)
                    $taskEmptyDirs.Add($taskChecked.Substring($taskRoot.Length + 1).Replace([char]92,[char]47))
                }
            }
        }
    }
    $taskReceipt.status = 'COMPLETE'
} catch {
    $taskReceipt.status = 'FAILED_RETAINED'
    $taskReceipt.error = $_.Exception.Message
    throw
} finally {
    $taskReceipt.ended_utc = [DateTime]::UtcNow.ToString('o')
    $taskReceipt.deleted_files = $taskDeleted.Count
    $taskReceipt.deleted_bytes = ($taskDeleted | Measure-Object bytes -Sum).Sum
    $taskReceipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskReceiptPath -Encoding UTF8
}
[PSCustomObject]@{ status=$taskReceipt.status; deleted_files=$taskDeleted.Count; deleted_bytes=$taskReceipt.deleted_bytes; removed_empty_directories=$taskEmptyDirs.Count } | ConvertTo-Json
