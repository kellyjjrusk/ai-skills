<#
  audit-seo-fields.ps1 — READ-ONLY.
  Pages with empty, too-long or duplicate SEO fields. Field names vary by solution — set them below
  (SXA headless defaults are often "Title", "MetaDescription"/"Description", "OpenGraphTitle").
#>
$database     = "master"
$scopeRoot    = "/sitecore/content/Site/Home"   # <-- set
$language     = "en"
$titleField   = "Title"                         # <-- set
$descField    = "MetaDescription"               # <-- set
$maxTitle     = 60
$maxDesc      = 160

$root = Get-Item -Path "$($database):$scopeRoot" -Language $language
$pages = @($root) + @(Get-ChildItem -Path "$($database):$scopeRoot" -Recurse -Language $language) |
    Where-Object { ($_.Fields["__Renderings"].Value -or $_.Fields["__Final Renderings"].Value) -and $_.Versions.Count -gt 0 }

$data = foreach ($p in $pages) {
    [PSCustomObject]@{
        Path  = $p.ItemPath
        Title = if ($p.Fields[$titleField]) { $p[$titleField] } else { $null }
        Desc  = if ($p.Fields[$descField]) { $p[$descField] } else { $null }
        HasTitleField = [bool]$p.Fields[$titleField]
        HasDescField  = [bool]$p.Fields[$descField]
    }
}
$dupTitles = $data | Where-Object { $_.Title } | Group-Object Title | Where-Object Count -gt 1 | ForEach-Object { $_.Name }
$dupDescs  = $data | Where-Object { $_.Desc }  | Group-Object Desc  | Where-Object Count -gt 1 | ForEach-Object { $_.Name }

$rows = foreach ($d in $data) {
    $issues = @()
    if (-not $d.HasTitleField) { $issues += "No '$titleField' field on template" }
    elseif ([string]::IsNullOrWhiteSpace($d.Title)) { $issues += "Empty title" }
    elseif ($d.Title.Length -gt $maxTitle) { $issues += "Title $($d.Title.Length) chars" }
    if (-not $d.HasDescField) { $issues += "No '$descField' field on template" }
    elseif ([string]::IsNullOrWhiteSpace($d.Desc)) { $issues += "Empty description" }
    elseif ($d.Desc.Length -gt $maxDesc) { $issues += "Description $($d.Desc.Length) chars" }
    if ($d.Title -and $dupTitles -contains $d.Title) { $issues += "Duplicate title" }
    if ($d.Desc -and $dupDescs -contains $d.Desc) { $issues += "Duplicate description" }
    if ($issues) { [PSCustomObject]@{ Path = $d.Path; Issues = ($issues -join "; "); Title = $d.Title; Description = $d.Desc } }
}
$rows = @($rows)
Write-Host "Pages: $(@($pages).Count). With SEO issues: $($rows.Count)"
if ($rows.Count) {
    $rows | Show-ListView -Property Path, Issues, Title -Title "SEO field issues"
    $p = "$($SitecoreDataFolder)\temp\seo-fields-$(Get-Date -Format yyyyMMddHHmmss).csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
}
