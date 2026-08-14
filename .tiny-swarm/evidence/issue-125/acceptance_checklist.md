# Issue #125 Acceptance Checklist

- [x] Canonical contract exists.
- [x] Reusable live-run template exists.
- [x] Redaction rules prohibit secrets, tokens, raw env and command dumps.
- [x] Smoke checklist covers consent, hosts, A/B/C, services and admin route.
- [x] Policy states, retry/stop, cleanup/rollback, checksums and review are
  defined.
- [x] Service Access, Traefik, TLS/DNS/browser and external-gate categories are
  represented.
- [x] No live commands or local live evidence were executed.
- [ ] A/B/C runtime evidence — `LIVE_CONSENT_MISSING`, deferred to Green-Path.
- [ ] External quality result — `EXTERNAL_GATE_UNAVAILABLE`.
