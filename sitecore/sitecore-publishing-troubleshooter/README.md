# sitecore-publishing-troubleshooter

**Find the real root cause when "I published and nothing changed," on Sitecore XP/XM (web database, Publishing Service) and SitecoreAI (Experience Edge).**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Administrator** · Platforms: **XP/XM 9.x–10.x**, **SitecoreAI**

---

## Why this exists

Publishing failures look identical to authors but have a dozen distinct causes:

- workflow state
- item and version restrictions
- missing language versions
- unpublished ancestors
- unpublished datasources and related items
- template/standard-values changes
- wrong targets
- hung queues
- HTML cache not cleared on CD
- remote events failing
- on SitecoreAI, Experience Edge's publish-time snapshot and front-end caching

Guessing costs hours. This skill collects evidence first, then walks a fixed decision tree to the first confirmed cause.

## What the skill does

1. **Triages** with only the missing questions: platform, item, language, action taken, symptom, scope, recent deploys.
2. **Diagnoses the item** with a read-only SPE script. It covers the item, its ancestors, rendering datasources (shared and final layout), template and standard values. For each it reports workflow state, restrictions, language versions, lock status, and existence plus `__Revision` match in each publishing target.
3. **Walks the XP/XM decision tree** (11 checks), from non-final workflow through HTML cache clearing, hung jobs, slow publishing and unexpected deletions.
4. **Walks the Experience Edge decision tree:** auxiliary entity failures, snapshot staleness (`_PublishingGroupingTemplate`), ISR/CDN caching and webhooks, URL collisions, sites sharing a start item, case-sensitive media, delta publish skips, and Edge's lack of item security.
5. **Parses publishing logs:** jobs, durations, unfinished jobs, per-item operations with skip reasons, deletions, and error signatures.
6. **Reports** root cause + evidence line, fix, prevention and author note. Bulk repairs are generated as dry-run SPE scripts.

## What's inside

```
sitecore-publishing-troubleshooter/
├── SKILL.md
├── README.md
├── references/
│   ├── publish-diagnose.ps1      # read-only SPE diagnostic for one item + dependencies
│   └── edge-revalidation.md      # Experience Edge webhook → Next.js on-demand revalidation
└── scripts/
    └── parse_publish_log.py      # publishing log parser (Python 3, stdlib only)
```

## Requirements

- SPE on the CM (to run the diagnostic)
- Log files: XP/XM `App_Data/logs/log.*.txt` and `Publishing.log.*.txt`; SitecoreAI logs via the Deploy app or `dotnet sitecore cloud environment log`
- Python 3.9+ for the log parser

---

## Using it with Claude

Example prompts:

- *"Authors approved /Home/News/Launch in English, published, and the live site still shows the old version. XP 10.3, no Publishing Service."*
- *"Here's the CSV from publish-diagnose.ps1. What's wrong?"*
- *"Publishing hangs on 'Initializing' every morning. Logs attached."*
- *"On XM Cloud, I edited a card inside a list, published it, and the page on Edge didn't change."*
- *"200 items are stuck in Awaiting Approval. Give me a safe script to move them to Approved."*

Claude asks for evidence before concluding and names the single next piece of evidence if the current set is inconclusive.

---

## Using it without Claude

### 1. Diagnose an item in Sitecore (read-only)

1. Open `references/publish-diagnose.ps1` in the SPE ISE.
2. Set the parameters at the top:
   ```powershell
   $path     = "master:/sitecore/content/Site/Home/Page"
   $language = "en"
   $includeAncestors   = $true
   $includeDatasources = $true
   $includeTemplate    = $true
   ```
3. Run it. A list view shows each related item with an **Issues** column, and a CSV downloads.

Issues it flags: `No version in <lang>`, `Workflow state not final`, `Never publish`, `Version hidden`, `Publish date in future`, `Unpublish date passed`, `Version valid-to passed`, `Locked by <user>`, `Not in <target>`, `Outdated in <target>`.

On SitecoreAI the Experience Edge target is not a queryable database, so target comparison is skipped automatically. Workflow and restriction checks still apply.

### 2. Parse logs

```bash
python3 scripts/parse_publish_log.py ./logs --out publish-report.md
python3 scripts/parse_publish_log.py Publishing.log.20261024.txt log.20261024.txt \
    --item "{11111111-2222-3333-4444-555555555555}" --out item-history.md
```

| Argument | Description |
|---|---|
| `paths` (positional, 1+) | Log files or folders (`.txt`/`.log`) |
| `--out` | Markdown report (default `publish-report.md`) |
| `--item` | Path fragment or ID to extract one item's publishing history |

Report sections:
- **Publish jobs:** start, end, duration, units, thread. Unfinished jobs are highlighted.
- **Slowest jobs.**
- **Item operations:** Created/Updated/Deleted/Skipped counts, top skip explanations, and a list of items deleted from the target.
- **Item history** (with `--item`).
- **Errors and publish warnings:** grouped by signature with first/last seen and stack head.

Per-item lines (`##Publish Item`) only appear when verbose publish logging is enabled. The report tells you if they're missing.

### 3. Follow the decision trees

`SKILL.md` contains both trees (XP/XM and Experience Edge) as check → evidence → fix tables. They work as a manual runbook.

### 4. Fix stale front-ends on SitecoreAI

`references/edge-revalidation.md` shows options (ISR window, Edge webhook → revalidation route, SSR) and a webhook route example for Next.js App Router.

### Use with another AI assistant

Provide `SKILL.md`, the diagnostic CSV and the parser output. Ask it to apply the decision tree.

---

## Most common causes (in order of how often they bite)

1. Item or datasource in a non-final workflow state
2. Datasource or related items never published
3. Missing language version
4. Version/item publishing restrictions
5. HTML cache not cleared on CD (site missing from `publish:end:remote` clearer list)
6. Experience Edge snapshot not refreshed after a child-item change
7. Front-end ISR/CDN cache serving old output

## Important notes and limits

- The diagnostic resolves GUID, path and `local:` datasources. `query:` datasources are skipped and must be resolved manually.
- Bulk repair scripts default to dry run. Use smart publish for repairs. Don't republish whole sites in business hours without accounting for cost.
- Verify Experience Edge limits on the current Sitecore docs before quoting numbers.

## Changelog

- **1.0.0** (2026-10): initial release.
