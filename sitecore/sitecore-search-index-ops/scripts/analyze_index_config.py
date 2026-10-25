#!/usr/bin/env python3
"""Analyze Sitecore ContentSearch index configuration (showconfig.xml) and Crawling logs.

Usage:
  python3 analyze_index_config.py showconfig.xml [--out index-config-report.md] [--crawling <files...>]
Stdlib only.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

LINE_RE = re.compile(r"^(?P<thread>(?:ManagedPoolThread #\d+|[\w .#-]+?|\d+))\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<level>DEBUG|INFO|WARN|ERROR|FATAL)\s+(?P<msg>.*)$")
DATE_RE = re.compile(r"(\d{8})")
REBUILD_START = re.compile(r"\[Index=(?P<idx>[^\]]+)\].*(?:Full Rebuild|Rebuild).*(?:started|Started)|Starting (?:full )?rebuild.*?index[ '\"]*(?P<idx2>[\w-]+)", re.I)
REBUILD_END = re.compile(r"\[Index=(?P<idx>[^\]]+)\].*(?:Full Rebuild|Rebuild).*(?:finished|Finished|completed|done)", re.I)
INDEX_TAG = re.compile(r"\[Index=([^\]]+)\]")


def strip_ns(root):
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def text_of(el, tag):
    c = el.find(tag)
    return (c.text or "").strip() if c is not None and c.text else ""


def resolve(val, idx_id):
    return (val or "").replace("$(id)", idx_id)


def analyze_config(path):
    tree = ET.parse(path)
    root = strip_ns(tree.getroot())
    # build ref lookup for strategies / configurations
    base = root if root.tag == "sitecore" else root.find(".//sitecore")
    if base is None:
        base = root

    def find_ref(ref):
        if not ref:
            return None
        cur = base
        for part in [p for p in ref.split("/") if p]:
            nxt = cur.find(part)
            if nxt is None:
                return None
            cur = nxt
        return cur

    indexes = []
    for idx in root.iter("index"):
        idx_id = idx.attrib.get("id")
        if not idx_id:
            continue
        itype = idx.attrib.get("type", "")
        params = {p.attrib.get("desc", ""): resolve((p.text or "").strip(), idx_id) for p in idx.findall("param")}
        strategies = []
        st = idx.find("strategies")
        if st is not None:
            for s in st:
                ref = s.attrib.get("ref", "")
                if ref:
                    strategies.append(ref.split("/")[-1])
                elif s.attrib.get("type"):
                    strategies.append(s.attrib["type"].split(",")[0].split(".")[-1])
        crawlers = []
        loc = idx.find("locations")
        if loc is not None:
            for c in loc:
                crawlers.append((text_of(c, "Database"), text_of(c, "Root"), c.attrib.get("type", "").split(",")[0]))
        conf = idx.find("configuration")
        conf_ref = conf.attrib.get("ref", "") if conf is not None else ""
        computed = 0
        conf_node = conf if conf is not None and len(conf) else find_ref(conf_ref)
        if conf_node is not None:
            for fl in conf_node.iter("fields"):
                if "computedindexfield" in fl.attrib.get("hint", "").lower():
                    computed += len(fl.findall("field"))
        indexes.append({"id": idx_id, "type": itype, "params": params, "strategies": strategies,
                        "crawlers": crawlers, "conf_ref": conf_ref, "computed": computed})
    return indexes


def parse_crawling(paths):
    events = defaultdict(lambda: {"starts": [], "ends": [], "errors": 0, "warns": 0, "computed_fail": 0, "timeouts": 0, "samples": []})
    for p in paths:
        m = DATE_RE.search(os.path.basename(p))
        d = datetime.strptime(m.group(1), "%Y%m%d").date() if m else None
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                lm = LINE_RE.match(line.rstrip())
                if not lm:
                    continue
                msg = lm.group("msg")
                t = datetime.strptime(lm.group("time"), "%H:%M:%S").time()
                ts = datetime.combine(d, t) if d else lm.group("time")
                tag = INDEX_TAG.search(msg)
                idx = tag.group(1) if tag else "(unknown)"
                ev = events[idx]
                if REBUILD_END.search(msg):
                    ev["ends"].append(ts)
                elif REBUILD_START.search(msg):
                    ev["starts"].append(ts)
                if lm.group("level") in ("ERROR", "FATAL"):
                    ev["errors"] += 1
                    if len(ev["samples"]) < 3:
                        ev["samples"].append(msg[:200])
                if lm.group("level") == "WARN":
                    ev["warns"] += 1
                if "ComputedIndexField" in msg or "compute value" in msg.lower():
                    ev["computed_fail"] += 1
                if "timed out" in msg.lower() or "timeout" in msg.lower():
                    ev["timeouts"] += 1
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("showconfig")
    ap.add_argument("--out", default="index-config-report.md")
    ap.add_argument("--crawling", nargs="*", default=[])
    a = ap.parse_args()
    if not os.path.isfile(a.showconfig):
        sys.exit(f"Not found: {a.showconfig}")
    try:
        indexes = analyze_config(a.showconfig)
    except ET.ParseError as e:
        sys.exit(f"showconfig is not valid XML: {e}")

    flags = []
    cores = defaultdict(list)
    for ix in indexes:
        core = ix["params"].get("core") or ix["params"].get("activecollection") or ix["params"].get("mainalias") or ix["id"]
        ix["core"] = core
        cores[core.lower()].append(ix["id"])
        rebuild = ix["params"].get("rebuildcore") or ix["params"].get("rebuildcollection") or ix["params"].get("rebuildalias") or ""
        ix["rebuild"] = rebuild
        is_sor = "switchonrebuild" in ix["type"].lower()
        is_solr = "solr" in ix["type"].lower()
        is_master = any(db.lower() == "master" for db, _, _ in ix["crawlers"])
        is_web = any(db.lower() == "web" for db, _, _ in ix["crawlers"])
        custom = not ix["id"].startswith(("sitecore_", "sxa_", "xdb", "social_"))
        if not ix["strategies"]:
            flags.append(("High", ix["id"], "No update strategy — index never updates except on manual rebuild."))
        if "manual" in [s.lower() for s in ix["strategies"]]:
            flags.append(("Info", ix["id"], "Manual strategy — ensure a scheduled rebuild exists."))
        if is_master and "syncmaster" in [s.lower() for s in ix["strategies"]]:
            flags.append(("Medium", ix["id"], "syncMaster on master: every save indexes synchronously; on large repos use intervalAsyncMaster."))
        if is_web and not any(s.lower().startswith("onpublishend") for s in ix["strategies"]):
            flags.append(("Medium", ix["id"], f"Web-database index without onPublishEndAsync (strategies: {', '.join(ix['strategies']) or 'none'})."))
        for db, rt, _ in ix["crawlers"]:
            if custom and rt.rstrip("/").lower() in ("/sitecore", "/sitecore/content"):
                flags.append(("Medium", ix["id"], f"Custom index crawls `{rt}` ({db}) — too broad; narrow to the site/home or data folder."))
        if is_sor and not rebuild:
            flags.append(("High", ix["id"], "SwitchOnRebuild type but no rebuild core/collection param."))
        if is_sor and rebuild and rebuild.lower() == core.lower():
            flags.append(("Critical", ix["id"], "Rebuild core equals main core — SwitchOnRebuild will wipe the live index."))
        if is_solr and not is_sor and ix["id"] in ("sitecore_master_index", "sitecore_web_index"):
            flags.append(("Info", ix["id"], "Not SwitchOnRebuild — full rebuilds take this index's search offline for the duration."))
        if ix["computed"] > 25:
            flags.append(("Info", ix["id"], f"{ix['computed']} computed fields in its configuration — check their cost if rebuilds are slow."))
    for core, ids in cores.items():
        if len(ids) > 1:
            flags.append(("Critical", ", ".join(ids), f"Multiple indexes write to the same core/collection `{core}`."))

    sev = {"Critical": 0, "High": 1, "Medium": 2, "Info": 3}
    flags.sort(key=lambda f: sev[f[0]])
    out = ["# Index Configuration Report\n", f"Source: `{os.path.basename(a.showconfig)}` · Indexes: {len(indexes)}\n"]
    out.append("\n## Flags\n\n| Severity | Index | Finding |\n|---|---|---|")
    out += [f"| {s} | {i} | {m} |" for s, i, m in flags] or ["| — | — | none |"]
    out.append("\n## Indexes\n\n| Index | Type | Core | Rebuild core | Strategies | Crawlers | Config | Computed |\n|---|---|---|---|---|---|---|---|")
    for ix in indexes:
        t = ix["type"].split(",")[0].split(".")[-1]
        cr = "; ".join(f"{d}:{r}" for d, r, _ in ix["crawlers"])
        out.append(f"| {ix['id']} | {t} | {ix['core']} | {ix['rebuild']} | {', '.join(ix['strategies'])} | {cr} | {ix['conf_ref'].split('/')[-1]} | {ix['computed']} |")

    if a.crawling:
        files = []
        for p in a.crawling:
            if os.path.isdir(p):
                files += [os.path.join(p, f) for f in os.listdir(p) if f.lower().startswith("crawling")]
            elif os.path.isfile(p):
                files.append(p)
        ev = parse_crawling(sorted(files))
        out.append(f"\n## Crawling log ({len(files)} file(s))\n\n| Index | Rebuild starts | Rebuild ends | Last duration | Errors | Warns | Computed-field failures | Timeouts |\n|---|---|---|---|---|---|---|---|")
        for idx, e in sorted(ev.items()):
            dur = ""
            if e["starts"] and e["ends"] and isinstance(e["starts"][-1], datetime) and isinstance(e["ends"][-1], datetime) and e["ends"][-1] >= e["starts"][-1]:
                dur = str(e["ends"][-1] - e["starts"][-1])
            out.append(f"| {idx} | {len(e['starts'])} | {len(e['ends'])} | {dur} | {e['errors']} | {e['warns']} | {e['computed_fail']} | {e['timeouts']} |")
        samples = [(i, s) for i, e in ev.items() for s in e["samples"]]
        if samples:
            out.append("\n### Error samples\n")
            out += [f"- **{i}**: `{s}`" for i, s in samples[:20]]
        unfinished = [i for i, e in ev.items() if len(e["starts"]) > len(e["ends"])]
        if unfinished:
            out.append(f"\n> Rebuilds started without a logged finish: {', '.join(unfinished)} — failed, still running, or recycled mid-rebuild.")

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {a.out}: {len(indexes)} indexes, {len(flags)} flags")


if __name__ == "__main__":
    main()
