# Sitecore caching (XP/XM)

## Cache layers
| Cache | Scope | What | Cleared by |
|---|---|---|---|
| Prefetch | per database | items loaded at startup per prefetch config | rarely; restart |
| Data | per database | raw item data from SQL | item changes, publish |
| Item | per database | Item objects | item changes, publish |
| Path | per database | path → ID | item moves/renames |
| Standard values | per database | standard values | template changes |
| HTML | per site | rendering output | publish:end / publish:end:remote (`HtmlCacheClearer`), manual |
| AccessResult | global | security checks | security changes |
| Media | disk | resized media | media item changes |

## Sizing from cache.aspx
- Cache at ~100% of max with high churn (count drops/climbs between refreshes) → increase that cache.
- Cache far below max → fine; don't raise blindly.
- Sum of all max sizes must fit comfortably in available process memory; oversized caches cause GC pressure and recycles.
- `Caching.DisableCacheSizeLimits` = true only with ample RAM and monitoring.
- Per-database settings: `<cacheSizes>` under each `<database>` and site `htmlCacheSize`.

## HTML cache rules
- Turn on `Cacheable` for renderings whose output depends only on datasource, parameters, language, device.
- VaryBy flags: `VaryByData` (datasource), `VaryByParm`, `VaryByDevice`, `VaryByLogin`, `VaryByUser`, `VaryByQueryString`. Missing flags = wrong content served to others.
- Never cache personalized renderings without the right vary (personalization rules usually break HTML caching for that rendering).
- Clear Cache on Publish: confirm every site name is in `publish:end` and `publish:end:remote` HtmlCacheClearer `<sites>` lists (SXA sites may require the SXA-specific clearer).
- Use `stats.aspx`: renderings with high count, low "from cache", and high avg ms are the best HTML cache candidates.

## Other performance levers
- Replace `Axes.GetDescendants()`/`//*` queries in renderings with ContentSearch queries.
- Avoid `Database.SelectItems` with fast queries on large trees at request time.
- Link database and index updates async; `syncMaster` strategy only for small repos.
- Media: serve via CDN, set `MediaResponse.MaxAge`, avoid huge originals.
- Disable idle timeout; enable Application Initialization warm-up.
- Cleanup agents: EventQueue, PublishQueue, History tables; schedule SQL index maintenance.
