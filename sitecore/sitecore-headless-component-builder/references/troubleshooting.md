# Component troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Unknown component" / placeholder shows component name in red | `componentName` on rendering ≠ registered name (case-sensitive), or map not regenerated | Compare rendering field `componentName` with component map key; rerun map generation; rebuild |
| Renders locally, blank in Pages | Editing host not redeployed, editing secret mismatch, or component throws in editing mode | Check Deploy log for editing host; check browser console in Pages iframe; verify `SITECORE_EDITING_SECRET` |
| Fields render but aren't editable | Reading `.value` directly instead of SDK field components; or using `value` instead of `jsonValue` in GraphQL | Use `<Text field=…/>` etc.; switch query to `jsonValue` |
| Component missing from Pages toolbox | Not in site's Available Renderings (SXA) or placeholder settings don't allow it | Add to Presentation > Available Renderings; add to placeholder settings `Allowed Controls` |
| Datasource dialog shows wrong folder / no create option | `Datasource Location` empty or invalid; `Datasource Template` missing | Set location (e.g. `./Data` or `query:$site/*[@@name='Data']`); set template |
| Empty fields on live site, fine in preview | Datasource item not published or in non-final workflow state | Publish datasource (or publish with related items); check workflow |
| Integrated GraphQL stale after editing a child item | Edge stores snapshot at page publish | Republish page; consider `_PublishingGroupingTemplate` on the list item |
| 429 during build | Edge rate limit 80 req/s | Enable retries; reduce SSG `fallback` pages; ISR |
| Image 400/404 on Edge | Case mismatch in media path, or `remotePatterns` missing | Fix case; add `edge.sitecorecloud.io` to `images.remotePatterns` |
| Variant not appearing | Named export missing or variant item name ≠ export name | Export name must match variant item name |
| Rendering params ignored | Params template not set on rendering, or reading wrong prop | Set `Parameters Template`; read `props.params` |
