#!/usr/bin/env python3
"""Parse Sitecore log files for publishing activity.

Usage:
  python3 parse_publish_log.py <file-or-folder> [more ...] [--out publish-report.md] [--item "<path or id>"]

Handles classic Sitecore log4net format:
  "ManagedPoolThread #6 09:21:19 INFO  Publishing ended"
  "4432 09:21:19 ERROR Something failed"
plus continuation lines (exceptions/stack traces). Date comes from the file name
(log.20261024.093000.txt / Publishing.log.20261024.txt). Stdlib only.
"""
import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

LINE_RE = re.compile(r"^(?P<thread>(?:ManagedPoolThread #\d+|Heartbeat|[\w .#-]+?|\d+))\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<level>DEBUG|INFO|WARN|ERROR|FATAL|AUDIT)\s+(?P<msg>.*)$")
DATE_RE = re.compile(r"(\d{8})(?:\.(\d{6}))?")
JOB_START = re.compile(r"Job started:\s*(?P<name>.+)$", re.I)
JOB_END = re.compile(r"Job ended:\s*(?P<name>.+?)(?:\s*\(units processed:\s*(?P<units>\d+)\))?$", re.I)
PUB_ITEM = re.compile(r"##Publish Item:\s*(?P<body>.+)$")
KV = re.compile(r"(\w+)=([^,]*)")
PUB_STATS = re.compile(r"(?:Created|Updated|Deleted|Skipped):\s*\d+", re.I)
PUB_BEGIN = re.compile(r"(Publish(?:ing)? started|Starting publish|PublishInstance|Publishing to)", re.I)
PUB_END = re.compile(r"(Publishing ended|Publish(?:ing)? (?:finished|completed))", re.I)
GUID = re.compile(r"\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?")


def files_from(paths):
    for p in paths:
        if os.path.isdir(p):
            for dp, _, fn in os.walk(p):
                for f in sorted(fn):
                    if f.lower().endswith((".txt", ".log")):
                        yield os.path.join(dp, f)
        elif os.path.isfile(p):
            yield p


def file_date(path):
    m = DATE_RE.search(os.path.basename(path))
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            pass
    return None


def parse(path):
    d = file_date(path)
    entries = []
    cur = None
    last_t = None
    day_offset = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            m = LINE_RE.match(line)
            if m:
                t = datetime.strptime(m.group("time"), "%H:%M:%S").time()
                if last_t and t < last_t and (datetime.combine(datetime.min, last_t) - datetime.combine(datetime.min, t)).seconds > 3600:
                    day_offset += 1  # rolled past midnight within one file
                last_t = t
                ts = datetime.combine(d, t) + timedelta(days=day_offset) if d else None
                cur = {"file": os.path.basename(path), "ts": ts, "time": m.group("time"), "thread": m.group("thread").strip(),
                       "level": m.group("level"), "msg": m.group("msg"), "extra": []}
                entries.append(cur)
            elif cur is not None and line.strip():
                if len(cur["extra"]) < 12:
                    cur["extra"].append(line.strip())
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default="publish-report.md")
    ap.add_argument("--item", help="item path or ID to filter item-level history")
    a = ap.parse_args()

    entries = []
    flist = list(files_from(a.paths))
    if not flist:
        sys.exit("No log files found")
    for f in flist:
        entries.extend(parse(f))
    entries.sort(key=lambda e: (e["ts"] or datetime.min, e["file"]))

    jobs = []
    open_jobs = {}
    items = []
    errors = []
    op_counter = Counter()
    explanations = Counter()

    for e in entries:
        msg = e["msg"]
        ms = JOB_START.search(msg)
        if ms and "publish" in ms.group("name").lower():
            key = ms.group("name").strip()
            open_jobs[key] = {"name": key, "start": e["ts"] or e["time"], "end": None, "units": None, "file": e["file"], "thread": e["thread"]}
            continue
        me = JOB_END.search(msg)
        if me and "publish" in me.group("name").lower():
            key = me.group("name").strip()
            job = open_jobs.pop(key, {"name": key, "start": None, "file": e["file"], "thread": e["thread"]})
            job["end"] = e["ts"] or e["time"]
            job["units"] = me.group("units")
            jobs.append(job)
            continue
        mp = PUB_ITEM.search(msg)
        if mp:
            kv = dict((k.strip(), v.strip()) for k, v in KV.findall(mp.group("body")))
            kv["_ts"] = e["ts"] or e["time"]
            kv["_raw"] = mp.group("body")
            items.append(kv)
            op_counter[kv.get("Operation", "?")] += 1
            if kv.get("Explanation"):
                explanations[kv.get("Explanation")[:120]] += 1
            continue
        if e["level"] in ("ERROR", "FATAL") or (e["level"] == "WARN" and re.search(r"publish", msg, re.I)):
            errors.append(e)

    for key, job in open_jobs.items():
        job["end"] = None
        jobs.append(job)

    def dur(j):
        if isinstance(j.get("start"), datetime) and isinstance(j.get("end"), datetime):
            return (j["end"] - j["start"]).total_seconds()
        return None

    out = ["# Publishing Log Report\n", f"Files: {len(flist)} · Entries: {len(entries)}\n"]
    if flist:
        out.append("Files parsed: " + ", ".join(sorted({os.path.basename(f) for f in flist})[:20]) + "\n")

    out.append(f"\n## Publish jobs ({len(jobs)})\n\n| Start | End | Duration (s) | Units | Job | Thread |\n|---|---|---|---|---|---|")
    for j in jobs:
        d = dur(j)
        out.append(f"| {j.get('start') or '?'} | {j.get('end') or '**NOT ENDED**'} | {int(d) if d is not None else ''} | {j.get('units') or ''} | {j['name']} | {j.get('thread', '')} |")
    unfinished = [j for j in jobs if not j.get("end")]
    if unfinished:
        out.append(f"\n> {len(unfinished)} publish job(s) started without a matching end in these logs — hung, killed by app-pool recycle, or the end is in a later log file.")
    slow = sorted([j for j in jobs if dur(j)], key=dur, reverse=True)[:5]
    if slow:
        out.append("\n### Slowest jobs\n")
        out += [f"- {int(dur(j))}s — {j['name']} ({j.get('units') or '?'} units)" for j in slow]

    out.append(f"\n## Item operations ({len(items)})\n")
    if items:
        out.append("| Operation | Count |\n|---|---|")
        out += [f"| {k} | {v} |" for k, v in op_counter.most_common()]
        out.append("\n### Top explanations\n")
        out += [f"- ({v}) {k}" for k, v in explanations.most_common(15)]
        deleted = [i for i in items if i.get("Operation", "").lower() == "deleted"]
        if deleted:
            out.append(f"\n### Deleted from target ({len(deleted)})\n")
            out += [f"- {i['_ts']} — {i.get('Name', '')} `{i.get('Uri', '')}`" for i in deleted[:50]]
    else:
        out.append("No `##Publish Item` lines found. Item-level publish logging is off; enable verbose publish logging and reproduce to see per-item operations and skip reasons.")

    if a.item:
        needle = a.item.strip().lower().strip("{}")
        hist = [i for i in items if needle in i["_raw"].lower()]
        out.append(f"\n## History for `{a.item}` ({len(hist)})\n")
        out += [f"- {i['_ts']} — {i.get('Operation', '?')} / {i.get('ChildAction', '')} — {i.get('Explanation', '')}" for i in hist] or ["No item-level lines matched."]
        related = [e for e in entries if needle in e["msg"].lower() and not PUB_ITEM.search(e["msg"])]
        if related:
            out.append("\nOther log lines mentioning it:\n")
            out += [f"- {e['ts'] or e['time']} {e['level']} {e['msg'][:200]}" for e in related[:30]]

    out.append(f"\n## Errors and publish warnings ({len(errors)})\n")
    groups = defaultdict(list)
    for e in errors:
        sig = GUID.sub("{GUID}", re.sub(r"\d+", "N", e["msg"]))[:160]
        groups[sig].append(e)
    for sig, es in sorted(groups.items(), key=lambda x: -len(x[1]))[:25]:
        first = es[0]
        out.append(f"\n**{len(es)}×** `{sig}`  \nfirst: {first['ts'] or first['time']} ({first['file']}) · last: {es[-1]['ts'] or es[-1]['time']}")
        if first["extra"]:
            out.append("```\n" + "\n".join(first["extra"][:8]) + "\n```")

    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Wrote {a.out}: {len(jobs)} jobs ({len(unfinished)} unfinished), {len(items)} item ops, {len(errors)} errors/warnings")


if __name__ == "__main__":
    main()
