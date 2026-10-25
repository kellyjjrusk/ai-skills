#!/usr/bin/env python3
"""Build an IT governance plan (Markdown) and policy register (CSV) for any application.

Usage:
  python3 build_governance_pack.py --init intake.json            # write a starter intake file
  python3 build_governance_pack.py --intake intake.json --pack core   --out ./governance
  python3 build_governance_pack.py --intake intake.json --pack robust --out ./governance
  python3 build_governance_pack.py --intake intake.json --pack core --add P-15,P-17 --exclude P-09 --split
  python3 build_governance_pack.py --list                           # list the policy catalog

Outputs (in --out):
  GOVERNANCE-PLAN.md      full plan: committee, RACI, escalation, policies & standards, comms plan, roadmap
  policy-register.csv     one row per policy for tracking (owner, review date, status, evidence)
  policies/P-xx-*.md      one file per policy (with --split)
Stdlib only.
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, "..", "assets", "policy-catalog.json")
HOSTING = ("saas", "paas", "iaas", "on-prem")
ROLE_FALLBACK = {  # core pack has no robust roles: map them to the closest core role
    "security-lead": "infra-lead",
    "devops-lead": "dev-lead",
    "compliance-officer": "business-owner",
    "vendor-manager": "business-owner",
    "data-protection": "content-data-manager",
}
CSF = {"GV": "Govern", "ID": "Identify", "PR": "Protect", "DE": "Detect", "RS": "Respond", "RC": "Recover"}

INTAKE_TEMPLATE = {
    "organization": "Acme Corp",
    "document_owner": "Jane Smith, Business Owner",
    "effective_date": date.today().isoformat(),
    "version": "1.0",
    "application": {
        "name": "Sitecore XM Cloud",
        "type": "Content management system (CMS)",
        "vendor": "Sitecore",
        "version": "SaaS (continuously updated)",
        "hosting": "saas",
        "purpose": "Public marketing websites for three brands",
        "users": "120 authors, 15 developers, 4 administrators",
        "environments": ["Development", "QA", "Production"],
        "criticality": "Tier 2"
    },
    "regulatory": ["SOC 2", "GDPR"],
    "committee": {
        "exec-sponsor": "VP Digital",
        "business-owner": "Director of Web",
        "app-admin": "Sitecore Platform Admin",
        "infra-lead": "Cloud Infrastructure Manager",
        "dev-lead": "Web Engineering Lead",
        "content-data-manager": "Content Operations Manager",
        "business-stakeholder": "Marketing Operations Manager",
        "comms-lead": "Internal Communications Manager"
    },
    "meeting_cadence": "Monthly (60 minutes); quarterly policy review",
    "escalation": [
        {"severity": "Sev 1", "primary": "Sitecore Platform Admin", "backup": "Web Engineering Lead", "contact": "On-call phone / #web-incidents", "response": "15 minutes"},
        {"severity": "Sev 2", "primary": "Sitecore Platform Admin", "backup": "Web Engineering Lead", "contact": "Service desk P2 queue", "response": "1 hour"},
        {"severity": "Sev 3", "primary": "Service desk", "backup": "Sitecore Platform Admin", "contact": "Service desk ticket", "response": "1 business day"}
    ],
    "notes": "Free text: anything the plan should reflect (existing policies, constraints, known gaps)."
}


def load_catalog():
    with open(CATALOG, encoding="utf-8") as fh:
        return json.load(fh)


def fill(text, ctx):
    for k, v in ctx.items():
        text = text.replace("{" + k + "}", v)
    return text


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def validate_intake(it):
    errs = []
    app = it.get("application") or {}
    if not app.get("name"):
        errs.append("application.name is required")
    h = (app.get("hosting") or "").lower()
    if h not in HOSTING:
        errs.append(f"application.hosting must be one of {', '.join(HOSTING)} (got '{h}')")
    if not it.get("organization"):
        errs.append("organization is required")
    return errs


def role_name(roles, rid, ctx):
    r = roles.get(rid)
    return fill(r["name"], ctx) if r else rid


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", metavar="PATH", help="write a starter intake JSON and exit")
    ap.add_argument("--list", action="store_true", help="list catalog policies and exit")
    ap.add_argument("--intake")
    ap.add_argument("--pack", choices=["core", "robust"], default="core")
    ap.add_argument("--add", default="", help="comma-separated policy IDs to add (hybrid pack)")
    ap.add_argument("--exclude", default="", help="comma-separated policy IDs to drop")
    ap.add_argument("--out", default="governance")
    ap.add_argument("--split", action="store_true", help="also write one Markdown file per policy")
    a = ap.parse_args()

    cat = load_catalog()

    if a.init:
        with open(a.init, "w", encoding="utf-8") as fh:
            json.dump(INTAKE_TEMPLATE, fh, indent=2)
        print(f"Wrote starter intake to {a.init}. Edit it, then run with --intake {a.init}")
        return
    if a.list:
        for p in cat["policies"]:
            print(f"{p['id']}  [{p['pack']:6}]  {p['category']:<12} {p['name']}")
        return
    if not a.intake:
        sys.exit("--intake is required (or use --init / --list)")

    with open(a.intake, encoding="utf-8") as fh:
        it = json.load(fh)
    errs = validate_intake(it)
    if errs:
        sys.exit("Intake errors:\n  - " + "\n  - ".join(errs))

    app = it["application"]
    hosting = app["hosting"].lower()
    ctx = {"app": app["name"], "app_type": app.get("type", "application"), "vendor": app.get("vendor") or "the vendor"}

    ids_all = {p["id"] for p in cat["policies"]}
    add = {x.strip().upper() for x in a.add.split(",") if x.strip()}
    exclude = {x.strip().upper() for x in a.exclude.split(",") if x.strip()}
    unknown = (add | exclude) - ids_all
    if unknown:
        sys.exit(f"Unknown policy IDs: {', '.join(sorted(unknown))}. Use --list.")
    selected = [p for p in cat["policies"]
                if (p["pack"] == "core" or a.pack == "robust" or p["id"] in add) and p["id"] not in exclude]
    effective_pack = a.pack if not add else f"{a.pack} + {', '.join(sorted(add))}"

    role_defs = list(cat["roles"]["core"])
    if a.pack == "robust":
        role_defs += cat["roles"]["robust"]
    else:  # hybrid: only the robust roles that added robust policies actually reference
        referenced = set()
        for p in selected:
            if p["pack"] == "robust":
                rc = p["raci"]
                referenced |= {p["owner"], rc["R"], rc["A"], *rc.get("C", []), *rc.get("I", [])}
        role_defs += [rd for rd in cat["roles"]["robust"] if rd["id"] in referenced]
    roles = {r["id"]: r for r in role_defs}

    def r(rid):
        if rid not in roles:
            rid = ROLE_FALLBACK.get(rid, rid)
        return rid

    committee = it.get("committee") or {}

    def who(rid):
        rid = r(rid)
        person = committee.get(rid)
        title = role_name(roles, rid, ctx)
        return f"{title} ({person})" if person else title

    today = it.get("effective_date") or date.today().isoformat()
    try:
        eff = datetime.strptime(today, "%Y-%m-%d").date()
    except ValueError:
        eff = date.today()

    def add_months(d, m):
        y, mo = divmod(d.month - 1 + m, 12)
        day = min(d.day, 28)
        return date(d.year + y, mo + 1, day)

    os.makedirs(a.out, exist_ok=True)
    org = it["organization"]
    regs = it.get("regulatory") or []

    L = []
    L.append(f"# {app['name']} Governance Plan")
    L.append("")
    L.append(f"**Organization:** {org}  ")
    L.append(f"**Document owner:** {it.get('document_owner', who('business-owner'))}  ")
    L.append(f"**Version:** {it.get('version', '1.0')} · **Effective:** {today} · **Next full review:** {add_months(eff, 12).isoformat()}  ")
    L.append(f"**Policy pack:** {effective_pack} ({len(selected)} policies)")
    L.append("")
    L.append("## 1. Purpose and scope")
    L.append("")
    L.append(f"This plan defines how {org} governs **{app['name']}** ({ctx['app_type']}): who decides, which rules apply, how those rules are carried out, and how they are communicated. It applies to everyone who administers, develops for, integrates with, or uses {app['name']}, and to vendors acting on the organization's behalf.")
    L.append("")
    L.append("| Attribute | Value |")
    L.append("|---|---|")
    for label, key in (("Application", "name"), ("Type", "type"), ("Vendor", "vendor"), ("Version", "version"),
                       ("Hosting model", "hosting"), ("Business purpose", "purpose"), ("Users", "users"), ("Criticality", "criticality")):
        if app.get(key):
            L.append(f"| {label} | {app[key]} |")
    if app.get("environments"):
        L.append(f"| Environments | {', '.join(app['environments'])} |")
    if regs:
        L.append(f"| Regulatory / contractual context | {', '.join(regs)} |")
    L.append("")
    L.append("### How this plan is organized")
    L.append("")
    L.append("- **Governance committee:** the people and roles accountable for decisions.")
    L.append("- **Policies and standards:** a *policy* states **what** must be true; a *standard* states **how** it is achieved here. Policies change rarely; standards evolve with the platform.")
    L.append("- **Communication plan:** how each audience learns about policies and changes.")
    L.append("- **Adoption roadmap:** start with a small set, achieve compliance, then expand. A working C+ beats a perfect plan nobody follows.")
    L.append("")
    L.append("Requirement language: **MUST** / **MUST NOT** are mandatory; **SHOULD** / **SHOULD NOT** are expected unless a documented reason exists; **MAY** is optional.")
    L.append("")

    L.append("## 2. Governance committee")
    L.append("")
    L.append("In smaller organizations one person may hold several roles; every role must still have a named holder.")
    L.append("")
    L.append("| Role | Holder | Responsibilities |")
    L.append("|---|---|---|")
    for rd in role_defs:
        L.append(f"| {fill(rd['name'], ctx)} | {committee.get(rd['id'], '_TBD_')} | {fill(rd['duties'], ctx)} |")
    L.append("")
    L.append("### 2.1 Meetings")
    L.append("")
    L.append(f"- **Cadence:** {it.get('meeting_cadence', 'Monthly; quarterly policy review')}")
    L.append("- **Standing agenda:** compliance metrics by policy · open exceptions · incidents since last meeting · upcoming changes and vendor releases · policy backlog (add / revise / retire) · communications due")
    L.append("- **Decisions:** recorded in the decision log with date, decision, owner and rationale. Quorum: Business Owner plus at least half of the role holders.")
    L.append("- **Escalation of disputes:** Business Owner → Executive Sponsor (final).")
    L.append("")
    L.append("### 2.2 Operational escalation")
    L.append("")
    esc = it.get("escalation") or []
    L.append("| Severity | Primary | Backup | Contact method | Response target |")
    L.append("|---|---|---|---|---|")
    if esc:
        for e in esc:
            L.append(f"| {e.get('severity','')} | {e.get('primary','')} | {e.get('backup','')} | {e.get('contact','')} | {e.get('response','')} |")
    else:
        L.append("| Sev 1 | _TBD_ | _TBD_ | _TBD_ | 15 minutes |")
        L.append("| Sev 2 | _TBD_ | _TBD_ | _TBD_ | 1 hour |")
        L.append("| Sev 3 | _TBD_ | _TBD_ | _TBD_ | 1 business day |")
    L.append("")
    L.append("Severity definitions are in policy P-08 if selected; otherwise use the organization's incident standard.")
    L.append("")

    L.append("### 2.3 RACI summary")
    L.append("")
    L.append("R = Responsible · A = Accountable · C = Consulted · I = Informed")
    L.append("")
    L.append("| Policy | R | A | C | I |")
    L.append("|---|---|---|---|---|")
    for p in selected:
        rc = p["raci"]
        cs = ", ".join(dict.fromkeys(role_name(roles, r(x), ctx) for x in rc.get("C", [])))
        iss = ", ".join(dict.fromkeys(role_name(roles, r(x), ctx) for x in rc.get("I", [])))
        L.append(f"| {p['id']} {p['name']} | {role_name(roles, r(rc['R']), ctx)} | {role_name(roles, r(rc['A']), ctx)} | {cs} | {iss} |")
    L.append("")

    L.append("## 3. Policies and standards")
    L.append("")
    L.append("| ID | Policy | Category | Owner | Review | NIST CSF 2.0 |")
    L.append("|---|---|---|---|---|---|")
    for p in selected:
        csf = ", ".join(CSF.get(c, c) for c in p.get("csf", []))
        L.append(f"| {p['id']} | {p['name']} | {p['category']} | {role_name(roles, r(p['owner']), ctx)} | {p['review_months']} months | {csf} |")
    L.append("")

    policy_docs = {}
    register = []
    for p in selected:
        stds = [s for s in p["standards"] if not s.get("when") or hosting in s["when"]]
        B = []
        B.append(f"### {p['id']} — {p['name']}")
        B.append("")
        B.append(f"**Category:** {p['category']} · **Owner:** {who(p['owner'])} · **Review:** every {p['review_months']} months (next {add_months(eff, p['review_months']).isoformat()})")
        B.append("")
        B.append(f"**Purpose.** {fill(p['purpose'], ctx)}")
        B.append("")
        B.append("**Policy (what)**")
        B.append("")
        for i, s in enumerate(p["statements"], 1):
            B.append(f"{i}. {fill(s, ctx)}")
        B.append("")
        B.append(f"**Standards (how, for {app['name']} on {hosting})**")
        B.append("")
        for s in stds:
            B.append(f"- {fill(s['text'], ctx)}")
        B.append("")
        B.append("**Compliance measures**")
        B.append("")
        for m in p.get("metrics", []):
            B.append(f"- {m}")
        B.append("")
        rel = [t for t in p.get("tags", []) if any(t.split(" ")[0].lower() in x.lower() for x in regs)] if regs else []
        if rel:
            B.append(f"**Supports obligations:** {', '.join(rel)}")
            B.append("")
        B.append("**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).")
        B.append("")
        policy_docs[p["id"]] = (p, B)
        L.extend(B)
        register.append({
            "Policy ID": p["id"], "Policy": p["name"], "Category": p["category"], "Pack": p["pack"],
            "Owner role": role_name(roles, r(p["owner"]), ctx), "Owner": committee.get(r(p["owner"]), ""),
            "Accountable": role_name(roles, r(p["raci"]["A"]), ctx),
            "Review months": p["review_months"], "Next review": add_months(eff, p["review_months"]).isoformat(),
            "Status": "Draft", "Compliance (Not started/Partial/Compliant)": "Not started",
            "Metrics": "; ".join(p.get("metrics", [])), "Evidence location": "", "Open exceptions": 0,
            "NIST CSF": ", ".join(CSF.get(c, c) for c in p.get("csf", [])),
            "Frameworks": ", ".join(p.get("tags", [])),
        })

    L.append("## 4. Communication plan")
    L.append("")
    L.append(f"Policies that aren't communicated aren't followed. The {role_name(roles, 'comms-lead', ctx)} owns this plan. Every message answers: who is affected, what changes, when, what they must do, and *what's in it for them*. Keep messages short and avoid message fatigue: bundle minor changes into scheduled updates.")
    L.append("")
    L.append("| Audience | What they need | Channel and format | Timing |")
    L.append("|---|---|---|---|")
    L.append("| Executive leadership | Business impact, risk reduced, decisions needed | Concise bulleted email or slide | Before the relevant leadership meeting |")
    L.append("| Managers | How to reinforce the change and check compliance in their teams | Short email with FAQ | Two messages, one week apart |")
    L.append(f"| Practitioners ({app['name']} users, admins, developers) | Exact steps, impact on daily work, where to get help, escalation points | Detailed email or wiki page with steps and FAQ, plus chat channel updates | Three touches, one week apart, starting two weeks before the effective date |")
    L.append("| Vendors and partners | Obligations that apply to them | Formal notice through the vendor manager | At least 30 days before effective date |")
    L.append("| New joiners | Policies relevant to their role | Onboarding pack and training (P-10) | Before access is granted |")
    L.append("")
    L.append("**Feedback loop:** a single channel (e.g. a governance mailbox or chat channel) for questions and suggested changes, reviewed at each committee meeting.")
    L.append("")

    L.append("## 5. Adoption roadmap")
    L.append("")
    core_ids = [p["id"] for p in selected if p["pack"] == "core"]
    extra_ids = [p["id"] for p in selected if p["pack"] != "core"]
    L.append("Start small, reach compliance, then expand. Prioritize the policies that reduce the most risk for the least effort.")
    L.append("")
    L.append("| Phase | Scope | Exit criteria | Target |")
    L.append("|---|---|---|---|")
    L.append(f"| 1. Establish | Committee named, plan approved, communication plan launched | Plan signed by Executive Sponsor | {add_months(eff, 1).isoformat()} |")
    L.append(f"| 2. Core compliance | {', '.join(core_ids) or 'n/a'} | Each policy at least 'Partial' with evidence; critical gaps have dated actions | {add_months(eff, 3).isoformat()} |")
    if extra_ids:
        L.append(f"| 3. Extend | {', '.join(extra_ids)} | Each policy at least 'Partial'; exceptions registered | {add_months(eff, 9).isoformat()} |")
    L.append(f"| {'4' if extra_ids else '3'}. Improve | Raise policies to 'Compliant'; refine standards from metrics and incidents | Annual review completed | {add_months(eff, 12).isoformat()} |")
    L.append("")

    L.append("## 6. Plan maintenance")
    L.append("")
    L.append("- The plan is reviewed in full every 12 months, and policies on their individual review cycles.")
    L.append("- Triggers for an out-of-cycle review: major incident, audit finding, new regulation, change in hosting model or vendor, major version upgrade.")
    L.append("- Changes follow: proposal → committee review → Accountable approval → communication per section 4 → version update.")
    L.append("")
    L.append("### Revision history")
    L.append("")
    L.append("| Version | Date | Author | Summary |")
    L.append("|---|---|---|---|")
    L.append(f"| {it.get('version', '1.0')} | {today} | {it.get('document_owner', '')} | Initial plan ({effective_pack} pack) |")
    L.append("")
    L.append("### Approval")
    L.append("")
    L.append("| Role | Name | Signature | Date |")
    L.append("|---|---|---|---|")
    L.append(f"| Executive Sponsor | {committee.get('exec-sponsor', '')} | | |")
    L.append(f"| Business Owner | {committee.get('business-owner', '')} | | |")
    L.append("")
    if it.get("notes") and it["notes"] != INTAKE_TEMPLATE["notes"]:
        L.append("## Appendix A. Intake notes")
        L.append("")
        L.append(it["notes"])
        L.append("")
    L.append("## Appendix B. Glossary")
    L.append("")
    L.append("| Term | Meaning |")
    L.append("|---|---|")
    L.append("| Policy | A rule stating what must be true. Approved by the committee. |")
    L.append("| Standard | The specific, measurable way a policy is met for this application. |")
    L.append("| Exception | An approved, time-limited deviation from a policy with compensating controls. |")
    L.append("| RTO / RPO | Recovery time objective / recovery point objective. |")
    L.append("| RACI | Responsible, Accountable, Consulted, Informed. |")
    L.append("| NIST CSF 2.0 | Cybersecurity Framework functions: Govern, Identify, Protect, Detect, Respond, Recover. |")

    plan_path = os.path.join(a.out, "GOVERNANCE-PLAN.md")
    with open(plan_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    reg_path = os.path.join(a.out, "policy-register.csv")
    with open(reg_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(register[0].keys()))
        w.writeheader()
        w.writerows(register)

    if a.split:
        pdir = os.path.join(a.out, "policies")
        os.makedirs(pdir, exist_ok=True)
        for pid, (p, B) in policy_docs.items():
            with open(os.path.join(pdir, f"{pid}-{slug(p['name'])}.md"), "w", encoding="utf-8") as fh:
                fh.write(f"<!-- {app['name']} governance · {org} · effective {today} -->\n\n" + "\n".join(B).replace("### ", "# ", 1) + "\n")

    print(f"Wrote {plan_path} ({len(selected)} policies, pack: {effective_pack}, hosting: {hosting})")
    print(f"Wrote {reg_path}")
    if a.split:
        print(f"Wrote {len(policy_docs)} policy files to {os.path.join(a.out, 'policies')}")
    missing = [fill(rd["name"], ctx) for rd in role_defs if not committee.get(rd["id"])]
    if missing:
        print("Roles without a named holder (marked TBD): " + "; ".join(missing))


if __name__ == "__main__":
    main()
