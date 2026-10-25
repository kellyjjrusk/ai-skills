# How Sitecore evaluates access

## Rights
`item:read`, `item:write`, `item:rename`, `item:create`, `item:delete`, `item:admin` (change security), `language:read`, `language:write`, `site:enter`, `insert:show`, `field:read`/`field:write` (field-level), workflow: `workflowState:delete`, `workflowState:write`, `workflowCommand:execute`.

## Permission values per rule
Allow, Deny, or not set — plus inheritance control (Allow/Deny inheritance) per right, and propagation: **Entity** (this item only), **Descendants** (children down, not this item), **Any** (both).

## Evaluation (simplified, faithful to documented rules)
1. Administrators (`IsAdministrator`) bypass item security entirely — and bypass workflow (no new version on edit of a final-state item, no state move).
2. For each right, Sitecore walks from the item up the tree until a rule decides it, unless inheritance is denied at some level.
3. At a given item, rules for the **user account** beat rules for the user's **roles**.
4. Among roles at the same level: **Deny beats Allow**. One denying role hides the item even if five others allow.
5. An explicit rule on the item beats an inherited rule from an ancestor.
6. A role that is a member of another role accumulates that role's rights.
7. `Everyone` applies to all accounts in its domain context; `sitecore\Everyone` vs `extranet\Everyone` matter.

## Worked example
User `sitecore\jdoe` in roles `Authors` and `Brand Reviewers`.
- `/content/Site` : `Authors` Allow read/write (Any)
- `/content/Site/Legal` : `Brand Reviewers` Deny write (Any)
Result on `/content/Site/Legal/Terms`: write is **denied** (deny on a role at a nearer level; no user-level rule overrides). Fix: remove the deny and stop granting write to Brand Reviewers on Legal, or grant `jdoe` a user rule (discouraged), or split roles.

## Workflow visibility
A command is visible only if the user has `workflowState:write` on its state (or holds the item lock), `workflowCommand:execute` on the command, and read on the command item. Denying read on a broad role hides the whole workflow for multi-role users.

## Good role design
- Role-per-capability, composed: `Site X Authors`, `Site X Approvers`, `Site X Publishers`, plus Sitecore client roles (`Sitecore Client Authoring`, `Sitecore Client Publishing`).
- Grant at the highest correct node with inheritance; avoid explicit deny.
- Never grant `Sitecore Client Securing` or `Developing` to content roles.
- Keep admin count to named break-glass accounts.
