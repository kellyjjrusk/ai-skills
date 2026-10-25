# Hardening checklist

Mark each: Pass / Fail / Needs evidence. Cite the evidence (file + line, screenshot, command output).

## XP/XM — patching
| ID | Check |
|---|---|
| P1 | Version in Mainstream or paid Extended support (KB0641167) |
| P2 | All applicable security bulletins/hotfixes installed (list bulletin IDs) |
| P3 | OS, IIS, .NET Framework 4.8, SQL, Solr patched |
| P4 | Subscribed to Sitecore security notifications |

## XP/XM — exposure
| ID | Check |
|---|---|
| E1 | CM not reachable from internet, or IP-restricted + SSO/MFA |
| E2 | CD blocks `/sitecore/admin`, `/sitecore/shell`, `/sitecore/login`, `/sitecore/api/ssc` (unless needed), `/-/speak`, `/unicorn.aspx`, `/sitecore modules` |
| E3 | CD role has no SPE, Unicorn, dev tools, Sitecore Client UI enabled |
| E4 | SPE remoting disabled or restricted to specific accounts/IPs; SPE elevated session required; delegated access least-privilege |
| E5 | HTTPS everywhere; HSTS; TLS 1.2+ only |
| E6 | Security headers on CD: CSP, X-Content-Type-Options, Referrer-Policy, frame-ancestors |
| E7 | Solr, xConnect, Identity Server not internet-exposed; client certs/keys rotated |
| E8 | Directory browsing off; `App_Config`, `App_Data`, `/data` not web-served |
| E9 | Telerik UI and legacy handlers patched or removed |

## XP/XM — identity & config
| ID | Check |
|---|---|
| I1 | Default `sitecore\admin` removed or renamed and strong-passworded |
| I2 | Password hash algorithm SHA512 (not SHA1), migration done |
| I3 | Membership password policy strengthened; lockout enabled |
| I4 | SSO via Identity Server/federated provider for CM users; MFA |
| I5 | Unique `machineKey` per environment; not default |
| I6 | Connection strings encrypted or in a secret store |
| I7 | `compilation debug="false"`, `customErrors` on, no stack traces to users |
| I8 | Identity Server client secrets rotated; DevEx client-credentials clients scoped |
| I9 | Audit logging enabled; logs shipped to SIEM; admin actions reviewed |

## SitecoreAI
| ID | Check |
|---|---|
| S1 | Cloud Portal SSO enforced; MFA |
| S2 | Org Owners/Admins limited to named people; quarterly review |
| S3 | Automation clients owned, scoped, rotated ≤ 90 days, stored in CI secret store |
| S4 | Preview Context ID / preview tokens not shipped to public front-end |
| S5 | Editing host on secure hostnames; editing secret rotated, not in repo |
| S6 | Marketplace apps: approved list, API access minimal |
| S7 | Item ACLs still reviewed (Mode A) for authoring roles |
| S8 | Rendering host security headers and cookie flags |
| S9 | Offboarding removes Cloud Portal access same day |
