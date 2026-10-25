---
name: sitecore-log-performance-diagnostics
description: Diagnose Sitecore errors, outages and slowness from evidence the user exports — Sitecore log files (log.*.txt), IIS W3C logs, SitecoreAI environment logs, /sitecore/admin/cache.aspx and stats.aspx output, and Next.js rendering-host logs. Groups errors by signature, finds app-pool restarts, memory/timing/item threshold warnings, slow URLs, cache misconfiguration and event-queue problems, then gives a ranked root-cause analysis with fixes. Use whenever the user shares Sitecore logs, says the site is slow, CM is sluggish, CPU/memory is high, pages time out, app pool keeps recycling, errors spike after a deploy, or asks how to tune Sitecore caching.
---

# Sitecore Log & Performance Diagnostics

Sitecore logs are noisy — thousands of lines where three distinct problems hide among recurring harmless warnings. The value here is reducing a log dump to a short, ranked list of real causes with the evidence line for each, and then giving the fix.

## Operating constraint: no server access

You cannot read logs, open admin pages or attach profilers. The user gets you the evidence:

| Platform | How the user gets logs |
|---|---|
| XP/XM on-prem/IaaS | `<webroot>/App_Data/logs/` (`log.*.txt`, `Publishing.log.*`, `Crawling.log.*`, `Search.log.*`) and IIS `C:\inetpub\logs\LogFiles\W3SVC*` |
| Azure PaaS / Managed Cloud | Kudu → `App_Data/logs`, or App Insights query export |
| SitecoreAI CM | `dotnet sitecore cloud environment log list --environment-id <id> --latest`, then the CLI's log download subcommand (confirm flags with `dotnet sitecore cloud environment log --help`), or Deploy app → environment → Logs |
| Rendering host | Vercel/Netlify function logs; `DEBUG=content-sdk:*` locally |
| Caches | Save `/sitecore/admin/cache.aspx` and `/sitecore/admin/stats.aspx` as HTML (XP/XM; CM and each CD) |

Ask for the time window of the incident and the logs covering it from **every** instance involved (CM and each CD). A single CD's log rarely explains a farm-wide problem.

## Workflow

### 1. Parse

```bash
python3 scripts/analyze_sitecore_logs.py <files or folders> --out log-report.md \
    [--from "2026-10-24 08:00"] [--to "2026-10-24 10:00"] [--iis <iis-folder>] [--cache cache.html] [--stats stats.html]
```

The report contains:
- **Timeline**: starts/shutdowns (with shutdown reason when logged), first/last error, error rate per 10 minutes
- **Error signatures**: messages normalized (GUIDs, numbers, paths) and grouped, with count, first/last seen, exception type and the first stack frames from your code vs Sitecore code
- **Threshold warnings**: `Timing threshold exceeded`, `Item threshold exceeded`, `Memory threshold exceeded` — top URLs by count and worst value
- **Memory monitor / GC** warnings, `Cache ... cleared` storms
- **Event queue / remote events** errors (CD not receiving publish:end → stale caches)
- **Solr/search** exceptions summary (send detailed index problems to the index skill)
- **IIS** (if given): top URLs by total and p95 `time-taken`, 5xx by URL, request rate per minute
- **Caches** (if given): caches at/near max size, high-churn caches, HTML cache disabled sites
- **Rendering stats** (if given): renderings with high avg/max time and low cache-hit ratio

### 2. Rank causes

Order findings by user impact, not by count. A single `OutOfMemoryException` matters more than 40,000 known-harmless warnings. Use `references/signatures.md` to classify common signatures as Known-harmless / Symptom / Root cause and to pick fixes.

Typical root-cause patterns:
- **App pool recycles** → look at the shutdown reason: config change (someone edited `App_Config`), memory limit (private bytes recycle), unhandled exception, health monitoring, deployment. Repeated cold starts = slow site.
- **Slow pages** with `Timing threshold exceeded` + `Item threshold exceeded` on the same URLs → renderings iterating huge item sets (`Axes.GetDescendants`, `.GetChildren()` on big folders, Sitecore Query `//` lookups) instead of search/index or caching.
- **Slow after publish** → HTML cache cleared site-wide on every publish; frequent scheduled publishing; prefetch cache misconfigured; Solr commit storms.
- **Stale content on CD** → EventQueue errors, `publish:end:remote` handler missing the site, clock skew, EventQueue table bloat.
- **High CPU on CM** → indexing strategy `syncMaster` on large repositories, analytics aggregation, link database rebuilds, long-running SPE jobs.
- **Memory growth** → static caches in custom code, oversized `Caching.*` settings beyond available RAM, very large media in memory.

### 3. Cache tuning (XP/XM)

Use `references/caching.md`. In short: enable HTML caching on renderings that are deterministic per (datasource, params, language, device) with the right VaryBy flags; never cache user-specific output without VaryByUser; size data/item/prefetch caches from cache.aspx evidence (caches pinned at max size with constant evictions need more; caches far below max are fine); check `publish:end` HTML cache clearer lists every site.

### 4. SitecoreAI specifics

There is no CD to tune. Performance problems live in:
- the **rendering host** (SSR vs SSG/ISR choices, per-request GraphQL fan-out, missing caching of Edge responses, cold starts)
- **Experience Edge** limits (80 req/s → 429s; 1,000-entity query cap; heavy integrated GraphQL)
- the **CM** (Pages slowness: editing host cold start, heavy components in editing mode, large page layouts)

Ask for the rendering host logs and a HAR or network timing of a slow page. Point to the specific request that dominates.

### 5. Report

Write `DIAGNOSIS.md`: one-paragraph summary; ranked findings (cause, evidence line with file:time, impact, fix, confidence); what's known-harmless and can be ignored; the next evidence to collect if confidence is low; prevention (monitoring alerts to add). Keep it terse.

## References

- `references/signatures.md` — common log signatures and what they mean
- `references/caching.md` — Sitecore cache types, sizing, VaryBy rules
- `scripts/analyze_sitecore_logs.py` — parser (stdlib only)
