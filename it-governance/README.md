# IT Governance Skills

Skills for creating, running and maturing IT governance: committees, policies, standards, communication and compliance. They are **application-agnostic** and work for a CMS, ERP, CRM, collaboration suite, data platform or custom application, on any hosting model.

Part of the [AI Skills Library](../README.md). New skills are added over time.

---

## Skills

| Skill | What it does | Bundled tooling |
|---|---|---|
| [**it-governance-plan-builder**](./it-governance-plan-builder/) | Builds a governance plan for any application: committee, RACI, escalation, policies (what) and standards (how) tailored to the app and hosting model, communication plan, adoption roadmap and policy register. Choose a **Core** pack (10 application policies) or a **Robust** pack (28 policies including networking, DevOps, security, BC/DR, privacy, vendor risk, cloud and AI usage). | Policy catalog (JSON), `build_governance_pack.py` generator, policy-writing guide, app tailoring guide, communication templates |

## Approach

Every skill in this category follows the same principles:

1. **Plan before policy.** Name the committee and the communication plan first; policies without owners and audiences don't stick.
2. **Separate the what from the how.** Policies state what must be true; standards state how it's done for a specific platform.
3. **Start small.** Ten policies at compliance beat fifty on paper. Aim for a working C+, then improve.
4. **Measure.** Every policy has an owner, an accountable role, indicators and a review date.
5. **Be honest about compliance.** Plans support obligations; audits certify them.

## Layout

```
it-governance/
├── README.md                       ← you are here
└── it-governance-plan-builder/
    ├── README.md
    ├── SKILL.md
    ├── assets/policy-catalog.json
    ├── references/
    └── scripts/build_governance_pack.py
```

## Using these skills

Install and usage instructions are in the [root README](../README.md#using-the-skills-with-claude). Each skill's README explains how to use it with Claude and on its own (scripts, templates, other AI assistants).

## License

MIT. See the [LICENSE](../LICENSE) file at the root of the AI Skills Library.
