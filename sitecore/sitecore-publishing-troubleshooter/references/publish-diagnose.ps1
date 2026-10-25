<#
  Publishing diagnostic for one item and its dependencies. READ-ONLY.
  Run in the SPE ISE (XP/XM or SitecoreAI CM). Set $path and $language, then Run.
  Output: a list view plus a CSV download to attach to the conversation.
#>
$path     = "master:/sitecore/content/Site/Home/Page"   # <-- set
$language = "en"                                        # <-- set
$includeAncestors   = $true
$includeDatasources = $true
$includeTemplate    = $true

$now = [DateTime]::Now
$master = Get-Database "master"
$targets = Get-ChildItem -Path "master:/sitecore/system/Publishing targets" |
    ForEach-Object { $_["Target database"] } | Where-Object { $_ } | Select-Object -Unique
if (-not $targets) { $targets = @("web") }
# Keep only targets that are real databases on this instance.
# SitecoreAI's Experience Edge target is not a queryable database: comparison is skipped there.
$targets = @($targets | Where-Object {
    try { $null -ne [Sitecore.Configuration.Factory]::GetDatabase($_, $false) } catch { $false }
})
if (-not $targets) { Write-Host "No queryable target database (normal on SitecoreAI/Edge). Target comparison skipped." -ForegroundColor Yellow }

function Inspect($item, $role) {
    if (-not $item) { return }
    $wf = $master.WorkflowProvider.GetWorkflow($item)
    $state = if ($wf) { $wf.GetState($item) } else { $null }
    $versions = $item.Versions.GetVersionNumbers() | ForEach-Object { $_.Number }
    $row = [ordered]@{
        Role          = $role
        Path          = $item.ItemPath
        ID            = $item.ID.ToString()
        Language      = $item.Language.Name
        Version       = $item.Version.Number
        VersionsInLang= ($versions -join ",")
        HasVersion    = ($item.Versions.Count -gt 0)
        Workflow      = if ($wf) { $wf.Appearance.DisplayName } else { "(none)" }
        State         = if ($state) { $state.DisplayName } else { "" }
        FinalState    = if ($state) { $state.FinalState } else { "n/a" }
        NeverPublish  = $item.Publishing.NeverPublish
        PublishDate   = if ($item.Publishing.PublishDate -ne [DateTime]::MinValue) { $item.Publishing.PublishDate } else { "" }
        UnpublishDate = if ($item.Publishing.UnpublishDate -ne [DateTime]::MaxValue) { $item.Publishing.UnpublishDate } else { "" }
        HideVersion   = $item.Publishing.HideVersion
        ValidFrom     = if ($item.Publishing.ValidFrom -ne [DateTime]::MinValue) { $item.Publishing.ValidFrom } else { "" }
        ValidTo       = if ($item.Publishing.ValidTo -ne [DateTime]::MaxValue) { $item.Publishing.ValidTo } else { "" }
        Publishable   = $item.Publishing.IsPublishable($now, $false)
        LockedBy      = if ($item.Locking.IsLocked()) { $item.Locking.GetOwner() } else { "" }
        MasterRev     = $item["__Revision"]
        Updated       = $item["__Updated"]
        UpdatedBy     = $item["__Updated by"]
    }
    foreach ($t in $targets) {
        $ti = Get-Item -Path "$($t):" -ID $item.ID -Language $item.Language.Name -ErrorAction SilentlyContinue
        $row["InTarget_$t"]  = [bool]$ti
        $row["TargetRev_$t"] = if ($ti) { $ti["__Revision"] } else { "" }
        $row["UpToDate_$t"]  = if ($ti) { $ti["__Revision"] -eq $item["__Revision"] } else { $false }
    }
    [PSCustomObject]$row
}

$rows = @()
$item = Get-Item -Path $path -Language $language -ErrorAction Stop
$rows += Inspect $item "Target item"

if ($includeAncestors) {
    $p = $item.Parent
    while ($p -and $p.ItemPath -ne "/sitecore") {
        $rows += Inspect (Get-Item -Path "master:" -ID $p.ID -Language $language) "Ancestor"
        $p = $p.Parent
    }
}

if ($includeDatasources) {
    $seen = @{}
    foreach ($layoutType in @("Shared","Final")) {
        $renderings = if ($layoutType -eq "Final") { Get-Rendering -Item $item -FinalLayout -ErrorAction SilentlyContinue } else { Get-Rendering -Item $item -ErrorAction SilentlyContinue }
        foreach ($r in $renderings) {
            $ds = $r.Datasource
            if ([string]::IsNullOrWhiteSpace($ds)) { continue }
            if ($ds.StartsWith("local:")) {
                $ds = $item.ItemPath + $ds.Substring(6)
            } elseif (-not ($ds -match "^\{?[0-9A-Fa-f-]{36}\}?$" -or $ds.StartsWith("/sitecore"))) {
                continue   # query: or computed datasource; resolve manually
            }
            if ($seen.ContainsKey($ds)) { continue }
            $seen[$ds] = $true
            $dsItem = if ($ds -match "^\{?[0-9A-Fa-f-]{36}\}?$") { Get-Item -Path "master:" -ID $ds -Language $language -ErrorAction SilentlyContinue } else { Get-Item -Path "master:$ds" -Language $language -ErrorAction SilentlyContinue }
            if ($dsItem) {
                $rows += Inspect $dsItem "Datasource ($layoutType)"
            } else {
                $rows += [PSCustomObject]@{ Role = "Datasource ($layoutType)"; Path = $ds; ID = ""; Language = $language; HasVersion = $false; State = "MISSING IN MASTER" }
            }
        }
    }
}

if ($includeTemplate) {
    $tpl = Get-Item -Path "master:" -ID $item.TemplateID
    $rows += Inspect $tpl "Template"
    $svId = $tpl["__Standard values"]
    if ($svId) {
        $sv = Get-Item -Path "master:" -ID $svId -Language $language -ErrorAction SilentlyContinue
        if ($sv) { $rows += Inspect $sv "Standard values" }
    }
}

# Flag problems
$problems = foreach ($r in $rows) {
    $issues = @()
    if ($r.HasVersion -eq $false -and $r.Role -notmatch "Template") { $issues += "No version in $language" }
    if ($r.FinalState -eq $false) { $issues += "Workflow state not final ($($r.State))" }
    if ($r.NeverPublish -eq $true) { $issues += "Never publish" }
    if ($r.HideVersion -eq $true) { $issues += "Version hidden" }
    if ($r.PublishDate -and [DateTime]$r.PublishDate -gt $now) { $issues += "Publish date in future" }
    if ($r.UnpublishDate -and [DateTime]$r.UnpublishDate -lt $now) { $issues += "Unpublish date passed" }
    if ($r.ValidTo -and [DateTime]$r.ValidTo -lt $now) { $issues += "Version valid-to passed" }
    if ($r.LockedBy) { $issues += "Locked by $($r.LockedBy)" }
    foreach ($t in $targets) {
        if ($r.PSObject.Properties["InTarget_$t"] -and -not $r."InTarget_$t") { $issues += "Not in $t" }
        elseif ($r.PSObject.Properties["UpToDate_$t"] -and -not $r."UpToDate_$t") { $issues += "Outdated in $t" }
    }
    $r | Add-Member -NotePropertyName Issues -NotePropertyValue ($issues -join "; ") -Force -PassThru
}

$problems | Show-ListView -Property Role, Path, Language, State, Issues, Publishable, LockedBy, Updated, UpdatedBy -Title "Publish diagnostic: $($item.ItemPath) [$language]"

$csv = "$($SitecoreDataFolder)\temp\publish-diagnose-$(Get-Date -Format yyyyMMddHHmmss).csv"
$problems | Export-Csv -Path $csv -NoTypeInformation -Encoding UTF8
Out-Download -Path $csv | Out-Null
Write-Host "Targets checked: $($targets -join ', ')"
