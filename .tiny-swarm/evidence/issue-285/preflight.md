# Safe Preflight: #285 / CRED-07

## Read-only observations

Executed from the repository checkout on 2026-09-03:

```text
kernel=Linux DESKTOP-AD2FST4 6.18.33.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun 18 21:54:43 UTC 2026 x86_64 GNU/Linux
python=Python 3.14.4
wsl_signal=microsoft-kernel
mnt_d=present
systemd_runtime=present
incus_binary=present
docker_binary=present
native_linux_evidence_root=absent
```

The current checkout is therefore observable as a WSL2 environment under
`/mnt/d`. The presence of Incus and Docker client binaries is not evidence of
daemon readiness, managed-node ownership, Swarm state, or service health; the
clients were not invoked. No native-Linux target or recoverable target scope is
available from this checkout's read-only preflight.

## Safety state

- WSL2 live lifecycle: `LIVE_CONSENT_MISSING` before mutation.
- Native-Linux lifecycle: `LIVE_PREREQUISITE_MISSING` because no target was
  supplied or identified.
- Browser/service authentication: `LIVE_CONSENT_MISSING`; no live endpoint was
  contacted.
- External quality: no CRED-07-specific external result was required at this
  preparation stage.
- No `incus`, `docker swarm`, compose deployment, networking, bootstrap, or
  installer reset command was executed.

Before proceeding, the operator must provide scoped approval for the guarded
live-validation command, confirm that the WSL2/Native-Linux targets are
disposable or recoverable, and identify the native-Linux test environment. Any
custom override must be supplied through a protected native-Linux file path;
no secret belongs in this branch or in chat.
