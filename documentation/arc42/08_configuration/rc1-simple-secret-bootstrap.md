# RC1 Simple Secret Bootstrap

For the Classic `internal-test` installation path, credential handling is
intentionally reduced to one catalog-backed lifecycle.

## Normal installation contract

`./install.sh` has the following standard behavior:

1. Resolve missing `internal-test` credentials from the canonical catalog.
2. Preserve explicit `TSW_*` environment overrides.
3. Bootstrap Infisical from the resolved values; Infisical is not queried for
   its own startup inputs.
4. Run the existing governed reset/setup workflow.
5. After successful setup, print only the credentials an operator needs to
   enter manually:
   - Portainer admin password
   - Infisical login email and bootstrap admin password

All database passwords, service passwords, encryption keys, auth secrets, tokens and generated Traefik dashboard material remain internal and are not printed.

The standard path uses the deterministic CRED-01 catalog. The canonical
human-facing internal-test password is `TSW1234STW5678`; component-specific
formats such as Pulsar tokens, Infisical keys, and Traefik `htpasswd` are
derived by that catalog. These values are `INTERNAL/TEST ONLY` and must never
be reused for production or publicly exposed environments.

## Canonical state

The standard internal-test source of truth is the committed catalog:

```text
src/tiny_swarm_world/domain/configuration/internal_test_credentials.py
```

The standard path does not create or require a local ordinary-password or
generated-password recovery file. Re-running or recreating an internal-test
environment therefore resolves the same catalog values without filesystem
state.

An operator may explicitly provide a protected compatibility override file by
setting `TSW_BOOTSTRAP_SECRET_ENV_FILE` (or the legacy
`TSW_BOOTSTRAP_STATE_DIR`). Its values are loaded as explicit inputs; the
standard path never creates that file. Full override precedence and the
supported Infisical/Vault lifecycle are defined by CRED-03.

Legacy generated-state behavior remains behind the old installer execution
layer only until CRED-04 removes or isolates it.

The former generated bootstrap source of truth was:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world/bootstrap-secrets.env
```

The parent directory is restricted to `0700`; the secret file is restricted to `0600`. This intentionally keeps bootstrap secrets away from a repository located on `/mnt/c`, `/mnt/d` or another Windows-mounted WSL filesystem where POSIX owner-only permissions may not be reliable.

`TSW_BOOTSTRAP_STATE_DIR` or `TSW_BOOTSTRAP_SECRET_ENV_FILE` now identify an
explicit compatibility input and are not used by the normal catalog-backed
path unless supplied by the operator.

## Removed from the normal RC1 interface

The standard installer no longer exposes secret-source selection. In particular, operators do not choose between `generated`, `fixed` and `infisical`, and they do not maintain separate fixed/generated/bootstrap secret files.

The former installer remains temporarily available as an internal compatibility layer for the already tested reset/setup/evidence execution path. The new RC1 entry point pins that layer to generated/reuse semantics and redirects its persistent secret inputs to the canonical bootstrap store.

## Lifecycle rules

- **Fresh install:** resolve catalog defaults and explicit overrides, bootstrap services, and print Portainer and Infisical access credentials.
- **Rerun:** resolve the same catalog defaults; no implicit rotation or recovery-file dependency.
- **Failure:** no generated default state is written; a retry resolves the same defaults again.
- **Rotation/reset of credentials:** must be an explicit future workflow; the normal installer never rotates secrets merely because it is run again.

This contract deliberately favors deterministic RC1 installation over a generalized secret-provider abstraction.
