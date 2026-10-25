---
name: sitecore-marketplace-app-builder
description: Design and build Sitecore Marketplace apps (custom or public) that extend SitecoreAI — Pages context panel, custom field, dashboard widget, full-screen and standalone extension points — using the Marketplace SDK (client, xmc, ai packages), including Authoring GraphQL calls, Pages events, auth architecture, hosting, Cloud Portal App Studio registration and the public-app security checklist. Use whenever the user wants to extend SitecoreAI, build a Sitecore plugin/app/extension, a custom field type for XM Cloud, a Pages sidebar tool, an AI helper inside Sitecore, a dashboard widget, or asks how to replace an XP Content Editor customization in SitecoreAI.
---

# Sitecore Marketplace App Builder

In SitecoreAI you cannot drop custom .NET into the editing UI the way XP allowed. The supported way to add author-facing tools — custom fields, Pages panels, dashboards, AI helpers — is a Marketplace app: your own web app, hosted by you, loaded by Sitecore in a sandboxed iframe at an extension point, talking to Sitecore through the Marketplace SDK. Custom apps (private to your organization) need no Sitecore approval, which makes them the fast path for internal tooling.

## Operating constraint: no CMS or Cloud Portal access

You cannot register the app, install it, or open Pages. You produce the app code, the configuration values to enter in App Studio, and a test script. The user performs the portal steps and reports back what they see (screenshots, console errors).

## The SDK is 0.x — verify before coding

Before writing SDK calls, web-search `Sitecore Marketplace SDK QueryMap MutationMap` and open the current reference on doc.sitecore.com (or the package README on npm/GitHub). Query and mutation keys change between 0.x releases. Use `references/sdk-patterns.md` as the shape, then confirm each key you use against the live reference. Say in the deliverable which SDK version you targeted.

## Workflow

### 1. Pin down the app

Ask (or infer) and write down:
- **Job to be done** for the author, in one sentence.
- **Extension point(s)**:
  | Extension point | Where it shows | Good for |
  |---|---|---|
  | Pages context panel | Right panel in Pages builder | Page-level tools: SEO checks, AI summaries, analytics for the open page |
  | Custom field | Modal from a field in Pages / content | Pickers: icons, DAM assets, external product IDs, structured JSON |
  | Dashboard widget | SitecoreAI site dashboard | KPIs, status, queues |
  | Full screen (SitecoreAI) | Apps menu in SitecoreAI nav | Admin tools, bulk ops, reports |
  | Standalone | Cloud Portal, full screen | Org-wide tools not tied to an environment |
- **APIs needed**: none, SitecoreAI APIs (Authoring GraphQL, sites, pages), AI skills API.
- **Architecture**: client-side only (SDK calls from browser, simplest) vs. full-stack (your server calls Sitecore APIs with an auth token — needed for secrets, third-party keys, heavy work). If the app holds any third-party secret, it must be full-stack.
- **Custom vs public**: start custom. Public requires the Sitecore security checklist and approval.

### 2. Scaffold

Preferred: Sitecore's Next.js quickstart via Blok registry:

```bash
npx create-next-app@latest my-sc-app --ts --app --eslint
cd my-sc-app
npx shadcn@latest add https://blok.sitecore.com/r/marketplace/next/quickstart-with-client-side-xmc.json
```

Or clone the Marketplace Starter (it demonstrates all five extension points). Check doc.sitecore.com "Quick start (CLI)" for the current command if this fails.

Generate full files per the user's preference for complete code. Use `references/app-skeleton.md` for the file layout, SDK init hook, extension-point routing and error handling.

### 3. Implement against the SDK

Rules that prevent the common failures:
- **Initialize once** at app root; the SDK handshake with the parent frame fails if two clients race. Expose the client through a React context/hook.
- **Get context first**: `application.context` gives the app's installation context, including the **Sitecore context ID** for the environment. Every SitecoreAI API call needs it.
- **Subscribe, don't poll** for Pages state (`pages.context` with subscribe) so the panel updates when the author navigates.
- **After mutating content**, tell Pages to refresh the canvas (the SDK exposes a reload mutation) — otherwise authors think the change failed.
- **Authoring GraphQL** writes go through the SDK's xmc authoring mutation, scoped by the context ID. Use variables, check `errors[]` in the response, and handle partial failure.
- **Custom field value** is a string Sitecore stores; serialize structured data as JSON and validate on read. Return it through the SDK's field-value mutation and close the modal.
- **Sandbox**: pop-ups, clipboard and downloads are blocked unless enabled in App Studio permissions. Request only what you use.
- **No secrets in the browser.** Full-stack apps verify the request originates from the Sitecore session per the SDK's server-side auth guidance.

### 4. Host it

Any public HTTPS host (Vercel, Netlify, Azure Static Web Apps, Cloudflare). Sitecore does not host apps. Required: HTTPS, stable URL, allow framing by Sitecore origins. Set `Content-Security-Policy: frame-ancestors` to the Sitecore domains rather than removing framing protection. Local dev: App Studio can point to `http://localhost:3000` for your own testing.

### 5. Register and install (user does this — give exact values)

Produce `APP-STUDIO-SETUP.md` with:
1. Cloud Portal → App Studio → Create app → **Custom**.
2. App name, description, icon.
3. Extension points to enable and, for each, the route path in your app (e.g. `/panel`, `/field`, `/widget`).
4. Deployment URL.
5. API access toggles (SitecoreAI APIs, AI).
6. Permissions (clipboard, pop-ups) only if used.
7. Install to organization → choose environment(s) → grant team members access.
8. Note: changing extension-point groups or API access after install can require the app to be updated/re-authorized.

### 6. Test script

Give the user a checklist to run in each extension point: loads without console errors, context shows correct site/page, a read call returns data, a write call persists and canvas refreshes, permission-denied paths show a friendly message, works for a non-admin author.

### 7. Public app (only if asked)

Walk the Sitecore security checklist (`references/security-checklist.md`): TLS per Mozilla guidance, OWASP security headers and cookie attributes, authenticate/authorize every endpoint, only supported APIs, documented stable endpoints, incident notification within 72 hours, a monitored security contact. Produce a compliance matrix with evidence per item.

## Replacing XP customizations

Map old → new when the user is migrating:
| XP customization | Marketplace replacement |
|---|---|
| Custom Content Editor field type | Custom field extension point |
| Content Editor warning / gutter | Pages context panel check |
| Custom ribbon command | Full-screen app or context panel action |
| SPE report shown to authors | Dashboard widget or full-screen app |
| Experience Editor custom button | Pages context panel |

## References

- `references/sdk-patterns.md` — init, context, queries, mutations, subscriptions (verify keys)
- `references/app-skeleton.md` — Next.js file layout with per-extension routes
- `references/security-checklist.md` — public-app compliance matrix template
