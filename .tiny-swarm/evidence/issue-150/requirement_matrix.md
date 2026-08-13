# Issue #150 Requirement Matrix

Status vocabulary follows `documentation/process/verification-state-policy.md`.
`VERIFIED_LOCAL` means repository evidence exists; it does not mean live
deployment, browser, TLS, DNS, or SonarQube success.

| ID | Requirement | Implementation / evidence | Verification | Status |
|---|---|---|---|---|
| R150-01 | Dedicated operator dashboard route | `traefik-dashboard` router for `Host(traefik.tsw.local)` | compose/static tests | VERIFIED_LOCAL |
| R150-02 | Route uses HTTPS | router uses `websecure` and `tls: {}` | compose/static tests | VERIFIED_LOCAL |
| R150-03 | Route targets Traefik dashboard internally | service is `api@internal` | compose/static tests | VERIFIED_LOCAL |
| R150-04 | Authentication is mandatory | BasicAuth middleware is attached to router | compose/static tests | VERIFIED_LOCAL |
| R150-05 | Credentials remain operator-managed | external Docker secret and users-file reference only | config inspection/tests | VERIFIED_LOCAL |
| R150-06 | Raw credentials are absent | no htpasswd values in repository or evidence | repository inspection/tests | VERIFIED_LOCAL |
| R150-07 | Secret name is configurable and deterministic | `TSW_TRAEFIK_GUI_USERS_SECRET_NAME` with safe default | contract/composition/installer tests | VERIFIED_LOCAL |
| R150-08 | Insecure API mode is forbidden | no `api.insecure` flag/configuration | compose/static tests | VERIFIED_LOCAL |
| R150-09 | No additional dashboard port is introduced | existing `80`/`443` ingress only | compose inspection/tests | VERIFIED_LOCAL |
| R150-10 | Service Access remains intact | existing stack/routes untouched by dashboard addition | regression tests/docs | VERIFIED_LOCAL |
| R150-11 | TLS/auth prerequisites fail closed | external secret and TLS references are required | contract/docs evidence | VERIFIED_LOCAL |
| R150-12 | Rollback is bounded | remove dashboard router/auth reference; retain ingress and Service Access | ADR/docs | VERIFIED_LOCAL |
| R150-13 | Architecture boundaries are preserved | Traefik remains infrastructure/deployment concern | ADR/arc42 review | VERIFIED_LOCAL |
| R150-14 | Security model aligns with #123/#126/#128 | admin-surface, secret, and review governance referenced | workflow/ADR review | VERIFIED_LOCAL |
| R150-15 | Static and targeted regression coverage exists | compose, composition, installer, secret-management tests | WSL test results | VERIFIED_LOCAL |
| R150-16 | Full local quality gate passes | required WSL quality command | `quality_gate.py quality` | VERIFIED_LOCAL |
| R150-17 | Live TLS/DNS/browser behavior is proven | requires explicit live run | live evidence contract | NOT_VERIFIED |
| R150-18 | Fresh/reconcile/update behavior is proven live | requires explicit live run | #125 contract handoff | NOT_VERIFIED |
| R150-19 | No live mutation occurs in default execution | workflow and tests use static/mocked checks | workflow review | VERIFIED_LOCAL |

The two live requirements remain intentionally unverified until explicit live
consent and a disposable/recoverable Linux or WSL2 target are available.
