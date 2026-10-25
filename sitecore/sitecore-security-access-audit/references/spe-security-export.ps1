<#
  Sitecore security export — READ-ONLY. Run in SPE ISE as an administrator.
  Produces users.csv, roles.csv, acl.csv, workflow-acl.csv (downloaded via Out-Download).
  Large trees: limit $roots or run per root. No passwords or secrets are exported.
#>
$db = "master"
$roots = @(
    "/sitecore/content",
    "/sitecore/media library",
    "/sitecore/templates",
    "/sitecore/layout",
    "/sitecore/system"
)
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$tmp = "$($SitecoreDataFolder)\temp"

function Save($rows, $name) {
    $p = "$tmp\$name-$stamp.csv"
    $rows | Export-Csv -Path $p -NoTypeInformation -Encoding UTF8
    Out-Download -Path $p | Out-Null
    Write-Host "$name : $(@($rows).Count) rows"
}

# ---------- Users ----------
$users = foreach ($u in Get-User -Filter "*") {
    $mu = $null
    try { $mu = [System.Web.Security.Membership]::GetUser($u.Name) } catch {}
    [PSCustomObject]@{
        User          = $u.Name
        Domain        = $u.Domain.Name
        IsAdmin       = $u.IsAdministrator
        Approved      = if ($mu) { $mu.IsApproved } else { "" }
        LockedOut     = if ($mu) { $mu.IsLockedOut } else { "" }
        Created       = if ($mu) { $mu.CreationDate.ToString("s") } else { "" }
        LastLogin     = if ($mu) { $mu.LastLoginDate.ToString("s") } else { "" }
        LastActivity  = if ($mu) { $mu.LastActivityDate.ToString("s") } else { "" }
        Email         = if ($mu) { ($mu.Email -replace "(^.).*(@.*$)", '$1***$2') } else { "" }
        Roles         = ($u.Roles | ForEach-Object { $_.Name }) -join "|"
    }
}
Save $users "users"

# ---------- Roles ----------
$roles = foreach ($r in Get-Role -Filter "*") {
    $members = @()
    try { $members = Get-RoleMember -Identity $r.Name -ErrorAction SilentlyContinue } catch {}
    $memberUsers = $members | Where-Object { $_ -is [Sitecore.Security.Accounts.User] } | ForEach-Object { $_.Name }
    $memberRoles = $members | Where-Object { $_ -is [Sitecore.Security.Accounts.Role] } | ForEach-Object { $_.Name }
    $memberOf = @()
    try { $memberOf = [Sitecore.Security.Accounts.RolesInRolesManager]::GetRolesForRole($r, $false) | ForEach-Object { $_.Name } } catch {}
    [PSCustomObject]@{
        Role        = $r.Name
        Domain      = $r.Domain.Name
        MemberUsers = ($memberUsers -join "|")
        MemberRoles = ($memberRoles -join "|")
        MemberOf    = ($memberOf -join "|")
    }
}
Save $roles "roles"

# ---------- Item ACLs (explicit rules only) ----------
function Get-RulesRows($item) {
    $raw = $item.Fields["__Security"].Value
    if ([string]::IsNullOrWhiteSpace($raw)) { return }
    foreach ($rule in $item.Security.GetAccessRules()) {
        [PSCustomObject]@{
            Path        = $item.ItemPath
            ID          = $item.ID.ToString()
            Template    = $item.TemplateName
            Account     = $rule.Account.Name
            AccountType = $rule.Account.AccountType
            Right       = $rule.AccessRight.Name
            Permission  = $rule.SecurityPermission
            Propagation = $rule.PropagationType
        }
    }
}
$acl = foreach ($root in $roots) {
    $rootItem = Get-Item -Path "$($db):$root" -ErrorAction SilentlyContinue
    if (-not $rootItem) { continue }
    Get-RulesRows $rootItem
    Get-ChildItem -Path "$($db):$root" -Recurse -ErrorAction SilentlyContinue | ForEach-Object { Get-RulesRows $_ }
}
Save $acl "acl"

# ---------- Workflow ACLs ----------
$wfacl = Get-ChildItem -Path "$($db):/sitecore/system/Workflows" -Recurse | ForEach-Object { Get-RulesRows $_ }
Save $wfacl "workflow-acl"

Write-Host "Done. Review CSVs before sharing; they contain account names."
