# MIGRATION-PLAN.md — <app name>

## 1. Targets
| Item | Current | Target |
|---|---|---|
| SDK | JSS x.y | Content SDK x.y |
| Next.js | | |
| React | | |
| Node | | |
| Router | Pages | Pages / App |

Path chosen: fresh scaffold + port | in-place. Reason: …

## 2. Package swap
| Remove | Add | Version |
|---|---|---|

## 3. File actions
| File | Action (keep / replace from scaffold / port / delete) | Notes |
|---|---|---|

## 4. Components
| Component | Uses EE/chromes? | Custom GraphQL? | Ported | Verified in Pages |
|---|---|---|---|---|

## 5. Middleware & plugins
| JSS plugin | Purpose | Content SDK replacement |
|---|---|---|

## 6. Environment variables
| Old | New | Local | Deploy app | Delivery host |
|---|---|---|---|---|

## 7. Editing host verification
- [ ] Editing secret matches CM
- [ ] Pages canvas renders
- [ ] Inline edit + save works
- [ ] Add component from toolbox
- [ ] Personalization variants render

## 8. Test plan
- Build: `npm run build` clean, zero `sitecore-jss` refs
- Routes: home, deep page, 404, 500, multilingual, personalized
- Performance: SSG build completes under Edge rate limit with retries

## 9. Author impact
- Experience Editor removed → Pages only
- Content Editor preview not supported

## 10. Rollback
- Keep JSS branch deployable until Content SDK passes UAT
- Deploy app: redeploy previous deployment ID if needed
