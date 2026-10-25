<#
  audit-language-coverage.ps1 — READ-ONLY.
  Pages (items with presentation) missing a version in any required language.
#>
$database  = "master"
$scopeRoot = "/sitecore/content/Site/Home"   # <-- set
$required  = @("en", "fr-CA", "es")          # <-- set

$root = Get-Item -Path "$($database):$scopeRoot"
$pages = @($root) + @(Get-ChildItem -Path "$($database):$scopeRoot" -Recurse) |
    Where-Object { $_.Fields["__Renderings"].Value -or $_.Fields["__Final Renderings"].Value }

$rows = foreach ($p in $pages) {
    $missing = foreach ($lang in $required) {
        $v = Get-Item -Path "$($database):" -ID $p.ID -Language $lang -ErrorAction SilentlyContinue
        if (-not $v -or $v.Versions.Count -eq 0) { $lang }
    }
    if ($missing) {
        [PSCustomObject]@{ Path = $p.ItemPath; Template = $p.TemplateName; Missing = ($missing -join ", "); MissingCount = @($missing).Count }
    }
}
$rows = @($rows)
Write-Host "Pages checked: $(@($pages).Count). Missing at least one language: $($rows.Count)"
foreach ($lang in $required) {
    $n = @($rows | Where-Object { $_.Missing -split ", " -contains $lang }).Count
    Write-Host ("  {0,-8} missing on {1} page(s)" -f $lang, $n)
}
if ($rows.Count) {
    $rows | Sort-Object MissingCount -Descending | Show-ListView -Property Path, Template, Missing -Title "Language coverage gaps"
    $p = "$($SitecoreDataFolder)\temp\language-coverage-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
