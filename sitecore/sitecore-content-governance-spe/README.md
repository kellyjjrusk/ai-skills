# sitecore-content-governance-spe

**Content audits and safe bulk operations in Sitecore with Sitecore PowerShell Extensions (SPE): find the rot, then fix it without destroying anything.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Administrator / Content operations** · Platforms: **XP/XM 9.x–10.x**, **SitecoreAI** (SPE on the CM)

---

## Why this exists

Sitecore repositories decay:
- thousands of unused media items
- pages stuck in Draft for years
- broken internal links and orphaned datasources
- missing translations
- empty or duplicate SEO metadata
- folders with thousands of children

SPE can find and fix all of it from inside the CMS. It can also delete a content tree in one line.

This skill gives you **read-only audits** and **bulk-change scripts that are safe by construction**. It also includes a generator that turns a spreadsheet of changes into a validated, dry-run-first SPE script.

## What the skill does

1. **Clarifies scope** in one exchange: platform, database, site roots, languages, templates, report vs fix.
2. **Runs audits** from a library of 9 read-only SPE scripts. Each outputs a list view, a CSV and a summary.
3. **Analyzes results:** totals, top offenders, patterns (one template, editor or date range), and a ranked action list. Deletion always requires sign-off from the content owner.
4. **Generates bulk changes** that follow a non-negotiable safety contract (below), either from a CSV or from the bulk template.
5. **Accounts for SitecoreAI differences:** DAM-hosted media, Edge publishing jobs, CM restarts during deployments.

## The safety contract

Every script that writes content has all of these, in this order:

1. **Parameters**: `$dryRun = $true`, `$scopeRoot`, `$database`, `$language`, `$maxItems`
2. **Scope guard**: refuses `/sitecore`, `/sitecore/content`, `/sitecore/system`, `/sitecore/templates`, `/sitecore/layout` and the media library root unless `$allowBroadScope = $true`
3. **Collect first, act second**: builds the full change list (Path, ID, Field, Old, New, Action) before touching anything
4. **Preview**: list view plus CSV download of the plan
5. **Cap**: aborts if changes exceed `$maxItems`
6. **Backup**: exports affected items to a Sitecore package and downloads it. Deletions go to the recycle bin.
7. **Act**: inside `BulkUpdateContext`, with explicit `BeginEdit`/`EndEdit` and `CancelEdit` on failure
8. **Log**: every change via `Write-Log`, plus a summary of successes and failures
9. **No publishing**: publishing is a separate, deliberate step

## What's inside

```
sitecore-content-governance-spe/
├── SKILL.md
├── README.md
├── assets/spe/
│   ├── _template-bulk.ps1                  # safety-contract skeleton for any bulk operation
│   ├── audit-broken-links.ps1              # links + datasources pointing to missing items (link DB)
│   ├── audit-unused-media.ps1              # media with no referrers, with size and age filter
│   ├── audit-large-media.ps1               # media over N MB, grouped by extension
│   ├── audit-stale-workflow.ps1            # non-final items idle > N days, by state and editor
│   ├── audit-language-coverage.ps1         # pages missing required language versions
│   ├── audit-publishing-restrictions.ps1   # never-publish, future/past dates, hidden/expired versions
│   ├── audit-seo-fields.ps1                # empty/too-long/duplicate title + meta description
│   ├── audit-folder-size.ps1               # items with > N children (bucket-aware)
│   └── audit-orphan-datasources.ps1        # datasource items no page references
└── scripts/
    └── csv_to_spe_bulk.py                  # CSV → validated SPE bulk-update script (Python 3, stdlib only)
```

## Requirements

- Sitecore PowerShell Extensions on the CM; a user with SPE access and write rights to the scope (an elevated session where SPE requires it)
- Python 3.9+ for the CSV generator
- A current **link database** for referrer-based audits (broken links, unused media, orphan datasources). Rebuild via Control Panel → Database → Rebuild Link Database if results look wrong (heavy operation).

---

## Using it with Claude

Example prompts:

- *"Find all unused media over 30 days old in /sitecore/media library/Project/Acme and tell me how much space we'd recover."*
- *"Which pages under /Acme/Home are missing French-Canadian and Spanish versions?"*
- *"Here's a spreadsheet of 800 pages with new meta descriptions. Generate the update script."*
- *"Move everything under /Home/Archive/2019 to /Home/Archive/Old and rename items to lowercase. Make it safe."*
- *"Here's the stale-workflow CSV. What should we do about it?"*

Claude never runs anything. It writes complete scripts with the safety contract and analyzes the CSVs you send back.

---

## Using it without Claude

### Run an audit (read-only)

1. Open the script from `assets/spe/` in the SPE ISE.
2. Set the parameters at the top (`$scopeRoot`, `$language`, thresholds, field names).
3. Run it. Review the list view; the CSV downloads automatically.

| Script | Key parameters |
|---|---|
| `audit-broken-links.ps1` | `$scopeRoot` |
| `audit-unused-media.ps1` | `$mediaRoot`, `$excludes`, `$minAgeDays` |
| `audit-large-media.ps1` | `$mediaRoot`, `$minSizeMB` |
| `audit-stale-workflow.ps1` | `$scopeRoot`, `$languages`, `$staleDays` |
| `audit-language-coverage.ps1` | `$scopeRoot`, `$required` |
| `audit-publishing-restrictions.ps1` | `$scopeRoot`, `$language` |
| `audit-seo-fields.ps1` | `$scopeRoot`, `$titleField`, `$descField`, `$maxTitle`, `$maxDesc` |
| `audit-folder-size.ps1` | `$scopeRoot`, `$threshold` |
| `audit-orphan-datasources.ps1` | `$scopeRoot`, `$dataFolderNames` |

### Generate a bulk update from a CSV

CSV format (header required, case-insensitive):

| Column | Required | Notes |
|---|---|---|
| `ItemPath` or `ItemID` | one of them | Path must be inside `--scope`; ID must be a GUID |
| `Field` | yes | Field name |
| `Value` | for set/append | Text value |
| `Language` | no | Defaults to `--language` |
| `Action` | no | `set` (default), `append`, `clear` |

```csv
ItemPath,ItemID,Field,Value,Language,Action
/sitecore/content/Acme/Home/About,,MetaDescription,"About Acme, the company's story",en,set
,{AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE},Title,O'Reilly & Sons,fr-CA,set
/sitecore/content/Acme/Home/News,,Teaser,,en,clear
```

```bash
python3 scripts/csv_to_spe_bulk.py changes.csv \
    --scope "/sitecore/content/Acme" \
    --database master --language en --max-items 1000 \
    --out bulk-update.ps1
```

| Argument | Description |
|---|---|
| `csv` (positional) | Changes file |
| `--scope` | Required. Every row must fall under this path. |
| `--database` | Default `master` |
| `--language` | Default language for rows without one (default `en`) |
| `--max-items` | Cap embedded in the script (default 1000) |
| `--out` | Output script (default `bulk-update.ps1`) |

**Validation (script is not written if any error is found, exit code 1):** missing path/ID, malformed GUIDs, paths outside scope, empty field names, invalid actions or language codes, conflicting duplicate rows for the same item/field/language. **Warnings:** standard fields (`__*`), empty `set` values.

**The generated script then:**
- resolves every item
- reports rows it can't apply (not found, outside scope, no version, field not on template)
- skips unchanged values
- previews and records the plan
- enforces the cap and dry run
- backs up to a package, applies in `BulkUpdateContext`, and logs
- prints a summary, without publishing

### Write any other bulk operation

Copy `assets/spe/_template-bulk.ps1`, fill in section 3 (selection and computed changes) and the action switch in section 7. Keep every section.

### Use with another AI assistant

Provide `SKILL.md`, `_template-bulk.ps1` and the relevant audit script. Require it to keep the safety contract intact.

---

## Important notes and limits

- **Test write scripts on a non-production CM first**, every time.
- Referrer-based audits only see links tracked in the link database. Media used only from code, CSS, external systems or untracked rich-text references will look "unused."
- Large-tree audits (`-Recurse` on `/sitecore/content`) can take minutes. Narrow the scope for speed.
- Field names in the SEO audit vary by solution. Set them to match your templates.
- SPE scripts have been syntax-checked with PowerShell 7.4. Report any runtime issue on your Sitecore/SPE version.

## Changelog

- **1.0.0** (2026-10): initial release.
