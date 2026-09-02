# Acceptance Checklist: #280 / CRED-02

- [x] `install.sh` normal path pins execution to `internal-test`.
- [x] Portainer and every required manifest key resolve through the CRED-01 catalog.
- [x] Infisical startup values are resolved locally before any execution call.
- [x] Fresh resolution creates no default bootstrap/recovery credential file.
- [x] Repeated resolution returns identical catalog values.
- [x] Catalog-specific Traefik `htpasswd` value is retained and validated.
- [x] Random generation is not called by the standard resolver.
- [x] Explicit environment and explicitly named file overrides are preserved.
- [x] Internal credential output remains redacted outside intentional operator login output.
- [x] Focused tests and the full local quality gate pass.
- [x] Changed Python code has at least 95% focused branch-aware coverage.
- [x] Documentation and key-only issue evidence are synchronized.
- [x] Configuration and deployment contracts explicitly distinguish the
  catalogued internal-test Traefik exception from custom operator overrides.
- [x] The install-script fixture executes the actual normal `simple_installer`
  path.
- [x] Governing documentation hash cache is synchronized for the changed
  Arc42 file.
- [ ] Live WSL2/native-Linux installation and service authentication — deferred to CRED-07 by issue scope.
