# sitecore-headless-component-builder

**Build production-ready Sitecore headless components end to end: the React/Next.js component, data template, JSON rendering, variants and GraphQL, generated together so they can't drift apart.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Developer** · Platforms: **SitecoreAI (Content SDK)**, **XM/XP headless (JSS / headless SXA)**

---

## Why this exists

A headless component is three things that must agree exactly:

1. the front-end component that reads `fields.<FieldName>`
2. the **rendering item** whose `componentName` points at that component (case-sensitive)
3. the **datasource template** whose field names the component reads

Most *"renders locally but not in Pages"*, *"Unknown component"* and *"fields aren't editable"* bugs come from a mismatch between those three. Hand-writing serialized YAML with GUIDs is error-prone too. This skill generates all three from a single spec. It creates CMS items through the Sitecore API (via SPE) so you never hand-craft field IDs, then you serialize them into source control.

## What the skill does

1. **Reads your repo conventions first:** SDK (Content SDK vs JSS), import paths, typing, styling, file layout, naming case. Generated code is then adapted to match.
2. **Confirms a component spec:** name, module, fields and types (with required markers), datasource rules, placeholders, variants, rendering parameters.
3. **Scaffolds:**
   - a typed TSX component using SDK field components (`Text`, `RichText`, `NextImage`, `Link`, `DateField`, `File`). It handles empty datasources and keeps empty fields clickable in editing mode.
   - an **idempotent SPE script** that creates the template folder, template, section, fields (with sort order), `__Standard Values`, required-field validators, JSON Rendering (`componentName`, `Datasource Template`, `Datasource Location`) and optional headless SXA variants.
   - an optional **integrated GraphQL** query using `jsonValue`, so fields stay editable.
   - a README with run order and verification steps.
4. **Applies Experience Edge rules:** 80 req/s rate limit, 1,000-entity query cap, no mixed literal/variable inputs, publish-time snapshot behavior, case-sensitive media URLs.
5. **Verifies** through a Pages checklist and troubleshoots from real errors.

## What's inside

```
sitecore-headless-component-builder/
├── SKILL.md
├── README.md
├── references/
│   ├── graphql-patterns.md      # integrated query, Edge search with pagination, retry-safe fetch-all
│   └── troubleshooting.md       # symptom → cause → fix
└── scripts/
    └── scaffold_component.py    # generator (Python 3, stdlib only)
```

## Requirements

- Python 3.9+
- A dev CM with SPE (SitecoreAI CM or XM/XP with headless services) to run the generated item script
- Sitecore CLI with a serialization module that covers the new paths (`dotnet sitecore ser pull`)
- Your Next.js rendering host repo

---

## Using it with Claude

Example prompts:

- *"Create a PromoCard component: heading (required), body rich text, image (required), CTA link. Module Feature/Promotions. Content SDK."*
- *"Turn this Figma frame / HTML snippet into a Sitecore component with a Default and Compact variant for our headless SXA site Acme/AcmeSite."*
- *"Add an integrated GraphQL query so PromoList renders its child PromoCards."*
- *"My component shows 'Unknown component' in Pages but renders locally. Here's the rendering item and component map."*

Claude reads one of your existing components first and matches its style. It then gives you the TSX, the SPE script to run, and the serialize-and-verify steps.

---

## Using it without Claude

### Generate a component

```bash
python3 scripts/scaffold_component.py \
  --name PromoCard \
  --module "Feature/Promotions" \
  --fields "Heading:Single-Line Text!,Body:Rich Text,Image:Image!,Cta:General Link,PublishDate:Date" \
  --sdk content-sdk \
  --variants "Default,Compact" \
  --site-collection "Acme/AcmeSite" \
  --graphql \
  --out ./out
```

| Argument | Required | Description |
|---|---|---|
| `--name` | yes | Component name, PascalCase. Becomes `componentName`, template and rendering name. |
| `--module` | yes | Path under `/sitecore/templates/` and `/sitecore/layout/Renderings/`, e.g. `Feature/Promotions` |
| `--fields` | yes | Comma-separated `Name:Type`. Append `!` to mark required. |
| `--sdk` | no | `content-sdk` (default) or `jss` |
| `--variants` | no | Comma-separated PascalCase variant names → named exports + SXA variant items |
| `--site-collection` | no | `Collection/Site` for creating headless SXA variant items |
| `--graphql` | no | Also emit an integrated GraphQL query |
| `--out` | no | Output folder (default `.`) |

**Supported field types:** Single-Line Text, Multi-Line Text, Rich Text, Image, General Link, Checkbox, Date, Datetime, Number, Integer, File.

**Output files:**

| File | Purpose |
|---|---|
| `PromoCard.tsx` | Component with typed fields, editing-aware rendering, empty-datasource state, variant exports |
| `create-PromoCard.ps1` | SPE script that creates template, fields, standard values, validators, JSON rendering, variants. Safe to re-run. |
| `PromoCard.graphql` | Integrated query (if `--graphql`). Paste it into the rendering's ComponentQuery field. |
| `README-PromoCard.md` | Run order and checks |

### Run order

1. Review, then run `create-PromoCard.ps1` in the **SPE ISE on a dev CM**.
2. Confirm the items exist under `/sitecore/templates/<module>` and `/sitecore/layout/Renderings/<module>`.
3. Make sure a serialization module includes those paths, then run `dotnet sitecore ser pull` and commit the YAML.
4. Copy the TSX into `src/components/`, adapt it to repo conventions, and regenerate the component map.
5. For headless SXA, add the rendering to the site's **Available Renderings**.
6. `npm run build`, then in Pages: add the component, create a datasource, edit every field, save, publish, verify on the delivery site.

### Use with another AI assistant

Give it `SKILL.md`, both references, one existing component from your repo, and the generator output. Ask it to adapt the TSX to your conventions.

---

## Important notes and limits

- The generated TSX is a correct skeleton, not your house style. Adapt imports, classes and file layout.
- Editing-mode detection differs between SDK versions. The generated code marks the line to confirm (`page.mode.isEditing` for Content SDK, `sitecoreContext.pageEditing` for JSS).
- Headless SXA variant template paths vary slightly by version. The script checks for the variant root and tells you if it can't create them.
- The SPE script writes items. Run it on a dev CM, never directly in production.
- For the full symptom → fix list, see `references/troubleshooting.md`.

## Changelog

- **1.0.0** (2026-10): initial release.
