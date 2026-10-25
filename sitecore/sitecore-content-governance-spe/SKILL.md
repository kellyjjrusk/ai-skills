---
name: sitecore-content-governance-spe
description: Run content audits and safe bulk operations in Sitecore using Sitecore PowerShell Extensions (SPE) — broken links, unused and oversized media, stale workflow items, missing language versions, expired or never-published pages, missing SEO/metadata fields, oversized folders, orphaned datasources — and bulk updates, moves, renames, language-version creation, workflow transitions, publishing and cleanup with dry-run, scope guards, package backup and change logs. Generates ready-to-run SPE scripts and turns a user's CSV into a validated bulk-update script. Use whenever the user wants a Sitecore content report, cleanup, inventory, mass edit, bulk field change, migration of content values, find items by criteria, or mentions SPE/PowerShell for Sitecore — on XP/XM or SitecoreAI.
---

# Sitecore Content Governance with SPE

Sitecore repositories decay: thousands of unused media items, pages stuck in Draft for years, broken internal links, missing translations, metadata nobody filled in. SPE can find and fix all of it from inside the CMS — and can also destroy a content tree in one line. This skill produces audit scripts that are read-only and bulk scripts that are safe by construction.

## Operating constraint: no CMS access

You never run anything. You write SPE scripts the user runs in the SPE ISE (or Console), and you analyze the CSV/list output they paste or attach. SPE runs as the logged-in user with the full Sitecore API — treat every write script as production-dangerous.

## Safety contract for every write script (non-negotiable)

Every script that changes content must have all of these, in this order:

1. **Parameters block** at the top: `$dryRun = $true`, `$scopeRoot`, `$database`, `$language`, `$maxItems`.
2. **Scope guard**: refuse to run if `$scopeRoot` is `/sitecore`, `/sitecore/content`, `/sitecore/system`, `/sitecore/templates` or `/sitecore/layout` unless the user explicitly set `$allowBroadScope = $true`.
3. **Collect first, act second**: build the full change list as objects (`Path`, `ID`, `Field`, `Old`, `New`, `Action`) before touching anything.
4. **Preview**: `Show-ListView` of the change list; also `Export-Csv` + `Out-Download` so there's a record.
5. **Cap**: abort if the change count exceeds `$maxItems` (prevents runaway queries).
6. **Backup** (when not dry run): export affected items to a package (`New-Package` + `New-ItemSource`/`New-ExplicitItemSource` + `Export-Package`) and download it, or for deletions use recycle (never `-Permanently` unless asked twice).
7. **Act** inside `New-UsingBlock (New-Object Sitecore.Data.BulkUpdateContext)` for performance; edit with `$item.Editing.BeginEdit()/EndEdit()`; respect workflow (do not silently bypass it — say so if the script does).
8. **Log**: write every change with `Write-Log` and return a final summary (counts by action, failures with reasons).
9. **Publishing** is a separate, explicit step — never publish inside a bulk edit script unless the user asks.

Use `assets/spe/_template-bulk.ps1` as the skeleton. Do not drop any section to make a script shorter.

## Workflow

### 1. Clarify scope in one exchange

Ask only what's missing: platform (XP/XM version or SitecoreAI), database, site root path(s), languages, template names/IDs involved, and whether the output is a report, a fix, or both.

### 2. Audits (read-only)

Pick from `assets/spe/` and parameterize:

| Script | Finds |
|---|---|
| `audit-broken-links.ps1` | Internal links and rendering datasources pointing to missing items, per field |
| `audit-unused-media.ps1` | Media with no referrers in the link database (+ size), excluding system folders |
| `audit-large-media.ps1` | Media over a size threshold, by extension |
| `audit-stale-workflow.ps1` | Items in non-final states older than N days, by state and last editor |
| `audit-language-coverage.ps1` | Pages missing versions in required languages |
| `audit-publishing-restrictions.ps1` | Expired, future-dated, never-publish and hidden versions |
| `audit-seo-fields.ps1` | Pages with empty/duplicate title, meta description, or too-long values |
| `audit-folder-size.ps1` | Folders with more than N children (performance risk; bucket candidates) |
| `audit-orphan-datasources.ps1` | Datasource items under Data folders not referenced by any page |

All audits: read-only, output `Show-ListView` + CSV download, with a summary line. The link database must be current for referrer-based audits — tell the user to rebuild it (Control Panel → Database → Rebuild Link Database) if results look wrong, and warn that it is heavy.

### 3. Analyze results

When the user attaches the CSV, summarize: totals, top offenders, patterns (one template, one editor, one date), and a recommended action list ranked by value and risk. Don't recommend deleting media or content without a business owner sign-off — say who should decide.

### 4. Bulk changes

For a CSV-driven change (the most common request: "update these 800 items' field X"), validate and generate:

```bash
python3 scripts/csv_to_spe_bulk.py changes.csv --database master --language en --scope "/sitecore/content/Acme" --out bulk-update.ps1
```

CSV columns: `ItemPath` or `ItemID` (one required), `Field`, `Value`, optional `Language`, `Action` (`set` default, `append`, `clear`). The generator rejects malformed IDs, paths outside scope, duplicate (item, field, language) rows with conflicting values, and empty field names; it embeds the data, follows the safety contract, compares old vs new so unchanged rows are skipped, and reports rows whose item or field doesn't exist.

For other bulk operations (move, rename, add language versions, workflow transition, set publishing restrictions, delete-to-recycle-bin), write them from `_template-bulk.ps1`.

### 5. SitecoreAI notes

SPE is available on the SitecoreAI CM. Differences: media may live in Content Hub/DAM rather than the media library; publishing goes to Experience Edge (bulk publish via `Publish-Item` still works but each publish creates Edge jobs — batch sensibly); link database behaves the same; avoid long-running scripts during deployments (the CM may restart).

## Output

Full `.ps1` files (complete, never fragments), each with a header comment saying what it does, whether it writes, and how to run it. For analyses: a short findings summary and a ranked action list.

## References

- `assets/spe/_template-bulk.ps1` — the safety-contract skeleton
- `assets/spe/audit-*.ps1` — audit library
- `scripts/csv_to_spe_bulk.py` — CSV → validated SPE bulk-update generator (stdlib only)
