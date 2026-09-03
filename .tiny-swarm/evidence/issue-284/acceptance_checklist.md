# Acceptance Checklist: #284 / CRED-06

- [x] Getting-started path is `clone -> install -> login` without credential
      preparation ceremony.
- [x] Installer output provides actionable URLs and login identifiers without
      printing password values.
- [x] The canonical internal-test convention is authoritative in the CRED-01
      catalog and linked from user-facing guidance.
- [x] Component-specific exceptions and derivations remain discoverable from
      the catalog.
- [x] Override precedence and the qualified Infisical role are documented.
- [x] AD/LDAP/SSO/VPN/firewall/network-segmentation/IAM boundaries are explicit.
- [x] Stale generated-password, mode, and recovery-preparation guidance is
      removed or explicitly negative.
- [x] `.env.example` reflects optional empty overrides for the normal path.
- [x] Documentation, installer-output, hygiene, and entry-point checks pass.
- [x] `python3 tools/quality_gate.py quality` passed with 1,900 tests and 18
      expected skips.
- [x] Branch-aware diff coverage passed with 7/7 added executable production
      lines and 0/0 added source branch arcs.
- [x] No live infrastructure, browser E2E, or external bootstrap success is
      claimed; live proof remains assigned to CRED-07 / #285.
