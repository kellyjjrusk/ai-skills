# sitecore-marketplace-app-builder

**Design and build Sitecore Marketplace apps that extend SitecoreAI: Pages context panels, custom fields, dashboard widgets, full-screen and standalone apps.**

Part of the [AI Skills Library](../../README.md) › [Sitecore AI Skills](../README.md) · Category: **Developer** · Platform: **SitecoreAI**

---

## Why this exists

In SitecoreAI you cannot drop custom .NET into the editing UI the way XP allowed. Custom field types, Content Editor warnings, ribbon buttons and Experience Editor buttons all need a new home. The supported answer is a **Marketplace app**:

- your own web app, hosted by you
- loaded by Sitecore in a sandboxed iframe at an extension point
- talking to Sitecore through the Marketplace SDK

**Custom apps** (private to your organization) need no Sitecore approval, which makes them the fast path for internal tooling.

The SDK is young (0.x) and its API keys change between releases. This skill gives you the architecture, the patterns that avoid common failures, and a disciplined "verify against the live reference" step.

## What the skill does

1. **Pins down the app:** the author's job to be done, extension point(s), APIs needed, client-side vs full-stack architecture, custom vs public.
2. **Scaffolds** with Sitecore's Next.js quickstart (Blok registry) or the Marketplace Starter.
3. **Implements against the SDK** with rules that prevent the usual failures:
   - initialize once, and resolve the Sitecore context ID from the application context
   - subscribe to Pages context instead of polling
   - reload the canvas after content mutations
   - use variables in Authoring GraphQL and check `errors[]`
   - store custom field values as JSON
   - request only the sandbox permissions you use, and keep secrets server-side
4. **Hosts** it with correct `frame-ancestors` CSP (never `X-Frame-Options: DENY`).
5. **Writes `APP-STUDIO-SETUP.md`** with the exact values to enter in Cloud Portal → App Studio, plus installation steps.
6. **Gives you a test script** for each extension point, including non-admin authors.
7. **For public apps**, walks the Sitecore security checklist and produces a compliance matrix with evidence.
8. **Maps XP customizations to Marketplace replacements.**

## What's inside

```
sitecore-marketplace-app-builder/
├── SKILL.md
├── README.md
└── references/
    ├── sdk-patterns.md          # init provider, context, Pages subscription, Authoring GraphQL, custom field, errors
    ├── app-skeleton.md          # Next.js App Router layout, per-extension routes, security headers
    └── security-checklist.md    # public-app compliance matrix template
```

This skill has no scripts. The deliverable is your app's code.

## Requirements

- Node.js 18+ and a Next.js toolchain
- A public HTTPS host (Vercel, Netlify, Azure Static Web Apps, Cloudflare, …)
- Cloud Portal access to App Studio to register and install the app (Organization Admin/Owner to install)
- The current Marketplace SDK reference (doc.sitecore.com or the npm/GitHub README)

---

## Using it with Claude

Example prompts:

- *"Build a Pages context panel that checks the open page for SEO problems (title length, missing meta description, image alt text)."*
- *"We had a custom 'Icon Picker' field type in XP. Rebuild it as a Marketplace custom field."*
- *"Make a dashboard widget showing pages stuck in Draft for more than 14 days."*
- *"We want to publish our app publicly. What do we need for the security checklist?"*

Claude verifies SDK query and mutation keys against the current reference before coding. You get complete app files, `APP-STUDIO-SETUP.md`, and a test checklist.

---

## Using it without Claude

1. **Choose the extension point** using the table in `SKILL.md` (context panel, custom field, dashboard widget, full screen, standalone).
2. **Scaffold:**
   ```bash
   npx create-next-app@latest my-sc-app --ts --app --eslint
   cd my-sc-app
   npx shadcn@latest add https://blok.sitecore.com/r/marketplace/next/quickstart-with-client-side-xmc.json
   ```
   If the command has changed, use the "Quick start (CLI)" page in Sitecore's Marketplace SDK docs.
3. **Build from `references/app-skeleton.md`** (layout, provider, routes, `next.config.ts` headers) and **`references/sdk-patterns.md`** (calls). Confirm every query/mutation key against the live SDK reference.
4. **Deploy** to an HTTPS host.
5. **Register** in Cloud Portal → App Studio → Create app → Custom: set extension points with route paths, the deployment URL, API access and permissions. Then install to your organization and environment(s).
6. **Test** each extension point as an admin and as a regular author.
7. **Public app?** Fill `references/security-checklist.md` with evidence for each requirement.

### Use with another AI assistant

Provide `SKILL.md` and the three references as context, plus the current SDK reference page. Instruct it to confirm API keys against that page.

---

## XP → Marketplace replacement map

| XP customization | Marketplace replacement |
|---|---|
| Custom Content Editor field type | Custom field extension point |
| Content Editor warning / gutter icon | Pages context panel check |
| Ribbon command | Full-screen app or context panel action |
| SPE report for authors | Dashboard widget or full-screen app |
| Experience Editor custom button | Pages context panel |

## Important notes and limits

- **The SDK is 0.x.** Query/mutation names in `sdk-patterns.md` show the shape and must be verified. The file marks the most volatile keys.
- Apps run in a sandboxed iframe. Pop-ups, clipboard and downloads are blocked unless enabled in App Studio.
- Sitecore does not host apps. Your host must serve HTTPS and allow framing by Sitecore origins.
- Changing extension-point groups or API access after installation may require re-authorizing the app.

## Changelog

- **1.0.0** (2026-10): initial release.
