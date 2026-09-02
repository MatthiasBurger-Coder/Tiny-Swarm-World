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
5. After successful setup, print service URLs, login identifiers, and the
   `INTERNAL/TEST ONLY` catalog convention. Password values are intentionally
   not printed; operators use the catalog or their protected override source.

All database passwords, service passwords, encryption keys, auth secrets, tokens
and derived Traefik dashboard material remain internal and are not printed.

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

The standard path does not create or require a local password or recovery
file. Re-running or recreating an internal-test environment therefore resolves
the same catalog values without credential filesystem state.

An operator may explicitly provide a protected bootstrap override file by
setting `TSW_BOOTSTRAP_SECRET_ENV_FILE` (or the supported
`TSW_BOOTSTRAP_STATE_DIR` alias). Its values are loaded as explicit inputs; the
normal path never creates that file. Full override precedence and the
supported Infisical lifecycle are defined by CRED-03. The file must be on a
WSL-native Linux filesystem with a user-owned `0700` parent and `0600` file
permissions.

## Removed from the normal RC1 interface

The standard installer has one credential path: deterministic catalog defaults,
explicit operator overrides, and (where applicable) a ready secure source.
There is no secret-source selector and no separate fixed, generated, or
recovery credential file.

## Lifecycle rules

- **Fresh install:** resolve catalog defaults and explicit overrides, bootstrap services, and print Portainer and Infisical access targets without password values.
- **Rerun:** resolve the same catalog defaults; no implicit rotation or recovery-file dependency.
- **Failure:** no default credential state is written; a retry resolves the same defaults again.
- **Rotation/reset of credentials:** must be an explicit future workflow; the normal installer never rotates secrets merely because it is run again.

This contract deliberately favors deterministic RC1 installation over a generalized secret-provider abstraction.
