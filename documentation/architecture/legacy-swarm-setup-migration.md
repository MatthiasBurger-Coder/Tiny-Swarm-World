# Legacy Swarm Setup Migration Analysis

Status: Slice 01 migration evidence.

This document classifies the legacy `infra/swarm` helper area before runtime
setup behavior changes. It is static repository evidence only. No
`infra/swarm` script is a supported setup entry point, and no live
infrastructure command was run for this analysis.

## Governance Boundaries

- `infra/swarm` remains legacy evidence until later slices migrate useful
  behavior behind typed Python contracts, tests, and explicit live-consent
  guards.
- Direct execution, sudo relaunch, host repair, package installation, network
  mutation, and process management from the legacy scripts are not migrated as
  default product behavior.
- Concrete local addresses, user names, host paths, raw command payloads,
  stdout, stderr, environment payloads, tokens, passwords, passphrases, and
  Swarm join tokens must not be copied into committed product configuration or
  evidence.
- Sandbox or static review may identify migration candidates, but it must not
  be reported as real WSL2, Multipass daemon, Docker Swarm, or forwarding
  success.

## Evidence Index

| Evidence | Role in this analysis |
| --- | --- |
| `infra/swarm/README.md` | Existing legacy helper status and canonical entry-point guidance. |
| `infra/swarm/prepere.py` | Transitional orchestration sketch with missing helper modules and direct elevation behavior. |
| `infra/swarm/file_copy.py` | Legacy file staging and permission mutation helper. |
| `infra/swarm/multipass/multipass_setup.py` | Multipass install, readiness, group, socket, and passphrase behavior. |
| `infra/swarm/multipass/multipass_socat_setup.py` | Legacy socat install, process, and forwarding behavior. |
| `infra/swarm/multipass/socat_config.yaml` | Legacy host-specific forwarding configuration. |
| `infra/swarm/multipass/cloud-init-template.yaml` | Legacy netplan-style cloud-init template. |
| `infra/swarm/network/network_manager.py` | Legacy WSL, Multipass address discovery, Windows port proxy, and iptables behavior. |
| `documentation/system/live-operation-surfaces.adoc` | Current supported, retired, legacy, and asset classification catalog. |
| `documentation/architecture/adr-autonomous-setup-safety.adoc` | Accepted fail-closed live-consent setup safety contract. |
| `documentation/workflow/workflow.md` | Active Linux/WSL-aware Swarm setup migration workflow and Slice 01 scope. |

## Classification Matrix

| Legacy behavior | Classification | Evidence | Migration decision |
| --- | --- | --- | --- |
| Treating `infra/swarm` as a supported setup entry point | `REJECT` | `infra/swarm/README.md`; `documentation/workflow/workflow.md` | Keep the directory as migration evidence only. Supported setup stays behind the Python entry point and composition root. |
| Legacy stage inventory in `prepere.py` | `DOCUMENT_ONLY` | `infra/swarm/prepere.py` | Use only as a clue about former setup intent. Missing imported modules prevent any implementation claim. |
| `prepere.py` direct sudo relaunch and direct setup invocation | `REJECT` | `infra/swarm/prepere.py` | Do not migrate direct privilege escalation or script-driven orchestration. Live consent remains CLI-governed. |
| Multipass executable, version, and list readiness probes | `MIGRATE_WITH_CHANGES` | `infra/swarm/multipass/multipass_setup.py` | Later slices may keep the read-only readiness concept, but must expose typed status, timeouts, sanitized evidence, and fail-closed results. |
| Automatic Multipass installation | `DOCUMENT_ONLY` | `infra/swarm/multipass/multipass_setup.py`; `documentation/system/multipass-setup.adoc` | Keep as operator host-preparation guidance unless a later ADR authorizes package installation automation. |
| Multipass group and socket repair | `DOCUMENT_ONLY` | `infra/swarm/multipass/multipass_setup.py`; `documentation/system/multipass-setup.adoc` | Keep as remediation guidance. Do not auto-repair permissions in default setup slices. |
| Static Multipass passphrase configuration | `REJECT` | `infra/swarm/multipass/multipass_setup.py` | Do not migrate static passphrase behavior, example secrets, or credential-setting patterns. |
| Socat forwarding as a WSL2 access concept | `MIGRATE_WITH_CHANGES` | `infra/swarm/multipass/multipass_socat_setup.py`; `documentation/system/network.adoc` | Later slices may model forwarding strategies as typed plans with placeholders and explicit operator approval. |
| Socat install, restart, kill, and background process management | `REJECT` | `infra/swarm/multipass/multipass_socat_setup.py` | Do not migrate blind package installation, process termination, or process startup as default automation. |
| Host-specific socat forwarding values | `REJECT` | `infra/swarm/multipass/socat_config.yaml` | Treat as legacy risk evidence only. Do not copy concrete forwarding values into product defaults. |
| WSL and Multipass address discovery | `MIGRATE_WITH_CHANGES` | `infra/swarm/network/network_manager.py` | Later slices may migrate discovery as typed probes with sanitized summaries and no persisted concrete addresses. |
| Windows port proxy automation | `REJECT` | `infra/swarm/network/network_manager.py`; workflow assumptions | Keep as operator-confirmed troubleshooting guidance only. Do not make Windows host mutation default product behavior. |
| iptables and IP forwarding mutation | `REJECT` | `infra/swarm/network/network_manager.py` | Later slices may migrate the planning concern, not blind host network mutation. |
| Cloud-init network template shape | `MIGRATE_WITH_CHANGES` | `infra/swarm/multipass/cloud-init-template.yaml` | Preserve only the template idea. Later implementation must validate against current `infra/config` assets and avoid committed host-specific addresses. |
| File copy staging into a user directory | `REJECT` | `infra/swarm/file_copy.py` | Do not migrate recursive copy, deletion, ownership, or chmod behavior into the setup workflow. |
| Legacy README status and warning text | `DOCUMENT_ONLY` | `infra/swarm/README.md` | Keep as navigation evidence. Product behavior remains in supported workflow and system documentation. |

## Later Slice Handoff

Slice 02 may introduce typed domain concepts for host environment, Multipass
readiness, and forwarding plans. This document does not claim that those
concepts are implemented yet.

Slice 03 through Slice 06 may migrate read-only host and Multipass readiness
concepts. They must preserve the hexagonal boundary: infrastructure adapters
own subprocess, filesystem, platform, and host probing details; application
services orchestrate ports and domain results; domain models remain independent
from infrastructure.

Slice 07 may migrate WSL2 forwarding as planning and verification, not blind
mutation. Forwarding strategies must be explicit, operator-readable, and free of
committed local addresses.

Slice 10 must synchronize user-facing documentation after behavior exists. It
must not describe planned migration behavior as already implemented.

## Stop Conditions

Stop future migration work if a planned change would:

- execute or promote `infra/swarm` scripts as canonical setup;
- copy host-specific values, raw command payloads, raw outputs, credentials, or
  local environment details from the legacy area;
- treat sandbox/static review as real WSL2 or Multipass live validation;
- automate package installation, socket repair, Windows port proxy mutation,
  iptables mutation, socat process mutation, VM creation, Docker Swarm
  initialization, or stack deployment without explicit live consent and any
  required ADR;
- weaken the setup safety contract in
  `documentation/architecture/adr-autonomous-setup-safety.adoc`;
- move infrastructure details into domain or application services.

## Verification

Slice 01 is documentation-only. Required verification is:

```bash
git diff --check
```

Execution evidence for this slice:

- S3D result: `EXECUTION_PLAN`; Slice 01 had no dependencies and locked only
  this document for writes.
- Subagent review: Senior Documentation Engineer, Senior System Architect, and
  Senior Python Automation Developer reported no blockers.
- Verification commands run: `git diff --check` and an explicit untracked-file
  whitespace check for this document.
- Live infrastructure commands: not run.
