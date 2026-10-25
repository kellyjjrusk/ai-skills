# Disposition matrix

Effort sizes (per item, one experienced developer): S = 2–8h, M = 8–24h, L = 24–80h, XL = 80h+. Adjust after reviewing real code; these are defaults for the first estimate.

| Category | Signal | Default disposition | Size | Notes |
|---|---|---|---|---|
| MVC view rendering (`.cshtml`, no controller) | View rendering item, Razor file | Rebuild (headless) | S–M | Port markup to TSX; map fields to Content SDK field components |
| MVC controller rendering | `: Controller`, `SitecoreController` | Rebuild (headless) | M–L | Logic moves to GraphQL query, rendering contents resolver, or Next.js server code |
| SXA MVC component | `Sitecore.XA.*` refs | Rebuild (headless SXA) | S–M | Many have headless SXA equivalents out of the box |
| `httpRequestBegin` / `mvc.*` processor | config patch | Move to edge/app | M–L | Next.js middleware |
| `getContentEditorWarnings`, `uiGetMasters`, item:saved handlers | config patch | Keep (CM-side) | S | Re-validate on SitecoreAI CM |
| Scheduled agent / task | `<agent>` or `/sitecore/system/Tasks` | Keep (CM) or Move to app | S–M | Long-running jobs better in external scheduler |
| Custom field type | `Sitecore.Shell.Applications.ContentEditor` | Replace | M–L | Marketplace custom field app |
| `ContentSearch` query at render time | `IProviderSearchContext` in rendering path | Replace | L | Sitecore Search, or GraphQL `search` on Edge for simple cases |
| Computed index field | `IComputedIndexField` | Replace | M | Re-model in Sitecore Search crawler/extractor |
| `Tracker.Current`, goals, profiles | `Sitecore.Analytics` | Replace | L–XL | SitecoreAI personalize / CDP; behavior is not 1:1 |
| xConnect client, marketing automation | `Sitecore.XConnect` | Replace | XL | External CDP/MA |
| EXM | `Sitecore.EmailCampaign` | Replace | L | External ESP |
| Sitecore Forms | `Sitecore.ExperienceForms` | Replace | M–L | SitecoreAI Forms or third-party |
| WFFM | `Sitecore.Forms.*` | Replace | M–L | Long dead; replace |
| Commerce (XC) | `Sitecore.Commerce` | Replace | XL | Composable commerce partner |
| Unicorn / TDS | config or `.scproj` | Replace | S–M | SCS |
| Glass Mapper / Synthesis | package refs | Retire | M | Headless removes the need |
| Coveo for Sitecore | `Coveo.*` | Replace | L | Coveo headless or Sitecore Search |
| Custom WebAPI on CD | `ApiController` | Move to edge/app | M–L | Next.js API routes or separate service |
| Session state, `HttpContext.Current.Session` | code | Move to edge/app | M | Cookies/edge storage |
| Item-level security for end users | `__Security` on content | Replace | L | Delivery is anonymous; implement auth in front-end |
| Multiple sites sharing a start item | site config | Rebuild | M | Not supported on Edge |
| Aliases, wildcard items | content | Rebuild | S–M | Next.js routes / redirects map |
| Content migration | item counts | Move | by volume | Script with SCS/CLI or Authoring GraphQL; budget 1 day per 10k items plus QA |
