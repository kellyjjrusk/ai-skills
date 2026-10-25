#!/usr/bin/env python3
"""Inventory a Sitecore XP/XM .NET solution for SitecoreAI migration assessment.

Usage:
  python3 inventory_solution.py <solution-root> [--showconfig showconfig.xml]
                                [--out inventory.md] [--json inventory.json]
Stdlib only. Read-only.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

SKIP_DIRS = {".git", "bin", "obj", "node_modules", "packages", ".vs", "dist", "out"}

CATEGORIES = {
    # name: (disposition, size, [regexes over .cs/.cshtml])
    "MVC controller": ("Rebuild (headless)", "M-L", [r":\s*(Sitecore)?Controller\b", r"SitecoreController"]),
    "xDB / Analytics": ("Replace (SaaS)", "L-XL", [r"\bTracker\.Current\b", r"Sitecore\.Analytics", r"\bContactManager\b", r"RegisterGoal", r"\bTriggerGoal\b"]),
    "xConnect / Marketing Automation": ("Replace (SaaS)", "XL", [r"Sitecore\.XConnect", r"XConnectClient", r"Sitecore\.Marketing\.Automation"]),
    "EXM": ("Replace (SaaS)", "L", [r"Sitecore\.EmailCampaign", r"Sitecore\.Modules\.EmailCampaign"]),
    "ContentSearch (Solr) query": ("Replace (SaaS)", "L", [r"IProviderSearchContext", r"ContentSearchManager", r"GetQueryable<", r"SearchResultItem"]),
    "Computed index field": ("Replace (SaaS)", "M", [r"IComputedIndexField", r"AbstractComputedIndexField"]),
    "Sitecore Forms": ("Replace (SaaS)", "M-L", [r"Sitecore\.ExperienceForms"]),
    "WFFM": ("Replace (SaaS)", "M-L", [r"Sitecore\.Forms\.(Core|Mvc)", r"Sitecore\.WFFM"]),
    "Commerce": ("Replace (SaaS)", "XL", [r"Sitecore\.Commerce"]),
    "Glass Mapper / Synthesis": ("Retire", "M", [r"Glass\.Mapper", r"\bSynthesis\b"]),
    "Coveo": ("Replace (SaaS)", "L", [r"\bCoveo\."]),
    "Session state": ("Move to edge/app", "M", [r"HttpContext\.Current\.Session", r"\.Session\["]),
    "Web API on CD": ("Move to edge/app", "M-L", [r":\s*ApiController\b", r"System\.Web\.Http"]),
    "Custom field type": ("Replace (Marketplace custom field)", "M-L", [r"Sitecore\.Shell\.Applications\.ContentEditor", r":\s*(Edit|Input|Text)\b.*Sitecore\.Web\.UI"]),
    "Outbound integration": ("Review", "M", [r"\bHttpClient\b", r"WebRequest\.Create", r"\bServiceReference\b", r"SoapHttpClientProtocol"]),
    "Item event handler": ("Keep (CM-side)", "S", [r"item:(saved|saving|added|deleted|moved|renamed)"]),
}
COMPILED = {k: (d, s, [re.compile(p) for p in rx]) for k, (d, s, rx) in CATEGORIES.items()}

CD_PIPELINES = ("httpRequestBegin", "httpRequestProcessed", "httpRequestEnd", "mvc.", "renderLayout",
                "insertRenderings", "renderRendering", "getRenderingDatasource", "preprocessRequest",
                "startTracking", "initializeTracker", "createVisit")
CM_PIPELINES = ("getContentEditorWarnings", "uiGetMasters", "publish", "publishItem", "getLookupSourceItems",
                "saveUI", "uiDuplicateItem", "uiDeleteItems", "expandInitialFieldValue")
MODULE_MARKERS = {
    "SXA (MVC)": r"Sitecore\.XA\.",
    "Unicorn": r"Unicorn",
    "TDS": r"HedgehogDevelopment|\.scproj",
    "SPE": r"Cognifide\.PowerShell|Spe\.",
    "Sitecore Forms": r"Sitecore\.ExperienceForms",
    "Coveo": r"Coveo\.",
    "Glass Mapper": r"Glass\.Mapper",
    "Commerce": r"Sitecore\.Commerce",
    "JSS (server)": r"Sitecore\.JavaScriptServices",
    "Headless Services": r"Sitecore\.LayoutService",
}


def walk(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            yield os.path.join(dp, f)


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def local(tag):
    return tag.split("}", 1)[-1]


def scan_config(path, text, rel, findings):
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return
    stack = [(root, [])]
    while stack:
        el, ancestors = stack.pop()
        name = local(el.tag)
        path_names = ancestors + [name]
        t = el.attrib.get("type", "")
        if name == "processor" and t:
            pipeline = next((a for a in reversed(ancestors) if a not in ("processor", "patch:before", "patch:after")), "?")
            group = ancestors[-2] if len(ancestors) >= 2 else ""
            full = f"{group}/{pipeline}" if group in ("group", "pipelines") or group else pipeline
            if any(pipeline.startswith(p) or p in full for p in CD_PIPELINES):
                disp, size, cat = "Move to edge/app", "M-L", "CD-time pipeline processor"
            elif any(pipeline.startswith(p) for p in CM_PIPELINES):
                disp, size, cat = "Keep (CM-side)", "S", "CM pipeline processor"
            else:
                disp, size, cat = "Review", "S-M", "Pipeline processor"
            findings.append({"category": cat, "disposition": disp, "size": size, "file": rel,
                             "detail": f"{pipeline}: {t}"})
        elif name == "event" and el.attrib.get("name"):
            ev = el.attrib.get("name")
            for h in el.findall("handler"):
                ht = h.attrib.get("type", "")
                if not ht:
                    continue
                keep = ev.startswith("item:") or ev.startswith("publish")
                findings.append({"category": "Event handler", "disposition": "Keep (CM-side)" if keep else "Review",
                                 "size": "S", "file": rel, "detail": f"{h.attrib.get('method', '')} on {ev}: {ht}"})
        elif name == "agent" and t:
            findings.append({"category": "Scheduled agent", "disposition": "Keep (CM) or move to scheduler", "size": "S-M",
                             "file": rel, "detail": f"{t} interval={el.attrib.get('interval', '?')}"})
        elif name == "site" and el.attrib.get("name") and "sites" in ancestors:
            findings.append({"category": "Config site definition", "disposition": "Rebuild (headless SXA site)", "size": "S",
                             "file": rel, "detail": f"{el.attrib.get('name')} host={el.attrib.get('hostName', '')} root={el.attrib.get('rootPath', '')}{el.attrib.get('startItem', '')}"})
        elif name == "index" and el.attrib.get("id"):
            findings.append({"category": "Custom search index", "disposition": "Replace (SaaS)", "size": "M-L",
                             "file": rel, "detail": el.attrib.get("id")})
        for child in el:
            stack.append((child, path_names))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--showconfig")
    ap.add_argument("--out", default="inventory.md")
    ap.add_argument("--json", dest="json_out", default="inventory.json")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        sys.exit(f"Not a directory: {root}")

    findings = []
    stats = defaultdict(int)
    packages = {}
    modules = set()

    for p in walk(root):
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        low = p.lower()
        if low.endswith(".cshtml"):
            stats["Razor views"] += 1
        if low.endswith(".config") and ("app_config" in low or "include" in low):
            stats["Config patch files"] += 1
            text = read(p)
            scan_config(p, text, rel, findings)
            for m, rx in MODULE_MARKERS.items():
                if re.search(rx, text):
                    modules.add(m)
        if low.endswith(".scproj"):
            modules.add("TDS")
        if low.endswith((".csproj", "packages.config", "directory.packages.props")):
            text = read(p)
            for m in re.finditer(r'(?:PackageReference|package)\s+(?:Include|id)="(Sitecore[^"]*|Glass[^"]*|Unicorn[^"]*|Coveo[^"]*)"\s+(?:Version|version)="([^"]+)"', text):
                packages[m.group(1)] = m.group(2)
            for m in re.finditer(r'<PackageReference\s+Include="(Sitecore[^"]*|Glass[^"]*|Unicorn[^"]*|Coveo[^"]*)"[^>]*>\s*<Version>([^<]+)</Version>', text):
                packages[m.group(1)] = m.group(2)
            for mname, rx in MODULE_MARKERS.items():
                if re.search(rx, text):
                    modules.add(mname)
        if low.endswith(".cs"):
            stats["C# files"] += 1
            text = read(p)
            for cat, (disp, size, rxs) in COMPILED.items():
                for rx in rxs:
                    m = rx.search(text)
                    if m:
                        line = text[:m.start()].count("\n") + 1
                        findings.append({"category": cat, "disposition": disp, "size": size,
                                         "file": f"{rel}:{line}", "detail": m.group(0)[:100]})
                        break
            for mname, rx in MODULE_MARKERS.items():
                if re.search(rx, text):
                    modules.add(mname)

    if a.showconfig and os.path.isfile(a.showconfig):
        before = len(findings)
        scan_config(a.showconfig, read(a.showconfig), "showconfig.xml", findings)
        # keep only non-Sitecore types from showconfig to avoid listing the whole platform
        sc = findings[before:]
        findings = findings[:before] + [f for f in sc if not re.search(r"\bSitecore\.", f["detail"].split(":")[-1])]

    # de-duplicate
    seen = set()
    uniq = []
    for f in findings:
        k = (f["category"], f["file"], f["detail"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    findings = uniq

    by_cat = defaultdict(list)
    for f in findings:
        by_cat[f["category"]].append(f)
    by_disp = defaultdict(int)
    for f in findings:
        by_disp[f["disposition"]] += 1

    version = next((v for k, v in packages.items() if k.lower() in ("sitecore.kernel", "sitecore.nexus")), None)
    if not version:
        version = next((v for k, v in packages.items() if k.lower().startswith("sitecore.")), "unknown")

    md = ["# Solution Inventory\n", f"Root: `{root}`  ", f"Sitecore package version (from refs): **{version}**  "]
    md += [f"{k}: {v}  " for k, v in sorted(stats.items())]
    md.append("\n## Modules detected\n")
    md += [f"- {m}" for m in sorted(modules)] or ["- none"]
    md.append("\n## Disposition summary\n\n| Disposition | Findings |\n|---|---|")
    md += [f"| {d} | {n} |" for d, n in sorted(by_disp.items(), key=lambda x: -x[1])]
    md.append("\n## Findings by category\n")
    for cat in sorted(by_cat, key=lambda c: -len(by_cat[c])):
        items = by_cat[cat]
        md.append(f"\n### {cat} — {len(items)} (default: {items[0]['disposition']}, size {items[0]['size']})\n")
        md.append("| File | Detail |\n|---|---|")
        for f in items[:60]:
            md.append(f"| `{f['file']}` | `{f['detail']}` |")
        if len(items) > 60:
            md.append(f"| … | {len(items) - 60} more in JSON |")
    md.append("\n## Sitecore-related package references\n\n| Package | Version |\n|---|---|")
    md += [f"| {k} | {v} |" for k, v in sorted(packages.items())] or ["| none | |"]
    md.append("\n> Defaults only. Review each finding; CD-time code has no home in SitecoreAI.\n")

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    with open(a.json_out, "w", encoding="utf-8") as fh:
        json.dump({"root": root, "version": version, "stats": stats, "modules": sorted(modules),
                   "packages": packages, "findings": findings}, fh, indent=2)
    print(f"Wrote {a.out} and {a.json_out}: {len(findings)} findings, {len(modules)} modules, version {version}")


if __name__ == "__main__":
    main()
