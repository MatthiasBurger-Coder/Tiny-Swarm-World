# RC1 Simple Secret Bootstrap

For the Classic RC1 installation path, secret handling is intentionally reduced to one operator-independent bootstrap lifecycle.

## Normal installation contract

`./install.sh` has one secret behavior:

1. Load the canonical bootstrap secret store if it already exists.
2. Generate every missing machine secret exactly once.
3. Reuse those values on every later installer run.
4. Bootstrap Infisical from the resolved values.
5. Run the existing governed reset/setup workflow.
6. After successful setup, print only the credentials an operator needs to enter manually:
   - Portainer admin password
   - Infisical login email and bootstrap admin password

All database passwords, service passwords, encryption keys, auth secrets, tokens and generated Traefik dashboard material remain internal and are not printed.

## Canonical state

The persistent source of truth is a single Linux-native owner-only file:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world/bootstrap-secrets.env
```

The parent directory is restricted to `0700`; the secret file is restricted to `0600`. This intentionally keeps bootstrap secrets away from a repository located on `/mnt/c`, `/mnt/d` or another Windows-mounted WSL filesystem where POSIX owner-only permissions may not be reliable.

`TSW_BOOTSTRAP_STATE_DIR` or `TSW_BOOTSTRAP_SECRET_ENV_FILE` may override the location for controlled test or operator scenarios.

## Removed from the normal RC1 interface

The standard installer no longer exposes secret-source selection. In particular, operators do not choose between `generated`, `fixed` and `infisical`, and they do not maintain separate fixed/generated/bootstrap secret files.

The former installer remains temporarily available as an internal compatibility layer for the already tested reset/setup/evidence execution path. The new RC1 entry point pins that layer to generated/reuse semantics and redirects its persistent secret inputs to the canonical bootstrap store.

## Lifecycle rules

- **Fresh install:** generate missing values, persist them, bootstrap services, print Portainer and Infisical access credentials.
- **Rerun:** reuse existing values; no implicit rotation.
- **Failure:** keep the canonical store so a retry uses the same values.
- **Rotation/reset of credentials:** must be an explicit future workflow; the normal installer never rotates secrets merely because it is run again.

This contract deliberately favors deterministic RC1 installation over a generalized secret-provider abstraction.
