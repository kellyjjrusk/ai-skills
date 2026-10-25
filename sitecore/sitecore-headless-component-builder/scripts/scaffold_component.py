#!/usr/bin/env python3
"""Scaffold a Sitecore headless component: TSX + SPE item-creation script (+ optional GraphQL).

Example:
  python3 scaffold_component.py --name PromoCard --module "Feature/Promotions" \
    --fields "Heading:Single-Line Text,Body:Rich Text,Image:Image,Cta:General Link" \
    --sdk content-sdk --variants "Default,Compact" --graphql --out ./out
Stdlib only.
"""
import argparse
import os
import re
import sys

SUPPORTED = {
    "Single-Line Text": ("Field<string>", "text"),
    "Multi-Line Text": ("Field<string>", "text"),
    "Rich Text": ("Field<string>", "rich"),
    "Image": ("ImageField", "image"),
    "General Link": ("LinkField", "link"),
    "Checkbox": ("Field<boolean>", "bool"),
    "Date": ("Field<string>", "date"),
    "Datetime": ("Field<string>", "date"),
    "Number": ("Field<number>", "num"),
    "Integer": ("Field<number>", "num"),
    "File": ("FileField", "file"),
}


def parse_fields(spec):
    fields = []
    for raw in spec.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if ":" not in raw:
            sys.exit(f"Bad field spec '{raw}', expected Name:Type")
        name, ftype = [x.strip() for x in raw.split(":", 1)]
        required = ftype.endswith("!")
        ftype = ftype.rstrip("!").strip()
        if ftype not in SUPPORTED:
            sys.exit(f"Unsupported type '{ftype}'. Supported: {', '.join(SUPPORTED)}")
        if not re.match(r"^[A-Za-z][A-Za-z0-9]*$", name):
            sys.exit(f"Field name '{name}' must be alphanumeric, starting with a letter")
        fields.append({"name": name, "type": ftype, "ts": SUPPORTED[ftype][0], "kind": SUPPORTED[ftype][1], "required": required})
    if not fields:
        sys.exit("No fields given")
    return fields


def tsx(name, fields, sdk, variants):
    pkg = "@sitecore-content-sdk/nextjs" if sdk == "content-sdk" else "@sitecore-jss/sitecore-jss-nextjs"
    kinds = {f["kind"] for f in fields}
    imports = ["Field"]
    comps = []
    if "text" in kinds or "num" in kinds:
        comps.append("Text")
    if "rich" in kinds:
        comps.append("RichText")
    if "image" in kinds:
        imports.append("ImageField")
        comps.append("NextImage as SitecoreImage")
    if "link" in kinds:
        imports.append("LinkField")
        comps.append("Link as SitecoreLink")
    if "date" in kinds:
        comps.append("DateField")
    if "file" in kinds:
        imports.append("FileField")
        comps.append("File as SitecoreFile")
    hook = "useSitecore" if sdk == "content-sdk" else "useSitecoreContext"
    comps.append(hook)
    imp_line = ", ".join(sorted(set(imports)) + comps)

    iface = "\n".join(f"  {f['name']}: {f['ts']};" for f in fields)
    editing_expr = (
        "const { page } = useSitecore();\n  const isEditing = page.mode.isEditing; // confirm property path for your Content SDK version"
        if sdk == "content-sdk"
        else "const { sitecoreContext } = useSitecoreContext();\n  const isEditing = !!sitecoreContext.pageEditing;"
    )

    def render(f, indent="        "):
        n = f["name"]
        k = f["kind"]
        cls = n[0].lower() + n[1:]
        if k == "text":
            tag = "h2" if n.lower() in ("heading", "title", "headline") else "p"
            return f'{indent}{{(isEditing || fields.{n}?.value) && (\n{indent}  <Text tag="{tag}" className="{name.lower()}__{cls}" field={{fields.{n}}} />\n{indent})}}'
        if k == "num":
            return f'{indent}{{(isEditing || fields.{n}?.value !== undefined) && (\n{indent}  <Text tag="span" className="{name.lower()}__{cls}" field={{{{ value: String(fields.{n}?.value ?? \'\') }}}} />\n{indent})}}'
        if k == "rich":
            return f'{indent}{{(isEditing || fields.{n}?.value) && (\n{indent}  <RichText className="{name.lower()}__{cls}" field={{fields.{n}}} />\n{indent})}}'
        if k == "image":
            return f'{indent}{{(isEditing || fields.{n}?.value?.src) && (\n{indent}  <SitecoreImage className="{name.lower()}__{cls}" field={{fields.{n}}} />\n{indent})}}'
        if k == "link":
            return f'{indent}{{(isEditing || fields.{n}?.value?.href) && (\n{indent}  <SitecoreLink className="{name.lower()}__{cls}" field={{fields.{n}}} />\n{indent})}}'
        if k == "date":
            return f'{indent}{{(isEditing || fields.{n}?.value) && (\n{indent}  <DateField tag="time" className="{name.lower()}__{cls}" field={{fields.{n}}} render={{(d: Date | null) => d?.toLocaleDateString()}} />\n{indent})}}'
        if k == "bool":
            return f"{indent}{{/* {n} (Checkbox) is a flag: use fields.{n}?.value to drive behavior */}}"
        if k == "file":
            return f'{indent}{{(isEditing || fields.{n}?.value?.src) && (\n{indent}  <SitecoreFile className="{name.lower()}__{cls}" field={{fields.{n}}} />\n{indent})}}'
        return ""

    body = "\n".join(render(f) for f in fields)
    variant_names = variants or ["Default"]

    out = [
        f"import React, {{ JSX }} from 'react';",
        f"import {{ {imp_line} }} from '{pkg}';",
        "import { ComponentProps } from 'lib/component-props';",
        "",
        f"interface {name}Fields {{",
        iface,
        "}",
        "",
        f"type {name}Props = ComponentProps & {{",
        f"  fields: {name}Fields;",
        "};",
        "",
        f"const {name}Empty = ({{ isEditing }}: {{ isEditing: boolean }}): JSX.Element | null =>",
        "  isEditing ? (",
        f'    <div className="component {name.lower()} {name.lower()}--empty">',
        f'      <span className="is-empty-hint">{name}: select or create a datasource</span>',
        "    </div>",
        "  ) : null;",
        "",
    ]
    for v in variant_names:
        mod = "" if v == "Default" else f" {name.lower()}--{v.lower()}"
        out += [
            f"export const {v} = (props: {name}Props): JSX.Element | null => {{",
            f"  {editing_expr}",
            "  const { fields, params } = props;",
            f"  if (!fields) return <{name}Empty isEditing={{isEditing}} />;",
            "  const styles = params?.styles ? ` ${params.styles}` : '';",
            "  const id = params?.RenderingIdentifier;",
            "",
            "  return (",
            f'    <div className={{`component {name.lower()}{mod}${{styles}}`}} id={{id || undefined}}>',
            '      <div className="component-content">',
            body,
            "      </div>",
            "    </div>",
            "  );",
            "};",
            "",
        ]
    if "Default" not in variant_names:
        out += [f"export const Default = {variant_names[0]};", ""]
    return "\n".join(out)


def spe(name, module, fields, site_collection, variants):
    tpl_parent = f"/sitecore/templates/{module}"
    rnd_parent = f"/sitecore/layout/Renderings/{module}"
    field_rows = "\n".join(f'    @{{ Name = "{f["name"]}"; Type = "{f["type"]}"; Required = ${"true" if f["required"] else "false"} }},' for f in fields).rstrip(",")
    variant_block = ""
    if site_collection and variants:
        vlist = ", ".join(f'"{v}"' for v in variants)
        variant_block = f'''
# --- Headless variants (SXA) ---
# Template paths below match recent headless SXA; confirm them in your instance (/sitecore/templates/Feature/Experience Accelerator/Headless Variants).
$variantRoot = "master:/sitecore/content/{site_collection}/Presentation/Headless Variants"
if (Test-Path $variantRoot) {{
    $vFolder = Ensure-Item "$variantRoot/{name}" "Feature/Experience Accelerator/Headless Variants/Headless Variants"
    foreach ($v in @({vlist})) {{
        Ensure-Item "$variantRoot/{name}/$v" "Feature/Experience Accelerator/Headless Variants/Variant Definition" | Out-Null
    }}
}} else {{
    Write-Host "Variant root not found ($variantRoot); create variants manually." -ForegroundColor Yellow
}}
'''
    return f'''<#
  Creates template + JSON rendering for {name}.
  Run in SPE ISE on a DEV CM as admin, then serialize with: dotnet sitecore ser pull
  Idempotent: existing items are reused, not duplicated. Review before running.
#>
$ErrorActionPreference = "Stop"
$db = "master"

function Ensure-Folder($path, $folderTemplate) {{
    if (-not (Test-Path "$($db):$path")) {{
        $parentPath = $path.Substring(0, $path.LastIndexOf("/"))
        $leaf = $path.Substring($path.LastIndexOf("/") + 1)
        Ensure-Folder $parentPath $folderTemplate | Out-Null
        Write-Host "Creating folder $path"
        New-Item -Path "$($db):$parentPath" -Name $leaf -ItemType $folderTemplate | Out-Null
    }}
    Get-Item -Path "$($db):$path"
}}

function Ensure-Item($fullPath, $itemType) {{
    if (Test-Path $fullPath) {{ return Get-Item -Path $fullPath }}
    $parent = $fullPath.Substring(0, $fullPath.LastIndexOf("/"))
    $leaf = $fullPath.Substring($fullPath.LastIndexOf("/") + 1)
    Write-Host "Creating $fullPath"
    New-Item -Path $parent -Name $leaf -ItemType $itemType
}}

$fields = @(
{field_rows}
)

# --- Template ---
Ensure-Folder "{tpl_parent}" "System/Templates/Template Folder" | Out-Null
$template = Ensure-Item "$($db):{tpl_parent}/{name}" "System/Templates/Template"
$section  = Ensure-Item "$($db):{tpl_parent}/{name}/Content" "System/Templates/Template section"

$sort = 100
foreach ($f in $fields) {{
    $fi = Ensure-Item "$($db):{tpl_parent}/{name}/Content/$($f.Name)" "System/Templates/Template field"
    $fi.Editing.BeginEdit()
    $fi["Type"] = $f.Type
    $fi["__Sortorder"] = "$sort"
    $fi.Editing.EndEdit() | Out-Null
    $sort += 100
}}

# Standard values
$svPath = "$($db):{tpl_parent}/{name}/__Standard Values"
if (-not (Test-Path $svPath)) {{
    $sv = $template.Add("__Standard Values", [Sitecore.Data.TemplateID]$template.ID)
    $template.Editing.BeginEdit()
    $template["__Standard values"] = $sv.ID.ToString()
    $template.Editing.EndEdit() | Out-Null
    Write-Host "Created standard values"
}}

# Required-field validation (Quick Action / Validate bar)
$requiredRule = Get-Item -Path "$($db):" -ID "{{59D4EE10-627C-4FD3-A964-61A88B092CBC}}" -ErrorAction SilentlyContinue   # standard "Required" field rule
if (-not $requiredRule -or $requiredRule.Name -ne "Required") {{
    $requiredRule = Get-ChildItem -Path "$($db):/sitecore/system/Settings/Validation Rules/Field Rules" -Recurse |
        Where-Object {{ $_.Name -eq "Required" -and $_.TemplateName -notmatch "Folder" }} | Select-Object -First 1
}}
if (-not $requiredRule) {{ Write-Host "Required validation rule not found; set validators manually." -ForegroundColor Yellow }}
if ($requiredRule) {{
    foreach ($f in $fields | Where-Object {{ $_.Required }}) {{
        $fi = Get-Item -Path "$($db):{tpl_parent}/{name}/Content/$($f.Name)"
        $fi.Editing.BeginEdit()
        foreach ($vf in "Quick Action Bar","Validate Button","Validator Bar","Workflow") {{
            if (-not ($fi[$vf] -match [regex]::Escape($requiredRule.ID.ToString()))) {{
                $fi[$vf] = (($fi[$vf], $requiredRule.ID.ToString()) | Where-Object {{ $_ }}) -join "|"
            }}
        }}
        $fi.Editing.EndEdit() | Out-Null
    }}
}}

# --- JSON Rendering ---
Ensure-Folder "{rnd_parent}" "System/Layout/Renderings/Rendering Folder" | Out-Null
$rendering = Ensure-Item "$($db):{rnd_parent}/{name}" "Foundation/JavaScript Services/Json Rendering"
$rendering.Editing.BeginEdit()
$rendering["componentName"] = "{name}"
$rendering["Datasource Template"] = $template.Paths.FullPath
$rendering["Datasource Location"] = 'query:$site/*[@@name=''Data'']|query:./*[@@name=''Data'']'
$rendering.Editing.EndEdit() | Out-Null
{variant_block}
Write-Host ""
Write-Host "Done. Template: $($template.ID)  Rendering: $($rendering.ID)" -ForegroundColor Green
Write-Host "Next: add the rendering to the site's Available Renderings (SXA) or placeholder settings, then run 'dotnet sitecore ser pull'."
'''


def graphql(name, fields):
    sel = []
    for f in fields:
        sel.append(f"      {f['name']} {{ jsonValue }}")
    body = "\n".join(sel)
    return f'''# Integrated GraphQL for {name} — paste into the rendering's "ComponentQuery" field.
# Variables $datasource and $language are supplied by the layout service.
query {name}Query($datasource: String!, $language: String!) {{
  datasource: item(path: $datasource, language: $language) {{
    ... on {name} {{
{body}
    }}
  }}
}}
'''


def readme(name, module, fields, sdk, has_gql):
    rows = "\n".join(f"| {f['name']} | {f['type']} | {'yes' if f['required'] else 'no'} |" for f in fields)
    return f'''# {name}

| Field | Type | Required |
|---|---|---|
{rows}

## Run order
1. Review `create-{name}.ps1`, then run it in the SPE ISE on a **dev** CM.
2. Confirm items exist: `/sitecore/templates/{module}/{name}` and `/sitecore/layout/Renderings/{module}/{name}`.
3. Ensure a serialization module includes both paths, then `dotnet sitecore ser pull` and commit the YAML.
4. Copy `{name}.tsx` into `src/components/` (adapt to repo conventions); regenerate the component map.
5. {"Paste `" + name + ".graphql` into the rendering's ComponentQuery field and switch the TSX to read `fields.data.datasource`." if has_gql else "No integrated GraphQL; fields come from the datasource."}
6. `npm run build`, then test in Pages: add, create datasource, edit every field, save, publish, verify on delivery.

SDK target: {sdk}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--module", required=True, help='e.g. "Feature/Promotions" or "Project/Acme"')
    ap.add_argument("--fields", required=True, help='"Name:Type,Name:Type!" (! = required)')
    ap.add_argument("--sdk", choices=["content-sdk", "jss"], default="content-sdk")
    ap.add_argument("--variants", default="", help='"Default,Compact"')
    ap.add_argument("--site-collection", default="", help='e.g. "Acme/AcmeSite" for SXA variants')
    ap.add_argument("--graphql", action="store_true")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    if not re.match(r"^[A-Z][A-Za-z0-9]*$", a.name):
        sys.exit("--name must be PascalCase alphanumeric")
    module = a.module.strip("/")
    fields = parse_fields(a.fields)
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]
    for v in variants:
        if not re.match(r"^[A-Z][A-Za-z0-9]*$", v):
            sys.exit(f"Variant '{v}' must be PascalCase alphanumeric")
    os.makedirs(a.out, exist_ok=True)

    files = {
        f"{a.name}.tsx": tsx(a.name, fields, a.sdk, variants),
        f"create-{a.name}.ps1": spe(a.name, module, fields, a.site_collection, variants),
        f"README-{a.name}.md": readme(a.name, module, fields, a.sdk, a.graphql),
    }
    if a.graphql:
        files[f"{a.name}.graphql"] = graphql(a.name, fields)
    for fn, content in files.items():
        with open(os.path.join(a.out, fn), "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"wrote {os.path.join(a.out, fn)}")


if __name__ == "__main__":
    main()
