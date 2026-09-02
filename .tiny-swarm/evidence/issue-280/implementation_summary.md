# Implementation Summary: #280 / CRED-02

The normal `install.sh` path now uses the canonical CRED-01 catalog for the
`internal-test` profile.

- `simple_installer.main` pins the legacy execution compatibility layer to
  `secrets_mode=internal-test` with generation disabled.
- Missing required manifest keys are resolved through
  `validate_internal_test_consumers` and `internal_test_credential`; no second
  default inventory was introduced.
- The catalog Traefik `htpasswd` exception replaces the former random SHA
  generation in the normal path.
- Fresh and repeated resolution is stateless: the default path does not create
  or require `bootstrap-secrets.env`, `generated.local.env`, or an ordinary
  password file.
- Explicit process-environment values remain intact. An explicitly named
  compatibility override file is still read, but is never created by the
  standard path. Its full precedence and Infisical/Vault lifecycle remain
  follow-up scope for CRED-03; obsolete legacy machinery remains follow-up
  scope for CRED-04.
- The configuration contract and Arc42 deployment/configuration views now make
  the Traefik boundary explicit: internal-test may use the catalogued bcrypt
  exception, while custom profiles retain operator-owned overrides.
- The install-script fixture now copies and executes `simple_installer.py` for
  the normal path; legacy mode tests remain intentionally on the compatibility
  fallback.
- The governing documentation hash cache was refreshed for the changed Arc42
  concepts file; no unrelated registry entry was changed.

No live infrastructure, Infisical service, Docker, Swarm, or provider command
was run for CRED-02.
