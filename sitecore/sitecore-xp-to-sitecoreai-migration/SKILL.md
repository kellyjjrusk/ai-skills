---
name: sitecore-xp-to-sitecoreai-migration
description: Assess and plan a move from Sitecore XP/XM (MVC, on-prem or Managed Cloud) to SitecoreAI (formerly XM Cloud), or decide whether to upgrade to XP 10.4/10.5 instead. Inventories a .NET Sitecore solution, classifies every customization (pipelines, MVC renderings, xDB/analytics, Solr queries, modules, scheduled tasks) into keep/rebuild/replace/retire, estimates effort and produces an assessment report and phased roadmap. Use whenever the user mentions XP or XM end of support, upgrading Sitecore, moving to XM Cloud or SitecoreAI, headless migration, replatforming, Sitecore 10.x lifecycle dates, or asks "what will break if we go to XM Cloud".
---

# XP/XM → SitecoreAI Migration Assessment

Organizations on XP/XM face a forced decision: XP 10.0/10.1 extended support ends 31 Dec 2026, 10.2 extended ends 2027, 10.3 in 2028, and 10.4 is the only version in Mainstream Support (through 31 Dec 2027). SitecoreAI is SaaS, headless-only, with no CD server, no xDB, no module installation and no custom .NET on the delivery side. The assessment's job is to show — item by item — what survives that move and what it costs.

## Operating constraint: no CMS access

You cannot log in to the CM, Managed Cloud, or the Cloud Portal. Work from:
- the solution source (zip, repo, or pasted files)
- exports the user runs and pastes back: SPE reports (`references/spe-inventory.ps1`), `/sitecore/admin/showconfig.aspx` output saved as XML, IIS/Sitecore logs, content counts

Never assert a content volume, site count or module list you haven't seen evidence for. Mark unknowns explicitly as "Needs evidence" in the report.

## Verify lifecycle facts first

Support dates and SitecoreAI capabilities change. Before writing the report, web-search: `Sitecore product support lifecycle KB0641167`, `SitecoreAI limitations Experience Edge`, and the current SitecoreAI release notes. Use what you find, cite it, and note the date checked.

## Workflow

### 1. Gather evidence

Ask for (or locate in the workspace):
1. The solution folder (all `.csproj`, `App_Config/Include/**`, `Views/**`, `src/**`)
2. Output of `references/spe-inventory.ps1` run in the SPE console on the current CM (exports sites, templates, renderings, content counts, languages, workflows, modules) — the user runs it and attaches the CSVs
3. `showconfig.aspx` saved as `showconfig.xml` (the fully merged config — reveals patched pipelines that source search can miss)
4. Current version (`/sitecore/shell/sitecore.version.xml`), topology (XP Scaled/Single, XM), hosting
5. Business drivers and hard dates

### 2. Run the solution inventory

```bash
python3 scripts/inventory_solution.py <solution-root> [--showconfig showconfig.xml] --out inventory.md --json inventory.json
```

It classifies findings into categories with a default disposition (see `references/disposition-matrix.md`):
- Config patches: pipeline processors, events, scheduled agents, site definitions, custom providers
- MVC: controllers, `.cshtml` views, controller/view renderings
- xDB / analytics: `Tracker`, `Sitecore.Analytics`, xConnect, marketing automation, EXM
- Search: `ContentSearch`, `IProviderSearchContext`, custom indexes, computed fields
- Modules: SXA (MVC), Forms, WFFM, Commerce, Coveo, Unicorn/TDS, SPE, Glass/Synthesis
- Integrations: `HttpClient`, WCF, SOAP refs, custom APIs on CD
- Sitecore package versions from `.csproj` / `packages.config`

### 3. Classify every finding

Each item gets exactly one disposition:

| Disposition | Meaning | Typical SitecoreAI target |
|---|---|---|
| **Keep (CM-side)** | Runs on authoring only, allowed in SitecoreAI | Custom CM pipelines, item event handlers, SPE scripts — deployable to the CM |
| **Rebuild (headless)** | Presentation that must be re-implemented | MVC renderings → Content SDK Next.js components |
| **Replace (SaaS)** | XP feature with no SitecoreAI equivalent | xDB personalization → SitecoreAI/Personalize; EXM → external ESP; Solr site search → Sitecore Search |
| **Move to edge/app** | Delivery-time logic with no CD server | Next.js middleware, API routes, serverless functions |
| **Retire** | Unused, duplicated, or obsolete | — |

Be precise about the CD-server loss: anything that executes per request on CD (custom `httpRequestBegin` processors, `mvc.*` pipelines, rendering-time Solr queries, `Tracker.Current`, session state) has no home in SitecoreAI and must move to the rendering host or be replaced.

### 4. Estimate

Use the effort model in `references/disposition-matrix.md` (S/M/L/XL per item with hour ranges). Sum by workstream: Front-end rebuild, CM customizations, Search, Personalization/analytics, Integrations, Content migration, Testing. Give a range, not a point estimate, and state assumptions.

### 5. Decide: migrate now, upgrade first, or stay

Present the options honestly:
- **Direct to SitecoreAI** — Sitecore's own guidance: no efficiency benefit from upgrading XP before migrating. Best when timeline allows a full headless rebuild.
- **Upgrade to 10.4 (or 10.5) first** — buys Mainstream Support through 2027 (10.4) while the headless rebuild happens. Justified when the go-live of SitecoreAI is >12 months away and the current version is out of security support.
- **XM 10.4 + headless SXA as a stepping stone** — incremental, but you pay twice for infrastructure.
- **Stay on XP** — only defensible if xDB/marketing automation is core and the org accepts the platform's direction.

Recommend one, with the trigger conditions that would change the recommendation.

### 6. Write the deliverables

1. `ASSESSMENT.md` — executive summary (1 page), current state, inventory summary table, risk register, recommendation, roadmap (phases with exit criteria), effort range, open questions. Template: `references/assessment-template.md`.
2. `inventory.md` / `inventory.json` — from the script, annotated.
3. Optional: a Sheets/xlsx backlog of every rebuild item if the user asks.

Write for two audiences: the CIO reads the first page; the engineering lead reads the rest. Lead with the hard truth (cost, what's lost), not a sales pitch.

## Known SitecoreAI hard limits to check against

- No CD role; delivery is Experience Edge (GraphQL, 80 req/s, max 1,000 entities per query, published snapshot of layout).
- No xDB, xConnect, Marketing Automation, EXM, Path Analyzer, Experience Profile.
- No module installation via packages on delivery; CM customization is limited and deployed via source.
- MVC renderings not supported; headless SXA required.
- Experience Edge: no aliases, no virtual folders, no wildcard items on delivery, no multiple site definitions pointing to the same start item (common in XP/SXA), max 1,000 sites per tenant, case-sensitive media URLs, security restrictions not enforced (use publishing restrictions).
- Item-level security for end users doesn't apply to anonymous delivery.

Flag every inventory finding that collides with one of these.

## References

- `references/disposition-matrix.md` — category → default disposition → effort size
- `references/assessment-template.md` — report skeleton
- `references/spe-inventory.ps1` — SPE script the user runs on their CM to export the content-side inventory
- `scripts/inventory_solution.py` — solution scanner (stdlib only)
