<#
  Sitecore content-side inventory for migration assessment.
  Run in the Sitecore PowerShell Extensions ISE on the CM as an administrator.
  Read-only: it creates no items and changes nothing.
  Output: CSV downloads (one per section) via Out-Download.
  Tested patterns: SPE 6.x / 7.x on Sitecore 9.3–10.4 and SitecoreAI CM.
#>

$db = "master"
$stamp = Get-Date -Format "yyyyMMdd-HHmm"

function Save-Csv($data, $name) {
    $path = "$($SitecoreDataFolder)\temp\$name-$stamp.csv"
    $data | Export-Csv -Path $path -NoTypeInformation -Encoding UTF8
    Out-Download -Path $path | Out-Null
}

# 1. Sites (SXA site items + config sites)
$sites = @()
Get-ChildItem -Path "$($db):/sitecore/content" -Recurse |
    Where-Object { $_.TemplateName -match "^(Headless )?Site$" } |
    ForEach-Object {
        $sites += [PSCustomObject]@{
            Name = $_.Name; Path = $_.ItemPath; Template = $_.TemplateName; ID = $_.ID
        }
    }
[Sitecore.Configuration.Factory]::GetSiteNames() | ForEach-Object {
    $s = [Sitecore.Configuration.Factory]::GetSite($_)
    if ($s -and $s.RootPath -like "/sitecore/content*") {
        $sites += [PSCustomObject]@{ Name = $s.Name; Path = "$($s.RootPath)$($s.StartItem)"; Template = "config site"; ID = "" }
    }
}
Save-Csv $sites "sites"

# 2. Content volume by top-level branch
$volume = Get-ChildItem -Path "$($db):/sitecore/content" | ForEach-Object {
    $count = (Get-ChildItem -Path $_.ProviderPath -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
    [PSCustomObject]@{ Branch = $_.ItemPath; Items = $count + 1 }
}
$mediaCount = (Get-ChildItem -Path "$($db):/sitecore/media library" -Recurse | Measure-Object).Count
$volume += [PSCustomObject]@{ Branch = "/sitecore/media library"; Items = $mediaCount }
Save-Csv $volume "content-volume"

# 3. Languages
$langs = Get-ChildItem -Path "$($db):/sitecore/system/Languages" | ForEach-Object {
    [PSCustomObject]@{ Language = $_.Name; ID = $_.ID }
}
Save-Csv $langs "languages"

# 4. Renderings (non-system)
$renderings = Get-ChildItem -Path "$($db):/sitecore/layout/Renderings" -Recurse |
    Where-Object { $_.TemplateName -notmatch "Folder" -and $_.ItemPath -notmatch "/System/" } |
    ForEach-Object {
        [PSCustomObject]@{
            Name = $_.Name; Path = $_.ItemPath; Type = $_.TemplateName
            Controller = $_["Controller"]; Action = $_["Controller Action"]; ViewPath = $_["Path"]
            ComponentName = $_["componentName"]; Datasource = $_["Datasource Template"]
            Cacheable = $_["Cacheable"]; ID = $_.ID
        }
    }
Save-Csv $renderings "renderings"

# 5. Rendering usage counts (final layout, default device) — can be slow on large trees
$usage = @{}
Get-ChildItem -Path "$($db):/sitecore/content" -Recurse | ForEach-Object {
    $item = $_
    try {
        Get-Rendering -Item $item -FinalLayout -ErrorAction SilentlyContinue | ForEach-Object {
            $id = $_.ItemID
            if ($usage.ContainsKey($id)) { $usage[$id]++ } else { $usage[$id] = 1 }
        }
    } catch {}
}
$usageRows = $usage.GetEnumerator() | ForEach-Object {
    $r = Get-Item -Path "$($db):" -ID $_.Key -ErrorAction SilentlyContinue
    [PSCustomObject]@{ Rendering = if ($r) { $r.ItemPath } else { $_.Key }; Uses = $_.Value }
}
Save-Csv ($usageRows | Sort-Object Uses -Descending) "rendering-usage"

# 6. Custom templates
$templates = Get-ChildItem -Path "$($db):/sitecore/templates" -Recurse |
    Where-Object { $_.TemplateName -eq "Template" -and $_.ItemPath -notmatch "^/sitecore/templates/(System|Sample|Foundation/Experience Accelerator|Feature/Experience Accelerator|Branches)" } |
    ForEach-Object {
        [PSCustomObject]@{ Name = $_.Name; Path = $_.ItemPath; BaseTemplates = $_["__Base template"]; ID = $_.ID }
    }
Save-Csv $templates "templates"

# 7. Workflows
$wf = Get-ChildItem -Path "$($db):/sitecore/system/Workflows" | ForEach-Object {
    $states = (Get-ChildItem -Path $_.ProviderPath | Where-Object { $_.TemplateName -eq "State" } | ForEach-Object { $_.Name }) -join "; "
    [PSCustomObject]@{ Workflow = $_.Name; States = $states; ID = $_.ID }
}
Save-Csv $wf "workflows"

# 8. Installed modules (by folder presence)
$modules = Get-ChildItem -Path "$($db):/sitecore/system/Modules" | ForEach-Object {
    [PSCustomObject]@{ Module = $_.Name; Path = $_.ItemPath }
}
Save-Csv $modules "modules"

# 9. Aliases and wildcard items (unsupported on Experience Edge)
$aliases = Get-ChildItem -Path "$($db):/sitecore/system/Aliases" -Recurse | Where-Object { $_.TemplateName -eq "Alias" } |
    ForEach-Object { [PSCustomObject]@{ Alias = $_.ItemPath; Target = $_["Linked item"] } }
Save-Csv $aliases "aliases"
$wild = Get-ChildItem -Path "$($db):/sitecore/content" -Recurse | Where-Object { $_.Name -eq "*" } |
    ForEach-Object { [PSCustomObject]@{ Path = $_.ItemPath; Template = $_.TemplateName } }
Save-Csv $wild "wildcards"

Write-Host "Inventory complete. Attach all downloaded CSVs to the assessment conversation."
