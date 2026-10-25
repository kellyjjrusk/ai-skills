<#
  audit-folder-size.ps1 — READ-ONLY.
  Items with more direct children than a threshold (Content Editor slowness, publishing and API cost).
  Bucketed items are reported separately; buckets are designed for large child counts.
#>
$database  = "master"
$scopeRoot = "/sitecore/content"
$threshold = 100

$rows = @(Get-Item -Path "$($database):$scopeRoot") + @(Get-ChildItem -Path "$($database):$scopeRoot" -Recurse) |
    Where-Object { $_.HasChildren } |
    ForEach-Object {
        $n = $_.Children.Count
        if ($n -gt $threshold) {
            $isBucket = $false
            try { $isBucket = [Sitecore.Buckets.Managers.BucketManager]::IsBucket($_) } catch {}
            [PSCustomObject]@{ Path = $_.ItemPath; Children = $n; Template = $_.TemplateName; IsBucket = $isBucket }
        }
    }
$rows = @($rows)
Write-Host "Items with > $threshold children: $($rows.Count) (non-bucket: $(@($rows | Where-Object { -not $_.IsBucket }).Count))"
if ($rows.Count) {
    $rows | Sort-Object Children -Descending | Show-ListView -Property Path, Children, Template, IsBucket -Title "Large folders"
    $p = "$($SitecoreDataFolder)\temp\folder-size-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
