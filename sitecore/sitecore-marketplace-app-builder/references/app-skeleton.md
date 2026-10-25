# Next.js App Router skeleton

```
my-sc-app/
├─ app/
│  ├─ layout.tsx            # wraps everything in <MarketplaceProvider>
│  ├─ page.tsx              # standalone / full-screen landing
│  ├─ panel/page.tsx        # Pages context panel route
│  ├─ field/page.tsx        # custom field modal route
│  ├─ widget/page.tsx       # dashboard widget route
│  └─ api/                  # full-stack only: server routes holding secrets
│     └─ summarize/route.ts
├─ components/
│  ├─ marketplace-provider.tsx
│  ├─ not-in-sitecore.tsx   # shown when SDK init fails
│  └─ ui/…                  # shadcn/Blok components
├─ lib/
│  ├─ sitecore-context.ts   # resolve context ID from application.context
│  └─ graphql.ts            # typed helpers around xmc.authoring.graphql
├─ next.config.ts           # headers(): CSP frame-ancestors
└─ .env.local               # server-only secrets (full-stack)
```

## next.config.ts headers

```ts
import type { NextConfig } from 'next';

const frameAncestors = [
  "'self'",
  'https://*.sitecorecloud.io',
  'https://*.sitecore.cloud',
].join(' ');

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Content-Security-Policy', value: `frame-ancestors ${frameAncestors};` },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
        ],
      },
    ];
  },
};
export default nextConfig;
```

Confirm the exact Sitecore host domains your tenant uses (open the app inside Sitecore and read the parent origin in the console) and tighten the list. Do not send `X-Frame-Options: DENY`.

## Route pattern

Each extension route renders only after `ready`; shows `<NotInSitecore/>` on error; reads context; does one job. Keep panel UIs narrow (~320–400px) and field modals focused on a single choice.
