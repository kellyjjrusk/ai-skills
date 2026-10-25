<#
  Index status export — READ-ONLY. Run in SPE ISE on the CM (or the instance that indexes).
  Shows each ContentSearch index, its document count, rebuild state, last update and strategies.
#>
$rows = foreach ($idx in Get-SearchIndex) {
    $summary = $null
    try { $summary = $idx.Summary } catch {}
    $strategies = @()
    try { $strategies = $idx.Strategies | ForEach-Object { $_.GetType().Name } } catch {}
    $crawlerRoots = @()
    try { $crawlerRoots = $idx.Crawlers | ForEach-Object { "$($_.Database):$($_.Root)" } } catch {}
    $isRebuilding = $false
    try { $isRebuilding = [Sitecore.ContentSearch.Maintenance.IndexCustodian]::IsRebuilding($idx) } catch {}
    [PSCustomObject]@{
        Index          = $idx.Name
        Type           = $idx.GetType().Name
        Documents      = if ($summary) { $summary.NumberOfDocuments } else { "" }
        IsHealthy      = if ($summary) { $summary.IsHealthy } else { "" }
        OutOfDate      = if ($summary) { $summary.OutOfDateIndex } else { "" }
        LastUpdated    = if ($summary) { $summary.LastUpdated } else { "" }
        Rebuilding     = $isRebuilding
        Strategies     = ($strategies -join ", ")
        CrawlerRoots   = ($crawlerRoots -join "; ")
    }
}
$rows | Show-ListView -Title "Search index status"
$p = "$($SitecoreDataFolder)\temp\index-status-$(Get-Date -Format yyyyMMddHHmmss).csv"
$rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
Out-Download -Path $p | Out-Null

# Item counts under crawler roots for plausibility checks
$counts = foreach ($r in $rows) {
    foreach ($root in ($r.CrawlerRoots -split "; ")) {
        if (-not $root) { continue }
        $db, $path = $root -split ":", 2
        $n = (Get-ChildItem -Path "$($db):$path" -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        [PSCustomObject]@{ Index = $r.Index; Root = $root; Items = $n + 1; IndexDocuments = $r.Documents }
    }
}
$counts | Show-ListView -Title "Crawler root item counts vs documents (documents include language versions)"
