param([switch]$Supplement)
$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath('D:\MAESTRO')
$taskLogRoot = Join-Path $taskRoot 'log'
$taskDataRoot = Join-Path $taskRoot 'data'
$taskRecordRoot = Join-Path $taskLogRoot '20261023\report_consolidation'
$taskPlanName = if ($Supplement) { 'DATA_MIGRATION_SUPPLEMENT_PLAN.json' } else { 'DATA_MIGRATION_PLAN.json' }
$taskReceiptName = if ($Supplement) { 'DATA_MIGRATION_SUPPLEMENT_RECEIPT.json' } else { 'DATA_MIGRATION_RECEIPT.json' }
$taskPlan = Get-Content -LiteralPath (Join-Path $taskRecordRoot $taskPlanName) -Raw | ConvertFrom-Json
$taskReceiptPath = Join-Path $taskRecordRoot $taskReceiptName
if (Test-Path -LiteralPath $taskReceiptPath) { throw 'Migration receipt already exists' }
$taskCompleted = [System.Collections.Generic.List[object]]::new()
$taskReceipt = [ordered]@{ status='RUNNING'; started_utc=[DateTime]::UtcNow.ToString('o'); files=$taskCompleted }
try {
    foreach ($taskEntry in $taskPlan.files) {
        $taskSource = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskEntry.old_path))
        $taskTarget = [System.IO.Path]::GetFullPath((Join-Path $taskRoot $taskEntry.data_path))
        if (-not $taskSource.StartsWith($taskLogRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Source outside log' }
        if (-not $taskTarget.StartsWith($taskDataRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Destination outside data' }
        if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw ('Source changed: ' + $taskEntry.old_path) }
        [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($taskTarget)) | Out-Null
        if (Test-Path -LiteralPath $taskTarget) {
            if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'Destination conflict' }
            Remove-Item -LiteralPath $taskSource -Force
        } else {
            Move-Item -LiteralPath $taskSource -Destination $taskTarget
        }
        if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw 'Moved data hash mismatch' }
        $taskCompleted.Add([PSCustomObject]@{ old_path=$taskEntry.old_path; data_path=$taskEntry.data_path; bytes=$taskEntry.bytes; sha256=$taskEntry.sha256; hash_verified=$true })
        if ($taskCompleted.Count % 1000 -eq 0) { Write-Output ('Moved and verified: ' + $taskCompleted.Count) }
    }
    $taskReceipt.status = 'COMPLETE'
} catch {
    $taskReceipt.status = 'FAILED_RETAINED'
    $taskReceipt.error = $_.Exception.Message
    throw
} finally {
    $taskReceipt.ended_utc = [DateTime]::UtcNow.ToString('o')
    $taskReceipt.file_count = $taskCompleted.Count
    $taskReceipt.bytes = ($taskCompleted | Measure-Object bytes -Sum).Sum
    $taskReceipt | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $taskReceiptPath -Encoding UTF8
}
[PSCustomObject]@{ status=$taskReceipt.status; files=$taskCompleted.Count; bytes=$taskReceipt.bytes } | ConvertTo-Json
