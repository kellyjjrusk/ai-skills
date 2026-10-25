# Sitecore AI Skills

Skills for the hardest, most in-demand Sitecore work, grouped into **developer** and **administrator** skills. Part of the [AI Skills Library](../README.md); new skills are added over time. They cover Sitecore XP/XM (on-prem, IaaS, Managed Cloud) and **SitecoreAI** (formerly XM Cloud).

Each skill packages expert knowledge, a step-by-step workflow, and ready-to-run tooling: Python analyzers and Sitecore PowerShell Extensions (SPE) scripts. They were written as [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) for Claude, but **none of the value is locked to Claude**. Every script runs on its own, and every `SKILL.md` is plain Markdown you can read as a runbook or load into any AI assistant.

---

## Contents

- [Design principle: the CMS is behind a login](#design-principle-the-cms-is-behind-a-login)
- [The skills](#the-skills)
- [Platform coverage](#platform-coverage)
- [Repository layout](#repository-layout)
- [Using the skills with Claude](#using-the-skills-with-claude)
- [Using the skills without Claude](#using-the-skills-without-claude)
- [Requirements](#requirements)
- [Safety model](#safety-model)
- [Validation status](#validation-status)
- [Keeping it current](#keeping-it-current)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Design principle: the CMS is behind a login

Sitecore's CM, Cloud Portal, Deploy app, Solr admin and logs all sit behind authentication. An AI assistant cannot log in, and you should not give it credentials. So every skill is built on an **evidence loop**:

```
 ┌──────────────┐  code, logs, configs, CSV exports  ┌───────────────────────────┐
 │     You      │ ─────────────────────────────────▶ │ Skill (Claude, or you)     │
 │ (logged in)  │                                    │ analyzes the evidence      │
 │              │ ◀───────────────────────────────── │ writes the scripts to run  │
 └──────────────┘  SPE scripts, CLI commands, code    └───────────────────────────┘
        │
        └── you run the scripts inside Sitecore, then share the output back
```

- **Read-only exports first.** SPE scripts you run in the SPE ISE export exactly what's needed (users and roles, renderings, index status, publish diagnostics) as CSV.
- **Local analyzers second.** Python scripts turn those exports, or your repo, logs and `showconfig.xml`, into ranked findings.
- **Changes last, and safely.** Any script that writes content is a dry run by default, guards its scope, previews every change, and backs up first.

This also means **no Sitecore credentials ever leave your environment**.

---

## The skills

### Developer skills

| Skill | What it does | Bundled tooling |
|---|---|---|
| [**sitecore-content-sdk-migration**](./sitecore-content-sdk-migration/) | Migrates JSS Next.js apps to the Sitecore Content SDK. JSS 22.x support ended June 2026, and JSS 23.x does not support SitecoreAI. | `scan_jss_usage.py` repo scanner, JSS→Content SDK mapping table, migration plan template |
| [**sitecore-xp-to-sitecoreai-migration**](./sitecore-xp-to-sitecoreai-migration/) | Assesses an XP/XM solution for a move to SitecoreAI (or an upgrade). Classifies every customization and produces an assessment and roadmap. | `inventory_solution.py` .NET solution scanner, SPE content inventory, disposition and effort matrix, report template |
| [**sitecore-headless-component-builder**](./sitecore-headless-component-builder/) | Builds a headless component end to end: TSX, data template, JSON rendering, variants and GraphQL, kept in sync from one spec. | `scaffold_component.py` generator (TSX + SPE item-creation script + GraphQL), GraphQL patterns, troubleshooting table |
| [**sitecore-serialization-cicd**](./sitecore-serialization-cicd/) | Designs and fixes Sitecore Content Serialization (SCS) and CI/CD pipelines. Catches configs that can delete authored content. | `analyze_scs.py` analyzer with CI gate, module patterns, Unicorn/TDS→SCS maps, GitHub Actions and Azure DevOps pipelines |
| [**sitecore-marketplace-app-builder**](./sitecore-marketplace-app-builder/) | Builds Marketplace apps that extend SitecoreAI: Pages panels, custom fields, dashboard widgets, full-screen and standalone apps. | SDK patterns, Next.js app skeleton, public-app security compliance matrix |

### Administrator skills

| Skill | What it does | Bundled tooling |
|---|---|---|
| [**sitecore-publishing-troubleshooter**](./sitecore-publishing-troubleshooter/) | Finds the root cause of "I published and nothing changed" on XP/XM and Experience Edge. | `publish-diagnose.ps1` SPE item diagnostic, `parse_publish_log.py`, Edge revalidation pattern |
| [**sitecore-security-access-audit**](./sitecore-security-access-audit/) | Audits users, roles, access rights and workflow permissions, plus instance hardening and SitecoreAI identity hygiene. | `spe-security-export.ps1`, `analyze_security_export.py` severity-ranked analyzer, access-rule evaluation guide, hardening checklist |
| [**sitecore-log-performance-diagnostics**](./sitecore-log-performance-diagnostics/) | Turns Sitecore and IIS logs and the cache/stats pages into a ranked root-cause analysis of errors, outages and slowness. | `analyze_sitecore_logs.py`, log signature catalog, caching guide |
| [**sitecore-search-index-ops**](./sitecore-search-index-ops/) | Diagnoses and tunes Solr indexes (SwitchOnRebuild, update strategies, SolrCloud), and maps search options for SitecoreAI. | `analyze_index_config.py`, SPE index status and targeted re-index scripts, Solr runbook |
| [**sitecore-content-governance-spe**](./sitecore-content-governance-spe/) | Content audits and safe bulk operations with SPE. | 9 SPE audit scripts, safety-contract bulk template, `csv_to_spe_bulk.py` CSV→SPE generator |

---

## Platform coverage

| Skill | XP/XM 9.x–10.x | SitecoreAI / XM Cloud |
|---|---|---|
| Content SDK migration | — | ● |
| XP → SitecoreAI migration | ● (source) | ● (target) |
| Headless component builder | ● (JSS/headless SXA) | ● |
| Serialization & CI/CD | ● | ● |
| Marketplace app builder | — | ● |
| Publishing troubleshooter | ● | ● (Experience Edge) |
| Security & access audit | ● | ● (item ACLs + Cloud Portal) |
| Log & performance diagnostics | ● | ◐ (CM logs, rendering host, Edge) |
| Search & index ops | ● (Solr) | ◐ (Edge search, Sitecore Search guidance) |
| Content governance (SPE) | ● | ● (SPE runs on the SitecoreAI CM) |

● full support · ◐ partial / guidance · — not applicable

---

## Repository layout

```
sitecore/
├── README.md                              ← you are here
├── sitecore-content-sdk-migration/
│   ├── README.md                          ← human documentation
│   ├── SKILL.md                           ← skill instructions (YAML frontmatter + Markdown)
│   ├── references/                        ← deeper docs the skill loads on demand
│   └── scripts/                           ← standalone tools
├── sitecore-xp-to-sitecoreai-migration/
├── sitecore-headless-component-builder/
├── sitecore-serialization-cicd/
├── sitecore-marketplace-app-builder/
├── sitecore-publishing-troubleshooter/
├── sitecore-security-access-audit/
├── sitecore-log-performance-diagnostics/
├── sitecore-search-index-ops/
└── sitecore-content-governance-spe/
    └── assets/spe/                        ← SPE script library
```

Every skill follows the same anatomy:

| File/folder | Purpose |
|---|---|
| `SKILL.md` | The skill itself. Frontmatter `name` and `description` tell an agent when to use it; the body is the workflow. |
| `README.md` | Documentation for humans: what it is, how to use it with and without Claude. |
| `scripts/` | Python 3 tools, **standard library only**, with no `pip install` needed. |
| `references/` | Reference docs, templates and SPE scripts. |
| `assets/` | Files used as-is in output (e.g. the SPE script library). |

---

## Using the skills with Claude

### Claude Code

Copy the skill folders into a skills directory:

```bash
# all projects (personal)
mkdir -p ~/.claude/skills
cp -r sitecore-* ~/.claude/skills/

# or one project only (commit it so the whole team gets it)
mkdir -p .claude/skills
cp -r sitecore-* .claude/skills/
```

Claude reads each skill's `description` and loads the skill automatically when your request matches. For example, "our JSS app needs to move to Content SDK" triggers the migration skill. You can also name a skill explicitly.

### Claude apps (claude.ai, desktop, mobile)

Zip a skill folder, or use the pre-built `.skill` package if you publish one in Releases. Then upload it under **Settings → Capabilities → Skills**. Code execution must be enabled for the bundled scripts to run. Organization admins may need to allow custom skills.

### Claude API / Agent SDK

Upload the skill folders through the Skills API and attach them to requests, or point the Agent SDK at a directory containing them. See Anthropic's Agent Skills documentation for current endpoints.

### Packaging a `.skill` file

A `.skill` file is a zip of the skill folder. To build one:

```bash
cd sitecore
zip -r sitecore-publishing-troubleshooter.skill sitecore-publishing-troubleshooter -x "*/__pycache__/*"
```

---

## Using the skills without Claude

The library was built so that each layer is useful on its own.

**1. Run the tools directly.** Every Python script is a CLI with `--help`:

```bash
python3 sitecore-serialization-cicd/scripts/analyze_scs.py /path/to/repo --out scs-report.md
python3 sitecore-log-performance-diagnostics/scripts/analyze_sitecore_logs.py ./App_Data/logs --out log-report.md
python3 sitecore-security-access-audit/scripts/analyze_security_export.py --users users.csv --roles roles.csv --acl acl.csv
```

**2. Run the SPE scripts in Sitecore.** Open the SPE ISE (Desktop → PowerShell ISE, or Launchpad), paste a script from `references/` or `assets/spe/`, set the parameters at the top, and run it. Exports download as CSV.

**3. Read `SKILL.md` as a runbook.** Each one is a concise expert procedure: triage questions, decision trees, symptom → cause → fix tables and verification steps. Engineers can follow them by hand.

**4. Use with other AI assistants.** `SKILL.md` and `references/*.md` are plain Markdown and work as context or system instructions for:
- **GitHub Copilot:** add relevant content to `.github/copilot-instructions.md` or reference the files in chat.
- **Cursor / Windsurf:** add as project rules (e.g. `.cursor/rules/sitecore-publishing.mdc`).
- **ChatGPT / custom GPTs, Gemini, local LLMs:** upload the folder's Markdown as knowledge files or paste the `SKILL.md` body as instructions.

The YAML frontmatter is ignored by tools that don't understand it. Delete it if a tool complains.

**5. Put the analyzers in CI.** `analyze_scs.py --fail-on-critical` exits non-zero on dangerous serialization config. The other analyzers produce Markdown suitable for build artifacts or PR comments.

---

## Requirements

| For | You need |
|---|---|
| Python tools | Python 3.9+ (standard library only) |
| SPE scripts | Sitecore PowerShell Extensions 6.x/7.x on the CM, a user with SPE access (usually admin), and an elevated session where SPE requires it |
| Sitecore CLI commands | .NET SDK and Sitecore CLI pinned in `.config/dotnet-tools.json` |
| Claude usage | Claude Code, or a Claude plan with Skills and code execution enabled |

---

## Safety model

These skills can generate scripts that change production content. Guardrails are built into the scripts themselves, not left to good intentions:

- **Read-only by default.** All audit, export and diagnostic scripts only read.
- **Dry run by default.** Any write script starts with `$dryRun = $true` and shows exactly what it would change.
- **Scope guards.** Bulk scripts refuse to run on `/sitecore`, `/sitecore/content`, `/sitecore/system`, `/sitecore/templates`, `/sitecore/layout` or the media library root unless explicitly overridden.
- **Caps.** Scripts abort if the change count exceeds `$maxItems`.
- **Backups.** Bulk edits export affected items to a Sitecore package before writing. Deletions go to the recycle bin.
- **No implicit publishing.** Publishing is always a separate, deliberate step.
- **No secrets.** Exports mask emails and never include passwords. Analyzers flag secrets found in serialized YAML.

Always run write scripts in a non-production environment first.

---

## Validation status

Honest status as of October 2026:

| Component | Status |
|---|---|
| Python tools (9) | Executed against synthetic fixtures with planted defects, including negative cases. All passed. |
| PowerShell scripts (15 bundled + generated output) | Parsed cleanly with PowerShell 7.4 (syntax only). **Not yet executed against a live Sitecore instance.** |
| Skill workflows | Validated with the skill-creator validator. Formal test-prompt evaluations not yet run. |

Run every SPE script on a development CM before production, and please report anything that misbehaves.

---

## Keeping it current

Sitecore changes quickly: SDK versions, CLI flags, Experience Edge limits, support lifecycle dates and Marketplace SDK APIs (still 0.x). The skills deliberately tell the agent to **verify volatile facts against current Sitecore documentation** instead of trusting hard-coded values. When you update a skill:

1. Update `SKILL.md` and any affected `references/`.
2. Re-run the scripts against fixtures.
3. Note the change in the skill's README changelog.

Key facts baked in (verify before relying on them):
- JSS 22.x end of support: June 2026. JSS 23.x: XM/XP only.
- Content SDK 2.x: active (Next.js 16, React 19). 1.x: maintenance into early 2027.
- XP/XM 10.4: Mainstream Support through 31 Dec 2027.
- Experience Edge delivery API: 80 requests/second, 1,000 entities per query.

---

## Contributing

Issues and pull requests are welcome, especially:
- results from running the SPE scripts on real XP/XM versions or SitecoreAI
- new log signatures, index failure modes or publishing edge cases
- corrections where Sitecore's APIs or limits have changed

Keep Python tools stdlib-only, keep write scripts within the safety model, and keep each `SKILL.md` under ~500 lines (push detail into `references/`).

---

## Disclaimer

This is an independent community project. It is not affiliated with, endorsed by, or supported by Sitecore Corporation A/S or Anthropic. "Sitecore", "SitecoreAI", "XM Cloud" and related names are trademarks of their respective owners. Scripts are provided as-is; you are responsible for testing them in your environment.

---

## License

MIT. See the [LICENSE](../LICENSE) file at the root of the AI Skills Library.
