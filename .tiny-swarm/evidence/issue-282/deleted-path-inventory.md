# Deleted Credential Ballast Inventory: #282 / CRED-04

| Removed item | Previous responsibility | Current contract | Verification |
|---|---|---|---|
| `FixedEnvSecretSource` | Read `.tiny-swarm-world/local/fixed-secrets.env` | Explicit operator values use the single override/process-environment contract | source search; targeted tests |
| `DEFAULT_FIXED_LOCAL_ENV` | Fixed-mode default path | No fixed credential file | source/config search |
| `DEFAULT_BOOTSTRAP_LOCAL_ENV` | Infisical bootstrap-file path | No generated bootstrap credential file | source/config search |
| `DEFAULT_GENERATED_LOCAL_ENV` | Sync recovery-file path | Catalog-backed reruns are stateless | source/config search; install tests |
| `generated`, `fixed`, `infisical` mode branches | Selectable credential strategies | No credential-source selector | parser and source search |
| `--secrets-mode`, `--no-generate-secrets` | Installer mode switches | Rejected as unsupported CLI surface | installer parser tests |
| Installer random generators and SonarQube regeneration | Fill or rotate missing values | Catalog derivation or explicit operator input only | source search; deterministic tests |
| Sync `_generate_secret` and generated rotate path | Create recovery values | Sync never invents credential material | sync tests; source search |
| `.tiny-swarm/secrets/bootstrap.local.env` persistence | Store bootstrap payload values | Explicit override files are inputs only | silent-install and install tests |
| `.tiny-swarm/secrets/generated.local.env` persistence | Reuse generated sync values | No generated recovery state | install and sync tests |
| `TSW_INFISICAL_BOOTSTRAP_TOKEN` environment fallback | Reuse bootstrap token through process env | Bootstrap token remains client-local; legacy env name is ignored | Infisical client test |

Generic workflow recovery hints, evidence timestamps, TLS material generation,
and operation failure/retry handling are unrelated operational concerns and
remain intact.
