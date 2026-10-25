<#
  audit-unused-media.ps1 — READ-ONLY.
  Media items with no referrers in the link database. Requires a current link database.
  Note: media referenced only from code, CSS, external systems or rich text links not tracked
  by the link database will appear "unused" — confirm before deleting.
#>
$database   = "master"
$mediaRoot  = "/sitecore/media library"   # <-- narrow, e.g. /sitecore/media library/Project/Acme
$excludes   = @("/sitecore/media library/System", "/sitecore/media library/Experience Explorer", "/sitecore/media library/Feature", "/sitecore/media library/Foundation")
$minAgeDays = 30

$cutoff = (Get-Date).AddDays(-$minAgeDays)
$rows = Get-ChildItem -Path "$($database):$mediaRoot" -Recurse |
    Where-Object {
        $p = $_.ItemPath
        ($_.TemplateName -notmatch "folder") -and -not ($excludes | Where-Object { $p.StartsWith($_, [StringComparison]::OrdinalIgnoreCase) })
    } |
    Where-Object {
        $created = [Sitecore.DateUtil]::IsoDateToDateTime($_["__Created"])
        $created -lt $cutoff
    } |
    Where-Object { -not (Get-ItemReferrer -Item $_ -ErrorAction SilentlyContinue) } |
    ForEach-Object {
        $size = 0; [long]::TryParse($_["Size"], [ref]$size) | Out-Null
        [PSCustomObject]@{
            Path      = $_.ItemPath
            ID        = $_.ID.ToString()
            Extension = $_["Extension"]
            SizeKB    = [math]::Round($size / 1KB, 1)
            Created   = $_["__Created"]
            CreatedBy = $_["__Created by"]
        }
    }
$rows = @($rows)
$totalMB = [math]::Round((($rows | Measure-Object SizeKB -Sum).Sum) / 1024, 1)
Write-Host "Unused media: $($rows.Count) items, $totalMB MB"
if ($rows.Count) {
    $rows | Sort-Object SizeKB -Descending | Show-ListView -Property Path, Extension, SizeKB, Created, CreatedBy -Title "Unused media ($($rows.Count), $totalMB MB)"
    $p = "$($SitecoreDataFolder)\temp\unused-media-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
