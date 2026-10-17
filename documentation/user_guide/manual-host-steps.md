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
   ./prepare_linux.sh --dry-run --service-profile service-access
   ```

2. Authenticate privileged stages in that same ordinary-user terminal, then
   review and approve the displayed actions:

   ```bash
   sudo -v && ./prepare_linux.sh --service-profile service-access
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
   ./prepare_linux.sh --preflight --service-profile service-access
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
See the [operator configuration contract](../arc42/08_configuration/operator-configuration-contract.md).

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

## Optional Windows current-user trust helper

The GUI procedure above remains available. Alternatively, the reviewed
`tools/windows/tsw-tls-trust.ps1` helper provides separate `inspect`, `install`
and `remove` actions for `CurrentUser/Root` only. It never modifies machine-wide
trust and is not invoked by ordinary installation or the Windows bridge.

First inspect the selected CA on the installation host, then calculate its
DER SHA-256 fingerprint:

```bash
openssl x509 -in "$tsw_ca_cert" -noout -subject -issuer -dates -fingerprint -sha256
openssl x509 -in "$tsw_ca_cert" -outform DER | sha256sum
```

Use the verified 64-character hexadecimal DER fingerprint below, without colons.
It differs from the PEM file's byte digest, the Windows SHA-1 thumbprint, and
the combined CA/leaf lifecycle fingerprint. Transfer only the public certificate
and verify the copy as described above. Replace the example file path with its
actual local fixed-drive location. From the checkout in PowerShell, under the
Windows account that will use the services:

```powershell
./tools/windows/tsw-tls-trust.ps1 -Action inspect -CertificatePath C:/certs/tsw-ca.crt
./tools/windows/tsw-tls-trust.ps1 -Action install -CertificatePath C:/certs/tsw-ca.crt -ExpectedSha256 <verified-DER-SHA256> -Approve
```

Run installation in that user's interactive Windows session and accept the
Windows certificate confirmation if shown. SSH can fail with
`ERROR_NOT_SUPPORTED` despite administrative rights; `-Approve` does not replace
Windows' own confirmation. Do not change the store scope or account to bypass
this boundary. Import trusts the CA for that user, not just one service URL.

The helper rejects private keys, certificate bundles, non-CA certificates,
fingerprint mismatches and explicit key usage without certificate signing.
Installation rejects expired or not-yet-valid certificates. An exact certificate
already in the store is a no-op and grants no new removal authority. A newly
imported certificate is verified and recorded in a protected current-user
receipt under LocalApplicationData `TinySwarmWorld/TlsTrust`; the receipt is
bound to that user and exact certificate through DPAPI. Keep this state private.
If trust changes but receipt writing fails, inspect the result manually rather
than retrying a removal without proven ownership.

For helper-owned rollback, retain the original public certificate and matching
DER fingerprint and use the same Windows account:

```powershell
./tools/windows/tsw-tls-trust.ps1 -Action remove -CertificatePath C:/certs/tsw-ca.crt -ExpectedSha256 <verified-DER-SHA256> -Approve
```

Removal requires the matching protected receipt; pre-existing trust and GUI
imports are preserved. Expired owned certificates remain removable. Removal
consumes its receipt before changing trust; interrupted or failed removal
therefore requires manual inspection rather than reusable deletion authority.
Browser-managed stores still require their own verified import/removal.

Windows Schannel curl can reject a managed local CA with
`CRYPT_E_NO_REVOCATION_CHECK` when no revocation distribution point exists.
An explicit diagnostic policy can use `--ssl-revoke-best-effort` to retain
certificate-chain and hostname validation while tolerating unavailable
revocation information. In the intended Windows account's terminal:

```powershell
curl.exe --ssl-revoke-best-effort -sS -o NUL -w '%{http_code}\n' https://service-access.tsw.local/
```

Record that policy with the result. It is not a successful strict revocation
check or authenticated login. Do not replace it with `--insecure`. See the
[curl option contract](https://curl.se/docs/manpage.html#--ssl-revoke-best-effort).

## WSL bridge, restart and interrupted preparation

Initial Windows bridge registration requires an elevated interactive Windows
session of the account owning the selected WSL distribution. Its credential
dialog takes that Windows account's password for the Service Control Manager;
Linux sudo does not grant Windows administrator rights. A headless SSH session
cannot substitute for that interactive dialog. An owned matching registration
reuses its credentials; foreign paths or account mismatches block.

Use the existing [Windows preparation guide](windows-preparation.md) and
[bridge lifecycle instructions](../../tools/windows/README.windows-wsl-bridge.md)
for the selected distribution, bridge status and verification. The bridge remains
the owner of Windows hosts entries, portproxy, firewall rules and its service.
Do not add a competing updater. Bridge readiness and TCP checks do not establish
TLS trust or actual service login.

After a requested restart, perform only the printed scope. Save work in every
affected distribution before a global WSL resource change requires WSL shutdown;
do not substitute a global shutdown for a selected-distribution restart. Rerun
the same read-only preparation command with the same distribution, release,
profile and overrides, inspect fresh observations, and give new consent for
remaining actions.

A selected WSL distribution termination and relaunch can recreate PID 1 and
its namespaces while retaining the shared kernel's boot ID. For restart
verification, compare PID 1's start time and namespace identities before and
after relaunch; the kernel boot ID alone cannot prove that the selected
distribution restarted. Preserve the selected Lxss registration and unrelated
`.wslconfig` settings. After relaunch, verify the fresh bridge heartbeat and
current forwarding target, all three configured managed nodes, trusted HTTPS,
and actual API authentication with an authenticated read. A running distribution
or changed PID 1 does not establish service readiness.

Preserve interrupted-run evidence, checkpoints and configuration backups. Changed
source, target or selection can make a checkpoint stale and block apply. Review
and deliberately archive it into protected operator storage before replanning;
archival does not authorize another mutation. Never delete an APT lock, erase
state or reset the platform simply to retry. Ordinary installation reconciles
existing state. See the [bootstrap recovery contract](../contracts/bootstrap.md#boot-w08-resumable-preparation-and-protected-recovery).

For an interrupted download or dependency installation, retain the partial
virtual environment and protected state for inspection. Review the checkpoint,
reported effects, selected source and target, then obtain a fresh read-only plan
before an ordinary connected rerun with new consent. A successful resume and
subsequent no-action rerun establish only the exercised stage's recovery and
idempotence; an isolated stage probe is not full installer or CLI qualification.
Do not erase checkpoints, recreate the environment blindly or delete APT locks
to obtain a passing retry.

## Check a deliberate recovery before resuming

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
