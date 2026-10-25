---
name: sitecore-headless-component-builder
description: Build production-ready Sitecore headless components end to end — the Next.js/React component (Content SDK or JSS), the data template, the JSON rendering, datasource and placeholder settings, plus any custom GraphQL query for Experience Edge — and an SPE script that creates the CMS items so they can be serialized. Use whenever the user asks to create, scaffold or convert a Sitecore component, rendering, datasource template, placeholder, variant, or GraphQL integrated/connected query; converts a Figma design or HTML into a Sitecore component; or asks why a component shows "Unknown component", won't edit in Pages, or returns empty fields.
---

# Sitecore Headless Component Builder

A headless component is three things that must agree exactly: the front-end component, the rendering item whose `componentName` points at it, and the datasource template whose field names the component reads. Most "it renders locally but not in Pages" bugs are a mismatch between those three. This skill produces all three together from one spec, so they cannot drift.

## Operating constraint: no CMS access

You cannot create items in SitecoreAI or XM yourself. You produce:
1. Front-end code the user commits.
2. An **SPE script** the user runs once on a dev CM to create the template, rendering, and folders.
3. The serialization step (`dotnet sitecore ser pull`) the user runs to capture those items as YAML into source control.

This route uses the Sitecore API to create items, so you never hand-write GUIDs or field IDs that could be wrong. If the user has no SPE access, fall back to precise click-path instructions for Content Editor.

## Workflow

### 1. Read the repo's conventions before writing anything

Ask for (or open) one existing component, the component map / component builder file, `sitecore.config.ts` or `temp/config`, and one serialization module JSON. Match exactly: SDK (Content SDK vs JSS — check `package.json`), import paths, prop typing style, styling approach (Tailwind, CSS modules, SXA grid classes), file location (`src/components/<Name>.tsx` or folders), naming case. Code that doesn't match house style gets rewritten in review — avoid that.

### 2. Write the component spec

Confirm a short spec with the user (or derive from a design/HTML they gave):

```
Component: PromoCard
Module: Feature/Promotions          # template + rendering folder
Fields:
  - heading: Single-Line Text (required)
  - body: Rich Text
  - image: Image (required)
  - cta: General Link
Datasource: required, location ./Data or site Data folder
Placeholders exposed: none | promo-actions
Variants: Default, Compact  (headless SXA only)
Rendering params: none | theme (Droplist)
```

Field names become JS property names — use PascalCase or camelCase consistently with the repo (SXA starters use PascalCase like `Title`). The component must read `fields.<FieldName>` with that exact casing.

### 3. Generate the scaffold

```bash
python3 scripts/scaffold_component.py \
  --name PromoCard --module "Feature/Promotions" --site-collection "" \
  --fields "Heading:Single-Line Text,Body:Rich Text,Image:Image,Cta:General Link" \
  --sdk content-sdk --out ./out
```

Outputs:
- `PromoCard.tsx` — typed component using SDK field helpers with empty-datasource handling and Pages editing support
- `create-PromoCard.ps1` — SPE script: creates template + section + fields, `__Standard Values`, JSON Rendering with `componentName`, `Datasource Template`, `Datasource Location`; idempotent (skips existing)
- `PromoCard.graphql` — optional integrated GraphQL query if `--graphql` is passed
- `README-PromoCard.md` — run order and verification steps

Then adapt the generated TSX to the repo conventions from step 1. The script gives a correct skeleton; the repo's style wins.

### 4. Component rules (why they matter)

- **Always use SDK field components** (`Text`, `RichText`, `Image`/`NextImage`, `Link`) rather than reading `.value` directly. They emit the editing metadata Pages needs; raw `.value` renders but is not editable.
- **Handle missing datasource.** In Pages an author can drop a component before choosing a datasource. Render a helpful empty state in editing mode, nothing in live mode. Content SDK: check `page.mode.isEditing` (confirm the property name in the repo's version); JSS: `withDatasourceCheck`.
- **Never conditionally hide an empty field in editing mode** — authors need the empty field to click into. Hide only when not editing.
- **Images**: use the SDK `NextImage` (or `Image`) helper; configure `next.config` `images.remotePatterns` for `edge.sitecorecloud.io` and the media host. Media URLs on Edge are case-sensitive.
- **Links**: use the SDK `Link`; it handles internal/external/anchor and editing.
- **No data fetching inside the component** unless unavoidable. Prefer: datasource fields (simplest) → integrated GraphQL on the rendering (`ComponentQuery` field) for related items → `getComponentServerProps`/server component fetch only for truly external data.
- **Register the component** in the component map (Content SDK: regenerate the map via the CLI script in `package.json`; JSS: component builder regenerates on `bootstrap`). The registered name must equal the rendering's `componentName`, case-sensitive.

### 5. GraphQL on Experience Edge — limits that bite

- 80 requests/second per tenant on the delivery API; SSG builds of large sites need retries enabled.
- Max 1,000 entities per query; paginate with `first`/`after` and `pageInfo { hasNext endCursor }`.
- **Don't mix literals and variables** in one query — if any input uses a variable, all must.
- Edge is a published snapshot: integrated GraphQL results are frozen at publish time. Changing a referenced item requires republishing the page (or using `_PublishingGroupingTemplate` / publishing related items).
- Preview endpoint ≠ delivery endpoint; wildcards work on preview only.

Use `references/graphql-patterns.md` for integrated-query, search, and pagination examples.

### 6. Verification the user runs

1. Run `create-<Name>.ps1` in SPE on a **dev** CM. Read its output.
2. `dotnet sitecore ser pull` and commit the new YAML (confirm the module JSON `includes` cover the new paths — if not, add an include; see the serialization skill).
3. `npm run build` passes; component map contains the new name.
4. In Pages: add the component from the toolbox to a test page, create a datasource, edit every field inline, save, publish to Edge, view on the delivery site.
5. Remove the datasource and confirm the empty state shows in editing and nothing on the live page.

If anything fails, ask for the exact error (browser console, Pages error banner, build log) and use `references/troubleshooting.md`.

## Headless SXA specifics

If the site is headless SXA: place renderings under `/sitecore/layout/Renderings/Feature/<Module>`, add the rendering to the site's **Available Renderings** (Presentation > Available Renderings) or it won't appear in the toolbox, and create variants under `/sitecore/content/<collection>/<site>/Presentation/Headless Variants/<Component>`. Variants map to named exports in the component file (`export const Default`, `export const Compact`). The scaffold emits named exports when `--variants` is passed.

## References

- `references/graphql-patterns.md` — integrated query, Edge search, pagination
- `references/troubleshooting.md` — symptom → cause → fix
- `scripts/scaffold_component.py` — generator (stdlib only)
