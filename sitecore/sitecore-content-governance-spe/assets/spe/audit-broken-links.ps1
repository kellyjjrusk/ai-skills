<#
  audit-broken-links.ps1 — READ-ONLY.
  Lists links (fields and rendering datasources) whose target item no longer exists, using the link database.
  If results look incomplete, rebuild the link database first (Control Panel > Database > Rebuild Link Database).
#>
$database  = "master"
$scopeRoot = "/sitecore/content"     # <-- narrow to a site for speed/precision

$db = Get-Database $database
$broken = [Sitecore.Globals]::LinkDatabase.GetBrokenLinks($db)
$rows = foreach ($link in $broken) {
    $src = $link.GetSourceItem()
    if (-not $src) { continue }
    if (-not $src.Paths.FullPath.StartsWith($scopeRoot, [StringComparison]::OrdinalIgnoreCase)) { continue }
    $fieldName = ""
    try { $fieldName = $src.Fields[$link.SourceFieldID].Name } catch {}
    if (-not $fieldName) { $fieldName = $link.SourceFieldID.ToString() }
    [PSCustomObject]@{
        SourcePath = $src.Paths.FullPath
        SourceID   = $src.ID.ToString()
        Language   = $link.SourceItemLanguage.Name
        Version    = $link.SourceItemVersion.Number
        Field      = $fieldName
        TargetPath = $link.TargetPath
        TargetID   = $link.TargetItemID.ToString()
        UpdatedBy  = $src["__Updated by"]
        Updated    = $src["__Updated"]
    }
}
$rows = @($rows)
Write-Host "Broken links under $($scopeRoot): $($rows.Count)"
if ($rows.Count) {
    $rows | Show-ListView -Property SourcePath, Language, Field, TargetPath, TargetID, UpdatedBy -Title "Broken links ($($rows.Count))"
    $p = "$($SitecoreDataFolder)\temp\broken-links-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
    $rows | Group-Object Field | Sort-Object Count -Descending | Select-Object Count, Name | Format-Table -AutoSize
}
