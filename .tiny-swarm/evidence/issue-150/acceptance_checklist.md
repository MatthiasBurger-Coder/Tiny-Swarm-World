# Issue #150 Acceptance Checklist

## Local implementation

- [x] Dedicated `traefik.tsw.local` dashboard route exists in desired config.
- [x] Route uses `websecure` and `api@internal`.
- [x] BasicAuth is mandatory and references an external users file.
- [x] Secret names are configurable without committing secret values.
- [x] `api.insecure` is absent and no extra dashboard port is added.
- [x] Existing Service Access routing is preserved.
- [x] ADR, arc42 and configuration-contract docs are synchronized.
- [x] Targeted 203-test regression set passes.
- [x] Full WSL quality gate passes: 1760 tests, 28 skipped.

## Conditional live acceptance

- [ ] Live TLS/DNS/browser/authentication verification —
  `LIVE_CONSENT_MISSING`.
- [ ] Fresh install, reconcile/re-run and update evidence —
  `LIVE_CONSENT_MISSING`.

The unchecked items are explicit gates for the later Public-Beta Green-Path,
not claims hidden by the local test result.
