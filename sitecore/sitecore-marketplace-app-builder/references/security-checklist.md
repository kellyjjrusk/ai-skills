# Public app security compliance matrix

Re-read the live checklist (doc.sitecore.com → Marketplace → Sitecore security checklist) and note its revision date; it is revised periodically.

| Area | Requirement | How we meet it | Evidence |
|---|---|---|---|
| Transport | TLS per Mozilla server-side TLS guidance | | SSL Labs report |
| APIs | Only supported Sitecore APIs/SDKs | | dependency list |
| Endpoints | Stable, documented, shareable on request | | API doc link |
| Headers | OWASP security headers enabled | | securityheaders.com report |
| Cookies | Secure, HttpOnly, SameSite set per OWASP | | |
| AuthN/Z | Every exposed endpoint authenticates and authorizes | | code refs, tests |
| Secrets | No secrets client-side; rotated; stored in vault | | |
| Dependencies | Vulnerability scanning in CI | | scan report |
| Testing | Security testing (SAST/DAST/pen test) performed | | report |
| Logging | Security-relevant events logged, no sensitive data in logs | | |
| Incidents | Notify Sitecore within 72h of confirmed incident | | runbook |
| Contact | Monitored security contact email | | alias |
| Data | Data handling/retention documented; privacy policy | | |
