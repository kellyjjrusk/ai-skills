# sitecore-serialization-cicd

**Design, fix and automate Sitecore Content Serialization (SCS) and deployment pipelines, and stop deployments from deleting authored content.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Developer / DevOps** · Platforms: **SitecoreAI**, **XM/XP 10.x**

---

## Why this exists

In Sitecore, templates, renderings, placeholder settings and site configuration are database items that code depends on. Serialization turns them into YAML so they ship with the code. Done badly, it:

- **deletes authored content in production.** An include with `CreateUpdateAndDelete` over `/sitecore/content` removes everything not on disk.
- causes nondeterministic pushes through overlapping includes across modules
- leaves two sources of truth when Unicorn or TDS remain alongside SCS
- leaks secrets into source control through API keys in serialized fields

This skill makes serialization scopes deliberate, detects the dangerous configurations automatically, and gives you pipelines that are repeatable and gated.

## What the skill does

1. **Analyzes** `sitecore.json` and every `*.module.json`, plus the serialized YAML on disk.
2. **Applies an ownership model:** what developers own (templates, renderings), what is seeded once (`CreateOnly`), and what is never serialized (authored content, media).
3. **Fixes overlaps and conflicts:** moves child paths to owning modules, adds `Ignored` rules and `references` for push order. It outputs complete corrected module files.
4. **Migrates Unicorn/TDS to SCS** with concept-mapping tables and a side-by-side cutover method.
5. **Validates** locally with `ser validate`, `ser info` and `ser push --what-if`.
6. **Builds pipelines** for SitecoreAI (`cloud login --client-credentials`, `cloud deployment create --upload`, log capture) and XM/XP (file deploy + `ser push`, or items as resources). It pins the CLI version and gates on validation.
7. **Runs incident response** when a deployment overwrote or deleted content: stop, identify the include, restore, fix and add a CI guard.

## What's inside

```
sitecore-serialization-cicd/
├── SKILL.md
├── README.md
├── references/
│   ├── module-patterns.md   # sitecore.json, feature/project modules, rules, roles, Unicorn/TDS → SCS maps
│   └── pipelines.md         # GitHub Actions (SitecoreAI), Azure DevOps (XM/XP), CI gates
└── scripts/
    └── analyze_scs.py       # SCS analyzer + CI gate (Python 3, stdlib only)
```

## Requirements

- A repository using (or moving to) SCS
- Python 3.9+
- .NET SDK and Sitecore CLI (pinned in `.config/dotnet-tools.json`) for validation and pushes
- For pipelines: CI secrets for a SitecoreAI automation client, or Identity Server client-credentials for XM/XP

---

## Using it with Claude

Example prompts:

- *"Review our serialization config. sitecore.json and modules attached. Anything dangerous?"*
- *"Our last deploy wiped pages authors created in /Home. Here's the deployment log and module.json."*
- *"Convert our Unicorn configs to SCS modules."*
- *"Write a GitHub Actions pipeline that validates serialization and deploys to our SitecoreAI production environment."*
- *"`ser push` fails with 'item already serialized by another module'. Output attached."*

You'll get the analyzer report, complete corrected `*.module.json` files, pipeline YAML, and exact CLI commands to run.

---

## Using it without Claude

### Run the analyzer

```bash
python3 scripts/analyze_scs.py /path/to/repo --out scs-report.md
# in CI: exit code 1 when critical issues exist
python3 scripts/analyze_scs.py . --out scs-report.md --fail-on-critical
```

| Argument | Description |
|---|---|
| `root` (positional) | Repo root containing `sitecore.json` |
| `--out` | Markdown report (default `scs-report.md`) |
| `--fail-on-critical` | Exit 1 if any critical finding exists, for use as a CI gate |

**What it detects:**

| Severity | Finding |
|---|---|
| Critical | Missing or invalid `sitecore.json`; module globs matching nothing; invalid JSON |
| Critical | Invalid `scope` / `allowedPushOperations` values (e.g. `ItemsAndDescendants` typo) |
| Critical | `CreateUpdateAndDelete` over `/sitecore/content` or the media library (can delete author content) |
| Critical | Duplicate namespaces; the same path included twice; duplicate item IDs across YAML files |
| Critical | Possible secrets in YAML (API keys, tokens, passwords, JWTs, AWS keys) |
| Critical | Unicorn configs or TDS `.scproj` alongside SCS |
| Warning | Parent/child overlap across includes without an `Ignored` rule |
| Warning | `references` that match no module namespace |
| Warning | YAML paths near `maxRelativeItemPathLength` (Windows path-length risk) |

The report also includes a full module/include table: path, database, scope, push operation, rule count and YAML item count.

### Use the patterns and pipelines

- `references/module-patterns.md`: copy-ready module JSON for feature and project/site modules with rules, role serialization, and Unicorn/TDS → SCS conversion tables.
- `references/pipelines.md`: GitHub Actions for SitecoreAI, Azure DevOps for XM/XP, `dotnet-tools.json` pinning, and recommended gates. Copy `analyze_scs.py` into your repo (e.g. `tools/`) to use the gate.

### Use with another AI assistant

Provide `SKILL.md`, both references, your `sitecore.json`, module files and the analyzer output.

---

## The ownership model

| Item kind | Owner | Scope | Push operation |
|---|---|---|---|
| Templates, renderings, placeholder settings, layouts | Developers | ItemAndDescendants | CreateUpdateAndDelete |
| Site settings, SXA presentation, dictionary structure | Developers (structure) | rules | CreateAndUpdate |
| Seed pages (home, error pages) | Authors after first deploy | SingleItem | CreateOnly |
| Authored content, media | Authors | — | not serialized |

## Important notes and limits

- Confirm CLI flags with `dotnet sitecore <command> --help` for your pinned version. Flags have changed across CLI major versions.
- The "danger" check is heuristic. It flags delete-capable includes under content/media unless the path looks developer-owned (`/presentation`, `/settings`, `/dictionary`). Review every flag.
- Unicorn YAML is not byte-compatible with SCS YAML. Always re-pull with SCS.

## Changelog

- **1.0.0** (2026-10): initial release.
