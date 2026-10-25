# sitecore-content-sdk-migration

**Migrate Sitecore JSS Next.js applications to the Sitecore Content SDK for SitecoreAI (XM Cloud).**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Developer** · Platform: **SitecoreAI / XM Cloud**

---

## Why this exists

JSS 22.x reached end of support in **June 2026**, and JSS 23.x supports only XM/XP, **not SitecoreAI**. Every SitecoreAI front-end still on `@sitecore-jss/*` is running unsupported code. New platform capabilities (App Router, React 19 / Next.js 16, Agentic Studio integration, secure editing hostnames) ship only in the Content SDK.

The migration is not a package rename. It changes configuration (`temp/config` → `sitecore.config.ts`), component registration (factory → explicit component map), middleware (plugin pattern → `defineMiddleware`), data access (hand-built GraphQL services → `SitecoreClient`) and editing (Experience Editor removed, Pages only). This skill turns that into an inventory, a plan and verified code.

## What the skill does

1. **Inventories** the JSS app: packages and versions, every JSS import grouped by symbol, custom middleware plugins, env vars, router type and risk flags. It weights those flags into a Low/Medium/High effort score.
2. **Chooses a path:** a fresh Content SDK scaffold with code ported in (recommended for most apps), or an in-place upgrade.
3. **Writes `MIGRATION-PLAN.md`:** targets, package swaps, file-by-file actions, a component checklist, middleware rewrites, an env-var matrix (local / Deploy app / delivery host), editing-host verification, test plan and rollback.
4. **Performs the mechanical changes** using a symbol-level mapping table. It outputs complete files, not diffs.
5. **Checks the silent breakers:** Experience Editor and chromes code, Content Editor preview loss, case-sensitive `componentName` mismatches, editing secret mismatch, secure editing hostnames, Edge rate limits (80 req/s), personalization packages, and mixed literal/variable GraphQL.
6. **Verifies** with a runnable checklist (build, grep for leftover JSS, debug logging, route tests, Pages editing tests) and diagnoses any failures you paste back.

## What's inside

```
sitecore-content-sdk-migration/
├── SKILL.md                    # workflow and rules the agent follows
├── README.md
├── references/
│   ├── api-map.md              # JSS → Content SDK packages, config, runtime symbols, env vars
│   └── plan-template.md        # MIGRATION-PLAN.md skeleton
└── scripts/
    └── scan_jss_usage.py       # repo scanner (Python 3, stdlib only)
```

## Requirements

- The Next.js rendering-host repository (JSS 20.x–22.x)
- Python 3.9+ for the scanner
- Node.js and npm to build and verify the migrated app
- Access to the SitecoreAI Deploy app and your delivery host to update environment variables (you do this; the skill tells you exactly what to set)

---

## Using it with Claude

Install the skill (see the [library README](../README.md#using-the-skills-with-claude)), then ask naturally. The skill triggers on mentions of JSS, `sitecore-jss-nextjs`, Content SDK, JSS end of support, or a broken SitecoreAI front-end after an upgrade.

Example prompts:

- *"Our XM Cloud site is on JSS 22.4. Plan the move to Content SDK 2.x. The repo is attached."*
- *"Scan this repo and tell me how much JSS-specific code we have and what's risky."*
- *"Convert `src/components/Hero.tsx` and `src/lib/middleware/plugins/redirects.ts` to Content SDK."*
- *"After migrating, the Pages canvas is blank. Here's the browser console."*

What you'll get: `jss-inventory.md`, `MIGRATION-PLAN.md`, complete replacement files, and an author-impact note (what content authors will notice).

> Claude cannot log in to SitecoreAI. It will ask for files or output it needs and tell you exactly where to check environment settings.

---

## Using it without Claude

### 1. Run the scanner

```bash
python3 scripts/scan_jss_usage.py /path/to/nextjs-app --out jss-inventory.md
```

| Argument | Description |
|---|---|
| `root` (positional) | Repository root of the Next.js app |
| `--out` | Output Markdown path (default `jss-inventory.md`) |

The report contains:

| Section | Meaning |
|---|---|
| Router detected | Pages, App, Mixed or Unknown |
| Packages | Every `@sitecore-jss/*`, `@sitecore-cloudsdk/*`, `@sitecore-content-sdk/*`, `next`, `react` with versions |
| Risk flags | Experience Editor/chromes code, `temp/config` imports, component factory/builder, hand-built GraphQL services, page-props plugins, `SitecoreContext` usage, disconnected/preview mode, each with file:line |
| JSS modules / Symbols by module | Every imported symbol and where it's used, which is your search-and-replace worklist |
| Custom plugins | Files under `src/lib/**/plugins` that need rewriting |
| Environment variables | Every `process.env.X` and `.env*` key |
| Summary | Import sites, plugin count, weighted risk score → effort |

It skips `node_modules`, `.next`, build output and `.git`. It is read-only.

### 2. Follow the runbook

Read `SKILL.md` top to bottom. It is the migration procedure. Use `references/api-map.md` for every replacement and `references/plan-template.md` for the plan document.

### 3. Use with another AI assistant

Give your assistant `SKILL.md` + `references/api-map.md` as context (Cursor rule, Copilot instructions, custom GPT knowledge), plus the scanner output. Ask it to follow the workflow.

---

## Verification checklist (run after migrating)

```bash
npm ci && npm run lint && npm run build
grep -rn "sitecore-jss" src/ package.json     # must return nothing
DEBUG=content-sdk:* npm run dev               # watch layout/dictionary calls resolve
```

Then check: home page, deep page, 404, 500, multilingual page, personalized page. In SitecoreAI Pages, open pages, edit a field inline, add a component, save, publish to Edge, and confirm on the delivery site.

## Important notes and limits

- **Versions move fast.** The skill instructs the agent to look up the current upgrade guide and npm version before planning. Do the same if using it manually.
- **Author impact:** after migration, Experience Editor and Content Editor preview are unavailable. Plan training.
- **Env vars live in three places:** local `.env`, the SitecoreAI Deploy app (editing host), and the delivery host (Vercel/Netlify). A missing delivery-host variable is the most common "works locally, 500 in prod" cause.
- Some symbol names (e.g. editing-mode detection on the page object) differ between Content SDK minor versions. Confirm against the fresh scaffold.

## Changelog

- **1.0.0** (2026-10): initial release.
