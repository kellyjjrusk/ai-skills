# Experience Edge → Next.js on-demand revalidation

Problem: Edge has the new content, the site shows old content. The front-end is serving cached SSG/ISR output.

## Options (simplest first)

1. **Shorter ISR window** — `revalidate: 60` on page props / route segment. Cheap, eventually consistent.
2. **Edge webhook → revalidation route** — Edge calls your endpoint after publish; you revalidate the affected paths/tags. Near-instant.
3. **SSR for volatile pages** — no cache; costs more per request and hits Edge rate limits harder.

## Webhook route (App Router)

```ts
// app/api/revalidate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { revalidatePath, revalidateTag } from 'next/cache';

export async function POST(req: NextRequest) {
  const secret = req.headers.get('x-webhook-secret');
  if (!secret || secret !== process.env.EDGE_WEBHOOK_SECRET) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }
  const body = await req.json().catch(() => ({}));
  // Edge payload contains updated entities; shape varies by webhook mode — log once and map.
  const updates: Array<{ identifier?: string; entity_definition?: string; entity_culture?: string }> = body?.updates ?? [];
  const paths = new Set<string>();
  for (const u of updates) {
    if (u.entity_definition === 'LayoutData' && u.identifier) {
      // identifier often encodes item id + language; map to route via your own lookup or revalidate by tag
      revalidateTag(`item:${u.identifier}`);
    }
  }
  if (updates.length === 0 || body?.invocation_id === undefined) revalidatePath('/', 'layout');
  paths.forEach((p) => revalidatePath(p));
  return NextResponse.json({ ok: true, count: updates.length });
}
```

Tag your page fetches with `item:<id>` so a webhook can target them. Register the webhook through the Experience Edge Admin API (token from the Deploy app / Edge admin credentials); webhooks are environment-wide, not per site. Verify the current webhook registration API and payload format on doc.sitecore.com before implementing — the payload fields above are illustrative.

## Checks when it still doesn't refresh

- Webhook returns 200? (check Edge webhook execution/logs and your host's function logs)
- Secret matches?
- CDN in front of Next.js also caching? Purge or set `s-maxage` appropriately.
- Page was actually republished (snapshot model): child item edits require page republish or `_PublishingGroupingTemplate`.
