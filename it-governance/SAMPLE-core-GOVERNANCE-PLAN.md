# Sitecore XM Cloud Governance Plan

**Organization:** Acme Corp  
**Document owner:** Jane Smith, Business Owner  
**Version:** 1.0 · **Effective:** 2026-10-24 · **Next full review:** 2027-10-24  
**Policy pack:** core (10 policies)

## 1. Purpose and scope

This plan defines how Acme Corp governs **Sitecore XM Cloud** (Content management system (CMS)): who decides, which rules apply, how those rules are carried out, and how they are communicated. It applies to everyone who administers, develops for, integrates with, or uses Sitecore XM Cloud, and to vendors acting on the organization's behalf.

| Attribute | Value |
|---|---|
| Application | Sitecore XM Cloud |
| Type | Content management system (CMS) |
| Vendor | Sitecore |
| Version | SaaS (continuously updated) |
| Hosting model | saas |
| Business purpose | Public marketing websites for three brands |
| Users | 120 authors, 15 developers, 4 administrators |
| Criticality | Tier 2 |
| Environments | Development, QA, Production |
| Regulatory / contractual context | SOC 2, GDPR |

### How this plan is organized

- **Governance committee:** the people and roles accountable for decisions.
- **Policies and standards:** a *policy* states **what** must be true; a *standard* states **how** it is achieved here. Policies change rarely; standards evolve with the platform.
- **Communication plan:** how each audience learns about policies and changes.
- **Adoption roadmap:** start with a small set, achieve compliance, then expand. A working C+ beats a perfect plan nobody follows.

Requirement language: **MUST** / **MUST NOT** are mandatory; **SHOULD** / **SHOULD NOT** are expected unless a documented reason exists; **MAY** is optional.

## 2. Governance committee

In smaller organizations one person may hold several roles; every role must still have a named holder.

| Role | Holder | Responsibilities |
|---|---|---|
| Executive Sponsor | VP Digital | Owns governance at the leadership level, funds it, breaks ties, and removes organizational blockers. |
| Business Owner (Committee Lead) | Director of Web | Chairs the committee, owns the plan and the policy backlog, approves policies, and reports status to the sponsor. |
| Sitecore XM Cloud Administrator | Sitecore Platform Admin | Operates Sitecore XM Cloud: users, roles, configuration, upgrades and day-to-day enforcement of policies and standards. |
| Network & Infrastructure Lead | Cloud Infrastructure Manager | Owns hosting, network, identity integration and platform availability (or the vendor relationship for SaaS). |
| Development Lead | Web Engineering Lead | Owns customizations, integrations, code quality, release practices and technical standards. |
| Content / Data Manager | Content Operations Manager | Owns the information inside Sitecore XM Cloud: ownership, quality, lifecycle and author/user standards. |
| Business Stakeholder (e.g. Marketing, Operations) | Marketing Operations Manager | Represents the business teams that depend on Sitecore XM Cloud; brings requirements and validates that standards are workable. |
| Internal Communications Lead | Internal Communications Manager | Owns the communication plan: audiences, messages, channels, timing and feedback loops. |

### 2.1 Meetings

- **Cadence:** Monthly (60 minutes); quarterly policy review
- **Standing agenda:** compliance metrics by policy · open exceptions · incidents since last meeting · upcoming changes and vendor releases · policy backlog (add / revise / retire) · communications due
- **Decisions:** recorded in the decision log with date, decision, owner and rationale. Quorum: Business Owner plus at least half of the role holders.
- **Escalation of disputes:** Business Owner → Executive Sponsor (final).

### 2.2 Operational escalation

| Severity | Primary | Backup | Contact method | Response target |
|---|---|---|---|---|
| Sev 1 | Sitecore Platform Admin | Web Engineering Lead | On-call phone / #web-incidents | 15 minutes |
| Sev 2 | Sitecore Platform Admin | Web Engineering Lead | Service desk P2 queue | 1 hour |
| Sev 3 | Service desk | Sitecore Platform Admin | Service desk ticket | 1 business day |

Severity definitions are in policy P-08 if selected; otherwise use the organization's incident standard.

### 2.3 RACI summary

R = Responsible · A = Accountable · C = Consulted · I = Informed

| Policy | R | A | C | I |
|---|---|---|---|---|
| P-01 Secure Access & Authentication | Sitecore XM Cloud Administrator | Business Owner (Committee Lead) | Network & Infrastructure Lead | Internal Communications Lead |
| P-02 Roles, Permissions & Access Reviews | Sitecore XM Cloud Administrator | Business Owner (Committee Lead) | Content / Data Manager | Executive Sponsor |
| P-03 Content & Data Ownership and Lifecycle | Content / Data Manager | Business Owner (Committee Lead) | Business Stakeholder (e.g. Marketing, Operations) | Sitecore XM Cloud Administrator |
| P-04 Change & Release Management | Development Lead | Business Owner (Committee Lead) | Sitecore XM Cloud Administrator, Network & Infrastructure Lead | Internal Communications Lead, Business Stakeholder (e.g. Marketing, Operations) |
| P-05 Configuration & Customization Standards | Development Lead | Business Owner (Committee Lead) | Sitecore XM Cloud Administrator | Network & Infrastructure Lead |
| P-06 Patching, Upgrades & Vendor Support Lifecycle | Sitecore XM Cloud Administrator | Business Owner (Committee Lead) | Network & Infrastructure Lead, Development Lead | Executive Sponsor |
| P-07 Backup & Recovery | Network & Infrastructure Lead | Business Owner (Committee Lead) | Sitecore XM Cloud Administrator, Business Owner (Committee Lead) | Executive Sponsor |
| P-08 Monitoring, Incident Response & Escalation | Sitecore XM Cloud Administrator | Business Owner (Committee Lead) | Network & Infrastructure Lead, Development Lead | Internal Communications Lead, Executive Sponsor |
| P-09 Integrations & API Usage | Development Lead | Business Owner (Committee Lead) | Sitecore XM Cloud Administrator, Network & Infrastructure Lead | Network & Infrastructure Lead |
| P-10 Training, Onboarding & Offboarding | Content / Data Manager | Business Owner (Committee Lead) | Sitecore XM Cloud Administrator | Internal Communications Lead |

## 3. Policies and standards

| ID | Policy | Category | Owner | Review | NIST CSF 2.0 |
|---|---|---|---|---|---|
| P-01 | Secure Access & Authentication | Access | Sitecore XM Cloud Administrator | 12 months | Protect |
| P-02 | Roles, Permissions & Access Reviews | Access | Sitecore XM Cloud Administrator | 12 months | Protect, Govern |
| P-03 | Content & Data Ownership and Lifecycle | Information | Content / Data Manager | 12 months | Identify, Govern |
| P-04 | Change & Release Management | Change | Development Lead | 12 months | Protect, Govern |
| P-05 | Configuration & Customization Standards | Change | Development Lead | 12 months | Protect, Identify |
| P-06 | Patching, Upgrades & Vendor Support Lifecycle | Operations | Sitecore XM Cloud Administrator | 6 months | Protect, Identify |
| P-07 | Backup & Recovery | Operations | Network & Infrastructure Lead | 12 months | Recover, Protect |
| P-08 | Monitoring, Incident Response & Escalation | Operations | Sitecore XM Cloud Administrator | 12 months | Detect, Respond |
| P-09 | Integrations & API Usage | Change | Development Lead | 12 months | Identify, Protect |
| P-10 | Training, Onboarding & Offboarding | People | Business Owner (Committee Lead) | 12 months | Protect, Govern |

### P-01 — Secure Access & Authentication

**Category:** Access · **Owner:** Sitecore XM Cloud Administrator (Sitecore Platform Admin) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Ensure only verified people and systems can reach Sitecore XM Cloud, using strong, centrally managed authentication.

**Policy (what)**

1. All users MUST authenticate to Sitecore XM Cloud through the organization's approved identity provider (single sign-on) where Sitecore XM Cloud supports it.
2. Multi-factor authentication MUST be enforced for every account with administrative or elevated privileges, and SHOULD be enforced for all users.
3. Shared, generic or default accounts MUST NOT be used for interactive access.
4. Administrative interfaces of Sitecore XM Cloud MUST NOT be exposed to the public internet without compensating controls.

**Standards (how, for Sitecore XM Cloud on saas)**

- Integrate Sitecore XM Cloud with the corporate identity provider (SAML/OIDC); disable local accounts except documented break-glass accounts.
- Break-glass accounts: maximum two, vaulted credentials, MFA, usage alerted and reviewed within one business day.
- Enable the vendor's SSO, MFA enforcement and IP allow-listing options in the Sitecore admin console; document the settings chosen.
- Session timeout of 30 minutes idle or less for administrative sessions; all access over TLS 1.2+.

**Compliance measures**

- % of users authenticating via SSO
- % of privileged accounts with MFA
- Number of active local/shared accounts

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-02 — Roles, Permissions & Access Reviews

**Category:** Access · **Owner:** Sitecore XM Cloud Administrator (Sitecore Platform Admin) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Grant the least privilege needed for each job and keep it that way over time.

**Policy (what)**

1. Access to Sitecore XM Cloud MUST be granted through roles or groups, not assigned directly to individual accounts.
2. Users MUST receive the minimum permissions required for their role (least privilege).
3. Privileged roles MUST be limited to named individuals approved by the Business Owner.
4. Access MUST be reviewed at least quarterly for privileged roles and semi-annually for all roles.
5. Access MUST be removed within one business day of a role change or departure.

**Standards (how, for Sitecore XM Cloud on saas)**

- Maintain a role catalog for Sitecore XM Cloud: role name, purpose, permissions summary, approver, and typical members.
- Request and approve access through the service desk/ticketing system; the approver is the role owner, never the requester.
- Automate provisioning and deprovisioning from the HR/identity system (SCIM or directory group sync) where supported.
- Quarterly review: export users and roles, role owners attest, revocations ticketed and evidenced.
- Separate duties: users who author or change data SHOULD NOT also approve their own changes in workflows.

**Compliance measures**

- Privileged account count
- Access review completion on time
- Orphaned accounts found per review

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-03 — Content & Data Ownership and Lifecycle

**Category:** Information · **Owner:** Content / Data Manager (Content Operations Manager) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Make sure every piece of information in Sitecore XM Cloud has an owner, stays accurate, and is retired on time.

**Policy (what)**

1. Every major content area, data set or module in Sitecore XM Cloud MUST have a named business owner.
2. Owners MUST review their content/data for accuracy at a defined interval.
3. Information MUST be retained and disposed of according to the organization's retention schedule.
4. Obsolete content/data MUST be archived or removed rather than left active.

**Standards (how, for Sitecore XM Cloud on saas)**

- Maintain an ownership register: area, owner, backup owner, review interval, retention rule.
- Default review interval: 12 months for general content, 6 months for regulated or customer-facing information.
- Use Sitecore XM Cloud's workflow, expiry or archival features where available; otherwise run a scheduled stale-content report.
- Naming and structure conventions documented in a style guide and enforced at creation (templates, required fields, validation).

**Compliance measures**

- % of areas with a named owner
- % of items reviewed within interval
- Stale items count

**Supports obligations:** GDPR

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-04 — Change & Release Management

**Category:** Change · **Owner:** Development Lead (Web Engineering Lead) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Change Sitecore XM Cloud predictably so that releases don't surprise users or break production.

**Policy (what)**

1. All changes to Sitecore XM Cloud configuration, code, integrations or structure in production MUST follow the approved change process.
2. Changes MUST be tested in a non-production environment before production unless classified as an emergency change.
3. Emergency changes MUST be documented and retroactively reviewed within five business days.
4. Every production change MUST have a rollback plan.

**Standards (how, for Sitecore XM Cloud on saas)**

- Classify changes: standard (pre-approved, low risk), normal (committee or CAB approval), emergency (post-review).
- Minimum environments: development/test and production; staging/UAT for customer-facing or high-risk systems.
- Release notes published to affected users for any user-visible change; maintenance windows communicated at least 3 business days ahead.
- Track vendor release schedules and assess each release for impact before it reaches production.
- Freeze periods defined for peak business events.

**Compliance measures**

- Change success rate
- Emergency changes per month
- Changes without ticket

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-05 — Configuration & Customization Standards

**Category:** Change · **Owner:** Development Lead (Web Engineering Lead) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Keep Sitecore XM Cloud maintainable and upgradeable by controlling how it is configured and extended.

**Policy (what)**

1. Customizations and extensions to Sitecore XM Cloud MUST be approved by the Development Lead before build.
2. Out-of-the-box capabilities SHOULD be preferred over custom development.
3. All custom code, configuration-as-code and scripts MUST be stored in version control.
4. Third-party add-ons, plugins or modules MUST be approved before installation.

**Standards (how, for Sitecore XM Cloud on saas)**

- Document a design decision record for every significant customization: need, options considered, upgrade impact.
- Follow Sitecore's documented extension points and supported APIs; unsupported modifications are prohibited.
- Maintain an add-on/plugin register: name, version, owner, purpose, support status, renewal date.
- Code review required for all custom code; automated linting/tests in the build where feasible.

**Compliance measures**

- Customizations with design records
- Unapproved add-ons found
- Upgrade effort attributable to customizations

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-06 — Patching, Upgrades & Vendor Support Lifecycle

**Category:** Operations · **Owner:** Sitecore XM Cloud Administrator (Sitecore Platform Admin) · **Review:** every 6 months (next 2027-04-24)

**Purpose.** Keep Sitecore XM Cloud on supported, patched versions to limit security and support risk.

**Policy (what)**

1. Sitecore XM Cloud MUST run on a version supported by the vendor.
2. Security patches MUST be applied within defined timeframes based on severity.
3. An upgrade roadmap MUST be maintained showing support end dates and planned upgrades.
4. The organization MUST subscribe to Sitecore security and release notifications.

**Standards (how, for Sitecore XM Cloud on saas)**

- For SaaS, track the vendor's release calendar, test new releases in a sandbox/preview tenant, and review deprecation notices monthly.
- Maintain a lifecycle register: component, version, support phase, end date, next action.

**Compliance measures**

- Days behind on critical patches
- Months until end of support
- Open vendor advisories

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-07 — Backup & Recovery

**Category:** Operations · **Owner:** Network & Infrastructure Lead (Cloud Infrastructure Manager) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Recover Sitecore XM Cloud and its data within agreed times after failure, error or attack.

**Policy (what)**

1. Sitecore XM Cloud data and configuration MUST be backed up according to a defined schedule.
2. Recovery time and recovery point objectives (RTO/RPO) MUST be defined and approved by the Business Owner.
3. Restores MUST be tested at least annually.
4. Backups MUST be protected from unauthorized access and from ransomware (isolated or immutable copies).

**Standards (how, for Sitecore XM Cloud on saas)**

- Default objectives (adjust per business impact): RPO 24 hours, RTO 8 hours for internal systems; RPO 1 hour, RTO 4 hours for customer-facing systems.
- Confirm the vendor's backup scope, retention and restore process in the contract; export critical data on a schedule to an organization-controlled store.
- Annual restore test documented with achieved RTO/RPO and remediation items.

**Compliance measures**

- Backup success rate
- Last successful restore test date
- Achieved vs target RTO/RPO

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-08 — Monitoring, Incident Response & Escalation

**Category:** Operations · **Owner:** Sitecore XM Cloud Administrator (Sitecore Platform Admin) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Detect problems with Sitecore XM Cloud quickly and make sure everyone knows who to call and what happens next.

**Policy (what)**

1. Sitecore XM Cloud availability and key functions MUST be monitored.
2. Incidents MUST be classified by severity and handled according to the escalation matrix.
3. Severity 1 incidents MUST have a post-incident review within five business days.
4. Users MUST have a single, published channel to report problems.

**Standards (how, for Sitecore XM Cloud on saas)**

- Severity definitions: Sev 1 = Sitecore XM Cloud down or data at risk for many users; Sev 2 = major function impaired; Sev 3 = minor/workaround exists; Sev 4 = request/cosmetic.
- Escalation matrix published (role, primary, backup, contact method, response target) and tested twice a year.
- Synthetic uptime checks and alerting on error rate, response time and failed jobs; alerts route to an on-call rotation for Sev 1/2.
- Know the vendor support path: support tiers, contract number, how to open a priority case, and expected response times.
- Status updates to users every 60 minutes during Sev 1 through the communication channel defined in this plan.

**Compliance measures**

- Mean time to detect
- Mean time to restore
- Sev 1 count per quarter
- Post-incident reviews completed

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-09 — Integrations & API Usage

**Category:** Change · **Owner:** Development Lead (Web Engineering Lead) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Connect Sitecore XM Cloud to other systems securely, reliably and with clear ownership.

**Policy (what)**

1. Every integration with Sitecore XM Cloud MUST be registered with an owner, purpose, data exchanged and authentication method.
2. Integrations MUST use dedicated service identities with least privilege, never personal accounts.
3. Credentials and API keys MUST be stored in an approved secrets store, never in code or documents.
4. Integrations MUST be monitored for failure.

**Standards (how, for Sitecore XM Cloud on saas)**

- Integration register fields: name, systems, direction, data classification, auth method, owner, SLA, monitoring link.
- Use the vendor's supported APIs; respect documented rate limits and implement retries with back-off.
- Rotate integration credentials at least annually or on personnel change.
- New integrations reviewed by the Development Lead (and Security Lead in the robust pack) before production.

**Compliance measures**

- Registered vs discovered integrations
- Integration failures per month
- Credentials older than 12 months

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

### P-10 — Training, Onboarding & Offboarding

**Category:** People · **Owner:** Business Owner (Committee Lead) (Director of Web) · **Review:** every 12 months (next 2027-10-24)

**Purpose.** Make sure people know how to use Sitecore XM Cloud correctly and lose access when they no longer need it.

**Policy (what)**

1. Users MUST complete role-appropriate Sitecore XM Cloud training before receiving access.
2. Administrators MUST complete administrator training and read this governance plan.
3. Offboarding MUST remove access and transfer ownership of content, data and integrations.
4. Training material MUST be kept current with the deployed version.

**Standards (how, for Sitecore XM Cloud on saas)**

- Maintain role-based quick-start guides and a recorded walkthrough for each role in the role catalog.
- Access request form includes training completion confirmation.
- Offboarding checklist: disable account, revoke tokens, reassign owned items/workflows, transfer integration ownership.
- Annual refresher for administrators, including policy changes from the past year.

**Compliance measures**

- % of users trained before access
- Offboarding completed within 1 business day

**Supports obligations:** SOC 2

**Exceptions.** Deviations require a documented exception: justification, compensating controls, risk owner, approval by the policy Accountable role, and an expiry date (maximum 12 months).

## 4. Communication plan

Policies that aren't communicated aren't followed. The Internal Communications Lead owns this plan. Every message answers: who is affected, what changes, when, what they must do, and *what's in it for them*. Keep messages short and avoid message fatigue: bundle minor changes into scheduled updates.

| Audience | What they need | Channel and format | Timing |
|---|---|---|---|
| Executive leadership | Business impact, risk reduced, decisions needed | Concise bulleted email or slide | Before the relevant leadership meeting |
| Managers | How to reinforce the change and check compliance in their teams | Short email with FAQ | Two messages, one week apart |
| Practitioners (Sitecore XM Cloud users, admins, developers) | Exact steps, impact on daily work, where to get help, escalation points | Detailed email or wiki page with steps and FAQ, plus chat channel updates | Three touches, one week apart, starting two weeks before the effective date |
| Vendors and partners | Obligations that apply to them | Formal notice through the vendor manager | At least 30 days before effective date |
| New joiners | Policies relevant to their role | Onboarding pack and training (P-10) | Before access is granted |

**Feedback loop:** a single channel (e.g. a governance mailbox or chat channel) for questions and suggested changes, reviewed at each committee meeting.

## 5. Adoption roadmap

Start small, reach compliance, then expand. Prioritize the policies that reduce the most risk for the least effort.

| Phase | Scope | Exit criteria | Target |
|---|---|---|---|
| 1. Establish | Committee named, plan approved, communication plan launched | Plan signed by Executive Sponsor | 2026-11-24 |
| 2. Core compliance | P-01, P-02, P-03, P-04, P-05, P-06, P-07, P-08, P-09, P-10 | Each policy at least 'Partial' with evidence; critical gaps have dated actions | 2027-01-24 |
| 3. Improve | Raise policies to 'Compliant'; refine standards from metrics and incidents | Annual review completed | 2027-10-24 |

## 6. Plan maintenance

- The plan is reviewed in full every 12 months, and policies on their individual review cycles.
- Triggers for an out-of-cycle review: major incident, audit finding, new regulation, change in hosting model or vendor, major version upgrade.
- Changes follow: proposal → committee review → Accountable approval → communication per section 4 → version update.

### Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| 1.0 | 2026-10-24 | Jane Smith, Business Owner | Initial plan (core pack) |

### Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Executive Sponsor | VP Digital | | |
| Business Owner | Director of Web | | |

## Appendix B. Glossary

| Term | Meaning |
|---|---|
| Policy | A rule stating what must be true. Approved by the committee. |
| Standard | The specific, measurable way a policy is met for this application. |
| Exception | An approved, time-limited deviation from a policy with compensating controls. |
| RTO / RPO | Recovery time objective / recovery point objective. |
| RACI | Responsible, Accountable, Consulted, Informed. |
| NIST CSF 2.0 | Cybersecurity Framework functions: Govern, Identify, Protect, Detect, Respond, Recover. |
