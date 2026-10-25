# Marketplace SDK patterns

Shapes below reflect the 0.x SDK (`@sitecore-marketplace-sdk/client`, `/xmc`, `/ai`). **Confirm every query/mutation key against the current QueryMap / MutationMap reference before use** — keys are the most volatile part of the SDK.

## Install

```bash
npm i @sitecore-marketplace-sdk/client @sitecore-marketplace-sdk/xmc
# optional
npm i @sitecore-marketplace-sdk/ai
```

## Initialize once (React hook)

```tsx
'use client';
import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { ClientSDK } from '@sitecore-marketplace-sdk/client';
import { XMC } from '@sitecore-marketplace-sdk/xmc';

type Ctx = { client: ClientSDK | null; error: string | null; ready: boolean };
const MarketplaceContext = createContext<Ctx>({ client: null, error: null, ready: false });

export function MarketplaceProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Ctx>({ client: null, error: null, ready: false });
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;            // guard against React strict-mode double run
    started.current = true;
    ClientSDK.init({ target: window.parent, modules: [XMC] })
      .then((client) => setState({ client, error: null, ready: true }))
      .catch((e) => setState({ client: null, error: String(e?.message ?? e), ready: true }));
  }, []);

  return <MarketplaceContext.Provider value={state}>{children}</MarketplaceContext.Provider>;
}

export const useMarketplace = () => useContext(MarketplaceContext);
```

If the page is opened outside Sitecore (no parent frame), init fails — render a clear "Open this app from Sitecore" message rather than a blank screen.

## Application context (get the Sitecore context ID)

```ts
const { data: app } = await client.query('application.context');
// app.resourceAccess / app.resources hold per-environment entries; find the SitecoreAI one
// and read its context ID (property names: check the reference — commonly `context.preview`/`context.live`
// or `tenantId`/`contextId`).
```

## Subscribe to Pages context (context panel)

```ts
const unsubscribe = await client.query('pages.context', {
  subscribe: true,
  onSuccess: (page) => setPage(page),   // current page id, language, site, version
});
// call unsubscribe() on unmount if returned
```

## Authoring GraphQL (read/write content)

```ts
const res = await client.mutate('xmc.authoring.graphql', {
  params: {
    query: { sitecoreContextId: contextId },
    body: {
      query: `mutation UpdateTitle($id: ID!, $lang: String!, $value: String!) {
        updateItem(input: { itemId: $id, language: $lang, fields: [{ name: "Title", value: $value }] }) {
          item { itemId }
        }
      }`,
      variables: { id: page.pageInfo?.id, lang: page.pageInfo?.language, value: newTitle },
    },
  },
});
if (res?.data?.errors?.length) throw new Error(res.data.errors[0].message);
await client.mutate('pages.reloadCanvas');   // confirm key name
```

## Sites / pages queries (xmc)

```ts
const sites = await client.query('xmc.sites.listSites', { params: { query: { sitecoreContextId: contextId } } });
```

## Custom field

```ts
const { data: field } = await client.query('host.field');        // current value (confirm key)
await client.mutate('host.setValue', { params: JSON.stringify(value) });  // confirm key
await client.mutate('host.closeApp');                             // confirm key
```

## Errors

Wrap every call; surface `error.message` to the author in plain words and log details to the console. Distinguish: not initialized, not authorized (app lacks API access in App Studio), GraphQL errors, network errors.
