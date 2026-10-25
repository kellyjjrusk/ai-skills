---
name: sitecore-publishing-troubleshooter
description: Diagnose and fix Sitecore publishing problems on XP/XM (web database, Publishing Service) and SitecoreAI (Experience Edge) — content not appearing live, stuck or slow publishes, partial publishes, items unpublished unexpectedly, stale pages after publish, Edge publish failures, dictionary or related items missing. Generates an SPE diagnostic script for the affected item, parses publishing logs the user exports, and produces a root cause and fix. Use whenever the user says changes aren't showing, publish is stuck/hanging/slow, "I published but the site didn't update", Edge or webhook cache issues, publishing queue jams, or asks why an item won't publish.
---

# Sitecore Publishing Troubleshooter

Publishing failures look identical to authors ("I published and nothing changed") but have a dozen distinct causes across workflow, restrictions, language, ancestors, related items, targets, queues, caches and — on SitecoreAI — the Edge snapshot. Guessing wastes hours. This skill collects evidence first, then walks a fixed decision tree.

## Operating constraint: no CMS access

You cannot open the Content Editor, publishing dialogs, logs or databases. Evidence comes from the user running what you give them:
- `references/publish-diagnose.ps1` in the SPE ISE (read-only; outputs a report for one item and its dependencies)
- Log files they download (XP: `log.*.txt`, `Publishing.log.*.txt`; SitecoreAI: `dotnet sitecore cloud environment log list/download`, or the Deploy app → Logs)
- Screenshots of the item's Publish tab / Pages publish panel

Ask for evidence before concluding. One targeted question beats a list of ten possibilities.

## Step 0 — triage questions (ask only what's missing)

1. Platform: XP/XM (which version, Publishing Service yes/no) or SitecoreAI?
2. Which item (path or ID), which language, which site?
3. What was done (publish item / with subitems / related items / site publish / workflow approve)?
4. What is seen: old content, 404, partial page, or publish dialog never finishes?
5. One item or many? Started when? Anything deployed recently?

## Step 1 — run the item diagnostic

Have the user run `references/publish-diagnose.ps1` after setting `$path` and `$language` at the top. It reports, for the item, its ancestors, its renderings' datasources and its template/standard values:
- workflow + state + final flag
- item and version publishing restrictions (Never publish, Publish/Unpublish dates, Valid from/to, Hide version)
- language versions present
- existence and revision in each publishing target database (master vs target revision mismatch = not published or changed since)
- datasources not present/outdated in target
- locked by user

## Step 2 — decision tree (XP/XM)

Work top to bottom; stop at the first confirmed cause.

| # | Check | Evidence | Fix |
|---|---|---|---|
| 1 | Item in non-final workflow state | diagnostic: `FinalState=False` | Approve through workflow; publishing skips non-final versions silently |
| 2 | Publishing restrictions | `NeverPublish`, future `Publish` date, past `Unpublish`, `HideVersion`, `ValidTo` passed | Clear restriction; remember version restrictions are per version per language |
| 3 | Language version missing | no version in that language | Create/translate version; publish that language |
| 4 | Ancestor not in target | ancestor `InTarget=False` | Publish ancestors (or publish with "publish ancestors" if available) |
| 5 | Datasource/related items not published | datasource `InTarget=False` or revision mismatch | Publish with related items; or publish datasources; consider workflow on datasources |
| 6 | Template/standard values changed but not published | template revision mismatch | Publish template + `__Standard Values` |
| 7 | Wrong target / target misconfigured | targets list, `Target database` field | Fix target; check `connectionStrings` for target DB name |
| 8 | Published fine, site still stale | target revision matches master | HTML cache not cleared: check `publish:end` / `publish:end:remote` `HtmlCacheClearer` site list includes the site; CDN/output cache; CD instances not receiving remote events (EventQueue) |
| 9 | Publish dialog hangs / never finishes | log shows no `Job ended` | Check queue (Publishing Service dashboard or `/sitecore/admin/jobs.aspx`), long-running job, SQL blocking, `Publishing.TimeBeforeStatusExpires` too low on huge publishes, EventQueue/PublishQueue table bloat |
| 10 | Slow publishing | log durations | Republish vs smart vs incremental misuse; huge PublishQueue; cleanup agents disabled; consider Publishing Service; parallel publishing settings |
| 11 | Items deleted from web unexpectedly | log `Operation=Deleted` | Parent moved/renamed; "publish subitems" from a parent where items were deleted in master; Publishing Service orphan handling |

For 8–11, parse the logs (step 3).

## Step 2b — decision tree (SitecoreAI / Experience Edge)

| # | Check | Fix |
|---|---|---|
| 1 | Workflow / restrictions / language (same as XP 1–3) | same |
| 2 | Edge publish errors | Logs/Deploy app; consult "Publishing failures and diagnostics" page — many failures are auxiliary entities (dictionary, translations) and don't mean the page failed |
| 3 | Page published, child/datasource change not visible | Edge stores a **layout snapshot at publish time**. Republish the page, or mark list/container items with `_PublishingGroupingTemplate` so related changes republish together |
| 4 | Published on Edge, site still stale | Front-end cache: SSG/ISR `revalidate` too long, no on-demand revalidation webhook, CDN cache. Configure Edge webhook → Next.js revalidate API route |
| 5 | Item missing on Edge only | Edge limits: two items differing only by space vs dash collide (same URL identifier); `*` target hostname breaks publish; multiple sites sharing a start item; wildcard items unsupported on delivery |
| 6 | Media 404 on Edge | case-sensitive media URLs |
| 7 | Delta publish skipped items | `CheckDeltaPublishBlock` errors in logs → republish affected items |
| 8 | Content visible that should be private | Edge enforces no item security; use publishing restrictions |

Verify the current Edge limits page before citing numbers — web-search `Experience Edge limitations doc.sitecore.com`.

## Step 3 — parse logs

```bash
python3 scripts/parse_publish_log.py <log files or folder> --out publish-report.md [--item "<path or id>"]
```

Extracts publish jobs (start, end, duration, target, mode, units processed), per-item operations from `##Publish Item` lines (Created/Updated/Deleted/Skipped with explanation) when verbose publish logging is on, errors/exceptions with stack heads, and timelines. `--item` filters to one item's history. If no `##Publish Item` lines exist, tell the user how to enable item-level publish logging (set `Publishing.LogInterval` / publish log level per their version) and reproduce.

## Step 4 — report

Deliver, briefly: **Root cause** (one sentence, with the evidence line), **Fix** (exact steps or SPE script), **Prevention** (workflow/config change), and **Author note** if authors need to do something differently. If evidence is inconclusive, say so and name the single next piece of evidence needed.

For bulk fixes (e.g. 500 items stuck in a non-final state, or republishing datasources), generate an SPE script with a dry-run switch defaulting to `$true`, output a list, and only act when the user sets it to `$false`. Always use smart publish for repairs, never republish of a whole site in business hours without saying what it costs.

## References

- `references/publish-diagnose.ps1` — read-only SPE diagnostic
- `references/edge-revalidation.md` — Edge webhook → Next.js on-demand revalidation pattern
- `scripts/parse_publish_log.py` — log parser (stdlib only)
