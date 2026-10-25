---
name: sitecore-search-index-ops
description: Operate, troubleshoot and tune Sitecore search indexes — Solr for XP/XM (sitecore_master/web/core and custom indexes, xDB indexes), SwitchOnRebuild, index update strategies, computed fields, managed schema, SearchStax/SolrCloud topology — and the search options on SitecoreAI (Edge GraphQL search, Sitecore Search). Analyzes index configuration from showconfig, parses Crawling/Search logs, generates SPE scripts for status, targeted re-indexing and verification. Use whenever the user mentions Solr, index rebuild failing or slow, search results missing or stale, "Index not found", Content Editor search broken, SolrConnectionException, shards, SwitchOnRebuild, populate managed schema, computed index fields, or choosing search for SitecoreAI.
---

# Sitecore Search & Index Operations

On XP/XM, Solr indexes drive Content Editor search, item buckets, many site features and xDB. When they break, symptoms appear far from the cause (empty listings, broken buckets, CM sluggishness, 500s). Full rebuilds of large indexes take hours and can take search offline. This skill diagnoses from configuration and logs, then prescribes the least disruptive fix — usually a targeted re-index, not a full rebuild.

## Operating constraint: no server access

You cannot reach Solr, the Indexing Manager or the CM. Evidence comes from the user:
- `showconfig.xml` (save `/sitecore/admin/showconfig.aspx`) — the merged config is authoritative
- `Crawling.log.*.txt` and `Search.log.*.txt` from `App_Data/logs` (CM and the instance doing indexing)
- `references/spe-index-status.ps1` output (index list, document counts, rebuild state, last updated)
- Solr admin info they screenshot or paste: version, collections/cores, shards/replicas, `/admin/collections?action=CLUSTERSTATUS` JSON (SolrCloud)

## Workflow

### 1. Analyze configuration

```bash
python3 scripts/analyze_index_config.py showconfig.xml --out index-config-report.md [--crawling Crawling.log.*.txt ...]
```

Reports every index: provider type (standard vs SwitchOnRebuild), core and rebuild core names, update strategies, crawler roots/databases, computed fields count, and flags:
- `syncMaster` on master for a large repository (CM write latency; every save indexes synchronously)
- Crawler root `/sitecore` on custom indexes (indexes system, templates, layouts — slow, noisy)
- Custom index with no strategy (never updates) or `manual` without a rebuild job
- SwitchOnRebuild without a `rebuildcore`, or rebuild core equal to main core
- Duplicate core names across indexes (two indexes writing the same core = corrupted results)
- `web` index not using `onPublishEndAsync`
- Custom index sharing `defaultSolrIndexConfiguration` but declaring heavy computed fields
With `--crawling`: rebuild durations, item failures, computed field exceptions, timeouts, last successful rebuild per index.

### 2. Classify the symptom

| Symptom | First checks | Typical fix |
|---|---|---|
| Search returns nothing for new/changed items | strategy on that index; Crawling.log errors after save/publish | fix strategy; targeted re-index of subtree |
| Rebuild fails after seconds | `SolrConnectionException`, auth, URL, firewall to Solr, wrong core name | fix connection string `solr.search`; create cores; populate schema |
| Rebuild times out near the end | `Optimize` after rebuild on large index | override rebuild to skip optimize (`Rebuild(true, false)`); increase SolrNet timeout |
| `no servers hosting shard` (SolrCloud) | CLUSTERSTATUS: rebuild collection with numShards>1, replicas in recovery | recreate collection with 1 shard + replicationFactor N; reduce load |
| Rebuild very slow | SQL index fragmentation on Items/Fields tables, crawler roots too broad, computed fields doing item lookups, low batch size | rebuild SQL indexes; narrow roots; cache in computed fields; tune `ContentSearch.ParallelIndexing` |
| `Index 'x' was not found` | index config not enabled on this role; typo | enable config on the role; check role-based config `role:require` |
| Field missing from results | schema not populated / field not in field map | Populate Managed Schema; add field to fieldMap; rebuild |
| Content Editor search error | `sitecore_master_index` / `core_index` broken | rebuild those two (SwitchOnRebuild if large) |
| Results stale on CD only | web index strategy; publish:end:remote not reaching indexing instance | check which instance indexes; EventQueue health |
| xDB search issues | xConnect indexer worker, `-rr` rebuild, `xdb_rebuild` core | xConnect IndexWorker; clean rebuild index `-cri` after swap |

Use `references/solr-runbook.md` for exact procedures (SwitchOnRebuild setup with aliases, schema population, rebuild-without-optimize patch, SolrCloud collection recreation, SQL index maintenance, version compatibility).

### 3. Prefer targeted operations

Full rebuild is the last resort on production. In order:
1. Re-index one item / subtree (`references/spe-index-ops.ps1` → `Initialize-SearchIndexItem`).
2. Rebuild a small custom index.
3. Rebuild a large index **with SwitchOnRebuild** so queries keep using the old core.
4. Plain full rebuild during a maintenance window, with authors warned.

All generated SPE scripts default to `$dryRun = $true`, list what they would index, and only execute when the user flips the flag.

### 4. Verify

After any fix, the user runs the status script again and a `Find-Item` query for a known changed item. Confirm document counts are plausible (compare master item count under the crawler roots to Solr document count, allowing for language versions) and that Crawling.log shows no new errors.

## SitecoreAI

There is no Solr and no ContentSearch API on delivery. Options:
- **Experience Edge GraphQL `search`** — simple filtering/sorting/pagination over published items; no relevance tuning, no facets of note; 1,000-entity cap; rate limit 80 req/s.
- **Sitecore Search** — full-text, facets, relevance, personalization; content indexed by crawler/push; separate product and contract.
- **Third-party** (Coveo, Algolia, Elastic) via webhook or crawler.
Map each XP search feature the user relies on to one of these, flagging features with no equivalent (e.g. arbitrary LINQ over master, computed fields at query time). Check the current Edge limits page before quoting numbers.

## Output

`INDEX-DIAGNOSIS.md`: cause with evidence line, fix steps, generated scripts as full files, verification steps, and a prevention item (strategy change, monitoring alert on rebuild failures, scheduled SQL index maintenance).

## References

- `references/solr-runbook.md` — procedures and patches
- `references/spe-index-status.ps1` — read-only index status export
- `references/spe-index-ops.ps1` — targeted re-index with dry run
- `scripts/analyze_index_config.py` — config + crawling log analyzer (stdlib only)
