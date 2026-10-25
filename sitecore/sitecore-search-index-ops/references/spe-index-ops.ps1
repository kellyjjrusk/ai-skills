<#
  Targeted index operations with dry run. Run in SPE ISE.
  Default is DRY RUN: lists what would be (re)indexed. Set $dryRun = $false to execute.
#>
$dryRun    = $true
$indexName = "sitecore_master_index"                      # <-- set
$rootPath  = "master:/sitecore/content/Site/Home/News"    # <-- set; subtree to refresh
$mode      = "Subtree"   # Subtree | Item | FullRebuild

$index = Get-SearchIndex -Name $indexName -ErrorAction Stop
Write-Host "Index: $($index.Name)  Type: $($index.GetType().Name)"

switch ($mode) {
    "Item" {
        $item = Get-Item -Path $rootPath
        Write-Host "Would refresh 1 item: $($item.ItemPath)"
        if (-not $dryRun) { Initialize-SearchIndexItem -Item $item -Name $indexName; Write-Host "Refreshed." -ForegroundColor Green }
    }
    "Subtree" {
        $items = @(Get-Item -Path $rootPath) + @(Get-ChildItem -Path $rootPath -Recurse)
        Write-Host "Would refresh $($items.Count) items under $rootPath"
        $items | Select-Object -First 50 ItemPath, TemplateName | Show-ListView -Title "First 50 items to refresh"
        if (-not $dryRun) {
            $root = Get-Item -Path $rootPath
            Initialize-SearchIndexItem -Item $root -Name $indexName   # refreshes item and descendants
            Write-Host "Subtree refresh started (background job). Monitor Crawling.log." -ForegroundColor Green
        }
    }
    "FullRebuild" {
        Write-Host "FULL REBUILD of $indexName requested." -ForegroundColor Yellow
        if ($index.GetType().Name -notmatch "SwitchOnRebuild") {
            Write-Host "Index is NOT SwitchOnRebuild: search on this index will be incomplete until rebuild finishes." -ForegroundColor Red
        }
        if (-not $dryRun) {
            Initialize-SearchIndex -Name $indexName
            Write-Host "Rebuild started. Track progress in Control Panel > Indexing Manager or Crawling.log." -ForegroundColor Green
        }
    }
}

# Verify with a query (edit criteria)
$check = Find-Item -Index $indexName -Criteria @{ Filter = "StartsWith"; Field = "_fullpath"; Value = ((Get-Item $rootPath).ItemPath.ToLower()) } -First 10
$check | Select-Object Name, Path, Language, Updated | Show-ListView -Title "Index check (first 10 docs under root)"
