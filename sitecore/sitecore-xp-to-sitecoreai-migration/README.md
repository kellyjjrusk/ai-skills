# sitecore-xp-to-sitecoreai-migration

**Assess a Sitecore XP/XM solution and plan the move to SitecoreAI (formerly XM Cloud), or decide whether to upgrade first.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Developer / Architecture** · Platforms: **XP/XM 9.x–10.x → SitecoreAI**

---

## Why this exists

XP/XM customers face a forced decision. XP 10.0/10.1 extended support ends 31 Dec 2026, 10.2 in 2027 and 10.3 in 2028. XP 10.4 is the only version in Mainstream Support, through 31 Dec 2027. SitecoreAI is SaaS and headless-only, with:

- no CD server
- no xDB, xConnect, Marketing Automation or EXM
- no package-installed modules
- no MVC renderings
- Experience Edge delivery with real limits

The question every CIO asks, *"what breaks and what does it cost?"*, needs an item-by-item answer backed by evidence. This skill produces it.

## What the skill does

1. **Gathers evidence:** solution source, an SPE content inventory you run on your CM, `showconfig.xml`, version and topology, business drivers.
2. **Inventories the solution** with a scanner. It covers config patches (pipeline processors split into CD-time vs CM-side, events, scheduled agents, site definitions, custom indexes), MVC controllers and views, xDB/analytics, xConnect, EXM, ContentSearch, computed fields, Forms/WFFM, Commerce, Glass/Synthesis, Coveo, session state, Web API, custom field types, outbound integrations, and Sitecore package versions.
3. **Classifies every finding** into exactly one disposition: **Keep (CM-side) · Rebuild (headless) · Replace (SaaS) · Move to edge/app · Retire**.
4. **Estimates effort** per item (S/M/L/XL with hour ranges) and rolls it up by workstream as a range with stated assumptions.
5. **Lays out the decision:** direct to SitecoreAI, upgrade to 10.4/10.5 first, XM + headless SXA stepping stone, or stay on XP. It recommends one, with the triggers that would change that recommendation.
6. **Writes the deliverables:** `ASSESSMENT.md` (a one-page executive summary for the CIO plus the detail for engineering) and the annotated inventory.
7. **Flags collisions with SitecoreAI hard limits:** aliases, wildcard items, multiple sites sharing a start item, end-user item security, Edge entity and rate limits, and more.

## What's inside

```
sitecore-xp-to-sitecoreai-migration/
├── SKILL.md
├── README.md
├── references/
│   ├── disposition-matrix.md     # category → default disposition → effort size
│   ├── assessment-template.md    # ASSESSMENT.md skeleton
│   └── spe-inventory.ps1         # read-only SPE content inventory (run on your CM)
└── scripts/
    └── inventory_solution.py     # .NET solution scanner (Python 3, stdlib only)
```

## Requirements

- Solution source (all `.csproj`, `App_Config/Include/**`, `Views/**`, code)
- Python 3.9+
- SPE on the current CM to run the content inventory (admin user)
- Optional: `showconfig.xml`, saved from `/sitecore/admin/showconfig.aspx`

---

## Using it with Claude

Example prompts:

- *"We're on XP 10.2 scaled with SXA MVC and Forms. Assess what it takes to move to SitecoreAI. Solution zip attached."*
- *"Our extended support ends next year. Should we upgrade to 10.4 or go straight to XM Cloud?"*
- *"Here are the CSVs from the SPE inventory and our showconfig. Build the assessment report."*
- *"Which of our pipeline processors have no home in SitecoreAI?"*

Claude verifies current lifecycle dates (Sitecore KB0641167) and SitecoreAI limits before writing, marks unknowns as "Needs evidence", and leads with the hard truths rather than a sales pitch.

---

## Using it without Claude

### 1. Run the content inventory in Sitecore (read-only)

1. Open **SPE ISE** on the current CM as an administrator.
2. Paste `references/spe-inventory.ps1` and run it.
3. It downloads CSVs: `sites`, `content-volume`, `languages`, `renderings`, `rendering-usage`, `templates`, `workflows`, `modules`, `aliases`, `wildcards`.

The rendering-usage section walks the whole content tree and can take a while on large repositories. Run it off-hours.

### 2. Run the solution scanner

```bash
python3 scripts/inventory_solution.py /path/to/solution \
    --showconfig showconfig.xml \
    --out inventory.md --json inventory.json
```

| Argument | Description |
|---|---|
| `root` (positional) | Solution root |
| `--showconfig` | Optional merged config. Adds non-Sitecore processors, handlers and agents that source scanning can miss. |
| `--out` | Markdown report (default `inventory.md`) |
| `--json` | Machine-readable findings (default `inventory.json`) for spreadsheets/backlogs |

Report sections: detected Sitecore version (from package refs), file stats, modules detected, a disposition summary, findings by category with file:line, and package references.

### 3. Build the assessment

Apply `references/disposition-matrix.md` to each finding, then fill `references/assessment-template.md`. The workflow in `SKILL.md` describes how to weigh options and present the recommendation.

### 4. Use with another AI assistant

Provide `SKILL.md`, both Markdown references, `inventory.md` and the SPE CSVs as context. Ask it to produce the assessment following the template.

---

## Disposition model at a glance

| Disposition | Examples |
|---|---|
| **Keep (CM-side)** | Content Editor warnings, item:saved handlers, CM pipelines, SPE scripts |
| **Rebuild (headless)** | MVC view/controller renderings → Content SDK components; SXA MVC → headless SXA |
| **Replace (SaaS)** | xDB personalization → SitecoreAI personalize/CDP; EXM → ESP; Solr search → Sitecore Search; Forms |
| **Move to edge/app** | `httpRequestBegin`/`mvc.*` processors → Next.js middleware; CD Web API → API routes; session state |
| **Retire** | Glass Mapper/Synthesis, unused modules, dead code |

## Important notes and limits

- Defaults in the matrix are a starting estimate. Review real code before committing numbers.
- The scanner is heuristic (regex + XML parsing). It finds the common patterns. It does not prove the absence of others.
- Sitecore's own guidance: upgrading XP before migrating to SitecoreAI usually adds no efficiency. Upgrade first only when you need supported security patches during a long rebuild.

## Changelog

- **1.0.0** (2026-10): initial release.
