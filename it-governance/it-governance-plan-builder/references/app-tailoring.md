# Tailoring the plan to the application

The catalog is deliberately generic. Tailoring turns "integrate with the identity provider" into "configure Okta SAML for Salesforce, enforce MFA via session security level High Assurance for System Administrator profiles". Always verify specifics against the vendor's current documentation.

## By hosting model (shared responsibility)

| Area | SaaS | PaaS | IaaS / On-prem |
|---|---|---|---|
| Patching | Vendor; you test releases and track deprecations | Vendor patches platform; you patch your code/dependencies | You patch everything |
| Backup | Vendor scope varies; you export critical data and verify contract terms | Platform backups configurable; you set retention and test restores | You own backups end to end |
| Network | Vendor edge; you control IP allow-lists / conditional access | Private endpoints, VNet integration | Full segmentation, firewalls, WAF |
| Logging | Enable and export vendor audit logs before retention expires | Platform diagnostics → your SIEM | Everything → your SIEM |
| Evidence | Vendor SOC 2 / ISO reports + your CUECs | Mix | Yours |

## By application type

| Type | Tailor these first | Typical specifics |
|---|---|---|
| CMS / DXP (Sitecore, Adobe AEM, Optimizely, WordPress) | P-02, P-03, P-04, P-05 | Author/approver/publisher roles, workflow states, content ownership by site/section, template/component governance, publishing approvals, plugin/module approval |
| ERP (SAP, Oracle, Dynamics, NetSuite) | P-02, P-04, P-25 | Segregation of duties matrices, transport/change management, period-close freezes, SOX controls |
| CRM (Salesforce, Dynamics CE, HubSpot) | P-02, P-09, P-20 | Profiles/permission sets, sandbox refresh and data masking, managed packages, integration users, PII in records |
| HRIS / payroll (Workday, SuccessFactors) | P-02, P-20, P-21 | Sensitive data domains, security groups, data residency, vendor attestations |
| Collaboration (Microsoft 365, Google Workspace, Slack) | P-01, P-03, P-20, P-24 | External sharing, retention labels, guest access, app consent, AI assistant data boundaries |
| Data/analytics (Snowflake, Databricks, Power BI) | P-02, P-16, P-20, P-22 | Row/column security, workspace ownership, dataset certification, cost controls |
| Custom web application | P-05, P-11, P-15, P-17 | Secure SDLC, dependency management, CI/CD gates, secrets, pen testing |

## Worked example: Sitecore

How generic standards become platform-specific (abbreviated):

| Policy | Generic standard | Sitecore XP (self-hosted) | SitecoreAI (SaaS) |
|---|---|---|---|
| P-01 | Admin interfaces not public | Block `/sitecore/admin`, `/sitecore/shell`, `/sitecore/login` on CD; CM only via VPN | Cloud Portal SSO + MFA; restrict org admins |
| P-02 | Role catalog, least privilege | Site-specific Author/Approver/Publisher roles; nobody but admins in Client Securing/Developing; SPE limited to developers | Cloud Portal roles plus item ACLs inside the CM |
| P-03 | Ownership & lifecycle | Owners per site/section; stale-content and unused-media reports via SPE | Same, plus DAM ownership if media lives in Content Hub |
| P-04 | Change process | Serialized items (SCS) deployed via pipeline; publish restrictions during freezes | Deploy app pipelines; Pages changes through workflow |
| P-05 | Customization control | Helix/module conventions; no unsupported pipeline overrides; approved marketplace modules only | Marketplace apps approved; Content SDK components via code review |
| P-06 | Patching/lifecycle | Track Sitecore security bulletins and KB0641167 lifecycle dates | Track SitecoreAI release notes and SDK deprecations (e.g. JSS → Content SDK) |
| P-08 | Escalation | CD/CM/Solr health checks; Sitecore support portal case path | Edge/rendering host monitoring; Sitecore support case path |

Sitecore governance committee example: Executive Sponsor, Business Owner (lead), Sitecore Administrator, Network & Infrastructure Lead, Sitecore Development Lead, Sitecore Content Manager, Sitecore Marketing Manager, Internal Communications Lead.

## Questions to ask the vendor documentation

1. What identity providers and MFA enforcement options exist?
2. What built-in roles exist, and can they be customized?
3. What audit logs exist, what do they record, and how long are they retained?
4. What does the vendor back up, how long, and how is a restore requested?
5. What is the release cadence and how are breaking changes announced?
6. What are the API rate limits and integration authentication options?
7. What attestations are available (SOC 2 Type II, ISO 27001) and what are the complementary user entity controls?
8. What are the support tiers and severity response targets?
