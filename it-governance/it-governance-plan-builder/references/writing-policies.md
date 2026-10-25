# Writing policies and standards that get followed

## Policy vs standard

| | Policy | Standard |
|---|---|---|
| Answers | **What** must be true | **How** it is achieved here |
| Example | All users must log in to the CMS securely. | The CMS sits in an application tier; only directory-authenticated users can reach its URL, and only through VPN. |
| Changes | Rarely; approved by the committee | As the platform, tools or hosting change |
| Audience | Everyone in scope | People who implement and operate it |
| Measured by | Whether the standards are met | Specific, checkable indicators |

Optional third layer: **procedures** (step-by-step runbooks) linked from standards. Keep them out of the plan itself.

## Requirement language

Use consistent keywords (adapted from RFC 2119):
- **MUST / MUST NOT** — mandatory. Deviation requires an approved exception.
- **SHOULD / SHOULD NOT** — expected; deviation needs a documented reason, not a formal exception.
- **MAY** — optional.

Avoid "try to", "where possible", "best effort" in policy statements — they make compliance unmeasurable. If something is conditional, state the condition.

## Make every statement measurable

| Weak | Strong |
|---|---|
| Access should be reviewed regularly. | Privileged access MUST be reviewed quarterly; all access semi-annually. |
| Keep the system patched. | Critical security patches MUST be applied within 7 days of release. |
| Backups must be taken. | Production data MUST be backed up daily with a tested restore at least annually (RPO 24h, RTO 8h). |

## One owner, one accountable

The **owner** keeps the policy current and reports on it. The **accountable** role approves it and answers for it. They can be the same person in small organizations, but both must be named.

## Exceptions

A policy without an exceptions process gets ignored silently instead of broken openly. Every exception records: policy ID, requester, justification, compensating controls, risk owner, approver, and expiry (maximum 12 months). Review open exceptions at every committee meeting.

## Size and scope

- Aim for 10 policies first. Add more only when the first ten are at least "Partial" with evidence.
- One policy per topic; 3–5 statements per policy; standards as long as they need to be.
- If a statement can't be followed today, either fund the gap with a dated action or don't publish the statement yet.

## Review

Each policy carries its own review interval (6 or 12 months typical). Out-of-cycle triggers: major incident, audit finding, new regulation, hosting or vendor change, major upgrade.
