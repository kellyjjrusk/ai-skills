# JSS → Content SDK mapping

Verify against the current upgrade guide before relying on any single row; symbols shift between minor versions. When a row says "check scaffold", open the same file in a fresh `create-content-sdk-app` project and copy its pattern.

## Packages

| JSS | Content SDK |
|---|---|
| `@sitecore-jss/sitecore-jss-nextjs` | `@sitecore-content-sdk/nextjs` |
| `@sitecore-jss/sitecore-jss-react` | (re-exported by `@sitecore-content-sdk/nextjs`; remove) |
| `@sitecore-jss/sitecore-jss` | `@sitecore-content-sdk/core` (usually transitive; remove direct dep) |
| `@sitecore-jss/sitecore-jss-cli` | `@sitecore-content-sdk/cli` |
| `@sitecore-jss/sitecore-jss-dev-tools` | `@sitecore-content-sdk/cli` |
| `@sitecore-cloudsdk/personalize` / `events` | `@sitecore-content-sdk/personalize`, `@sitecore-content-sdk/events`, `@sitecore-content-sdk/analytics-core` |

## Configuration

| JSS | Content SDK |
|---|---|
| `src/temp/config.js` (generated) | `sitecore.config.ts` using `defineConfig` |
| `scjssconfig.json`, `scripts/generate-config.ts` | delete; values come from `sitecore.config.ts` + env |
| `scripts/generate-component-builder` / `temp/componentBuilder.ts` | generated component map (`.sitecore/component-map.ts` or as the scaffold names it) via Content SDK CLI |
| `scripts/bootstrap.ts` | delete; replaced by CLI scripts in `package.json` |
| `package.json > config.sitecoreConfigPath` etc. | delete |

## Runtime

| JSS | Content SDK |
|---|---|
| `GraphQLLayoutService`, `GraphQLDictionaryService`, `layoutServiceFactory`, `dictionaryServiceFactory` | `SitecoreClient` (`lib/sitecore-client.ts`) — `getPage`, `getDictionary`, `getErrorPage`, etc. |
| `sitecorePagePropsFactory` + page-props plugins | `client.getPage()` in `getStaticProps`/`getServerSideProps` or App Router server components |
| `src/lib/middleware/plugins/*.ts` + `middleware.ts` loop | `defineMiddleware(...)` composing `LocaleMiddleware`, `MultisiteMiddleware`, `RedirectsMiddleware`, `PersonalizeMiddleware` + custom |
| `EditingRenderMiddleware`, `EditingConfigMiddleware` API routes | provided by SDK; keep the API route files the scaffold generates |
| `SitecoreContext` / `useSitecoreContext` | `SitecoreProvider` / `useSitecore` (check scaffold for exact names in your version) |
| `isEditorActive`, `EditFrame`, chromes | remove — Experience Editor not supported |
| `withDatasourceCheck` | still available; confirm import path |
| `Text`, `RichText`, `Image`, `Link`, `DateField`, `File`, `Placeholder` | same names from `@sitecore-content-sdk/nextjs` |
| `NextImage` | `NextImage` from `@sitecore-content-sdk/nextjs` |

## Environment variables

| JSS | Content SDK | Notes |
|---|---|---|
| `SITECORE_EDGE_CONTEXT_ID` | `SITECORE_EDGE_CONTEXT_ID` | server-side |
| — | `NEXT_PUBLIC_SITECORE_EDGE_CONTEXT_ID` | client-side calls (personalize/events) |
| `SITECORE_SITE_NAME` / `JSS_APP_NAME` | `NEXT_PUBLIC_DEFAULT_SITE_NAME` | |
| `JSS_EDITING_SECRET` / `SITECORE_EDITING_SECRET` | `SITECORE_EDITING_SECRET` | must match CM |
| `GRAPH_QL_ENDPOINT`, `SITECORE_API_KEY`, `SITECORE_API_HOST` | local-container/non-Edge only; prefer Edge context ID | |
| `GRAPH_QL_SERVICE_RETRIES` | retry options on client config | |
| `DEBUG=sitecore-jss:*` | `DEBUG=content-sdk:*` | |

Every env var must be set in three places: local `.env.local`, the SitecoreAI Deploy app (editing host), and the delivery host (Vercel/Netlify/other). A missing delivery-host var is the most common "works locally, 500 in prod" cause.
