#!/usr/bin/env python3
"""Analyze Sitecore security CSV exports (from spe-security-export.ps1).

Usage:
  python3 analyze_security_export.py --users users.csv --roles roles.csv --acl acl.csv
      [--workflow workflow-acl.csv] [--dormant-days 90] [--admin-allow "sitecore\\breakglass1,..."]
      [--out security-findings.md]
Stdlib only.
"""
import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta

POWER_ROLES = {
    "sitecore\\sitecore client developing": "can edit templates/layouts and run developer tools",
    "sitecore\\sitecore client securing": "can change security on items",
    "sitecore\\sitecore client account managing": "can create/modify users and roles",
    "sitecore\\sitecore client maintaining": "can access maintenance/admin tools",
    "sitecore\\powershell extensions remoting": "can execute PowerShell remotely",
    "sitecore\\sitecore client designing": "can change presentation details",
}
SPE_HINT = ("powershell", "spe ")
ANON = {"everyone", "sitecore\\everyone", "extranet\\everyone", "extranet\\anonymous", "default\\anonymous"}
WRITE_RIGHTS = {"item:write", "item:delete", "item:create", "item:rename", "item:admin", "field:write", "language:write"}
SYSTEM_PATHS = ("/sitecore/system", "/sitecore/templates", "/sitecore/layout")


def load(path):
    if not path:
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_dt(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(s.split(".")[0], fmt)
        except ValueError:
            continue
    return None


def truthy(v):
    return str(v).strip().lower() in ("true", "1", "yes")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", required=True)
    ap.add_argument("--roles", required=True)
    ap.add_argument("--acl", required=True)
    ap.add_argument("--workflow")
    ap.add_argument("--dormant-days", type=int, default=90)
    ap.add_argument("--admin-allow", default="", help="comma-separated accepted admin accounts")
    ap.add_argument("--out", default="security-findings.md")
    a = ap.parse_args()

    users = load(a.users)
    roles = load(a.roles)
    acl = load(a.acl)
    wf = load(a.workflow)
    allow_admins = {x.strip().lower() for x in a.admin_allow.split(",") if x.strip()}
    now = datetime.now()
    findings = []  # (sev, id, title, evidence, fix)

    def add(sev, fid, title, evidence, fix):
        findings.append((sev, fid, title, evidence, fix))

    # role graph
    member_of = defaultdict(set)    # role -> parent roles
    role_users = defaultdict(set)
    role_names = set()
    for r in roles:
        name = r.get("Role", "").strip()
        role_names.add(name.lower())
        for p in filter(None, (r.get("MemberOf") or "").split("|")):
            member_of[name.lower()].add(p.strip().lower())
        for u in filter(None, (r.get("MemberUsers") or "").split("|")):
            role_users[name.lower()].add(u.strip().lower())

    def expand(role_set):
        seen, stack = set(), list(role_set)
        depth = 0
        while stack:
            r = stack.pop()
            if r in seen:
                continue
            seen.add(r)
            stack.extend(member_of.get(r, ()))
        return seen

    def nesting_depth(role, visited=None):
        visited = visited or set()
        if role in visited:
            return 0
        visited.add(role)
        parents = member_of.get(role, ())
        return 1 + max((nesting_depth(p, visited) for p in parents), default=0)

    # ---------- users ----------
    admins = []
    dormant = []
    user_roles = {}
    for u in users:
        name = u.get("User", "").strip()
        lname = name.lower()
        direct = {x.strip().lower() for x in (u.get("Roles") or "").split("|") if x.strip()}
        user_roles[lname] = expand(direct)
        enabled = not (str(u.get("Approved", "")).strip().lower() == "false") and not truthy(u.get("LockedOut"))
        if truthy(u.get("IsAdmin")):
            admins.append(name)
        last = parse_dt(u.get("LastLogin")) or parse_dt(u.get("LastActivity"))
        if enabled and last and last.year > 1900 and (now - last) > timedelta(days=a.dormant_days):
            dormant.append((name, last.date().isoformat(), truthy(u.get("IsAdmin"))))
        if lname == "sitecore\\admin" and enabled:
            add("Critical", "U1", "Default `sitecore\\admin` account is enabled",
                f"users.csv: {name}, last login {u.get('LastLogin')}",
                "Create named admin accounts, then disable or delete sitecore\\admin (or rename and rotate password).")
        for pr, why in POWER_ROLES.items():
            if pr in user_roles[lname] and not truthy(u.get("IsAdmin")):
                add("High", "U2", f"`{name}` holds power role `{pr}`", f"Role {why}",
                    "Confirm need; remove from role or replace with a narrower custom role.")
        if any(any(h in r for h in SPE_HINT) for r in user_roles[lname]) and not truthy(u.get("IsAdmin")):
            add("High", "U3", f"`{name}` is in a PowerShell Extensions role", ", ".join(sorted(r for r in user_roles[lname] if any(h in r for h in SPE_HINT))),
                "SPE executes arbitrary code with the Sitecore API; restrict to developers/admins and require elevated sessions.")

    extra_admins = [x for x in admins if x.lower() not in allow_admins and x.lower() != "sitecore\\admin"]
    if len(admins) > 3 or extra_admins and allow_admins:
        add("Critical" if len(admins) > 6 else "High", "U4", f"{len(admins)} administrator accounts",
            ", ".join(admins[:30]),
            "Reduce to named break-glass accounts; give everyone else capability roles. Admins bypass item security and workflow.")
    for name, last, is_admin in dormant:
        add("Critical" if is_admin else "High", "U5", f"Dormant enabled account `{name}`",
            f"last login {last} (> {a.dormant_days} days)", "Disable; confirm offboarding process.")

    # ---------- roles ----------
    for r in roles:
        name = r.get("Role", "").strip()
        ln = name.lower()
        d = nesting_depth(ln)
        if d > 4:
            add("Medium", "R1", f"Deep role nesting for `{name}` (depth {d - 1})", f"member of: {r.get('MemberOf')}",
                "Flatten; deep nesting makes effective rights impossible to reason about.")
        if not (r.get("MemberUsers") or r.get("MemberRoles")) and not ln.startswith("sitecore\\sitecore ") and not ln.endswith("\\everyone"):
            add("Info", "R2", f"Role `{name}` has no members", "", "Delete if unused, or document its purpose.")

    # ---------- ACL ----------
    direct_user_rules = defaultdict(list)
    roles_with_rights = set()
    for row in acl:
        acc = (row.get("Account") or "").strip()
        lacc = acc.lower()
        atype = (row.get("AccountType") or "").lower()
        right = (row.get("Right") or "").lower()
        perm = (row.get("Permission") or "").lower()
        path = row.get("Path") or ""
        lpath = path.lower()
        if atype == "role":
            roles_with_rights.add(lacc)
        if lacc in ANON and "allow" in perm and right in WRITE_RIGHTS:
            add("Critical", "A1", f"`{acc}` is allowed `{right}`", f"{path} ({row.get('Propagation')})",
                "Remove immediately; anonymous/everyone must never have write/delete/admin.")
        if atype == "user" and "inheritance" not in perm:
            direct_user_rules[acc].append(f"{path} {right} {perm}")
        if "deny" in perm and "inheritance" not in perm and atype == "role":
            add("High" if lacc.endswith("everyone") or len(role_users.get(lacc, ())) > 10 else "Medium", "A2",
                f"Explicit deny `{right}` for role `{acc}`", f"{path} ({row.get('Propagation')})",
                "Deny overrides allow for every member, including multi-role users. Prefer not granting over denying.")
        if "denyinheritance" in perm.replace(" ", ""):
            add("Medium", "A3", f"Inheritance broken for `{right}` (`{acc}`)", path,
                "Confirm explicit grants exist below; broken inheritance is a common cause of 'author can't see item'.")
        if lpath.startswith(SYSTEM_PATHS) and "allow" in perm and right in WRITE_RIGHTS and atype == "role" \
                and not lacc.startswith("sitecore\\sitecore client"):
            add("High", "A4", f"Role `{acc}` can `{right}` under system area", path,
                "Templates/layout/system should be developer-only and deployed via serialization.")
    for acc, rules in direct_user_rules.items():
        add("High", "A5", f"Rights assigned directly to user `{acc}` ({len(rules)} rule(s))", "; ".join(rules[:5]),
            "Move to a role; direct user rights survive role changes and are invisible in role reviews.")

    # ---------- workflow ----------
    wf_users = set()
    for row in wf:
        acc = (row.get("Account") or "").lower()
        if (row.get("AccountType") or "").lower() == "role":
            for u, rs in user_roles.items():
                if acc in rs:
                    wf_users.add(u)
        else:
            wf_users.add(acc)
    admin_l = {x.lower() for x in admins}
    wf_admins = sorted(admin_l & wf_users)
    if wf_admins:
        add("High", "W1", "Administrators participate in workflow", ", ".join(wf_admins[:20]),
            "Admins bypass workflow (no new version, no state change on edit). Use non-admin accounts for content work.")
    for u, rs in user_roles.items():
        if "sitecore\\sitecore client authoring" in rs and "sitecore\\sitecore client securing" in rs and u in wf_users:
            add("Medium", "W2", f"`{u}` combines Authoring + Securing and is a workflow user", "",
                "They can grant themselves rights to skip workflow; split roles.")

    sev_order = {"Critical": 0, "High": 1, "Medium": 2, "Info": 3}
    findings.sort(key=lambda f: (sev_order[f[0]], f[1]))
    counts = defaultdict(int)
    for f in findings:
        counts[f[0]] += 1

    out = ["# Sitecore Security Findings\n",
           f"Generated: {now:%Y-%m-%d %H:%M} · Users: {len(users)} · Roles: {len(roles)} · Explicit ACL rules: {len(acl)} · Workflow rules: {len(wf)}\n",
           "\n## Summary\n", "| Severity | Count |", "|---|---|"]
    out += [f"| {s} | {counts.get(s, 0)} |" for s in ("Critical", "High", "Medium", "Info")]
    out.append(f"\nAdministrators ({len(admins)}): {', '.join(admins) or 'none'}\n")
    out.append("\n## Findings\n\n| # | Sev | ID | Finding | Evidence | Fix |\n|---|---|---|---|---|---|")
    for i, (sev, fid, title, ev, fix) in enumerate(findings, 1):
        ev = ev.replace("|", "\\|")
        out.append(f"| {i} | {sev} | {fid} | {title} | {ev} | {fix} |")
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {a.out}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
