#!/usr/bin/env python3
"""Scan a Next.js repo for Sitecore JSS usage and write a Markdown inventory.

Usage: python3 scan_jss_usage.py <repo-root> [--out jss-inventory.md]
Stdlib only.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

SKIP_DIRS = {"node_modules", ".next", ".git", "dist", "out", "build", ".turbo", "coverage"}
CODE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

IMPORT_RE = re.compile(
    r"""import\s+(?:type\s+)?(?:\{([^}]*)\}|(\*\s+as\s+\w+)|(\w+))?(?:\s*,\s*\{([^}]*)\})?\s*(?:from\s+)?['"](@sitecore-jss/[^'"]+|@sitecore-cloudsdk/[^'"]+)['"]""",
    re.S,
)
REQUIRE_RE = re.compile(r"""require\(\s*['"](@sitecore-jss/[^'"]+)['"]\s*\)""")
ENV_RE = re.compile(r"process\.env\.([A-Z0-9_]+)")
TEMP_CONFIG_RE = re.compile(r"""['"][^'"]*temp/config['"]""")

RISK_PATTERNS = {
    "Experience Editor / chromes (not supported in Content SDK)": re.compile(
        r"\b(EditFrame|isExperienceEditorActive|isEditorActive|ExperienceEditor|chromes?|resetEditorChromes)\b"
    ),
    "temp/config import (replaced by sitecore.config.ts)": TEMP_CONFIG_RE,
    "componentFactory / componentBuilder (replaced by component map)": re.compile(
        r"\b(componentFactory|componentBuilder|moduleFactory)\b"
    ),
    "Hand-built GraphQL services (replace with SitecoreClient)": re.compile(
        r"\b(GraphQLLayoutService|GraphQLDictionaryService|GraphQLRequestClient|layoutServiceFactory|dictionaryServiceFactory)\b"
    ),
    "Page-props plugin pattern": re.compile(r"\b(sitecorePagePropsFactory|PagePropsFactory|Plugin\s*<)"),
    "SitecoreContext usage": re.compile(r"\b(SitecoreContext|useSitecoreContext|withSitecoreContext)\b"),
    "Content Editor preview / disconnected mode": re.compile(r"\b(disconnected|jss start:disconnected|PreviewData)\b"),
}


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            yield os.path.join(dirpath, f)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def split_names(s):
    if not s:
        return []
    out = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        part = re.sub(r"^type\s+", "", part)
        out.append(part.split(" as ")[0].strip())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default="jss-inventory.md")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        sys.exit(f"Not a directory: {root}")

    packages = {}
    pkg_files = []
    for path in walk(root):
        if os.path.basename(path) == "package.json":
            pkg_files.append(path)
            try:
                data = json.loads(read(path) or "{}")
            except json.JSONDecodeError:
                continue
            for sect in ("dependencies", "devDependencies", "peerDependencies"):
                for name, ver in (data.get(sect) or {}).items():
                    if name.startswith(("@sitecore-jss/", "@sitecore-cloudsdk/", "@sitecore-content-sdk/", "next", "react")):
                        if name in ("next", "react", "react-dom") or name.startswith("@sitecore"):
                            packages[(os.path.relpath(path, root), name)] = ver

    symbols = defaultdict(set)          # symbol -> files
    module_files = defaultdict(set)     # module -> files
    env_vars = defaultdict(set)
    risks = defaultdict(list)           # label -> [(file, line, text)]
    plugin_files = []
    code_files = 0
    router = {"pages": False, "app": False}

    for path in walk(root):
        rel = os.path.relpath(path, root)
        norm = rel.replace(os.sep, "/")
        if norm.startswith("src/pages/") or norm.startswith("pages/"):
            router["pages"] = True
        if norm.startswith("src/app/") or norm.startswith("app/"):
            router["app"] = True
        if not path.endswith(CODE_EXT):
            continue
        code_files += 1
        text = read(path)
        if "/plugins/" in norm and ("src/lib" in norm or norm.startswith("lib/")):
            plugin_files.append(norm)
        for m in IMPORT_RE.finditer(text):
            named, star, default, named2, module = m.groups()
            module_files[module].add(norm)
            for n in split_names(named) + split_names(named2):
                symbols[(module, n)].add(norm)
            if default:
                symbols[(module, default + " (default)")].add(norm)
            if star:
                symbols[(module, star)].add(norm)
        for m in REQUIRE_RE.finditer(text):
            module_files[m.group(1)].add(norm)
        for m in ENV_RE.finditer(text):
            env_vars[m.group(1)].add(norm)
        lines = text.splitlines()
        for label, rx in RISK_PATTERNS.items():
            for i, line in enumerate(lines, 1):
                if rx.search(line):
                    risks[label].append((norm, i, line.strip()[:140]))

    for envfile in (".env", ".env.local", ".env.example", ".env.development", ".env.production"):
        p = os.path.join(root, envfile)
        if os.path.isfile(p):
            for line in read(p).splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    env_vars[line.split("=", 1)[0].strip()].add(envfile)

    jss_mods = [m for m in module_files if m.startswith("@sitecore-jss/")]
    out = []
    out.append("# JSS Inventory\n")
    out.append(f"Repo: `{root}`  \nCode files scanned: {code_files}  \n")
    rt = "App Router" if router["app"] and not router["pages"] else "Pages Router" if router["pages"] and not router["app"] else "Mixed" if router["app"] else "Unknown"
    out.append(f"Router detected: **{rt}**\n")

    out.append("\n## Packages\n\n| package.json | Package | Version |\n|---|---|---|")
    for (f, n), v in sorted(packages.items()):
        out.append(f"| {f} | `{n}` | {v} |")
    if not packages:
        out.append("| — | none found | — |")

    out.append("\n## Risk flags\n")
    if not risks:
        out.append("None detected.")
    for label, hits in risks.items():
        out.append(f"\n### {label} — {len(hits)} hit(s)\n")
        for f, ln, t in hits[:40]:
            out.append(f"- `{f}:{ln}` — `{t}`")
        if len(hits) > 40:
            out.append(f"- …and {len(hits) - 40} more")

    out.append("\n## JSS modules imported\n\n| Module | Files |\n|---|---|")
    for m in sorted(jss_mods):
        out.append(f"| `{m}` | {len(module_files[m])} |")

    out.append("\n## Symbols by module\n\n| Module | Symbol | Files | Example |\n|---|---|---|---|")
    for (mod, sym), files in sorted(symbols.items()):
        ex = sorted(files)[0]
        out.append(f"| `{mod}` | `{sym}` | {len(files)} | `{ex}` |")

    out.append("\n## Custom plugins (src/lib/**/plugins)\n")
    out.extend([f"- `{p}`" for p in sorted(plugin_files)] or ["None found."])

    out.append("\n## Environment variables referenced\n\n| Variable | Where |\n|---|---|")
    for k in sorted(env_vars):
        where = ", ".join(sorted(env_vars[k])[:4])
        out.append(f"| `{k}` | {where} |")

    total_import_sites = sum(len(v) for v in module_files.values() if v)
    score = len(risks.get("Experience Editor / chromes (not supported in Content SDK)", [])) * 3 \
        + len(plugin_files) * 2 + len(risks.get("Hand-built GraphQL services (replace with SitecoreClient)", [])) * 2
    effort = "Low" if score < 10 else "Medium" if score < 40 else "High"
    out.append(f"\n## Summary\n\n- JSS import sites: {total_import_sites}\n- Custom plugins: {len(plugin_files)}\n- Weighted risk score: {score} → **{effort} effort**\n")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {args.out} ({effort} effort, {total_import_sites} JSS import sites)")


if __name__ == "__main__":
    main()
