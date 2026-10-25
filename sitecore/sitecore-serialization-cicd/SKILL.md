---
name: sitecore-serialization-cicd
description: Design, fix and automate Sitecore Content Serialization (SCS) and deployment pipelines — sitecore.json and *.module.json authoring, include/rule scoping, overlap and conflict detection, Unicorn/TDS to SCS migration, Sitecore CLI (ser pull/push/validate, items as resources, cloud deployment), and GitHub Actions / Azure DevOps pipelines for SitecoreAI or XM/XP. Use whenever the user mentions serialization, SCS, module.json, Unicorn, TDS, "ser push" errors, items overwritten between environments, deploying templates/renderings, Sitecore CLI, CI/CD for Sitecore, or a deployment that lost content.
---

# Sitecore Serialization & CI/CD

In Sitecore, templates, renderings, placeholder settings and site config are database items that code depends on. Serialization turns them into YAML so they ship with the code. Done badly, it overwrites authored content in production or silently drops items. This skill makes serialization scopes deliberate and pipelines repeatable.

## Operating constraint: no CMS access

You cannot run the CLI against the user's environments. You produce config files, pipeline definitions and exact commands; the user runs them and pastes output back. When diagnosing, ask for: `sitecore.json`, all `*.module.json`, the CLI command used, and its full output with `--trace`.

## Core model (explain it when the user is confused)

- `sitecore.json` (repo root) lists module globs, plugins, and defaults.
- Each `*.module.json` has a unique `namespace`, optional `references` (other namespaces it depends on), and `items.includes[]`. Each include: `name`, `path`, `database` (default master), `scope`, `allowedPushOperations`, optional `rules[]` to override scope for sub-paths.
- **Scope**: `SingleItem`, `ItemAndChildren`, `ItemAndDescendants` (default), `DescendantsOnly`, `Ignored`.
- **allowedPushOperations**: `CreateUpdateAndDelete` (default — disk is truth, deletes extras in target), `CreateAndUpdate` (never deletes), `CreateOnly` (seed once; never overwrite — use for content authors own).
- Push with `CreateUpdateAndDelete` on a content path **deletes authored content** that isn't on disk. This is the #1 serialization disaster.

## Workflow

### 1. Analyze what exists

```bash
python3 scripts/analyze_scs.py <repo-root> --out scs-report.md
```

Reports:
- Modules, namespaces, include counts, YAML item counts per include
- **Overlaps**: two includes covering the same path (parent/child across modules without an `Ignored` rule) — causes nondeterministic push order and "item already serialized" errors
- **Danger**: `CreateUpdateAndDelete` on `/sitecore/content`, `/sitecore/media library`, or site Data/Home paths
- Invalid scope / operation values, missing references, duplicate namespaces
- Duplicate item IDs across YAML files, over-long paths (`maxRelativeItemPathLength`)
- Possible secrets in YAML (API keys, passwords, tokens)
- Mixed tooling: Unicorn configs or TDS `.scproj` alongside SCS

Read the "Critical" section first and fix those before anything else.

### 2. Scope by ownership

Apply this ownership model; it prevents most incidents:

| Item kind | Owner | Scope | Push op |
|---|---|---|---|
| Templates, renderings, placeholder settings, layouts | Developers | ItemAndDescendants | CreateUpdateAndDelete |
| Site definitions, SXA site settings, dictionary structure | Developers (structure) | ItemAndChildren or rules | CreateAndUpdate |
| Page/content seed data (home, error pages) | Authors after first deploy | SingleItem / ItemAndDescendants | CreateOnly |
| Authored content, media | Authors | not serialized | — |
| Roles (`/sitecore/system/...` roles via `roles` include) | Admins | as needed | CreateAndUpdate |

Never serialize Sitecore-shipped base items unless intentionally customizing them.

Use `references/module-patterns.md` for Helix-style module templates, rules examples, role/user serialization, and the Unicorn → SCS and TDS → SCS conversion maps.

### 3. Fix overlaps and conflicts

For each overlap, either (a) move the child path to its own include in the owning module and add `{ "path": "<child>", "scope": "Ignored" }` as a rule in the parent include, or (b) merge into one module. Add `references` so dependent modules push after their dependencies.

Output complete, corrected `*.module.json` files (not fragments).

### 4. Validate locally

Give the user this sequence:

```bash
dotnet tool restore
dotnet sitecore ser validate            # checks YAML integrity, duplicate IDs, orphans
dotnet sitecore ser validate --fix      # only after reviewing what it will fix
dotnet sitecore ser info                # shows modules and include resolution
dotnet sitecore ser push --what-if      # preview: never push blind to a shared environment
```

Confirm `--what-if` flag availability with `dotnet sitecore ser push --help` on their CLI version; if absent, push to a throwaway environment first.

### 5. Build the pipeline

Pick by target. Templates are in `references/pipelines.md`:

- **SitecoreAI**: `dotnet sitecore cloud login --client-credentials ...` with an automation client (Deploy app → Credentials), then `dotnet sitecore cloud deployment create --environment-id <id> --upload`. Serialized items are applied by the deployment via `xmcloud.build.json` (`postActions` → serialization). Watch with `cloud deployment watch` and pull logs with `cloud deployment log -o`.
- **XM/XP (self-hosted / Managed Cloud)**: build web artifacts, deploy files, then `dotnet sitecore login --client-credentials ... --cm <url> --authority <id-server>` and `dotnet sitecore ser push`, or ship items as resources (`dotnet sitecore itemres create`) with the web deploy so items load from the `.dat` files without a push step.

Every pipeline must: pin the CLI version via `.config/dotnet-tools.json`, keep secrets in the CI secret store (never in YAML or repo), fail on `ser validate` errors, and publish deployment logs as artifacts.

### 6. Incident: "deployment deleted/overwrote content"

1. Stop further deploys.
2. Ask for the deployment log and the module JSON that covered the path.
3. Identify the include with `CreateUpdateAndDelete` over authored content.
4. Restore: SitecoreAI — Sitecore support / environment backup; XP — DB restore or recycle bin/archive (`/sitecore/system/Archives` via SPE: `Get-Archive`, `Restore-ArchiveItem`). Provide the SPE restore script if recycle bin applies.
5. Fix the scope (CreateOnly or remove include), add a pipeline guard: fail the build if `analyze_scs.py --fail-on-critical` reports danger.

## References

- `references/module-patterns.md` — module.json patterns, rules, roles, Unicorn/TDS conversion
- `references/pipelines.md` — GitHub Actions and Azure DevOps YAML for SitecoreAI and XP
- `scripts/analyze_scs.py` — analyzer (stdlib only); `--fail-on-critical` exits 1 for CI gating
