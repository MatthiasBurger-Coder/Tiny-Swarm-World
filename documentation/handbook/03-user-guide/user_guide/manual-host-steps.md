# Manual host preparation, certificates and recovery

Use this checklist from an ordinary account in the Linux-native checkout, for
example `~/Tiny-Swarm-World`. Read the [installation guide](installation.adoc)
and the printed plan before consenting to host changes. Preparation readiness,
service reachability, trusted HTTPS and successful authentication are separate
results; each needs its own executed evidence.

## Retain the Git checkout metadata

Installer preflight checks effective secret-file ignore rules with Git. A plain
`git archive` extraction without repository metadata is insufficient for those
checks, even when its file hashes match. Use the installation guide's Git clone
path for manual installation, and retain the trusted repository metadata:

```bash
git rev-parse --is-inside-work-tree
git check-ignore .env .env.local .tiny-swarm-world/
```

Require `true` from the first command and all three paths in the second
command's output. Its zero exit alone does not prove that every path is ignored.

A successful preparation check alone does not establish installer readiness.

## Authentication and provider access

1. Review the current plan from the terminal that will run preparation:

   ```bash
   ./modules/tsw_native_linux/boostrap/prepare_linux.sh --dry-run --service-profile service-access
   ```

2. Authenticate privileged stages in that same ordinary-user terminal, then
   review and approve the displayed actions:

   ```bash
   sudo -v && ./modules/tsw_native_linux/boostrap/prepare_linux.sh --service-profile service-access
   ```

   A cached login in another terminal, SSH connection or Windows-to-WSL process
   does not establish this session's sudo permission. Expired authentication or
   cancelled elevation requires operator review and a new attempt.

3. If preparation adds `incus-admin` membership and returns
   `RESTART_REQUIRED/3`, log out completely and log back in. Another shell in the
   existing login may retain stale groups. Verify as the ordinary account:

   ```bash
   id -nG
   incus version
   incus info
   ./modules/tsw_native_linux/boostrap/prepare_linux.sh --preflight --service-profile service-access
   ```

   Running Incus with sudo does not prove ordinary-user access. Resume only
   after the relevant preparation checks pass.

4. An active or unobservable LXD runtime is an intentional blocker. Inspect the
   named units without changing them:

   ```bash
   systemctl show lxd.service snap.lxd.daemon.service snap.lxd.daemon.unix.socket --property=LoadState,ActiveState,SubState
   ```

   Preserve existing instances and state. Resolve the conflict through a
   separately reviewed, reversible host operation or select an isolated host.
   Preparation does not stop, remove or migrate LXD. An installed inactive
   executable alone does not establish an active runtime.

## Findings from preparation diagnostics

Network preparation recognizes that `ss` can render an owned dual-stack Incus
proxy listener as `*` even when the configured IPv4 listen address is `0.0.0.0`.
Acceptance requires an explicit `v6only:0` observation and matching configuration
and process ownership. Incus can also run a proxy as container root mapped to a
nonzero host UID; acceptance requires matching manager state, complete UID/GID
maps, namespaces and stable process identities. The corrected inventory checks
these facts rather than relying on the displayed address or host UID alone.

Unknown ownership, IPv6-only listeners and a wildcard listener for a loopback-only
contract still block. Do not rebind listeners or disable a firewall to bypass
the check. See [network preparation](network-preparation.md). These corrections
do not establish a completed installation, trusted certificates, browser login
or release qualification.

An existing Incus bridge with IPv6 enabled can also block the IPv4-only
preparation contract. Inventory its dependents before reviewing any migration;
do not disable IPv6 on an attached existing bridge merely to pass a test.

Retain the reviewed configuration root and resource selection when repeating a
run on an existing host. If `TSW_INFRA_ROOT`, `TSW_NATIVE_LINUX_VENV` or
`TSW_INSTALL_ENV_FILE` was explicitly selected, use the same reviewed values in
the new terminal. A default configuration or a different override file is a new
selection, not proof of a repeatable run; never increase node allocations or
change preserved credentials just to match defaults.

## Locate and inspect the public CA

The deployment TLS resolver creates the managed CA and ingress certificate when
deployment reaches that stage. Preparation alone does not generate them. Valid
managed material is reused on rerun; missing, invalid or incomplete existing
material requires explicit recovery rather than deletion or silent rotation.
There is no separate project certificate rotation command.

Managed state defaults to
`${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world/tls/traefik`.
`TSW_LOCAL_TLS_STATE_ROOT` overrides that directory. Its files are `ca.crt`,
`ca.key`, `tls.crt`, `tls.key` and `ca-bundle.pem`. Private keys stay in protected
local state; never transfer the whole directory or include keys in evidence.

An external CA takes precedence only with the complete
`TSW_TRAEFIK_CA_CERT_PATH`, `TSW_TRAEFIK_TLS_CERT_PATH` and
`TSW_TRAEFIK_TLS_KEY_PATH` tuple. `TSW_TRAEFIK_CA_KEY_PATH` is optional. Partial
external configuration blocks instead of falling back to managed material.
`TSW_LIVE_TLS_CA_BUNDLE`, if explicitly set, must resolve to the selected
canonical trust bundle: managed `ca-bundle.pem` or the external CA certificate.
See the [operator configuration contract](../../02-architecture/arc42/08_configuration/operator-configuration-contract.md).

Use the same environment and ordinary account as installation. The following
commands inspect the selected public certificate without changing a trust store:

```bash
tsw_tls_root="${TSW_LOCAL_TLS_STATE_ROOT:-${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world/tls/traefik}"
tsw_ca_cert="${TSW_TRAEFIK_CA_CERT_PATH:-$tsw_tls_root/ca.crt}"
test -f "$tsw_ca_cert"
openssl x509 -in "$tsw_ca_cert" -noout -subject -issuer -dates -fingerprint -sha256
curl --cacert "$tsw_ca_cert" -sS -o /dev/null -w '%{http_code}\n' https://service-access.tsw.local/
```

Stop if the file is missing or certificate inspection fails. The curl probe also
needs working name resolution, forwarding and the deployed ingress. Never use
`--insecure` or `-k` as certificate acceptance evidence. A successful trusted
HTTP response still does not prove service authentication.

## Optional Ubuntu trust installation

This is an explicit manual host mutation, separate from preparation. Inspect the
certificate fingerprint first. Check whether the destination already exists;
preserve a different existing certificate rather than overwriting it. On Ubuntu,
install only the selected public CA when that trust change is intended:

```bash
tsw_system_ca=/usr/local/share/ca-certificates/tiny-swarm-world-local-ca.crt
if sudo test -e "$tsw_system_ca"; then
    sudo cmp --silent -- "$tsw_ca_cert" "$tsw_system_ca"
else
    sudo install -m 0644 "$tsw_ca_cert" "$tsw_system_ca"
fi && sudo update-ca-certificates
curl -sS -o /dev/null -w '%{http_code}\n' https://service-access.tsw.local/
```

If the comparison fails, stop and review the different existing certificate;
the block leaves it untouched.

For rollback, first inspect the installed certificate with `openssl x509` and
compare its SHA-256 fingerprint with the certificate imported above. Remove only
that exact matching file, then rebuild the Ubuntu trust store:

```bash
tsw_system_ca=/usr/local/share/ca-certificates/tiny-swarm-world-local-ca.crt
sudo cmp --silent -- "$tsw_ca_cert" "$tsw_system_ca" &&
    sudo rm -- "$tsw_system_ca" && sudo update-ca-certificates
```

Do not remove another application's CA or the private installation TLS state.
These commands modify the current Ubuntu host or WSL distribution's trust store;
they do not modify Windows browser trust.

## Windows and browser trust

Transfer only the selected public CA certificate to the Windows account that
will use the browser, through an approved private transfer method. Compare its
file SHA-256 digest with the source before importing it. For a copy accessible
from WSL, set `tsw_windows_ca_copy` to its actual POSIX path under `/mnt/c`, then
compare the two printed digests:

```bash
sha256sum -- "$tsw_ca_cert" "$tsw_windows_ca_copy"
```

Both digests must match. A file digest is distinct from the certificate
fingerprint printed by OpenSSL; the Windows certificate dialog may instead
display a SHA-1 thumbprint. Do not compare values produced with different
algorithms. Do not transfer either private key, publish certificate material
in issue evidence, or import an unverified certificate merely to suppress a
browser warning.

Open **Manage user certificates** (`certmgr.msc`) for that Windows account.
Under **Trusted Root Certification Authorities**, use **Certificates > All Tasks
> Import** to import the verified public CA certificate into the current user's
store. This is a manual trust decision; the bridge does not install it. Restart
the browser and verify the deployed service without bypassing certificate errors.
Record the imported certificate's thumbprint from its Windows certificate details
and the store/account used, so its exact import can be identified for rollback.
If the browser uses its own certificate store, import that same verified public
CA through its certificate-authority settings as well.

For rollback, match the recorded Windows thumbprint and remove only that
certificate from the recorded Windows store/account. Identify the exact imported
certificate in each browser-managed store before removing it there. A same-name
certificate is insufficient proof of identity. Preserve
the installation's CA and keys unless a separate recovery or rotation plan
explicitly changes them.

## Removed Windows helpers

Windows certificate-trust and bridge lifecycle helpers are no longer shipped.
Historical commands must not be used as current setup instructions. Retain
operator ownership of any existing host trust and forwarding configuration.

## Check a deliberate recovery before resuming

Installer evidence directories and newly created parent directories use mode
`0700`, including when the shell uses `umask 002`. Existing directory permissions
are preserved; incompatible ownership or permissions remain blockers.

An instance snapshot on its existing storage pool is not a host operating-system
backup or disaster-recovery copy. Establish separately whether external volumes
and other dependencies are protected: a root-disk snapshot does not prove their
recovery. Record the original instance state, user configuration, devices,
profiles and private machine identity before an approved restore; compare them
afterwards without publishing raw identifiers or host configuration.

Do not discard every `volatile.*` field from a preservation comparison. Stable
instance UUID, MAC and ID maps remain relevant. Lifecycle fields such as recorded
power/readiness, a recreated host veth name and the generation UUID need explicit
field-specific validation. Incus changes the generation UUID when restoring an
earlier point in time; its host device name describes the runtime network
interface. See the [Incus instance-option reference](https://linuxcontainers.org/incus/docs/main/reference/instance_options/#volatile-internal-data).
An initial full-configuration mismatch must remain in the evidence alongside
any narrower validated comparison; neither comparison alone proves a fresh
installation or complete host recovery.

If a separately approved LXD pause is needed, first retain its original service
and socket states and instance inventory. Restore those exact states after the
test; do not start previously stopped instances or enable an originally inactive
socket. A service reporting active can precede API readiness. Wait with a finite
deadline and inspect the original instances through the original runtime before
claiming preservation. For Incus after its own approved restart, an example
read-only API readiness check is:

```bash
timeout 30s sh -c 'until incus info >/dev/null 2>&1; do sleep 1; done'
```

When the original LXD runtime is managed by its `lxc` client, check that original
runtime separately after restoring its service state:

```bash
timeout 30s sh -c 'until lxc info >/dev/null 2>&1; do sleep 1; done'
```

Incus readiness does not establish LXD preservation. A timeout remains a blocked check requiring inspection,
not permission to repeat the preceding restore or lifecycle mutation.

SSH can become available before Incus's boot startup check has completed.
Capture the original daemon and socket states before invoking clients that may
activate a runtime, and distinguish an early sample from bounded final readiness.

Cold restore and restart can leave services warming up after infrastructure
checks pass. An initial `502` or `503` is a pending observation, not service
success. Retain that failed sample, wait only to an explicit finite deadline,
and repeat the required trusted HTTPS and authenticated checks. On expiry,
inspect the affected service and its logs; do not reset the platform to retry.
A later successful check supplements the earlier sample rather than replacing it.

## Reuse credentials for an initialized Portainer

An initialization `409` followed by failed login can mean the selected credential
source does not match the preserved Portainer administrator. Before selecting
another override file, verify the actual existing credentials through a private
API client: require successful authentication and an authenticated read, not just
an HTTP response from the login endpoint. Select the verified existing protected
source with `TSW_INSTALL_ENV_FILE`, following the installation guide's override
file permissions and Linux-native storage rules. Preserve the previous source
for review; an old filename alone does not establish valid credentials. Do not
delete volumes, reset the platform, reinitialize the administrator or rotate its
password merely to retry. Keep credentials out of inline commands, shell history,
logs and issue evidence. A successful authenticated check does not establish a
complete installation.

Finish with the installation guide's runtime checks, trusted HTTPS from the
actual browser environment, and authenticated access to each required service.
Record commands, exits and redacted results separately. A login page, `401` or
`403` can establish reachability without establishing successful login.
