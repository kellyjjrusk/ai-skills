---
name: sitecore-security-access-audit
description: Audit and harden Sitecore security — users, roles, item access rights, workflow permissions, admin sprawl, dormant accounts, deny/allow conflicts, SPE and admin-page exposure, CM/CD hardening, patch status against Sitecore security bulletins, and SitecoreAI Cloud Portal roles and automation credentials. Generates read-only SPE export scripts, analyzes the exported CSVs, and produces a prioritized findings report and remediation scripts. Use whenever the user mentions Sitecore permissions, access rights, roles, "who can edit/publish", an author who can't see an item, security review, penetration test findings, hardening, compliance audit (SOC 2, ISO), offboarding users, or a Sitecore CVE/security bulletin.
---

# Sitecore Security & Access Audit

Sitecore access is the sum of item ACLs, role nesting, inheritance and workflow rights, and "deny overrides allow" makes small mistakes hide whole branches or grant far too much. Separately, XP installations are routinely breached through unpatched CVEs and exposed CM/admin endpoints. This skill answers two questions with evidence: *who can do what*, and *how exposed is the instance*.

## Operating constraint: no CMS access

You cannot read users, roles or ACLs. The user runs the read-only SPE export (`references/spe-security-export.ps1`) as an administrator and attaches the CSVs. For hardening, they attach config files or `showconfig.aspx` output and answer a short questionnaire. Treat exports as sensitive: tell the user to strip passwords/connection strings before sharing and never repeat secrets back.

Never write a script that changes security without a dry-run default and an explicit list of what it will change.

## Mode A — Access audit

### 1. Export

User sets `$roots` in the script (default: content, media library, templates, layout, system/Workflows) and runs it. It produces:
- `users.csv` — name, domain, admin flag, enabled/approved, locked out, created, last login, last activity, direct roles
- `roles.csv` — role, members (users/roles), member-of (nesting)
- `acl.csv` — every explicit access rule on items under the roots: item path, account, account type, right, permission (allow/deny), propagation (item/descendants/both), inheritance rules
- `workflow-acl.csv` — rights on workflow states/commands

### 2. Analyze

```bash
python3 scripts/analyze_security_export.py --users users.csv --roles roles.csv --acl acl.csv [--workflow workflow-acl.csv] --dormant-days 90 --out security-findings.md
```

Findings (severity-ranked):
- **Critical**: default `sitecore\admin` enabled; admins beyond a small named set; `Everyone`/`extranet\Anonymous` with write/delete/admin anywhere; non-admin users in `sitecore\Sitecore Client Developing`, `Sitecore Client Securing`, or SPE roles (`sitecore\PowerShell Extensions Remoting` and similar); write rights on `/sitecore/system` or `/sitecore/templates` for author roles.
- **High**: rights assigned directly to users (unmaintainable, survives role removal); dormant enabled accounts; admin accounts used as workflow participants (admins bypass workflow — new versions are not created and states not enforced); deny rules on broad roles (deny wins — hides content from multi-role users).
- **Medium**: deep role nesting (>3), roles with no members, roles granting nothing, domain-specific roles reused across sites, inheritance breaks (`DenyInheritance`) without matching explicit grants.
- **Info**: role → effective-capability summary.

### 3. Answer access questions

For "why can't X see/edit Y", trace it: list X's roles (including nested), then every explicit rule on Y and each ancestor up to `/sitecore`, applying Sitecore's evaluation order (`references/access-rules.md`). State the deciding rule. If the export lacks a needed ancestor, ask for an SPE one-liner result:

```powershell
Test-ItemAcl -Path "master:/sitecore/content/..." -Identity "domain\user" -AccessRight item:write
```

### 4. Remediate

Produce an SPE remediation script per finding group, structured as: `$whatIf = $true` → collect changes → show them in `Show-ListView` → apply only if `$whatIf -eq $false` → log every change. Remediation principles: grant to roles not users; use inheritance and grant at the highest correct node; prefer "not granted" over explicit deny; separate author / approver / publisher / developer / security-admin roles; workflow users must not be admins or members of Client Authoring+Securing combined.

## Mode B — Hardening review (XP/XM self-hosted or Managed Cloud)

Ask for: version + cumulative hotfixes installed, topology, `showconfig.xml` (or the `App_Config/Include` tree), `web.config` (redacted), IIS bindings/IP restrictions summary, which modules are installed on CD. Then:

1. **Patch status first.** Web-search current Sitecore security bulletins (`Sitecore security bulletin SC2025` / `SC2026`, and `site:support.sitecore.com security bulletin`). Map the user's version to every applicable bulletin; unpatched pre-auth RCEs are Critical regardless of anything else. Cite bulletin IDs and dates.
2. Run the checklist in `references/hardening-checklist.md` against the evidence; mark each Pass / Fail / Needs evidence.
3. Priorities: CM not internet-facing (or IP-restricted + SSO/MFA); `/sitecore/admin`, `/sitecore/shell`, `/sitecore/login` blocked on CD; SPE, Unicorn, and dev modules absent from CD; SPE remoting disabled or restricted; default admin renamed/removed; password hash upgraded from SHA1; machine keys unique per environment; connection strings encrypted/secret-stored; Identity Server client secrets rotated; telerik/legacy handlers patched or removed.

## Mode C — SitecoreAI

There are no servers to harden; the surface is identity and credentials. Review with the user:
- Cloud Portal org roles: Owner/Admin count, SSO enforced, MFA, guest users, offboarding cadence
- SitecoreAI app roles vs item ACLs (item ACLs still govern authoring access inside the CM)
- Automation clients (Deploy app credentials): who owns them, scope, last rotation, stored where
- Edge delivery/preview tokens and Context IDs: preview Context ID must never ship to a public front-end
- Editing host: secure hostnames (Content SDK/JSS ≥ 22.3.1), editing secret rotated and not in repo
- Marketplace apps installed: who approved, API access granted
- Front-end headers (CSP, HSTS, cookies) on the rendering host

## Output

`security-findings.md` (from script, then annotated by you): executive summary with counts by severity, findings table (ID, severity, evidence, risk, fix, effort), access-question answers, remediation scripts as separate full `.ps1` files, and a 30/60/90-day plan. Be blunt about severity — don't soften Critical findings.

## References

- `references/spe-security-export.ps1` — read-only export
- `references/access-rules.md` — how Sitecore evaluates rights; worked examples
- `references/hardening-checklist.md` — XP/XM and SitecoreAI checklist
- `scripts/analyze_security_export.py` — analyzer (stdlib only)
