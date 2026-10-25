# AI Skills Library

A free, open library of **AI skills**: packaged expertise that lets an AI assistant do specialized technical work the way an experienced practitioner would. Each skill bundles a step-by-step workflow, reference knowledge and ready-to-run tools. Skills are organized into collections by domain, and new collections and skills are added over time.

Skills follow the [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) format used by Claude, but **they are not locked to Claude**. Every script runs on its own, every template is usable by hand, and every `SKILL.md` is plain Markdown you can follow as a runbook or load into any AI assistant.

---

## Contents

- [Collections](#collections)
- [What is a skill?](#what-is-a-skill)
- [Repository layout](#repository-layout)
- [Using the skills with Claude](#using-the-skills-with-claude)
- [Using the skills without Claude](#using-the-skills-without-claude)
- [Requirements](#requirements)
- [Design principles](#design-principles)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Collections

| Collection | What it covers | Skills |
|---|---|---|
| [**Sitecore AI Skills**](./sitecore/) | Developer and administrator work on Sitecore XP/XM and SitecoreAI (XM Cloud): migrations, headless components, serialization and CI/CD, Marketplace apps, publishing, security, logs and performance, search indexes, content governance | [Browse →](./sitecore/README.md) |
| [**IT Governance Skills**](./it-governance/) | Application-agnostic IT governance: governance plans, committees, policies and standards, communication plans and compliance readiness for any platform | [Browse →](./it-governance/README.md) |

More collections are planned. Each collection has its own README listing its skills.

---

## What is a skill?

A skill is a folder:

```
skill-name/
├── SKILL.md        ← instructions: YAML frontmatter (name, description) + Markdown workflow
├── README.md       ← human documentation
├── scripts/        ← standalone tools (Python 3, standard library only)
├── references/     ← deeper docs, templates and scripts loaded only when needed
└── assets/         ← files used as-is (catalogs, script libraries, templates)
```

- The **`description`** in `SKILL.md` tells an AI agent *when* to use the skill. Agents load the skill automatically when a request matches.
- The **body** of `SKILL.md` tells the agent *how* to do the work: questions to ask, decision trees, rules that prevent common mistakes, and the deliverables to produce.
- **Scripts** do the deterministic parts (scanning, parsing, generating) so results are repeatable.
- **References** keep `SKILL.md` short. The agent reads them only when the task needs them.

---

## Repository layout

```
ai-skills-library/
├── README.md                    ← you are here
├── LICENSE
├── sitecore/                    ← Sitecore AI Skills collection
│   ├── README.md
│   ├── sitecore-content-sdk-migration/
│   ├── sitecore-xp-to-sitecoreai-migration/
│   ├── sitecore-headless-component-builder/
│   ├── sitecore-serialization-cicd/
│   ├── sitecore-marketplace-app-builder/
│   ├── sitecore-publishing-troubleshooter/
│   ├── sitecore-security-access-audit/
│   ├── sitecore-log-performance-diagnostics/
│   ├── sitecore-search-index-ops/
│   └── sitecore-content-governance-spe/
└── it-governance/               ← IT Governance Skills collection
    ├── README.md
    └── it-governance-plan-builder/
```

---

## Using the skills with Claude

### Claude Code

Copy the skills you want into a skills directory. Each skill folder goes directly under `skills/`; the collection folders are only for organizing this repository.

```bash
# personal: available in every project
mkdir -p ~/.claude/skills
cp -r sitecore/sitecore-* ~/.claude/skills/
cp -r it-governance/it-governance-plan-builder ~/.claude/skills/

# project: commit it so the whole team gets the skills
mkdir -p .claude/skills
cp -r it-governance/it-governance-plan-builder .claude/skills/
```

Claude picks a skill automatically when your request matches its description. You can also name it, e.g. "use the it-governance-plan-builder skill for our Salesforce org".

### Claude apps (claude.ai, desktop, mobile)

1. Zip a single skill folder (or download a `.skill` package from this repo's Releases, if published):
   ```bash
   cd it-governance
   zip -r it-governance-plan-builder.skill it-governance-plan-builder -x "*/__pycache__/*"
   ```
2. Upload it in **Settings → Capabilities → Skills**.
3. Make sure code execution is enabled so bundled scripts can run. Organization admins may need to allow custom skills.

### Claude API and Agent SDK

Upload skill folders through the Skills API and attach them to requests, or point the Agent SDK at a directory containing them. Check Anthropic's Agent Skills documentation for current endpoints.

---

## Using the skills without Claude

Every layer of a skill is useful on its own.

**1. Run the tools directly.** All scripts are Python 3 standard-library CLIs with `--help`:

```bash
python3 it-governance/it-governance-plan-builder/scripts/build_governance_pack.py --init intake.json
python3 it-governance/it-governance-plan-builder/scripts/build_governance_pack.py --intake intake.json --pack core --out governance
python3 sitecore/sitecore-serialization-cicd/scripts/analyze_scs.py /path/to/repo --out scs-report.md
```

**2. Use the templates and script libraries by hand.** For example, run the Sitecore PowerShell Extensions scripts in the SPE ISE, or edit the generated governance plan directly.

**3. Follow `SKILL.md` as a runbook.** Each is a concise expert procedure: intake questions, decision trees, symptom → cause → fix tables, quality checks.

**4. Use them with other AI assistants.** `SKILL.md` and `references/*.md` are plain Markdown:
- **GitHub Copilot:** add content to `.github/copilot-instructions.md`, or attach files in chat.
- **Cursor / Windsurf:** add as project rules (e.g. `.cursor/rules/it-governance.mdc`).
- **ChatGPT custom GPTs, Gemini Gems, local LLMs:** upload a skill's Markdown and assets as knowledge files, or paste the `SKILL.md` body as instructions.

Tools that don't understand YAML frontmatter ignore it. Delete it if a tool complains.

**5. Put the analyzers in CI.** Several scripts return non-zero exit codes on critical findings, and all write Markdown that works as a build artifact or PR comment.

---

## Requirements

| For | You need |
|---|---|
| Bundled scripts | Python 3.9+ (standard library only; no `pip install`) |
| Claude usage | Claude Code, or a Claude plan with Skills and code execution enabled |
| Collection-specific tools | Listed in each collection and skill README (e.g. Sitecore PowerShell Extensions for Sitecore SPE scripts) |

---

## Design principles

Every skill in this library follows the same rules:

1. **Evidence over guesses.** Skills ask for the files, exports or facts they need instead of assuming. Where an AI can't reach a system (anything behind a login), the skill gives you read-only scripts to run and analyzes what you bring back. Credentials never leave your environment.
2. **Safe by default.** Anything that changes a system is a dry run first, scoped, previewed, capped and backed up. Publishing and deployment are always deliberate steps.
3. **Complete deliverables.** Skills produce whole files, plans and scripts, not fragments.
4. **Verify what changes.** Product versions, limits and APIs move. Skills tell the agent to check current vendor documentation instead of trusting hard-coded facts.
5. **Portable.** Standard-library Python, plain Markdown and documented formats, so skills work with or without any particular AI.
6. **Honest.** Skills state their limits, validation status and what they can't confirm.

---

## Contributing

Contributions are welcome: new skills, new collections, fixes, and reports from real-world use.

- **New skill:** put it in the right collection folder (or propose a new collection). Include `SKILL.md` (under ~500 lines; push detail into `references/`), a `README.md` covering use with and without Claude, and stdlib-only scripts.
- **New collection:** add a folder with a `README.md` listing its skills, and add a row to the [Collections](#collections) table above.
- **Changes:** update the skill's README changelog and re-test its scripts.
- **Safety:** write operations must follow the safe-by-default principle above.

Open an issue first for larger changes so we can agree on scope.

---

## Disclaimer

This is an independent community project. It is not affiliated with, endorsed by, or supported by Anthropic or any vendor whose products the skills cover. Product names are trademarks of their respective owners. Skills, scripts and templates are provided as-is; test them in your own environment and have qualified people review governance and security outputs before relying on them.

---

## License

[MIT](./LICENSE). Free to use, modify and distribute, including commercially, with attribution.
