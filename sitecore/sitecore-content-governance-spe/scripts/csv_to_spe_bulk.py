#!/usr/bin/env python3
"""Validate a CSV of Sitecore field changes and generate a safe SPE bulk-update script.

CSV columns (header required, case-insensitive):
  ItemPath or ItemID (at least one), Field, Value, [Language], [Action: set|append|clear]

Usage:
  python3 csv_to_spe_bulk.py changes.csv --scope "/sitecore/content/Acme" \
      [--database master] [--language en] [--max-items 1000] [--out bulk-update.ps1]
Exit code 1 if validation errors are found (script is not written).
Stdlib only.
"""
import argparse
import csv
import re
import sys
from datetime import datetime

GUID = re.compile(r"^\{?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}?$")
LANG = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
BROAD = {"/sitecore", "/sitecore/content", "/sitecore/system", "/sitecore/templates", "/sitecore/layout", "/sitecore/media library"}


def ps_quote(s):
    return "'" + (s or "").replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--scope", required=True)
    ap.add_argument("--database", default="master")
    ap.add_argument("--language", default="en")
    ap.add_argument("--max-items", type=int, default=1000)
    ap.add_argument("--out", default="bulk-update.ps1")
    a = ap.parse_args()

    scope = "/" + a.scope.strip().strip("/")
    if scope.lower() in BROAD:
        print(f"WARNING: scope {scope} is broad; generated script will require $allowBroadScope = $true", file=sys.stderr)

    with open(a.csv, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            sys.exit("CSV has no header")
        cols = {c.lower().strip(): c for c in reader.fieldnames}
        need_id = "itemid" in cols or "itempath" in cols
        if not need_id or "field" not in cols:
            sys.exit("CSV needs ItemPath or ItemID, and Field (and Value unless all actions are clear)")
        rows = list(reader)

    errors, warnings, clean = [], [], []
    seen = {}
    for i, r in enumerate(rows, start=2):
        g = lambda k: (r.get(cols[k]) if k in cols else None)
        path = (g("itempath") or "").strip()
        iid = (g("itemid") or "").strip()
        field = (g("field") or "").strip()
        value = g("value") if "value" in cols else ""
        value = "" if value is None else value
        lang = (g("language") or a.language).strip()
        action = (g("action") or "set").strip().lower()
        if not path and not iid:
            errors.append(f"row {i}: no ItemPath or ItemID")
            continue
        if iid and not GUID.match(iid):
            errors.append(f"row {i}: invalid ItemID '{iid}'")
            continue
        if path:
            if not path.startswith("/sitecore"):
                errors.append(f"row {i}: ItemPath must start with /sitecore: '{path}'")
                continue
            if not (path.lower() == scope.lower() or path.lower().startswith(scope.lower() + "/")):
                errors.append(f"row {i}: path outside scope {scope}: '{path}'")
                continue
        if not field:
            errors.append(f"row {i}: empty Field")
            continue
        if field.startswith("__") and field.lower() not in ("__display name",):
            warnings.append(f"row {i}: standard field '{field}' — confirm this is intended")
        if action not in ("set", "append", "clear"):
            errors.append(f"row {i}: Action must be set|append|clear, got '{action}'")
            continue
        if not LANG.match(lang):
            errors.append(f"row {i}: invalid language '{lang}'")
            continue
        if action != "clear" and value == "" and action == "set":
            warnings.append(f"row {i}: empty Value with action 'set' (use 'clear' to make intent explicit)")
        key = ((iid.strip('{}').lower() if iid else path.lower()), field.lower(), lang.lower())
        if key in seen and seen[key] != (action, value):
            errors.append(f"row {i}: conflicts with row {seen[key][2] if len(seen[key]) > 2 else '?'} for same item/field/language")
            continue
        seen[key] = (action, value, i)
        clean.append({"path": path, "id": ("{" + iid.strip("{}").upper() + "}") if iid else "", "field": field,
                      "value": value, "lang": lang, "action": action.capitalize(), "row": i})

    for w in warnings[:50]:
        print("WARN", w, file=sys.stderr)
    if errors:
        for e in errors[:100]:
            print("ERROR", e, file=sys.stderr)
        print(f"{len(errors)} error(s); script not written.", file=sys.stderr)
        sys.exit(1)
    if len(clean) > a.max_items:
        print(f"WARNING: {len(clean)} rows exceeds --max-items {a.max_items}; script cap will abort unless raised.", file=sys.stderr)

    data_lines = ",\n".join(
        f"    @{{ Row={c['row']}; Path={ps_quote(c['path'])}; ID={ps_quote(c['id'])}; Field={ps_quote(c['field'])}; Value={ps_quote(c['value'])}; Language={ps_quote(c['lang'])}; Action={ps_quote(c['action'])} }}"
        for c in clean)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    script = f'''<#
  bulk-update.ps1 — generated {stamp} from {a.csv} ({len(clean)} rows)
  WRITES CONTENT: yes. Default is DRY RUN. Run in SPE ISE.
  Flow: resolve items → compare old/new → preview + CSV → cap → backup package → apply in BulkUpdateContext → summary.
  Does NOT publish.
#>

# ===== 1. Parameters =====
$dryRun          = $true
$database        = {ps_quote(a.database)}
$scopeRoot       = {ps_quote(scope)}
$maxItems        = {a.max_items}
$allowBroadScope = $false
$backupPackage   = $true

# ===== 2. Scope guard =====
$broad = @("/sitecore", "/sitecore/content", "/sitecore/system", "/sitecore/templates", "/sitecore/layout", "/sitecore/media library")
if (($broad -contains $scopeRoot.TrimEnd("/")) -and -not $allowBroadScope) {{
    Write-Host "Refusing broad scope '$scopeRoot'. Set `$allowBroadScope = `$true only if certain." -ForegroundColor Red
    return
}}

# ===== Data =====
$rows = @(
{data_lines}
)

# ===== 3. Resolve + compare =====
$changes  = New-Object System.Collections.Generic.List[object]
$problems = New-Object System.Collections.Generic.List[object]
foreach ($r in $rows) {{
    $item = $null
    if ($r.ID) {{ $item = Get-Item -Path "$($database):" -ID $r.ID -Language $r.Language -ErrorAction SilentlyContinue }}
    elseif ($r.Path) {{ $item = Get-Item -Path "$($database):$($r.Path)" -Language $r.Language -ErrorAction SilentlyContinue }}
    if (-not $item) {{ $problems.Add([PSCustomObject]@{{ Row=$r.Row; Path=$r.Path; ID=$r.ID; Problem="Item not found" }}); continue }}
    if (-not $item.Paths.FullPath.StartsWith($scopeRoot, [StringComparison]::OrdinalIgnoreCase)) {{
        $problems.Add([PSCustomObject]@{{ Row=$r.Row; Path=$item.Paths.FullPath; ID=$r.ID; Problem="Outside scope" }}); continue
    }}
    if ($item.Versions.Count -eq 0) {{ $problems.Add([PSCustomObject]@{{ Row=$r.Row; Path=$item.Paths.FullPath; ID=$r.ID; Problem="No version in $($r.Language)" }}); continue }}
    if (-not $item.Fields[$r.Field]) {{ $problems.Add([PSCustomObject]@{{ Row=$r.Row; Path=$item.Paths.FullPath; ID=$r.ID; Problem="Field '$($r.Field)' not on template" }}); continue }}
    $old = $item[$r.Field]
    $new = switch ($r.Action) {{ "Set" {{ $r.Value }} "Append" {{ $old + $r.Value }} "Clear" {{ "" }} }}
    if ($old -ceq $new) {{ continue }}
    $changes.Add([PSCustomObject]@{{ Row=$r.Row; Path=$item.Paths.FullPath; ID=$item.ID.ToString(); Language=$r.Language; Field=$r.Field; Old=$old; New=$new; Action=$r.Action }})
}}

# ===== 4. Preview + record =====
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Write-Host "Rows: $($rows.Count)  Changes: $($changes.Count)  Unchanged: $($rows.Count - $changes.Count - $problems.Count)  Problems: $($problems.Count)"
if ($problems.Count) {{ $problems | Show-ListView -Title "Rows that cannot be applied ($($problems.Count))" }}
if ($changes.Count -eq 0) {{ Write-Host "Nothing to change."; return }}
$planCsv = "$($SitecoreDataFolder)\\temp\\bulk-plan-$stamp.csv"
$changes | Export-Csv -Path $planCsv -NoTypeInformation -Encoding UTF8
Out-Download -Path $planCsv | Out-Null
$changes | Select-Object -First 200 | Show-ListView -Property Row, Path, Language, Field, Old, New -Title "Planned changes (first 200 of $($changes.Count))"

# ===== 5. Cap =====
if ($changes.Count -gt $maxItems) {{ Write-Host "Aborting: $($changes.Count) > `$maxItems ($maxItems)." -ForegroundColor Red; return }}
if ($dryRun) {{ Write-Host "DRY RUN — nothing changed. Set `$dryRun = `$false to apply." -ForegroundColor Yellow; return }}

# ===== 6. Backup =====
if ($backupPackage) {{
    $package = New-Package "BulkBackup-$stamp"
    $items = $changes | Select-Object -ExpandProperty ID -Unique | ForEach-Object {{ Get-Item -Path "$($database):" -ID $_ }}
    $source = $items | New-ExplicitItemSource -Name "Affected items" -InstallMode Overwrite
    $package.Sources.Add($source)
    $package.Metadata.Author = [Sitecore.Context]::User.Name
    $package.Metadata.Comment = "Backup before bulk update $stamp"
    Export-Package -Project $package -Path "BulkBackup-$stamp.zip" -Zip
    Out-Download -Path "$($SitecorePackageFolder)\\BulkBackup-$stamp.zip" | Out-Null
}}

# ===== 7. Apply =====
$stats = @{{ ok = 0 }}
$failed = New-Object System.Collections.Generic.List[object]
New-UsingBlock (New-Object Sitecore.Data.BulkUpdateContext) {{
    foreach ($c in $changes) {{
        $item = $null
        try {{
            $item = Get-Item -Path "$($database):" -ID $c.ID -Language $c.Language
            $item.Editing.BeginEdit()
            $item[$c.Field] = $c.New
            $item.Editing.EndEdit() | Out-Null
            Write-Log "BULK $stamp row $($c.Row) $($c.Action) '$($c.Field)' on $($c.Path) [$($c.Language)]"
            $stats.ok++
        }} catch {{
            if ($item) {{ $item.Editing.CancelEdit() }}
            $failed.Add([PSCustomObject]@{{ Row=$c.Row; Path=$c.Path; Field=$c.Field; Error=$_.Exception.Message }})
        }}
    }}
}}

# ===== 8. Summary =====
Write-Host "Applied: $($stats.ok)  Failed: $($failed.Count)" -ForegroundColor Green
if ($failed.Count) {{ $failed | Show-ListView -Title "Failures" }}
Write-Host "Not published. Review, then publish the affected items separately."
'''
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(script)
    print(f"Wrote {a.out}: {len(clean)} rows, {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
