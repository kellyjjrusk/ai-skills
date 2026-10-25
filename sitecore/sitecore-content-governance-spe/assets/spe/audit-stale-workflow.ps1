<#
  audit-stale-workflow.ps1 — READ-ONLY.
  Items (latest version per language) in a non-final workflow state with no update for N days.
#>
$database  = "master"
$scopeRoot = "/sitecore/content"
$languages = @("en")
$staleDays = 30

$db = Get-Database $database
$cutoff = (Get-Date).AddDays(-$staleDays)
$rows = foreach ($lang in $languages) {
    Get-ChildItem -Path "$($database):$scopeRoot" -Recurse -Language $lang |
        Where-Object { $_.Versions.Count -gt 0 -and $_["__Workflow state"] } |
        ForEach-Object {
            $wf = $db.WorkflowProvider.GetWorkflow($_)
            if (-not $wf) { return }
            $state = $wf.GetState($_)
            if (-not $state -or $state.FinalState) { return }
            $updated = [Sitecore.DateUtil]::IsoDateToDateTime($_["__Updated"])
            if ($updated -ge $cutoff) { return }
            [PSCustomObject]@{
                Path      = $_.ItemPath
                Language  = $lang
                Version   = $_.Version.Number
                Workflow  = $wf.Appearance.DisplayName
                State     = $state.DisplayName
                DaysIdle  = [int]((Get-Date) - $updated).TotalDays
                UpdatedBy = $_["__Updated by"]
                LockedBy  = if ($_.Locking.IsLocked()) { $_.Locking.GetOwner() } else { "" }
            }
        }
}
$rows = @($rows)
Write-Host "Stale non-final items (> $staleDays days): $($rows.Count)"
if ($rows.Count) {
    $rows | Sort-Object DaysIdle -Descending | Show-ListView -Property Path, Language, Workflow, State, DaysIdle, UpdatedBy, LockedBy -Title "Stale workflow items"
    $rows | Group-Object State | Select-Object Count, Name | Sort-Object Count -Descending | Format-Table -AutoSize
    $rows | Group-Object UpdatedBy | Select-Object Count, Name | Sort-Object Count -Descending | Select-Object -First 10 | Format-Table -AutoSize
    $p = "$($SitecoreDataFolder)\temp\stale-workflow-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
