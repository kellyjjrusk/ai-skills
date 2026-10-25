# Solr runbook (Sitecore XP/XM)

Confirm the Solr version supported by the user's Sitecore version in Sitecore's compatibility table (search `Sitecore Solr compatibility table`). Running an unsupported Solr is a frequent hidden cause.

## 1. Populate managed schema
After creating cores or upgrading Solr/Sitecore: Control Panel → Indexing → Populate Solr Managed Schema → select indexes → Populate. Then rebuild the affected indexes. Skipping this step causes "unknown field" errors and missing fields in results.

## 2. SwitchOnRebuild (zero-downtime rebuild)
Standalone Solr: create core `<index>_rebuild` with same configset.
SolrCloud: create collection `<index>_rebuild` (1 shard, replicationFactor = node count), and aliases per the provider's convention (e.g. `<index>_MainAlias`, `<index>_RebuildAlias`) — follow the doc for the user's Sitecore version.

Config patch (example for web index):
```xml
<configuration xmlns:patch="http://www.sitecore.net/xmlconfig/" xmlns:role="http://www.sitecore.net/xmlconfig/role/" xmlns:search="http://www.sitecore.net/xmlconfig/search/">
  <sitecore role:require="Standalone or ContentManagement" search:require="solr">
    <contentSearch>
      <configuration>
        <indexes>
          <index id="sitecore_web_index">
            <patch:attribute name="type">Sitecore.ContentSearch.SolrProvider.SwitchOnRebuildSolrSearchIndex, Sitecore.ContentSearch.SolrProvider</patch:attribute>
            <param desc="rebuildcore">$(id)_rebuild</param>
          </index>
        </indexes>
      </configuration>
    </contentSearch>
  </sitecore>
</configuration>
```
For SolrCloud the type is `SwitchOnRebuildSolrCloudSearchIndex` with alias params — check docs for your version.

## 3. Rebuild without optimize (large indexes timing out at the end)
```csharp
public class NoOptimizeSwitchOnRebuildSolrSearchIndex : Sitecore.ContentSearch.SolrProvider.SwitchOnRebuildSolrSearchIndex
{
    public NoOptimizeSwitchOnRebuildSolrSearchIndex(string name, string mainalias, string rebuildalias, string activecollection,
        string rebuildcollection, Sitecore.ContentSearch.Maintenance.IIndexPropertyStore propertyStore)
        : base(name, mainalias, rebuildalias, activecollection, rebuildcollection, propertyStore) { }

    public override void Rebuild() => Rebuild(true, false);
}
```
Constructor signatures differ between standalone/SolrCloud and Sitecore versions — decompile or check the base class for the user's version and match it exactly. Patch the index `type` to the new class.

Also raise the SolrNet timeout if connection timeouts occur: setting `ContentSearch.Solr.ConnectionTimeout` (ms) in the Solr provider config.

## 4. SolrCloud: "no servers hosting shard"
Cause: collection created with numShards=N, replicationFactor=1; a shard in recovery takes part of the index offline.
Fix: delete and recreate the collection with `numShards=1&replicationFactor=<nodes>`; repopulate schema; rebuild. Reduce indexing concurrency during peak.

## 5. Slow rebuild: SQL side
Rebuild/reorganize indexes on `Items`, `VersionedFields`, `UnversionedFields`, `SharedFields`, `Descendants` tables in the source database (often master). Schedule weekly maintenance (Ola Hallengren or Azure SQL automatic tuning). Fragmented SQL indexes can make crawling orders of magnitude slower.

## 6. Narrow crawler roots
Custom indexes should crawl only what they serve, e.g. `/sitecore/content/<site>/Home` rather than `/sitecore`. Exclude templates via `<exclude hint="list:AddExcludedTemplate">` in a custom index configuration.

## 7. Computed fields
Must be fast and null-safe; log and return null on failure. Avoid `Database.GetItem` chains per document; cache lookups per indexing run. Exceptions surface as `Could not compute value for ComputedIndexField` warnings in Crawling.log.

## 8. Update strategies
| Strategy | Use |
|---|---|
| `onPublishEndAsync` | web index (default) |
| `intervalAsyncMaster` | master index on large repos (CM-friendly) |
| `syncMaster` | small repos needing instant master search |
| `manual` | custom indexes rebuilt on schedule |
| `rebuildAfterFullPublish` | combine with onPublishEndAsync where full publishes are common |

## 9. xDB indexes
- Rebuild: on the xConnect IndexWorker, `Sitecore.XConnectSearchIndexer.exe -rr` (request rebuild).
- Clean rebuild core after swap (9.3+): `-cri`.
- Ensure `xdb` and `xdb_rebuild` cores/collections exist with xDB schema.
