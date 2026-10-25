# Common Sitecore log signatures

Class: **H** known-harmless (usually ignorable) · **S** symptom (find the cause) · **R** root cause.

| Signature (normalized) | Class | Meaning | Action |
|---|---|---|---|
| `Timing threshold exceeded for web page. Milliseconds: N. Threshold: N. Page URL: /x` | S | Request exceeded `StopMeasurements` threshold | Group by URL; inspect renderings on that page; correlate with item threshold |
| `Item threshold exceeded for web page. Items accessed: N` | R/S | Page touched many items — tree walking | Replace descendant walks/queries with search or cached data |
| `Memory threshold exceeded for web page. Memory used: N KB` | S | Large allocations per request | Large media, big lists, string building |
| `Memory usage exceeded the MemoryMonitor threshold` | S | Process private bytes above `MemoryMonitor` threshold | Check cache sizes vs RAM; leaks in custom statics |
| `**** Shutdown message ****` / `Sitecore shutting down` + `Shutdown reason: ConfigurationChange` | R | Someone/something changed config/bin → recycle | Find deploy/file change at that time |
| `Shutdown reason: HostingEnvironment` / `IdleTimeout` | H/S | IIS idle timeout or host recycle | Disable idle timeout on prod; warm-up |
| `Shutdown reason: BinDirChangeOrDirectoryRename` | R | Files changed in bin | Deployment or AV scanner touching bin |
| `Cache created: 'x' (max size: N, running total: N)` | H | Startup info | Use running total vs RAM for sizing |
| `Cache 'x' cleared` repeated | S | Clearing storms (publish, custom code) | Find trigger; scope clears per site |
| `Exception while handling event Sitecore.Eventing.Remote.*` | R | Remote event processing failing on CD | Fix exception; stale caches otherwise |
| `EventQueue ... Timeout expired` / `SqlException ... EventQueue` | R | EventQueue table bloat or blocking | Cleanup agent `CleanupEventQueue`, index, interval |
| `SolrConnectionException` / `Unable to connect to the remote server` (Solr) | R | Solr down/unreachable/timeouts | Index skill |
| `Could not resolve type` / `Could not create instance of type` | R | Config references missing assembly/type after deploy | Fix config or deploy missing DLL |
| `The ID ... is not a valid ID` / `Rendering ... not found` | S | Broken datasource/rendering references | Broken-links report |
| `ManagedPoolThread ... Job started: Index_Update` storms | S | Indexing pressure | Index strategy tuning |
| `Login failed for user` (SQL) | R | Credential/connection string issue | Fix connection string / secret rotation |
| `ERROR Application error` + `HttpException ... was not found` | H/S | 404 noise from bots | Filter; ensure 404 handled without exception |
| `A potentially dangerous Request.Path value was detected` | H | Bot probes | Ignore unless from legitimate traffic; WAF |
| `WARN Could not compute value for ComputedIndexField` | S | Computed field throwing for some items | Fix field code; check item types |
| `Health.Monitor` / `HealthMonitor` cache size warnings | S | Cache near limits | Tune per caching.md |
| `Unhandled exception ... OutOfMemoryException` | R | Process out of memory | Capture dump; check caches and large media |
| `Thread was being aborted` around shutdown | H | Side effect of recycle | Look at recycle reason instead |
| `Analytics ... xConnect ... failed` | S/R | xConnect unreachable / cert issues | Check certs, xConnect logs |
