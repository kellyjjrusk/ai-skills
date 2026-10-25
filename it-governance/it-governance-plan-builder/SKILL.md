---
name: it-governance-plan-builder
description: Build an IT governance plan for any application or platform — governance committee and roles, RACI, meeting cadence and escalation, policies (the "what") and standards (the "how") tailored to the application and its hosting model, a communication plan, adoption roadmap and policy register. Prompts for the application, then offers a Core pack (10 application-focused policies) or a Robust pack (Core plus 18 application-agnostic policies covering networking, DevOps/CI-CD, security, privileged access, secrets, logging, BC/DR, data privacy, vendor risk, cloud guardrails, AI usage and compliance). Use whenever the user asks for governance documentation, a governance plan or framework, IT policies and standards, a governance committee, RACI for a system, policy templates, or preparing a platform (CMS, ERP, CRM, SaaS, custom app) for audit or SOC 2/ISO readiness.
---

# IT Governance Plan Builder

Governance fails in two predictable ways: nobody writes it down, or someone writes 80 policies nobody reads or follows. This skill produces a governance plan people can actually run. It follows a proven shape:

1. **Governance plan** — a committee with clear roles, policies and standards, and a communication plan.
2. **Start with about 10 policies** and reach compliance before adding more.
3. **Meet regularly** and improve; aim for a working **C+**, not perfection.
4. **Communicate** every policy to every affected audience.

A **policy** says **what** must be true ("All users must sign in securely"). A **standard** says **how** it is achieved for this application ("SSO via the corporate IdP, MFA for admins, admin URLs reachable only through VPN"). Keep them separate: policies change rarely, standards evolve with the platform.

## Step 1 — Intake (always ask; don't assume)

Ask these together in one round (use the AskUserQuestion tool when available for the multiple-choice items; otherwise ask in plain text). Skip any the user already answered.

1. **Application:** name, type (CMS, ERP, CRM, HRIS, collaboration, data platform, custom web app, …), vendor, version.
2. **Hosting model:** SaaS · PaaS · IaaS (cloud VMs) · On-premises. This decides which standards apply.
3. **Policy pack:**
   - **Core** — 10 policies focused on the application itself (access, roles, content/data lifecycle, change, customization, patching, backup, incidents/escalation, integrations, training). Best first step; most organizations should start here.
   - **Robust** — Core plus 18 application-agnostic policies (security & vulnerability management, network segmentation, perimeter/remote access, privileged access, source control & CI/CD, environments & test data, secrets, logging/SIEM, BC/DR, data classification & privacy, vendor risk, asset/license/cost, capacity, acceptable use & AI, compliance & exceptions, architecture review, cloud guardrails, endpoints).
   - **Core + selected** — Core plus specific Robust policies the user picks.
4. **Context:** organization name, business purpose of the app, approximate users, criticality, regulatory/contractual obligations (SOC 2, ISO 27001, HIPAA, PCI DSS, GDPR, SOX, none).
5. **People:** names or titles for committee roles (it's fine to leave some TBD), meeting cadence, escalation contacts.

If the user wants speed, take sensible defaults, state them at the top of the plan, and mark unknowns as _TBD_.

## Step 2 — Generate the baseline

Write the intake to JSON (start from `python3 scripts/build_governance_pack.py --init intake.json`) and run:

```bash
python3 scripts/build_governance_pack.py --intake intake.json --pack core   --out governance
python3 scripts/build_governance_pack.py --intake intake.json --pack robust --out governance --split
python3 scripts/build_governance_pack.py --intake intake.json --pack core --add P-15,P-17,P-18 --out governance
```

`--list` shows the catalog. The script fills application names into every policy, filters standards by hosting model (e.g. SaaS gets vendor-console and contract standards instead of server patching), maps roles that don't exist in the chosen pack to the nearest core role, and writes:
- `GOVERNANCE-PLAN.md` — purpose & scope, committee, meetings, escalation matrix, RACI, policy index, each policy (purpose, policy statements, standards, compliance measures, obligations, exceptions), communication plan, adoption roadmap, maintenance, revision history, approvals, glossary
- `policy-register.csv` — tracking sheet (owner, accountable, next review, status, compliance, metrics, evidence, frameworks)
- `policies/*.md` — one file per policy (with `--split`)

The catalog (`assets/policy-catalog.json`) is the source of truth for policy content; read it if the script can't run, and build the same structure by hand.

## Step 3 — Tailor to the application (this is where the value is)

The baseline is application-agnostic. Make it specific:

1. **Research the application.** Web-search the vendor's security/hardening guide, admin/RBAC documentation, support lifecycle, release cadence, backup/DR responsibilities and audit-log capabilities. Cite what you used.
2. **Rewrite standards in the application's terms.** Replace generic standards with concrete ones: real role names, real admin console settings, real features. Use `references/app-tailoring.md` for per-type guidance and a worked Sitecore example.
3. **Respect the shared-responsibility line.** For SaaS/PaaS, say what the vendor does (and how the organization verifies it) versus what the organization must do.
4. **Map obligations.** If regulations were named, make sure each has at least one policy that supports it, and call out gaps honestly.
5. **Cut what doesn't apply.** A policy that can't be followed undermines the rest. Remove or mark "Not applicable — reason".
6. **Keep the policy/standard split clean.** Statements use MUST/SHOULD/MAY; standards are specific and measurable. See `references/writing-policies.md`.

## Step 4 — Communication plan

Tailor section 4 of the plan to the organization's real audiences and channels. Every message should answer what changes, when, what to do, and *what's in it for me*. Watch message fatigue. Use `references/communication-plan.md` for templates (announcement email, manager brief, practitioner guide, FAQ).

## Step 5 — Deliver

- Produce the plan as the format the user's environment favors: a shareable document (preferred where a document tool/artifact is available), a Word file if they ask for .docx, or Markdown for a repo/wiki.
- Deliver the policy register as a spreadsheet if a sheet tool is available; otherwise the CSV.
- Lead your reply with: pack chosen, number of policies, the top three gaps you found, and the first three actions for the committee.

## Quality bar

- Every role has a holder or is explicitly _TBD_.
- Every policy has an owner, an accountable role, measurable compliance indicators and a review date.
- No standard contradicts the hosting model (no "patch the servers" for SaaS).
- Nothing in the plan claims compliance with a framework; it *supports* obligations. Certification requires an audit.
- Start small: if the user picked Robust but has no governance today, say plainly that phasing Core first will work better, and show the roadmap that does that.

## References

- `assets/policy-catalog.json` — 28 policies (10 core, 18 robust) and committee roles
- `references/writing-policies.md` — policy vs standard, requirement language, measurability, exceptions
- `references/app-tailoring.md` — tailoring by application type and hosting model; Sitecore worked example
- `references/communication-plan.md` — audience matrix and message templates
- `scripts/build_governance_pack.py` — generator (stdlib only)
