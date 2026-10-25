# sitecore-search-index-ops

**Operate, troubleshoot and tune Sitecore search indexes: Solr on XP/XM, and the search options available on SitecoreAI.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Administrator / Operations** · Platforms: **XP/XM 9.x–10.x** (Solr, SolrCloud, SearchStax), **SitecoreAI** (guidance)

---

## Why this exists

On XP/XM, Solr indexes drive Content Editor search, item buckets, site listings and search pages, and xDB. When they break, symptoms appear far from the cause: empty listings, broken buckets, sluggish CM, 500s.

Common causes:
- wrong update strategies
- crawler roots that index all of `/sitecore`
- SwitchOnRebuild misconfiguration that wipes the live core
- two indexes writing to one core
- optimize-after-rebuild timeouts
- mis-sharded SolrCloud collections
- fragmented SQL tables slowing crawls by orders of magnitude

Full rebuilds of large indexes take hours. The skill prescribes the least disruptive fix.

## What the skill does

1. **Analyzes index configuration** from `showconfig.xml`: provider type, core and rebuild core, strategies, crawler roots and databases, configuration reference, computed-field count. It flags misconfigurations by severity.
2. **Parses Crawling logs:** rebuild starts and finishes, last duration, errors, warnings, computed-field failures, timeouts, and rebuilds that never finished.
3. **Classifies the symptom** with a table of first checks and typical fixes (10 common symptoms, including xDB).
4. **Prefers targeted operations:** single item → subtree → small index → SwitchOnRebuild → maintenance-window full rebuild. All SPE operations default to dry run.
5. **Verifies** with index status, a `Find-Item` check, and crawler-root item counts vs document counts.
6. **On SitecoreAI**, maps XP search features to Experience Edge GraphQL search, Sitecore Search, or third-party search, and flags features with no equivalent.
7. **Provides runbook procedures:** schema population, SwitchOnRebuild setup, rebuild-without-optimize patch, SolrCloud collection recreation, SQL index maintenance, crawler-root narrowing, computed-field hygiene, strategy selection, xDB index rebuild/cleanup.

## What's inside

```
sitecore-search-index-ops/
├── SKILL.md
├── README.md
├── references/
│   ├── solr-runbook.md           # procedures and code/config patches
│   ├── spe-index-status.ps1      # read-only index status + crawler-root counts
│   └── spe-index-ops.ps1         # targeted re-index / rebuild with dry run + verification query
└── scripts/
    └── analyze_index_config.py   # showconfig + Crawling.log analyzer (Python 3, stdlib only)
```

## Requirements

- `showconfig.xml`: save `/sitecore/admin/showconfig.aspx` from the CM (and the indexing instance, if different)
- `Crawling.log.*.txt` / `Search.log.*.txt` from `App_Data/logs`
- SPE on the CM to run status and re-index scripts
- Python 3.9+
- Optional: Solr version, core/collection list, SolrCloud `CLUSTERSTATUS` JSON

---

## Using it with Claude

Example prompts:

- *"Rebuild of sitecore_web_index times out right at the end. showconfig and Crawling.log attached."*
- *"Search on our news listing doesn't show articles published today."*
- *"SearchStax shows 'no servers hosting shard: shard2' during rebuilds."*
- *"Content Editor search throws 'An error occurred while searching'."*
- *"We're moving to XM Cloud. What replaces our Solr-driven product search?"*

Claude diagnoses from configuration and logs, generates dry-run SPE scripts, and gives verification steps plus a prevention item.

---

## Using it without Claude

### 1. Analyze configuration and logs

```bash
python3 scripts/analyze_index_config.py showconfig.xml --out index-config-report.md
python3 scripts/analyze_index_config.py showconfig.xml \
    --crawling ./logs/Crawling.log.20261024.txt ./logs/Crawling.log.20261023.txt \
    --out index-config-report.md
```

| Argument | Description |
|---|---|
| `showconfig` (positional) | Saved `showconfig.aspx` XML |
| `--crawling` | Crawling log files or a folder (files starting with `Crawling`) |
| `--out` | Report path (default `index-config-report.md`) |

**Flags it raises:**

| Severity | Finding |
|---|---|
| Critical | SwitchOnRebuild rebuild core equals the main core (would wipe the live index) |
| Critical | Multiple indexes writing to the same core/collection |
| High | No update strategy (never updates) |
| High | SwitchOnRebuild type without a rebuild core |
| Medium | `syncMaster` on master (synchronous indexing on every save) |
| Medium | Web-database index without `onPublishEndAsync` |
| Medium | Custom index crawling `/sitecore` or `/sitecore/content` |
| Info | Manual strategy (needs a scheduled rebuild); large master/web index not SwitchOnRebuild; many computed fields |

### 2. Check status in Sitecore (read-only)

Run `references/spe-index-status.ps1` in the SPE ISE. It shows every index's type, document count, health, out-of-date flag, last update, rebuilding state, strategies and crawler roots, then compares item counts under each crawler root to document counts.

### 3. Re-index safely

Open `references/spe-index-ops.ps1` and set:

```powershell
$dryRun    = $true                       # flip to $false to execute
$indexName = "sitecore_master_index"
$rootPath  = "master:/sitecore/content/Site/Home/News"
$mode      = "Subtree"                   # Item | Subtree | FullRebuild
```

A dry run lists what would be indexed. FullRebuild warns when the index isn't SwitchOnRebuild. A verification `Find-Item` query runs at the end.

### 4. Apply runbook fixes

`references/solr-runbook.md` contains the procedures and patches. Match constructor signatures and type names to your exact Sitecore version (standalone vs SolrCloud).

### Use with another AI assistant

Provide `SKILL.md`, the runbook and the analyzer report.

---

## SitecoreAI search options

| Option | Good for | Limits |
|---|---|---|
| Experience Edge GraphQL `search` | Simple filter/sort/paginate over published items | No relevance tuning; 1,000-entity cap; 80 req/s |
| Sitecore Search | Full-text, facets, relevance, personalization | Separate product and contract; crawler/push indexing |
| Third-party (Coveo, Algolia, Elastic) | Existing investment, advanced features | Integration via webhook/crawler |

## Important notes and limits

- Confirm Solr version compatibility with your Sitecore version. An unsupported Solr is a common hidden cause.
- Crawling-log parsing relies on `[Index=name]` tags, which Sitecore uses in most versions. Untagged lines are grouped under `(unknown)`.
- Full rebuilds of non-SwitchOnRebuild indexes take that index's search offline. Schedule them and warn authors.

## Changelog

- **1.0.0** (2026-10): initial release.
