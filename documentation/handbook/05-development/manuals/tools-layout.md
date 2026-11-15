# Bootstrap and developer-tool layout

[Product Handbook](../../../README.adoc) / [Part 5: Development](../README.adoc)

Installation preparation lives in `modules/tsw_native_linux/boostrap`.
Shared runtime tools live in `modules/tsw_core/tools/linux`; compatibility
forwarders remain under `modules/tsw_native_linux/tools`.

```text
modules/
  tsw_core/
    tools/linux/
      live/             Secure runtime paths for credentials and evidence
      qualification/    Bounded runtime inventory and Incus qualification
      ...               Quality, audit and developer tools
    tests/
      e2e/classic/      Opt-in live acceptance runner
      fixtures/         Isolated test assets
  tsw_native_linux/
    boostrap/           Prerequisites, preflight and installation diagnostics
    tools/              Compatibility forwarders to core tools
    tests/              Linux bootstrap and qualification tests
```

## Entry points

- Preparation: `./modules/tsw_native_linux/boostrap/prepare_linux.sh`.
- Installation: `./install.sh`, forwarding through the Linux module.
- CLI: `./tsw`, forwarding through the Linux module.
- Quality: `python3 modules/tsw_core/tools/linux/quality_gate.py quality`.
- Diagnostics: `python3 modules/tsw_native_linux/boostrap/install_debugger.py`.
- Live acceptance: `modules/tsw_core/tests/e2e/classic/run_classic_acceptance.py`;
  requires explicit live consent and is excluded from ordinary discovery.

Windows preparation, bridge, release-proof and resource-projection tools were
removed with the Windows module. This checkout has no Windows setup entry point.
Existing WSL runtime adapters and isolated fixtures remain in core. Historical
ADRs, audits and qualification snapshots describe their recorded revisions;
their paths and hashes do not establish current tool availability.

The Incus listener qualification runner and native maintenance source pins are
Linux-only. Windows snapshot producers, PowerShell transport and proof fields
have been removed. Route-state artifacts use `tsw.route-state.v3`; old Windows
approval fields are rejected. Only the bound native target is admitted. Source,
review, route, resource, fixture-identity and cleanup guards remain required.
New qualification needs fresh source-bound approval; no live run was performed
as part of this removal.

## Verification

Tests and quality gates run only when creating a pull request or when explicitly
requested. Follow `AGENTS.md` for the required SSH/WSL test host and credential
source; confirm that the remote checkout matches current changes first.
Test-host credentials alone do not authorize a run. No previous layout's results
qualify this cleanup or a live installation.
