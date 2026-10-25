# GraphQL patterns for Experience Edge

All examples use variables throughout (Edge rejects mixed literal/variable input).

## Integrated GraphQL (on the rendering's ComponentQuery field)

The layout service substitutes `$datasource`, `$contextItem`, `$language`. Result lands in `fields.data`.

```graphql
query PromoList($datasource: String!, $language: String!) {
  datasource: item(path: $datasource, language: $language) {
    ... on PromoList {
      heading { jsonValue }
      promos: children(first: 20) {
        results {
          id
          name
          ... on PromoCard {
            heading { jsonValue }
            image { jsonValue }
            cta { jsonValue }
          }
        }
      }
    }
  }
}
```

Use `jsonValue` so SDK field components receive the shape they expect (editable in Pages). Template names in fragments (`... on PromoCard`) are the template item names with spaces removed.

## Edge search with pagination

```graphql
query ArticlesByTemplate($root: String!, $template: String!, $language: String!, $first: Int!, $after: String) {
  search(
    where: {
      AND: [
        { name: "_path", value: $root, operator: CONTAINS }
        { name: "_templates", value: $template, operator: CONTAINS }
        { name: "_language", value: $language }
      ]
    }
    first: $first
    after: $after
    orderBy: { name: "publishDate", direction: DESC }
  ) {
    total
    pageInfo { hasNext endCursor }
    results {
      id
      url { path }
      ... on Article { title { value } publishDate { value } }
    }
  }
}
```

Pass template and root as GUIDs without braces/dashes in lowercase if the endpoint requires — test on the preview endpoint first. `first` max effectively 1,000 entities per query including nested children; keep pages small (10–100).

## Fetching all pages at build time (retry-safe)

```ts
async function fetchAll<T>(run: (after?: string) => Promise<{ results: T[]; pageInfo: { hasNext: boolean; endCursor: string } }>) {
  const all: T[] = [];
  let after: string | undefined;
  do {
    const page = await run(after);
    all.push(...page.results);
    after = page.pageInfo.hasNext ? page.pageInfo.endCursor : undefined;
  } while (after);
  return all;
}
```

Wrap the client with retries for 429/502–504/520–524 with exponential back-off; at 80 req/s, a 5,000-page SSG build without retries will fail intermittently.

## Dictionary and site queries

Use the SDK's `SitecoreClient` methods rather than hand-written dictionary/site queries; they handle site resolution and caching.
