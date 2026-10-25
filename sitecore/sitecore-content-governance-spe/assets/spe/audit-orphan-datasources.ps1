<#
  audit-orphan-datasources.ps1 — READ-ONLY.
  Items under datasource folders (default: any folder named "Data" under the scope) that no item references.
  Requires a current link database. Shared/global datasources referenced only via code or queries will
  appear orphaned — confirm with the owning team before cleanup.
#>
$database        = "master"
$scopeRoot       = "/sitecore/content/Site"   # <-- set (site root, not Home)
$dataFolderNames = @("Data", "Local Data", "Shared Data")

$folders = @(Get-ChildItem -Path "$($database):$scopeRoot" -Recurse | Where-Object { $dataFolderNames -contains $_.Name })
$rows = foreach ($f in $folders) {
    Get-ChildItem -Path "$($database):$($f.ItemPath)" -Recurse |
        Where-Object { $_.TemplateName -notmatch "folder" } |
        Where-Object { -not (Get-ItemReferrer -Item $_ -ErrorAction SilentlyContinue) } |
        ForEach-Object {
            [PSCustomObject]@{
                Path      = $_.ItemPath
                Template  = $_.TemplateName
                Created   = $_["__Created"]
                UpdatedBy = $_["__Updated by"]
                Children  = $_.Children.Count
            }
        }
}
$rows = @($rows)
Write-Host "Data folders scanned: $($folders.Count). Unreferenced datasource items: $($rows.Count)"
if ($rows.Count) {
    $rows | Show-ListView -Property Path, Template, Created, UpdatedBy, Children -Title "Orphan datasources"
    $rows | Group-Object Template | Select-Object Count, Name | Sort-Object Count -Descending | Format-Table -AutoSize
    $p = "$($SitecoreDataFolder)\temp\orphan-datasources-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
