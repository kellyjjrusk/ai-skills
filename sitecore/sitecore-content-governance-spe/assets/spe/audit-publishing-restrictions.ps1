<#
  audit-publishing-restrictions.ps1 — READ-ONLY.
  Never-publish items, future publish dates, passed unpublish dates, hidden versions, expired valid-to.
#>
$database  = "master"
$scopeRoot = "/sitecore/content"
$language  = "en"

$now = Get-Date
$rows = Get-ChildItem -Path "$($database):$scopeRoot" -Recurse -Language $language -Version * |
    ForEach-Object {
        $pub = $_.Publishing
        $issues = @()
        if ($pub.NeverPublish) { $issues += "Never publish (item)" }
        if ($pub.PublishDate -ne [DateTime]::MinValue -and $pub.PublishDate -gt $now) { $issues += "Item publish date in future: $($pub.PublishDate)" }
        if ($pub.UnpublishDate -ne [DateTime]::MaxValue -and $pub.UnpublishDate -lt $now) { $issues += "Item unpublish date passed: $($pub.UnpublishDate)" }
        if ($pub.HideVersion) { $issues += "Version hidden" }
        if ($pub.ValidFrom -ne [DateTime]::MinValue -and $pub.ValidFrom -gt $now) { $issues += "Version valid-from in future: $($pub.ValidFrom)" }
        if ($pub.ValidTo -ne [DateTime]::MaxValue -and $pub.ValidTo -lt $now) { $issues += "Version expired: $($pub.ValidTo)" }
        if ($issues) {
            [PSCustomObject]@{ Path = $_.ItemPath; Version = $_.Version.Number; Issues = ($issues -join "; "); UpdatedBy = $_["__Updated by"] }
        }
    }
$rows = @($rows)
Write-Host "Items/versions with restrictions: $($rows.Count)"
if ($rows.Count) {
    $rows | Show-ListView -Property Path, Version, Issues, UpdatedBy -Title "Publishing restrictions"
    $p = "$($SitecoreDataFolder)\temp\publishing-restrictions-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
