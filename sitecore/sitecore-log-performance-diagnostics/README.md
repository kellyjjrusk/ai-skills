# sitecore-log-performance-diagnostics

**Turn a pile of Sitecore logs into a short, ranked list of real causes for errors, outages and slowness, with the evidence line and fix for each.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Administrator / Operations** · Platforms: **XP/XM 9.x–10.x** (full), **SitecoreAI** (CM logs, rendering host, Edge)

---

## Why this exists

Sitecore logs are noisy. Thousands of lines of harmless warnings hide the three things that matter: the recycle reason, the custom handler throwing on every remote event, the rendering walking 25,000 items per request.

The value is reduction and ranking:
- normalize and group messages into signatures
- line up restarts, error spikes and slow URLs on one timeline
- separate known-harmless noise from root causes
- point at the specific code or configuration to fix

## What the skill does

1. **Gathers evidence from every instance involved** (CM and each CD) for the incident window. It tells you where to get logs on each platform: on-prem, Azure PaaS / Managed Cloud, SitecoreAI CLI or Deploy app, rendering host.
2. **Parses:**
   - **Lifecycle:** starts and shutdowns with shutdown reasons (config change, bin change, idle timeout…), with repeated recycles flagged
   - **Error rate** per 10 minutes
   - **Error signatures:** normalized (GUIDs, numbers, paths, URLs, quoted values stripped), grouped, categorized, with exception types and *non-framework stack frames* (likely your code)
   - **Warning signatures:** top 20
   - **Threshold warnings:** `Timing`, `Item` and `Memory threshold exceeded` by URL with max and p95, plus URLs in both timing and item lists (classic tree-walking)
   - **IIS W3C logs:** top URLs by total time, p95/max, 5xx by URL, peak request rate
   - **cache.aspx:** caches at ≥85% of max size
   - **stats.aspx:** renderings ranked by cost (count × average time) with cache-hit %
3. **Ranks causes by user impact,** not by count, using a signature catalog (known-harmless / symptom / root cause).
4. **Tunes caching** (XP/XM): HTML cache candidates, VaryBy rules, cache sizing from evidence, publish-time clearing.
5. **Covers SitecoreAI specifics:** rendering-host SSR/SSG/ISR choices, Edge 429s and query cost, Pages/editing-host slowness.
6. **Writes `DIAGNOSIS.md`:** summary, ranked findings with confidence, what to ignore, next evidence to collect, and monitoring to add.

## What's inside

```
sitecore-log-performance-diagnostics/
├── SKILL.md
├── README.md
├── references/
│   ├── signatures.md            # common log signatures: meaning, class, action
│   └── caching.md               # cache layers, sizing from cache.aspx, HTML cache rules, other levers
└── scripts/
    └── analyze_sitecore_logs.py # log/IIS/cache/stats analyzer (Python 3, stdlib only)
```

## Requirements

- Python 3.9+
- Sitecore logs (`log.*.txt`; also works on `Publishing.log`, `Crawling.log`, `Search.log`)
- Optional: IIS W3C logs, saved HTML of `/sitecore/admin/cache.aspx` and `/sitecore/admin/stats.aspx` (from each instance)

---

## Using it with Claude

Example prompts:

- *"The site was slow from 8 to 10 this morning. Logs from CM and both CDs attached."*
- *"App pool keeps recycling every couple of hours. Why?"*
- *"Errors spiked right after last night's deploy. Here's the log."*
- *"Here's cache.aspx and stats.aspx from CD1. Which renderings should we cache, and are our caches sized right?"*
- *"XM Cloud site pages are slow. Here's a HAR file and the Vercel function logs."*

Claude ranks by impact, quotes the evidence line (file and time) for every finding, and says explicitly when confidence is low and what to collect next.

---

## Using it without Claude

### Run the analyzer

```bash
# Sitecore logs only
python3 scripts/analyze_sitecore_logs.py ./App_Data/logs --out log-report.md

# Focused window + IIS + caches + rendering stats
python3 scripts/analyze_sitecore_logs.py ./cm-logs ./cd1-logs \
    --from "2026-10-24 08:00" --to "2026-10-24 10:00" \
    --iis ./W3SVC1 \
    --cache cd1-cache.html --stats cd1-stats.html \
    --out log-report.md
```

| Argument | Description |
|---|---|
| `paths` (positional, 1+) | Sitecore log files or folders |
| `--out` | Markdown report (default `log-report.md`) |
| `--from`, `--to` | Time window, format `YYYY-MM-DD HH:MM` |
| `--iis` | IIS W3C log files or folders (needs the `#Fields:` header) |
| `--cache` | Saved HTML of `/sitecore/admin/cache.aspx` |
| `--stats` | Saved HTML of `/sitecore/admin/stats.aspx` |

**Supported log formats:**
- Classic Sitecore log4net lines: `ManagedPoolThread #6 09:21:19 INFO  message` or `4432 09:21:19 ERROR message`, with continuation lines (exceptions, stack traces). The date comes from the file name (`log.20261024.093000.txt`), and midnight rollover is handled.
- ISO-timestamped lines (`2026-10-24 09:21:19 [Error] message`), useful for exported cloud logs.

### Interpret the results

- Look up each signature in `references/signatures.md` to see whether it's harmless, a symptom, or a root cause.
- Use `references/caching.md` to act on cache and rendering-stats findings.
- `SKILL.md` lists the typical root-cause patterns: recycles, slow pages, slow after publish, stale CD content, high CM CPU, memory growth.

### Use with another AI assistant

Provide `SKILL.md`, both references, and `log-report.md` (much smaller than raw logs, and it fits in context).

---

## Typical patterns the report reveals

| What you see | Likely cause |
|---|---|
| Several START events + `Shutdown reason: ConfigurationChange` | Something is writing to `App_Config` or `bin` (deploy, AV scanner, script) |
| Same URL in timing **and** item thresholds | A rendering walks huge item trees (`GetDescendants`, `//*` queries) |
| `Exception while handling event ...Remote...` with your code in the stack | Custom `publish:end:remote` handler failing, so CD caches go stale |
| A cache at 95–100% of max | Undersized cache, causing constant eviction |
| High-cost rendering with ~0% from cache | HTML cache candidate (if output is deterministic) |

## Important notes and limits

- Bring logs from every instance. A single CD rarely explains a farm-wide issue.
- Signature normalization is heuristic. Very different messages can occasionally merge, and identical ones with unusual formatting can split.
- The cache/stats HTML parsers find tables by header names, so heavily customized admin pages may not parse.
- On SitecoreAI the main performance levers are in the rendering host and Edge usage, not server caches.

## Changelog

- **1.0.0** (2026-10): initial release.
