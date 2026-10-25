# sitecore-security-access-audit

**Audit who can do what in Sitecore, and how exposed the instance is: users, roles, access rights, workflow permissions, hardening, patch status, and SitecoreAI identity hygiene.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Administrator / Security** · Platforms: **XP/XM 9.x–10.x**, **SitecoreAI**

---

## Why this exists

Sitecore access is the sum of item ACLs, role nesting, inheritance and workflow rights, with *deny overrides allow*. Small mistakes either hide whole branches from authors or grant far too much. Over time instances accumulate:

- admin sprawl and dormant accounts
- rights granted directly to users
- authors with security-admin roles
- non-admins with PowerShell access

Separately, self-hosted XP is routinely compromised through unpatched CVEs and exposed CM/admin endpoints.

This skill answers two questions with evidence: **who can do what**, and **how exposed is the instance**.

## What the skill does

**Mode A: Access audit**
1. Exports users, roles, explicit item ACLs and workflow ACLs with a read-only SPE script.
2. Analyzes them into severity-ranked findings (Critical / High / Medium / Info).
3. Answers *"why can't X see/edit Y?"* by tracing roles and rules using Sitecore's evaluation order, and names the deciding rule.
4. Generates remediation SPE scripts (dry run, preview, log) following role-based best practice.

**Mode B: Hardening review (XP/XM)**
1. Checks patch status against current Sitecore security bulletins first. Unpatched pre-auth RCEs are always Critical.
2. Runs a checklist covering patching, exposure (CM reachability, admin paths on CD, SPE/Unicorn on CD, SPE remoting, headers, TLS, Solr/xConnect exposure), and identity and config (default admin, hash algorithm, password policy, SSO/MFA, machine keys, connection strings, Identity Server secrets, audit logging).

**Mode C: SitecoreAI**
Reviews Cloud Portal roles, SSO/MFA, automation client ownership and rotation, preview Context ID leakage, editing host secure hostnames and secrets, installed Marketplace apps, front-end headers, and item ACLs inside the CM.

## What's inside

```
sitecore-security-access-audit/
├── SKILL.md
├── README.md
├── references/
│   ├── spe-security-export.ps1      # read-only export → users.csv, roles.csv, acl.csv, workflow-acl.csv
│   ├── access-rules.md              # how Sitecore evaluates rights, worked example, role design
│   └── hardening-checklist.md       # XP/XM + SitecoreAI checklist (Pass / Fail / Needs evidence)
└── scripts/
    └── analyze_security_export.py   # severity-ranked analyzer (Python 3, stdlib only)
```

## Requirements

- SPE on the CM and an administrator account to run the export
- Python 3.9+
- For hardening: version/hotfix list, `showconfig.xml` or the `App_Config` tree, a redacted `web.config`, and IIS/network restriction details

---

## Using it with Claude

Example prompts:

- *"Run a security review of our Sitecore roles and rights. Here are the four CSVs from the export."*
- *"Why can't jdoe edit /sitecore/content/Acme/Legal/Terms? She's in Acme Authors and Brand Reviewers."*
- *"We're on XP 10.2 Update-1. Which security bulletins apply and are we exposed?"*
- *"Our pen test flagged /sitecore/admin reachable on CD and SPE on the delivery role. Give us the fixes."*
- *"Audit our XM Cloud identity setup before our SOC 2 review."*

Claude treats exports as sensitive, never repeats secrets back, and doesn't soften Critical findings.

---

## Using it without Claude

### 1. Export (read-only, in Sitecore)

1. Open `references/spe-security-export.ps1` in the SPE ISE as an administrator.
2. Optionally narrow `$roots` (defaults: content, media library, templates, layout, system).
3. Run it. Four CSVs download:

| File | Columns |
|---|---|
| `users.csv` | User, Domain, IsAdmin, Approved, LockedOut, Created, LastLogin, LastActivity, Email (masked), Roles |
| `roles.csv` | Role, Domain, MemberUsers, MemberRoles, MemberOf |
| `acl.csv` | Path, ID, Template, Account, AccountType, Right, Permission, Propagation (explicit rules only) |
| `workflow-acl.csv` | Same as acl.csv, for `/sitecore/system/Workflows` |

No passwords or secrets are exported. Emails are masked.

### 2. Analyze

```bash
python3 scripts/analyze_security_export.py \
    --users users.csv --roles roles.csv --acl acl.csv --workflow workflow-acl.csv \
    --dormant-days 90 \
    --admin-allow "sitecore\breakglass1,sitecore\breakglass2" \
    --out security-findings.md
```

| Argument | Description |
|---|---|
| `--users`, `--roles`, `--acl` | Required export files |
| `--workflow` | Optional workflow ACL export |
| `--dormant-days` | Inactivity threshold for enabled accounts (default 90) |
| `--admin-allow` | Accepted admin accounts (comma-separated) |
| `--out` | Report path (default `security-findings.md`) |

**Finding IDs:**

| ID | Severity | Finding |
|---|---|---|
| U1 | Critical | Default `sitecore\admin` enabled |
| U2 | High | Non-admin holds a power role (Client Developing/Securing/Account Managing/Maintaining/Designing, SPE Remoting) |
| U3 | High | Non-admin in a PowerShell Extensions role |
| U4 | High/Critical | Too many administrators |
| U5 | High/Critical | Dormant enabled account (Critical if admin) |
| R1 | Medium | Deep role nesting |
| R2 | Info | Role with no members |
| A1 | Critical | Everyone/Anonymous allowed write/delete/create/rename/admin |
| A2 | Medium/High | Explicit deny on a role (deny beats allow for every member) |
| A3 | Medium | Inheritance broken |
| A4 | High | Non-system role can write under templates/layout/system |
| A5 | High | Rights assigned directly to a user |
| W1 | High | Administrators participate in workflow (admins bypass workflow) |
| W2 | Medium | Workflow user combines Authoring + Securing |

### 3. Answer access questions manually

Use `references/access-rules.md` (evaluation order and worked example) and verify with SPE:

```powershell
Test-ItemAcl -Path "master:/sitecore/content/Acme/Legal/Terms" -Identity "sitecore\jdoe" -AccessRight item:write
```

### 4. Hardening

Work through `references/hardening-checklist.md`, citing evidence for each item. Check current Sitecore security bulletins for your exact version and hotfixes first.

### Use with another AI assistant

Provide `SKILL.md`, `access-rules.md`, the checklist, and the analyzer output. Strip account names first if your policy requires it.

---

## Important notes and limits

- The export reads every item under `$roots`. On very large repositories, run it per root.
- On SitecoreAI, membership dates (last login) may be unavailable, since identity lives in the Cloud Portal. Use Cloud Portal user reports for dormancy.
- Remediation scripts change security. They default to dry run, list every change, and log what they apply. Test on non-production first.
- The analyzer is rule-based. It doesn't compute full effective rights for every user × item. Use the trace method for specific questions.

## Changelog

- **1.0.0** (2026-10): initial release.
