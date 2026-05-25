# EPIC: Autonomous Runnable Setup

## Status

```text
ACTIVE_BASELINE_EXTENSION
```

## Requirement Source

This EPIC extends `documentation/epics/system-unification.md` from these
repository-visible sources:

- user request: create a setup so the system can install itself into a
  runnable state;
- active workflow `documentation/workflow/workflow.md`, version
  `autonomous-runnable-setup-v1.0.0`;
- active provider migration workflow `documentation/workflow/workflow.md`,
  version `lxc-native-node-provider-v1.0.0`;
- accepted provider direction in
  `documentation/architecture/adr-lxc-native-node-provider.adoc`;
- root `AGENTS.md` Linux/WSL-only, Docker Swarm-first, Python automation
  identity;
- root `QUALITY.md` quality-gate authority;
- current arc42 runtime, deployment, quality, and risk documentation;
- current ADR convention indexed in
  `documentation/arc42/09_architecture_decisions.adoc`;
- live-operation classification in
  `documentation/system/live-operation-surfaces.adoc`;
- host and evidence readiness items in `OPERATIONAL_READINESS_CHECKLIST.md`.

This EPIC is the requirement baseline for autonomous setup. The canonical
`setup run` workflow-level orchestrator is implemented as a fail-closed,
live-consent-gated command, but this EPIC does not claim that the full live
runnable system is installed successfully.

The provider baseline is in transition. The current implementation remains
Multipass-centered, while the accepted target direction is `lxc_native`
through LXD or Incus as the planned default provider path. Multipass remains
the implemented provider surface until later slices move it behind an explicit
`multipass_legacy` selection path.

## EPIC Extensions

The service-access dashboard and Vaultwarden baseline extends this EPIC:

- `documentation/epics/service-access-dashboard-vaultwarden.md`

The extension defines a future service-access and credential visibility
capability for selected runnable profiles. It does not claim that Vaultwarden,
the service-access dashboard, routing, persistence, backup, readiness, or live
deployment is implemented.

## Relationship To System Unification

The system-unification EPIC defines the in-process boundaries that the setup
must preserve:

- Platform;
- Artifacts;
- Deployment;
- Shared;
- Console/status UI.

Autonomous setup is an execution goal built on those boundaries. It must not
extract new microservices, promote direct live scripts as canonical behavior,
introduce browser/React scope, or reintroduce Java/Maven structure into the
Python automation architecture.

## Mandatory EPIC Question

Does the implementation currently install Tiny Swarm World into the intended
runnable state?

```text
NO, FAIL-CLOSED ORCHESTRATOR IMPLEMENTED
```

The repository contains guarded workflow names, static preflight, command
safety concepts, inventory/evidence concepts, and blocked Platform,
Artifact, and Deployment contracts. The `setup run` command is listed by the
CLI, refuses missing live consent before setup service construction, and
orchestrates preflight, platform, artifact, deployment, and final verification
phases. Full live runnable setup still depends on later evidence for
command-backed platform verification, artifact publication, registry checks,
first-time stack bootstrap, and service readiness.

The accepted LXC-native provider direction is requirement drift that is now
tracked by ADR. The implementation does not yet default to LXD or Incus, does
not yet create LXC containers, and does not yet verify Docker Swarm inside
containers.

## Intent

Tiny Swarm World should provide one canonical setup path that can, after
explicit live-infrastructure consent, prepare a local Linux/WSL Docker
Swarm-first environment and verify that the selected system profile is
runnable.

The setup path must:

- validate host prerequisites before mutation;
- preserve existing live-consent controls;
- prepare or reconcile the selected provider's platform state only through
  governed Platform contracts;
- target LXC-native through LXD or Incus as the planned default provider path
  after the provider migration slices pass;
- keep Multipass available only through explicit legacy/fallback provider
  selection once the new provider contract is implemented;
- prepare artifact registry behavior through Artifacts contracts;
- deploy and verify service stacks through Deployment contracts;
- record redacted setup evidence under ignored local state;
- report actionable CLI or terminal-status progress and recovery guidance.

## Runnable State Definition

### Full Runnable State

The full runnable state is reached only when all of these facts are verified
through test-backed contracts or explicitly approved live smoke evidence:

- host prerequisites are satisfied for Linux or WSL;
- Python 3.12 runtime and project dependencies are available;
- the selected node provider prerequisites are satisfied and verified:
  currently Multipass for the implemented path, and later LXD/Incus capability
  gates for the accepted `lxc_native` target path;
- Docker CLI or Engine access required by the setup profile is available;
- required local ports are available or a tested alternative mapping is used;
- all required secret sources are present without committing secret values;
- platform VMs are created or reconciled without implicit destructive reset;
- Docker is installed and active where the profile requires it;
- Docker Swarm manager and workers are initialized or detected;
- Portainer is reachable;
- Nexus is reachable and artifact registry expectations are verified;
- Jenkins is reachable when included in the selected profile;
- RabbitMQ is reachable when included in the selected profile;
- SonarQube is reachable when included in the selected profile;
- Swagger/NGINX is reachable when included in the selected profile;
- service-access dashboard and Vaultwarden are reachable only if a later
  selected profile explicitly includes them and verifies stack registration,
  service readiness, credential-source availability, persistence ownership,
  backup/restore behavior, and redacted evidence;
- verification evidence is redacted and written only under
  `.tiny-swarm-world/evidence/live-installation/<run-id>/`;
- final setup status distinguishes `completed`, `refused`, `blocked`,
  `failed_to_apply`, `failed_to_verify`, and resource-gated outcomes.

### Resource-Gated State

Hosts that do not satisfy the full-run resource contract of 4 vCPU, 16 GiB
RAM, and 60 GiB free disk may not be reported as a full pass.

The setup may later support a reduced profile only when it is explicitly
approved and recorded as:

```text
PASS_WITH_RESOURCE_GATES
```

Resource-gated success must identify which services were omitted, why the
omission is acceptable, and which verification evidence was collected.

## Consent Model

Autonomous setup is not silent host mutation. Mutating setup execution must
preserve the current live-consent contract until a later ADR explicitly
changes it:

- `--live`;
- answer `y` at the short live-infrastructure confirmation prompt.

Missing consent must return `REFUSED_LIVE_CONSENT_MISSING` before any
Multipass, LXD, Incus, LXC container lifecycle, Docker Swarm, netplan, socat,
compose, stack, Portainer, Nexus, Jenkins, RabbitMQ, SonarQube,
Swagger/NGINX, image build, image push, or bootstrap command runs.

Non-interactive live execution is out of scope until a later workflow and ADR
define a separate consent contract.

## Credential And Configuration Model

Credentials and host-specific values must come only from operator-supplied
environment variables, command-line flags that do not persist values, or
ignored local files.

The current full guided setup profile selects `service-access` by default, and
the committed desired inventory is aligned with that profile. Required
password values must be operator-supplied and are not satisfied by committed
static defaults. For Vaultwarden, the committed default is the external Swarm
secret name
`tsw_vaultwarden_admin_token`; the Vaultwarden admin token value itself must
be operator-supplied and must not be committed.

The setup must not commit:

- passwords;
- tokens;
- Swarm join tokens;
- IP addresses or gateways that belong to a local host;
- user-specific absolute paths;
- raw command strings, stdout, stderr, or environment payloads;
- service bootstrap credentials.

Missing credentials must fail during preflight before stack deployment.

## Optional Live Smoke Boundary

The default development quality gate remains mocked or static. Optional live
smoke validation is a separate operator action and requires:

- explicit user approval for live infrastructure execution;
- disposable or recoverable local target environment;
- live consent;
- redacted evidence bundle;
- clear separation from `python3 tools/quality_gate.py quality`.

## Acceptance Criteria

- The autonomous setup requirement baseline is linked from the
  system-unification EPIC.
- Service-access dashboard and Vaultwarden are documented as the full guided
  setup's management surface, with live reachability scoped to observed smoke
  evidence and remaining host-forwarding gaps.
- Full runnable state and resource-gated state are explicit and testable.
- The setup preserves Platform, Artifacts, Deployment, Shared, and
  Console/status UI ownership.
- The setup documentation may claim the fail-closed `setup run` orchestration
  behavior that is implemented and tested, but it must not claim full live
  runnable success until later workflow slices implement and verify that
  evidence.
- Preflight failures identify host prerequisite, resource, secret,
  configuration, or consent blockers before mutation.
- Mutating setup phases use apply-then-verify semantics.
- A missing verification contract returns `blocked`, not success.
- Service health is never claimed without observed-state or smoke-test
  evidence.
- LXC-native through LXD or Incus is tracked as the planned default provider
  direction, while current implementation status remains explicit until later
  provider slices pass.
- Multipass fallback must be explicit and operator-visible; it must not hide a
  failed LXD/Incus readiness check.
- Direct scripts remain transitional, deprecated, or legacy until a later
  slice migrates behavior behind ports, adapters, tests, and consent controls.
- Documentation examples use POSIX paths and Linux/WSL command forms.

## Non-Functional Requirements

- Linux/WSL-only operation remains the baseline.
- Docker Swarm remains the current runtime target.
- Python automation remains the architecture driver.
- Setup orchestration uses asynchronous Python services where runtime
  orchestration is implemented.
- Verification evidence is deterministic, redacted, and local.
- CLI and terminal status output remain usable without relying on color alone.
- Quality gates must not run live infrastructure commands by default.

## Out Of Scope

- Live setup execution during Slice 01.
- Live LXD, Incus, LXC container, Docker-in-container, or Docker
  Swarm-in-container validation during Slice 01.
- Automatic host package installation.
- Non-interactive live consent.
- Kubernetes-first deployment.
- Browser React frontend work.
- Java-driven setup architecture.
- Microservice extraction.
- Direct promotion of scripts under `infra/prepare`, `infra/compose`, or
  `infra/swarm` as canonical setup behavior.
- Weakening `.importlinter`, architecture tests, or `QUALITY.md`.

## Stop Conditions

Stop execution when:

- runnable state cannot be tested or evidenced;
- minimum target profile is unclear;
- setup would require committed credentials or host-specific values;
- autonomous setup is redefined as silent host mutation;
- host package installation or non-interactive consent is introduced without
  ADR approval;
- direct scripts would bypass CLI consent controls;
- service health would be claimed without verification evidence;
- Vaultwarden or the service-access dashboard would be documented as
  installed, reachable, or production-like before evidence exists;
- planned behavior would be documented as implemented behavior;
- a change would weaken architecture or quality gates.
