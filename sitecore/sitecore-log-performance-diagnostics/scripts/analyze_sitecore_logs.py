#!/usr/bin/env python3
"""Analyze Sitecore logs (+ optional IIS W3C logs, cache.aspx and stats.aspx HTML).

Usage:
  python3 analyze_sitecore_logs.py <files/folders...> [--out log-report.md]
      [--from "YYYY-MM-DD HH:MM"] [--to "YYYY-MM-DD HH:MM"]
      [--iis <file-or-folder>] [--cache cache.html] [--stats stats.html]
Stdlib only.
"""
import argparse
import html
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

LINE_RE = re.compile(r"^(?P<thread>(?:ManagedPoolThread #\d+|Heartbeat|[\w .#-]+?|\d+))\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<level>DEBUG|INFO|WARN|ERROR|FATAL|AUDIT)\s+(?P<msg>.*)$")
ISO_LINE_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})(?:[.,]\d+)?\S*\s+\[?(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|FATAL|Information|Warning|Error|Critical)\]?\s+(?P<msg>.*)$", re.I)
DATE_RE = re.compile(r"(\d{8})(?:\.(\d{6}))?")
TIMING_RE = re.compile(r"Timing threshold exceeded for web page\. Milliseconds: ([\d.,]+)\. Threshold: [\d.,]+\. Page URL: (\S+)")
ITEMS_RE = re.compile(r"Item threshold exceeded for web page\. Items accessed: (\d+)\. Threshold: \d+\. Page URL: (\S+)")
MEM_RE = re.compile(r"Memory threshold exceeded for web page\. Memory used: (\d+)KB\. Threshold: \d+KB\. Page URL: (\S+)")
SHUTDOWN_RE = re.compile(r"(Shutdown message|shutting down|Sitecore is shutting down|_shutDownMessage|Shutdown reason)", re.I)
REASON_RE = re.compile(r"(?:Shutdown reason|_shutDownMessage|ShutdownReason)\s*[:=]?\s*(\w+)", re.I)
START_RE = re.compile(r"(Sitecore started|\*\*\*\*\s*Sitecore started|Instance started|Application started)", re.I)
EXC_TYPE_RE = re.compile(r"\b([A-Z][\w.]*(?:Exception|Error))\b")
GUID_RE = re.compile(r"\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?")
URL_RE = re.compile(r"https?://\S+")
PATH_RE = re.compile(r"(?:/[\w.\-%]+){2,}")
NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
QUOTED_RE = re.compile(r"'[^']{1,80}'|\"[^\"]{1,80}\"")
CATEGORY_RULES = [
    ("Performance thresholds", re.compile(r"threshold exceeded for web page", re.I)),
    ("Event queue / remote events", re.compile(r"EventQueue|Eventing\.Remote|publish:end:remote", re.I)),
    ("Search / Solr", re.compile(r"Solr|ContentSearch|IndexCustodian|Crawler", re.I)),
    ("Memory", re.compile(r"MemoryMonitor|OutOfMemory|Memory usage exceeded", re.I)),
    ("Cache", re.compile(r"\bCache\b.*(cleared|created|exceeded)|HtmlCache", re.I)),
    ("SQL / database", re.compile(r"SqlException|SqlClient|Login failed for user|deadlock", re.I)),
    ("Configuration / types", re.compile(r"Could not (resolve|create|find) type|ConfigurationException|Could not load (file or )?assembly", re.I)),
    ("xConnect / analytics", re.compile(r"xConnect|XConnect|Analytics|xDB", re.I)),
    ("Publishing", re.compile(r"Publish", re.I)),
    ("Rendering / MVC", re.compile(r"Rendering|Mvc\.|View .* not found|InvalidOperationException.*view", re.I)),
    ("Security / auth", re.compile(r"Unauthorized|AccessDenied|Login|Identity|token", re.I)),
]
OWN_CODE_EXCLUDE = re.compile(r"^\s*at (Sitecore\.|System\.|Microsoft\.|SolrNet\.|Newtonsoft\.|Glass\.Mapper\.|log4net\.|Lucene\.)")


def files_from(paths, exts=(".txt", ".log")):
    for p in paths:
        if os.path.isdir(p):
            for dp, _, fn in os.walk(p):
                for f in sorted(fn):
                    if f.lower().endswith(exts):
                        yield os.path.join(dp, f)
        elif os.path.isfile(p):
            yield p


def file_date(path):
    m = DATE_RE.search(os.path.basename(path))
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            return None
    return None


def parse_sitecore(path):
    d = file_date(path)
    entries, cur, last_t, offset = [], None, None, 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = LINE_RE.match(line)
            mi = None if m else ISO_LINE_RE.match(line)
            if m:
                t = datetime.strptime(m.group("time"), "%H:%M:%S").time()
                if last_t and t < last_t and (datetime.combine(datetime.min, last_t) - datetime.combine(datetime.min, t)).seconds > 3600:
                    offset += 1
                last_t = t
                ts = datetime.combine(d, t) + timedelta(days=offset) if d else None
                cur = {"file": os.path.basename(path), "ts": ts, "time": m.group("time"), "thread": m.group("thread").strip(),
                       "level": m.group("level").upper(), "msg": m.group("msg"), "extra": []}
                entries.append(cur)
            elif mi:
                ts = datetime.strptime(mi.group("ts").replace("T", " "), "%Y-%m-%d %H:%M:%S")
                lvl = mi.group("level").upper()
                lvl = {"INFORMATION": "INFO", "WARNING": "WARN", "CRITICAL": "FATAL"}.get(lvl, lvl)
                cur = {"file": os.path.basename(path), "ts": ts, "time": ts.strftime("%H:%M:%S"), "thread": "",
                       "level": lvl, "msg": mi.group("msg"), "extra": []}
                entries.append(cur)
            elif cur is not None and line.strip() and len(cur["extra"]) < 40:
                cur["extra"].append(line.rstrip())
    return entries


def signature(msg):
    s = URL_RE.sub("<url>", msg)
    s = GUID_RE.sub("<guid>", s)
    s = QUOTED_RE.sub("'<v>'", s)
    s = PATH_RE.sub("<path>", s)
    s = NUM_RE.sub("N", s)
    return re.sub(r"\s+", " ", s).strip()[:180]


def categorize(text):
    for name, rx in CATEGORY_RULES:
        if rx.search(text):
            return name
    return "Other"


def pct(values, p):
    if not values:
        return 0
    v = sorted(values)
    k = max(0, min(len(v) - 1, int(math.ceil(p / 100.0 * len(v))) - 1))
    return v[k]


def parse_iis(paths):
    rows = []
    for f in files_from(paths, (".log", ".txt")):
        fields = None
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("#Fields:"):
                    fields = line[len("#Fields:"):].split()
                    continue
                if line.startswith("#") or not fields:
                    continue
                parts = line.split()
                if len(parts) != len(fields):
                    continue
                r = dict(zip(fields, parts))
                try:
                    ts = datetime.strptime(f"{r.get('date')} {r.get('time')}", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ts = None
                rows.append({"ts": ts, "uri": r.get("cs-uri-stem", ""), "status": r.get("sc-status", ""),
                             "taken": int(r.get("time-taken", "0") or 0) if (r.get("time-taken", "0") or "0").isdigit() else 0,
                             "method": r.get("cs-method", "")})
    return rows


def html_table_rows(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S | re.I)]
        if cells:
            rows.append(cells)
    return rows


def to_num(s):
    s = s.replace(",", "").strip()
    m = re.match(r"^([\d.]+)\s*(KB|MB|GB|B)?$", s, re.I)
    if not m:
        try:
            return float(s)
        except ValueError:
            return None
    v = float(m.group(1))
    unit = (m.group(2) or "B").upper()
    return v * {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}[unit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default="log-report.md")
    ap.add_argument("--from", dest="dfrom")
    ap.add_argument("--to", dest="dto")
    ap.add_argument("--iis", nargs="*")
    ap.add_argument("--cache")
    ap.add_argument("--stats")
    a = ap.parse_args()
    dfrom = datetime.strptime(a.dfrom, "%Y-%m-%d %H:%M") if a.dfrom else None
    dto = datetime.strptime(a.dto, "%Y-%m-%d %H:%M") if a.dto else None

    entries = []
    flist = [f for f in files_from(a.paths)]
    for f in flist:
        entries.extend(parse_sitecore(f))
    if dfrom or dto:
        entries = [e for e in entries if e["ts"] is None or ((not dfrom or e["ts"] >= dfrom) and (not dto or e["ts"] <= dto))]
    entries.sort(key=lambda e: (e["ts"] or datetime.min))

    level_count = Counter(e["level"] for e in entries)
    errors = [e for e in entries if e["level"] in ("ERROR", "FATAL")]
    warns = [e for e in entries if e["level"] == "WARN"]

    # signatures
    sigs = defaultdict(list)
    for e in errors + warns:
        sigs[(e["level"], signature(e["msg"]))].append(e)

    # thresholds
    timing = defaultdict(list)
    items = defaultdict(list)
    mem = defaultdict(list)
    for e in warns:
        m = TIMING_RE.search(e["msg"])
        if m:
            timing[m.group(2).split("?")[0]].append(float(m.group(1).replace(",", "")))
            continue
        m = ITEMS_RE.search(e["msg"])
        if m:
            items[m.group(2).split("?")[0]].append(int(m.group(1)))
            continue
        m = MEM_RE.search(e["msg"])
        if m:
            mem[m.group(2).split("?")[0]].append(int(m.group(1)))

    # lifecycle
    lifecycle = []
    for e in entries:
        text = e["msg"] + " " + " ".join(e["extra"][:5])
        if START_RE.search(e["msg"]):
            lifecycle.append((e["ts"] or e["time"], e["file"], "START", ""))
        elif SHUTDOWN_RE.search(text):
            r = REASON_RE.search(text)
            reason = r.group(1) if r else ""
            prev = lifecycle[-1] if lifecycle else None
            same_burst = prev and prev[2] == "SHUTDOWN" and prev[1] == e["file"] and isinstance(prev[0], datetime) \
                and isinstance(e["ts"], datetime) and (e["ts"] - prev[0]).total_seconds() <= 10
            if same_burst:
                if reason and not prev[3]:
                    lifecycle[-1] = (prev[0], prev[1], "SHUTDOWN", reason)
            else:
                lifecycle.append((e["ts"] or e["time"], e["file"], "SHUTDOWN", reason))

    # error rate per 10 min
    buckets = Counter()
    for e in errors:
        if e["ts"]:
            b = e["ts"].replace(minute=(e["ts"].minute // 10) * 10, second=0)
            buckets[b] += 1

    out = ["# Sitecore Log Report\n",
           f"Files: {len(flist)} · Entries: {len(entries)} · " + " · ".join(f"{k}: {v}" for k, v in sorted(level_count.items())),
           f"Window: {entries[0]['ts'] if entries else '-'} → {entries[-1]['ts'] if entries else '-'}\n"]

    out.append(f"\n## Lifecycle ({len(lifecycle)} events)\n")
    if lifecycle:
        out.append("| Time | File | Event | Reason |\n|---|---|---|---|")
        out += [f"| {t} | {f} | {ev} | {r} |" for t, f, ev, r in lifecycle[:80]]
        starts = sum(1 for x in lifecycle if x[2] == "START")
        if starts > 2:
            out.append(f"\n> {starts} starts in window — repeated app-pool recycles. Check shutdown reasons above.")
    else:
        out.append("No start/shutdown markers found.")

    out.append("\n## Error rate (per 10 min)\n")
    if buckets:
        peak = max(buckets.values())
        for b in sorted(buckets):
            bar = "█" * max(1, int(30 * buckets[b] / peak))
            out.append(f"`{b:%Y-%m-%d %H:%M}` {bar} {buckets[b]}")
    else:
        out.append("No timestamped errors.")

    out.append("\n## Error signatures\n")
    err_sigs = sorted([(k, v) for k, v in sigs.items() if k[0] in ("ERROR", "FATAL")], key=lambda x: -len(x[1]))
    for (lvl, sig), es in err_sigs[:30]:
        first, last = es[0], es[-1]
        alltext = first["msg"] + "\n" + "\n".join(first["extra"])
        exc = EXC_TYPE_RE.findall(alltext)
        own = [l.strip() for l in first["extra"] if l.strip().startswith("at ") and not OWN_CODE_EXCLUDE.match(l)]
        files = sorted({x["file"] for x in es})
        out.append(f"\n### {len(es)}× {lvl} — {categorize(alltext)}\n`{sig}`  \nfirst {first['ts'] or first['time']} · last {last['ts'] or last['time']} · files: {', '.join(files[:4])}")
        if exc:
            out.append(f"Exception types: {', '.join(dict.fromkeys(exc))}")
        if own:
            out.append("Non-framework frames (likely your code):\n```\n" + "\n".join(own[:5]) + "\n```")
        elif first["extra"]:
            out.append("```\n" + "\n".join(first["extra"][:8]) + "\n```")

    out.append("\n## Warning signatures (top 20)\n\n| Count | Category | Signature |\n|---|---|---|")
    warn_sigs = sorted([(k, v) for k, v in sigs.items() if k[0] == "WARN"], key=lambda x: -len(x[1]))
    for (lvl, sig), es in warn_sigs[:20]:
        out.append(f"| {len(es)} | {categorize(es[0]['msg'])} | `{sig.replace('|', '/')}` |")

    def thr_table(title, data, unit):
        out.append(f"\n## {title}\n")
        if not data:
            out.append("None.")
            return
        out.append(f"| URL | Count | Max {unit} | p95 {unit} |\n|---|---|---|---|")
        for url, vals in sorted(data.items(), key=lambda x: (-len(x[1]), -max(x[1])))[:20]:
            out.append(f"| `{url}` | {len(vals)} | {int(max(vals))} | {int(pct(vals, 95))} |")

    thr_table("Timing threshold exceeded", timing, "ms")
    thr_table("Item threshold exceeded", items, "items")
    thr_table("Memory threshold exceeded", mem, "KB")
    both = set(timing) & set(items)
    if both:
        out.append(f"\n> {len(both)} URL(s) appear in both timing and item thresholds — classic tree-walking renderings: " + ", ".join(f"`{u}`" for u in list(both)[:8]))

    cats = Counter(categorize(e["msg"] + " " + " ".join(e["extra"][:3])) for e in errors)
    out.append("\n## Errors by category\n\n| Category | Count |\n|---|---|")
    out += [f"| {k} | {v} |" for k, v in cats.most_common()]

    if a.iis:
        rows = parse_iis(a.iis)
        if dfrom or dto:
            rows = [r for r in rows if r["ts"] is None or ((not dfrom or r["ts"] >= dfrom) and (not dto or r["ts"] <= dto))]
        out.append(f"\n## IIS ({len(rows)} requests)\n")
        by_uri = defaultdict(list)
        for r in rows:
            by_uri[r["uri"]].append(r["taken"])
        out.append("### Top by total time\n\n| URI | Requests | Total s | p95 ms | Max ms |\n|---|---|---|---|---|")
        for uri, vals in sorted(by_uri.items(), key=lambda x: -sum(x[1]))[:20]:
            out.append(f"| `{uri}` | {len(vals)} | {sum(vals) // 1000} | {pct(vals, 95)} | {max(vals)} |")
        five = Counter(r["uri"] for r in rows if r["status"].startswith("5"))
        out.append("\n### 5xx by URI\n\n| URI | Count |\n|---|---|")
        out += [f"| `{u}` | {c} |" for u, c in five.most_common(15)] or ["| none | |"]
        per_min = Counter(r["ts"].replace(second=0) for r in rows if r["ts"])
        if per_min:
            pk = max(per_min.items(), key=lambda x: x[1])
            out.append(f"\nPeak request rate: {pk[1]}/min at {pk[0]:%Y-%m-%d %H:%M}")

    if a.cache and os.path.isfile(a.cache):
        rows = html_table_rows(a.cache)
        out.append("\n## Caches (cache.aspx)\n")
        hdr_i = next((i for i, r in enumerate(rows) if any("name" in c.lower() for c in r) and any("max" in c.lower() for c in r)), None)
        if hdr_i is None:
            out.append("Could not find cache table header.")
        else:
            hdr = [c.lower() for c in rows[hdr_i]]
            ni = next(i for i, c in enumerate(hdr) if "name" in c)
            si = next((i for i, c in enumerate(hdr) if c.startswith("size")), None)
            mi = next((i for i, c in enumerate(hdr) if "max" in c), None)
            ci = next((i for i, c in enumerate(hdr) if "count" in c), None)
            hot = []
            for r in rows[hdr_i + 1:]:
                if len(r) <= max(x for x in (ni, si, mi) if x is not None):
                    continue
                size = to_num(r[si]) if si is not None else None
                mx = to_num(r[mi]) if mi is not None else None
                if size is not None and mx:
                    ratio = size / mx
                    if ratio >= 0.85:
                        hot.append((r[ni], r[si], r[mi], r[ci] if ci is not None else "", ratio))
            out.append("| Cache | Size | Max | Count | % of max |\n|---|---|---|---|---|")
            out += [f"| {n} | {s} | {m} | {c} | {int(100 * ra)}% |" for n, s, m, c, ra in sorted(hot, key=lambda x: -x[4])[:30]] or ["| none ≥85% | | | | |"]

    if a.stats and os.path.isfile(a.stats):
        rows = html_table_rows(a.stats)
        out.append("\n## Rendering statistics (stats.aspx)\n")
        hdr_i = next((i for i, r in enumerate(rows) if any("rendering" in c.lower() for c in r)), None)
        if hdr_i is None:
            out.append("Could not find stats table header.")
        else:
            hdr = [c.lower() for c in rows[hdr_i]]

            def col(*keys):
                return next((i for i, c in enumerate(hdr) if all(k in c for k in keys)), None)
            ri, si, cnt, fc, avg, mx = col("rendering"), col("site"), col("count"), col("from cache"), col("avg", "time"), col("max", "time")
            data = []
            for r in rows[hdr_i + 1:]:
                try:
                    c = to_num(r[cnt]) or 0
                    f = to_num(r[fc]) or 0 if fc is not None else 0
                    av = to_num(r[avg]) or 0
                    m = to_num(r[mx]) or 0 if mx is not None else 0
                except (IndexError, TypeError):
                    continue
                data.append((r[ri], r[si] if si is not None else "", c, f, av, m))
            out.append("| Rendering | Site | Count | From cache % | Avg ms | Max ms | Cost (count×avg s) |\n|---|---|---|---|---|---|---|")
            for rn, st, c, f, av, m in sorted(data, key=lambda x: -(x[2] * x[4]))[:25]:
                hit = int(100 * f / c) if c else 0
                out.append(f"| {rn} | {st} | {int(c)} | {hit}% | {int(av)} | {int(m)} | {int(c * av / 1000)} |")
            out.append("\nHigh cost + low cache % = best HTML cache candidates (if output is deterministic).")

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {a.out}: {len(errors)} errors in {len(err_sigs)} signatures, {len(warns)} warnings, {len(lifecycle)} lifecycle events")


if __name__ == "__main__":
    main()
