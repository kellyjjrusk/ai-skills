# it-governance-plan-builder

**Build an IT governance plan for any application or platform: committee, roles, RACI, escalation, policies and standards tailored to the application and its hosting model, a communication plan, an adoption roadmap and a policy register.**

Part of the [AI Skills Library](../../README.md) › [IT Governance Skills](../README.md) · Platforms: **any application** (CMS, ERP, CRM, HRIS, collaboration, data platforms, custom apps) on **SaaS, PaaS, IaaS or on-premises**

---

## Why this exists

Most organizations either have no governance for their key applications, or have a binder of policies nobody follows. Both fail audits and both fail in incidents ("who do we call when the site is down?").

This skill follows a simple, proven approach, originally published as [Sitecore Governance: How To and a Template Too](https://thebitsthatbyte.com/sitecore-governance-how-to-and-a-template-too/) and generalized here for any application:

1. **Create a governance plan:** a governance committee, policies and standards, and a communication plan.
2. **Start with about 10 policies** and ensure compliance before creating more.
3. **Meet regularly** and expand or improve. Aim for a working **C+**, not perfection.
4. **Communicate** policies and standards clearly to every audience.

A **policy** states **what** must be true. A **standard** states **how** it is achieved for this application. Keeping them separate lets policies stay stable while standards evolve with the platform.

## What the skill does

1. **Asks about your application:** name, type, vendor, version, hosting model, business purpose, users, criticality, and regulatory context.
2. **Lets you choose a policy pack:**

   | Pack | Policies | Best for |
   |---|---|---|
   | **Core** | 10 application-focused policies | First governance plan; small or mid-size teams; getting to compliance fast |
   | **Robust** | Core + 18 application-agnostic policies (28 total) | Mature or regulated organizations; audit preparation (SOC 2, ISO 27001, HIPAA, PCI DSS) |
   | **Core + selected** | Core plus any Robust policies you pick | Targeted gaps, e.g. Core + CI/CD + secrets + logging |

3. **Generates the plan:** purpose and scope, committee roles and holders, meetings, escalation matrix, RACI, policy index (with NIST CSF 2.0 functions), and every policy with statements, hosting-appropriate standards, compliance measures, obligations and an exceptions process. It also generates a communication plan, a phased adoption roadmap, maintenance rules, revision history, an approval block and a glossary.
4. **Tailors it to your application:** researches the vendor's security, RBAC, lifecycle, backup and audit-log capabilities, and rewrites standards in the application's own terms. It respects the shared-responsibility line for SaaS/PaaS.
5. **Produces a policy register** (CSV/spreadsheet) for tracking owner, next review, status, compliance, evidence and frameworks.
6. **Tells you plainly** when a pack is too ambitious for your starting point, and phases it.

## The policy catalog

### Core pack (application-focused)

| ID | Policy |
|---|---|
| P-01 | Secure Access & Authentication |
| P-02 | Roles, Permissions & Access Reviews |
| P-03 | Content & Data Ownership and Lifecycle |
| P-04 | Change & Release Management |
| P-05 | Configuration & Customization Standards |
| P-06 | Patching, Upgrades & Vendor Support Lifecycle |
| P-07 | Backup & Recovery |
| P-08 | Monitoring, Incident Response & Escalation |
| P-09 | Integrations & API Usage |
| P-10 | Training, Onboarding & Offboarding |

### Robust pack additions (application-agnostic)

| ID | Policy | Area |
|---|---|---|
| P-11 | Information Security & Vulnerability Management | Security |
| P-12 | Network Architecture & Segmentation | Networking |
| P-13 | Perimeter, Remote Access & Edge Protection | Networking |
| P-14 | Privileged Access Management | Security |
| P-15 | Source Control & CI/CD | DevOps |
| P-16 | Environment Management & Test Data | DevOps |
| P-17 | Secrets & Key Management | Security |
| P-18 | Logging, Audit Trails & Security Monitoring | Security |
| P-19 | Business Continuity & Disaster Recovery | Resilience |
| P-20 | Data Classification, Privacy & Retention | Data |
| P-21 | Third-Party & Vendor Risk Management | Vendor |
| P-22 | Asset, License & Cost Management | Operations |
| P-23 | Capacity & Performance Management | Operations |
| P-24 | Acceptable Use & AI Usage | People |
| P-25 | Compliance, Audit & Exceptions | Compliance |
| P-26 | Architecture Review & Technical Debt | Architecture |
| P-27 | Cloud Governance & Guardrails | Cloud |
| P-28 | Endpoint & Workstation Security | Security |

### Committee roles

**Core:** Executive Sponsor · Business Owner (Committee Lead) · {Application} Administrator · Network & Infrastructure Lead · Development Lead · Content/Data Manager · Business Stakeholder · Internal Communications Lead

**Robust adds:** Information Security Lead · DevOps/Platform Engineering Lead · Risk & Compliance Officer · Vendor/Procurement Manager · Data Protection/Privacy Lead

In smaller organizations one person can hold several roles. Every role still needs a named holder.

## What's inside

```
it-governance-plan-builder/
├── SKILL.md                         # workflow the agent follows
├── README.md
├── assets/
│   └── policy-catalog.json          # 28 policies + committee roles (single source of truth)
├── references/
│   ├── writing-policies.md          # policy vs standard, MUST/SHOULD/MAY, measurability, exceptions
│   ├── app-tailoring.md             # by hosting model and app type; Sitecore worked example
│   └── communication-plan.md        # audience matrix and message templates
└── scripts/
    └── build_governance_pack.py     # plan + register generator (Python 3, stdlib only)
```

## Requirements

- Python 3.9+ (standard library only) for the generator
- Basic facts about your application and organization (the intake)

---

## Using it with Claude

Install the skill (see the [root README](../../README.md#using-the-skills-with-claude)). Then ask:

- *"Create a governance plan for our Salesforce org."*
- *"We need governance documentation for Sitecore XM Cloud before our SOC 2 audit. Use the robust pack."*
- *"Build a core governance plan for our self-hosted WordPress sites, plus CI/CD and secrets policies."*
- *"Who should be on the governance committee for our Workday rollout, and what policies do we need first?"*

Claude asks about the application and lets you choose Core, Robust, or Core + selected. It generates the baseline, researches the vendor to tailor standards, and delivers the plan, register, and its top gaps and first actions.

---

## Using it without Claude

### 1. Create and fill the intake

```bash
python3 scripts/build_governance_pack.py --init intake.json
```

Edit `intake.json`:

| Field | Description |
|---|---|
| `organization` | Organization name (required) |
| `document_owner`, `effective_date`, `version` | Document control |
| `application.name` | Application name (required); fills every policy |
| `application.type`, `vendor`, `version` | Shown in scope; vendor fills vendor-specific statements |
| `application.hosting` | `saas`, `paas`, `iaas` or `on-prem` (required); filters standards |
| `application.purpose`, `users`, `environments`, `criticality` | Scope details |
| `regulatory` | e.g. `["SOC 2", "GDPR"]`; adds "Supports obligations" lines to matching policies |
| `committee` | Role ID → holder name/title (role IDs listed below) |
| `meeting_cadence` | e.g. "Monthly; quarterly policy review" |
| `escalation` | List of `{severity, primary, backup, contact, response}` |
| `notes` | Free text appended as an appendix |

Role IDs: `exec-sponsor`, `business-owner`, `app-admin`, `infra-lead`, `dev-lead`, `content-data-manager`, `business-stakeholder`, `comms-lead`, and for Robust: `security-lead`, `devops-lead`, `compliance-officer`, `vendor-manager`, `data-protection`.

### 2. Generate

```bash
python3 scripts/build_governance_pack.py --list                                      # see the catalog
python3 scripts/build_governance_pack.py --intake intake.json --pack core --out governance
python3 scripts/build_governance_pack.py --intake intake.json --pack robust --out governance --split
python3 scripts/build_governance_pack.py --intake intake.json --pack core --add P-15,P-17 --exclude P-09 --out governance
```

| Argument | Description |
|---|---|
| `--init PATH` | Write a starter intake file and exit |
| `--list` | Print the policy catalog and exit |
| `--intake` | Intake JSON |
| `--pack` | `core` (default) or `robust` |
| `--add` | Policy IDs to add to the pack (hybrid) |
| `--exclude` | Policy IDs to drop |
| `--out` | Output folder (default `governance`) |
| `--split` | Also write one Markdown file per policy |

**Outputs:**

| File | Contents |
|---|---|
| `GOVERNANCE-PLAN.md` | The complete plan, ready to edit, convert to Word/PDF, or publish to a wiki |
| `policy-register.csv` | One row per policy for tracking in Excel/Sheets |
| `policies/P-xx-*.md` | Individual policies (with `--split`), useful for wikis or policy portals |

Convert to Word if needed: `pandoc governance/GOVERNANCE-PLAN.md -o governance-plan.docx`.

**Behavior worth knowing:**
- **Hosting filter.** SaaS plans get vendor-console, contract and release-tracking standards instead of server patching and network zoning, and vice versa.
- **Role fallback.** In a Core pack, responsibilities that would belong to robust-only roles map to the nearest core role (e.g. Security Lead → Network & Infrastructure Lead).
- **Hybrid packs** add only the robust roles that the added policies reference.
- **Dates.** Review dates and roadmap targets are calculated from the effective date.

### 3. Tailor

Follow Step 3 of `SKILL.md`: research the vendor and rewrite standards in the application's own terms, using `references/app-tailoring.md`. Then cut what doesn't apply and check every statement is measurable (`references/writing-policies.md`).

### 4. Communicate

Adapt section 4 of the plan using the templates in `references/communication-plan.md`.

### Use with another AI assistant

Provide `SKILL.md`, `assets/policy-catalog.json`, the three references and your intake as context. Ask it to follow the workflow and keep the policy/standard split.

### Extend the catalog

Add policies to `assets/policy-catalog.json` with a new ID, `pack` (`core` or `robust`), statements and standards. Use `"when": ["saas"]` and similar to make a standard hosting-specific. Placeholders `{app}`, `{app_type}` and `{vendor}` are filled automatically. The generator picks up changes with no code edits.

---

## Important notes and limits

- The catalog's timeframes (patch SLAs, RTO/RPO, review intervals) are sensible defaults, not mandates. Set them to your risk appetite and obligations.
- The plan *supports* compliance obligations. It does not certify compliance; certification requires an audit.
- Framework tags (SOC 2, ISO 27001, HIPAA, etc.) indicate relevance, not specific control mappings. Build a control matrix (P-25) for audit-grade mapping.
- If you have no governance today, start with Core even if Robust is the goal. The generated roadmap phases it.

## Changelog

- **1.0.0** (2026-10): initial release. 28 policies (10 core, 18 robust), generator, references.
