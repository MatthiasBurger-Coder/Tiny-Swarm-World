# Remaining Risks: #281 / CRED-03

- External Infisical provider mode is explicitly rejected. A future external
  provider implementation must add a distinct source contract and live
  verification before enabling it.
- A self-hosted Vault value cannot retroactively change credentials already
  consumed by bootstrap-only processes. Consumers that need Vault precedence
  must resolve after readiness and be restarted or otherwise rebuilt; this is
  documented and covered by the post-bootstrap sync contract.
- `generated`, `fixed`, and legacy `infisical` modes remain as compatibility
  surfaces until CRED-04 removes or remaps them. They are not the normal
  internal-test path.
- Credential override files must live on a WSL-native Linux filesystem with
  the documented ownership and mode boundary. Windows-mounted `/mnt/d`
  storage is intentionally rejected for these files; CRED-05 covers the
  broader WSL2/RC1 preflight model.
- No live WSL2 or native-Linux installation was executed in this issue. The
  evidence state is local verification only, with CRED-07/#285 responsible for
  explicit live E2E proof.
