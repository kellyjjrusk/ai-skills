<#
  <SCRIPT NAME> — <one-line purpose>
  WRITES CONTENT: yes. Default is DRY RUN.
  Run in SPE ISE as a user with write access to the scope. Review the preview list before setting $dryRun = $false.
#>

# ===== 1. Parameters =====
$dryRun          = $true
$database        = "master"
$scopeRoot       = "/sitecore/content/Site/Home"      # <-- set
$language        = "en"
$maxItems        = 500
$allowBroadScope = $false
$backupPackage   = $true

# ===== 2. Scope guard =====
$broad = @("/sitecore", "/sitecore/content", "/sitecore/system", "/sitecore/templates", "/sitecore/layout", "/sitecore/media library")
if (($broad -contains $scopeRoot.TrimEnd("/")) -and -not $allowBroadScope) {
    Write-Host "Refusing to run on broad scope '$scopeRoot'. Set `$allowBroadScope = `$true only if you are certain." -ForegroundColor Red
    return
}
$root = Get-Item -Path "$($database):$scopeRoot" -Language $language -ErrorAction SilentlyContinue
if (-not $root) { Write-Host "Scope root not found: $scopeRoot" -ForegroundColor Red; return }

# ===== 3. Collect changes =====
$changes = New-Object System.Collections.Generic.List[object]
$candidates = @($root) + @(Get-ChildItem -Path "$($database):$scopeRoot" -Recurse -Language $language)
foreach ($item in $candidates) {
    # <-- selection + computed new value. Example: set empty "Meta Description" from "Title"
    # if ($item.TemplateName -ne "Page") { continue }
    # $old = $item["Meta Description"]; if (-not [string]::IsNullOrWhiteSpace($old)) { continue }
    # $new = $item["Title"]
    # $changes.Add([PSCustomObject]@{ Path=$item.ItemPath; ID=$item.ID.ToString(); Language=$item.Language.Name; Field="Meta Description"; Old=$old; New=$new; Action="Set" })
}

# ===== 4. Preview + record =====
Write-Host "Planned changes: $($changes.Count)"
if ($changes.Count -eq 0) { Write-Host "Nothing to do."; return }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$planCsv = "$($SitecoreDataFolder)\temp\plan-$stamp.csv"
$changes | Export-Csv -Path $planCsv -NoTypeInformation -Encoding UTF8
Out-Download -Path $planCsv | Out-Null
$changes | Select-Object -First 200 | Show-ListView -Property Path, Language, Field, Old, New, Action -Title "Planned changes (first 200 of $($changes.Count))"

# ===== 5. Cap =====
if ($changes.Count -gt $maxItems) {
    Write-Host "Aborting: $($changes.Count) changes exceeds `$maxItems ($maxItems)." -ForegroundColor Red
    return
}
if ($dryRun) { Write-Host "DRY RUN — nothing changed. Set `$dryRun = `$false to apply." -ForegroundColor Yellow; return }

# ===== 6. Backup =====
if ($backupPackage) {
    $package = New-Package "Backup-$stamp"
    $package.Sources.Clear()
    $ids = $changes | Select-Object -ExpandProperty ID -Unique
    $items = $ids | ForEach-Object { Get-Item -Path "$($database):" -ID $_ }
    $source = $items | New-ExplicitItemSource -Name "Affected items" -InstallMode Overwrite
    $package.Sources.Add($source)
    $package.Metadata.Author = [Sitecore.Context]::User.Name
    $package.Metadata.Comment = "Backup before bulk change $stamp"
    Export-Package -Project $package -Path "Backup-$stamp.zip" -Zip
    Out-Download -Path "$($SitecorePackageFolder)\Backup-$stamp.zip" | Out-Null
    Write-Host "Backup package downloaded."
}

# ===== 7. Act =====
$stats = @{ ok = 0 }; $failed = New-Object System.Collections.Generic.List[object]   # hashtable/list: mutations survive the using-block scope
New-UsingBlock (New-Object Sitecore.Data.BulkUpdateContext) {
    foreach ($c in $changes) {
        try {
            $item = Get-Item -Path "$($database):" -ID $c.ID -Language $c.Language
            $item.Editing.BeginEdit()
            switch ($c.Action) {
                "Set"    { $item[$c.Field] = $c.New }
                "Clear"  { $item[$c.Field] = "" }
                "Append" { $item[$c.Field] = $item[$c.Field] + $c.New }
            }
            $item.Editing.EndEdit() | Out-Null
            Write-Log "BULK $stamp $($c.Action) $($c.Field) on $($c.Path) [$($c.Language)]"
            $stats.ok++
        } catch {
            if ($item) { $item.Editing.CancelEdit() }
            $failed.Add([PSCustomObject]@{ Path = $c.Path; Field = $c.Field; Error = $_.Exception.Message })
        }
    }
}

# ===== 8. Summary =====
Write-Host "Applied: $($stats.ok)  Failed: $($failed.Count)" -ForegroundColor Green
if ($failed.Count) { $failed | Show-ListView -Title "Failures" }
Write-Host "Not published. Publish separately after review."
