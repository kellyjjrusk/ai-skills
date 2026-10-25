<#
  audit-large-media.ps1 — READ-ONLY.
  Media items over a size threshold, grouped by extension.
#>
$database  = "master"
$mediaRoot = "/sitecore/media library"
$minSizeMB = 2

$threshold = $minSizeMB * 1MB
$rows = Get-ChildItem -Path "$($database):$mediaRoot" -Recurse |
    Where-Object { $_.TemplateName -notmatch "folder" } |
    ForEach-Object {
        $size = 0; [long]::TryParse($_["Size"], [ref]$size) | Out-Null
        if ($size -ge $threshold) {
            [PSCustomObject]@{
                Path      = $_.ItemPath
                Extension = $_["Extension"]
                SizeMB    = [math]::Round($size / 1MB, 2)
                Dimensions= if ($_["Width"]) { "$($_['Width'])x$($_['Height'])" } else { "" }
                Referrers = @(Get-ItemReferrer -Item $_ -ErrorAction SilentlyContinue).Count
                Updated   = $_["__Updated"]
            }
        }
    }
$rows = @($rows)
Write-Host "Media >= $minSizeMB MB: $($rows.Count)"
if ($rows.Count) {
    $rows | Sort-Object SizeMB -Descending | Show-ListView -Property Path, Extension, SizeMB, Dimensions, Referrers, Updated -Title "Large media"
    $rows | Group-Object Extension | ForEach-Object {
        [PSCustomObject]@{ Extension = $_.Name; Count = $_.Count; TotalMB = [math]::Round(($_.Group | Measure-Object SizeMB -Sum).Sum, 1) }
    } | Sort-Object TotalMB -Descending | Format-Table -AutoSize
    $p = "$($SitecoreDataFolder)\temp\large-media-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
