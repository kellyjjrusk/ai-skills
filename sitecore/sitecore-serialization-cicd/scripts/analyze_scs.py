#!/usr/bin/env python3
"""Analyze Sitecore Content Serialization (SCS) configuration in a repo.

Usage: python3 analyze_scs.py <repo-root> [--out scs-report.md] [--fail-on-critical]
Stdlib only. Read-only.
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import sys
from collections import defaultdict

SCOPES = {"ignored", "singleitem", "itemandchildren", "itemanddescendants", "descendantsonly"}
OPS = {"createonly", "createandupdate", "createupdateanddelete"}
DANGER_PATHS = ("/sitecore/content", "/sitecore/media library")
DANGER_SUBSTR = ("/home", "/data", "/media")
SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|password|passwd|token|connectionstring|client[_-]?secret)\s*[:=]\s*\S{6,}")
VALUE_SECRET_RE = re.compile(r"(?i)\b(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,})")
ID_RE = re.compile(r'^ID:\s*"?\{?([0-9a-fA-F-]{36})\}?"?\s*$', re.M)
PATH_RE = re.compile(r"^Path:\s*(.+)$", re.M)


def load_json(path):
    with open(path, encoding="utf-8-sig") as fh:
        text = fh.read()
    # tolerate // comments
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    return json.loads(text)


def norm(p):
    return "/" + p.strip().strip("/").lower() if p else ""


def covers(parent, child):
    return child == parent or child.startswith(parent + "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default="scs-report.md")
    ap.add_argument("--fail-on-critical", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    critical, warnings, info = [], [], []
    sc_json = os.path.join(root, "sitecore.json")
    if not os.path.isfile(sc_json):
        critical.append("No `sitecore.json` at repo root — SCS not configured here (or run from the wrong folder).")
        cfg = {"modules": ["**/*.module.json"]}
    else:
        try:
            cfg = load_json(sc_json)
        except Exception as e:
            critical.append(f"`sitecore.json` is not valid JSON: {e}")
            cfg = {"modules": ["**/*.module.json"]}

    ser_cfg = cfg.get("serialization", {}) or {}
    max_len = int(ser_cfg.get("defaultMaxRelativeItemPathLength", 100) or 100)
    default_rel = ser_cfg.get("defaultModuleRelativeSerializationPath", "serialization")

    module_files = set()
    for pattern in cfg.get("modules", []) or []:
        for f in glob.glob(os.path.join(root, pattern), recursive=True):
            if "node_modules" not in f:
                module_files.add(os.path.abspath(f))
    if not module_files:
        critical.append("`modules` globs in sitecore.json match no *.module.json files.")

    modules = []
    namespaces = defaultdict(list)
    for mf in sorted(module_files):
        rel = os.path.relpath(mf, root)
        try:
            m = load_json(mf)
        except Exception as e:
            critical.append(f"`{rel}` invalid JSON: {e}")
            continue
        ns = m.get("namespace")
        if not ns:
            critical.append(f"`{rel}` has no `namespace`.")
        namespaces[ns].append(rel)
        items = m.get("items", {}) or {}
        ser_path = items.get("path", default_rel)
        base_dir = os.path.join(os.path.dirname(mf), ser_path)
        incs = []
        for inc in items.get("includes", []) or []:
            name = inc.get("name", "?")
            path = inc.get("path", "")
            scope = (inc.get("scope") or "ItemAndDescendants")
            op = (inc.get("allowedPushOperations") or "CreateUpdateAndDelete")
            db = inc.get("database", "master")
            if scope.lower() not in SCOPES:
                critical.append(f"`{rel}` include `{name}`: invalid scope `{scope}`.")
            if op.lower() not in OPS:
                critical.append(f"`{rel}` include `{name}`: invalid allowedPushOperations `{op}`.")
            rules = inc.get("rules", []) or []
            for r in rules:
                rs = (r.get("scope") or "").lower()
                ro = (r.get("allowedPushOperations") or "").lower()
                if rs and rs not in SCOPES:
                    critical.append(f"`{rel}` include `{name}` rule `{r.get('path')}`: invalid scope `{r.get('scope')}`.")
                if ro and ro not in OPS:
                    critical.append(f"`{rel}` include `{name}` rule `{r.get('path')}`: invalid op `{r.get('allowedPushOperations')}`.")
            np = norm(path)
            # danger: delete-capable push over authored content
            if op.lower() == "createupdateanddelete" and scope.lower() in ("itemanddescendants", "descendantsonly", "itemandchildren"):
                under_authored = any(covers(norm(d), np) for d in DANGER_PATHS)
                dev_owned = any(seg in np for seg in ("/presentation", "/settings", "/dictionary", "/system"))
                if under_authored and not dev_owned:
                    ignored_subs = [r.get("path") for r in rules
                                    if (r.get("scope") or "").lower() == "ignored"
                                    or (r.get("allowedPushOperations") or "").lower() == "createonly"]
                    critical.append(
                        f"`{rel}` include `{name}` (`{path}`) uses CreateUpdateAndDelete over authored content/media"
                        + (f" (mitigating rules: {', '.join(ignored_subs)})" if ignored_subs else "")
                        + " — a push can DELETE author content not on disk. Use CreateOnly/CreateAndUpdate or Ignored rules.")
            # count yml
            inc_dir = os.path.join(base_dir, name)
            ymls = glob.glob(os.path.join(inc_dir, "**", "*.yml"), recursive=True)
            incs.append({"name": name, "path": path, "np": np, "db": db, "scope": scope, "op": op,
                         "rules": rules, "yml": len(ymls), "dir": inc_dir})
        refs = m.get("references", []) or []
        roles = m.get("roles", []) or []
        modules.append({"file": rel, "ns": ns, "refs": refs, "includes": incs, "roles": roles, "dir": base_dir})

    for ns, files in namespaces.items():
        if ns and len(files) > 1:
            critical.append(f"Duplicate namespace `{ns}` in: {', '.join(files)}")

    all_ns = [m["ns"] for m in modules if m["ns"]]
    for m in modules:
        for r in m["refs"]:
            if not any(fnmatch.fnmatch(n, r) for n in all_ns):
                warnings.append(f"`{m['file']}` references `{r}` but no module namespace matches.")

    # overlaps across all includes
    flat = [(m, i) for m in modules for i in m["includes"] if i["scope"].lower() != "ignored"]
    for x in range(len(flat)):
        for y in range(x + 1, len(flat)):
            (m1, i1), (m2, i2) = flat[x], flat[y]
            if i1["db"] != i2["db"] or not i1["np"] or not i2["np"]:
                continue
            if covers(i1["np"], i2["np"]) or covers(i2["np"], i1["np"]):
                parent, child, pm, cm = (i1, i2, m1, m2) if covers(i1["np"], i2["np"]) else (i2, i1, m2, m1)
                if parent["scope"].lower() in ("singleitem",) and parent["np"] != child["np"]:
                    continue
                if parent["scope"].lower() == "itemandchildren" and child["np"].count("/") > parent["np"].count("/") + 1:
                    continue
                rel_child = child["np"][len(parent["np"]):] or "/"
                excluded = any(norm(r.get("path", "")) == norm(rel_child) and (r.get("scope") or "").lower() == "ignored"
                               for r in parent["rules"])
                if not excluded:
                    sev = critical if parent["np"] == child["np"] else warnings
                    sev.append(f"Overlap: `{pm['ns']}:{parent['name']}` ({parent['path']}) covers `{cm['ns']}:{child['name']}` ({child['path']}) "
                               f"with no Ignored rule for `{rel_child}`.")

    # yml checks
    ids = defaultdict(list)
    long_paths = []
    secrets = []
    yml_total = 0
    for m in modules:
        for f in glob.glob(os.path.join(m["dir"], "**", "*.yml"), recursive=True):
            yml_total += 1
            relf = os.path.relpath(f, root)
            relpath_in_module = os.path.relpath(f, m["dir"])
            if len(relpath_in_module) > max_len + 40:
                long_paths.append(relf)
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            mid = ID_RE.search(text)
            if mid:
                ids[mid.group(1).lower()].append(relf)
            for ln, line in enumerate(text.splitlines(), 1):
                if line.strip().startswith(("ID:", "Parent:", "Template:", "Path:", "Hint:", "- ID:")):
                    continue
                if SECRET_RE.search(line) or VALUE_SECRET_RE.search(line):
                    secrets.append(f"`{relf}:{ln}` — `{line.strip()[:100]}`")
    for gid, files in ids.items():
        if len(files) > 1:
            critical.append(f"Duplicate item ID `{gid}` in: {', '.join(files[:4])}")
    if secrets:
        critical.append(f"{len(secrets)} possible secret(s) in serialized YAML (see Secrets section).")
    if long_paths:
        warnings.append(f"{len(long_paths)} YAML file path(s) near/over maxRelativeItemPathLength={max_len}; risk of path-too-long on Windows.")

    # mixed tooling
    unicorn = [p for p in glob.glob(os.path.join(root, "**", "*.config"), recursive=True)
               if "unicorn" in os.path.basename(p).lower() and "node_modules" not in p]
    tds = glob.glob(os.path.join(root, "**", "*.scproj"), recursive=True)
    if unicorn and modules:
        critical.append(f"Unicorn config present alongside SCS ({len(unicorn)} file(s)) — two sources of truth.")
    if tds and modules:
        critical.append(f"TDS projects present alongside SCS ({len(tds)} .scproj) — two sources of truth.")

    out = ["# SCS Analysis\n", f"Root: `{root}`  ", f"Modules: {len(modules)} · Includes: {sum(len(m['includes']) for m in modules)} · YAML items: {yml_total}\n"]
    out.append(f"\n## Critical ({len(critical)})\n")
    out += [f"- {c}" for c in critical] or ["None."]
    out.append(f"\n## Warnings ({len(warnings)})\n")
    out += [f"- {w}" for w in warnings] or ["None."]
    out.append("\n## Modules\n\n| Module file | Namespace | References | Include | Path | DB | Scope | Push op | Rules | YAML |\n|---|---|---|---|---|---|---|---|---|---|")
    for m in modules:
        if not m["includes"]:
            out.append(f"| `{m['file']}` | {m['ns']} | {', '.join(m['refs'])} | — | — | — | — | — | — | — |")
        for i in m["includes"]:
            out.append(f"| `{m['file']}` | {m['ns']} | {', '.join(m['refs'])} | {i['name']} | `{i['path']}` | {i['db']} | {i['scope']} | {i['op']} | {len(i['rules'])} | {i['yml']} |")
        if m["roles"]:
            out.append(f"| `{m['file']}` | {m['ns']} | | roles | {json.dumps(m['roles'])} | | | | | |")
    if secrets:
        out.append("\n## Secrets (review and rotate)\n")
        out += [f"- {s}" for s in secrets[:50]]
    if unicorn or tds:
        out.append("\n## Legacy tooling found\n")
        out += [f"- `{os.path.relpath(p, root)}`" for p in (unicorn + tds)[:50]]

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {a.out}: {len(critical)} critical, {len(warnings)} warnings, {yml_total} YAML items")
    if a.fail_on_critical and critical:
        sys.exit(1)


if __name__ == "__main__":
    main()
