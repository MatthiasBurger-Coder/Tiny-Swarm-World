# S355-01 lifecycle failure inventory and contract

Status: ACCEPTED in S355-01; Requirement, Architect, Python and Test reviews PASS.
Baseline: 05e3bc5646a1c37ce63c4c1287cde2e3d189ee90. Workflow version 1.0.
All paths below are relative to src/tiny_swarm_world unless tests/documentation
are explicit. Table shorthand: adapters/ means infrastructure/adapters/; ports/
means application/ports/; composition_* means infrastructure/composition_*;
platform/ means application/services/platform/; local_state_paths.py means
infrastructure/adapters/repositories/local_state_paths.py. Reachability is through composition into platform, artifacts,
deployment and setup. Installer and simple-installer consume their child exits.

## Contract fixed before implementation

application/ports/operation_result.py owns these immutable types:

- OperationOutcome: success, failed, partial, rolled_back, blocked, refused.
- Recoverability: recoverable, nonrecoverable, unknown.
- OperationFailure: operation, component, cause, recoverability, recommended_action.
- OperationResult: outcome; failures tuple; completed_operations tuple;
  pending_operations tuple; uncertain_operations tuple; rollback_verified bool.
- OperationError: application-owned exception carrying .failure with safe static
  text. Compatibility bridge types retain existing public imports and catch types.

Use stable constrained identifiers and a declared cause/action catalogue. No raw
exception, command, credentials, path, stdout/stderr or arbitrary str(exc) enters
public fields. Use deterministic fresh list/string serialization under additive
operation_result; preserve all legacy fields and constructor defaults.

Success has no failures, pending or uncertain requested work. Partial requires
confirmed completed requested work plus an incomplete request. Passed guards alone
are not completed requested work. Failed and partial each require at least one structured failure. Failed cannot erase confirmed completed work. rollback_verified is false for every outcome except rolled_back.
Blocked/refused before execution is distinct; legacy blocked after completed work
maps to common partial while retaining legacy blocked. Unknown effects are retained
as uncertain_operations and never invented as successful mutation. Rolled_back
requires rollback_verified and no unresolved pending/uncertain work; producer tests
must prove observed original-image convergence. No-op verified recovery may require
no new mutation. Retain original failure context where available even after recovery.
Multiple origin failures remain separate rather than overwritten by outer wrappers.

Expected typed OperationError is handled before existing broad compatibility catches.
Existing catches of unexpected RuntimeError keep their returned failure/exit behavior
but use unexpected_failure, unknown recoverability and static guidance. Errors which
currently propagate (including composition/programming faults) must continue to do
so. Never convert all ValueError/RuntimeError into expected adapter failure. Cancellation,
KeyboardInterrupt and SystemExit propagate through adapters/workflows; entrypoints
retain explicit interruption codes. Suppress unsafe outward cause chains.

## Boundary catalogue and migration ownership

| Boundary / concrete files and symbols | Current behavior and consumers | Migration / owning slice | Verification |
|---|---|---|---|
| application/ports/commands/port_command_runner.py; infrastructure/adapters/command_runner/async_command_runner.py; adapters/exceptions/exception_command_execution.py | AsyncPortCommandRunner feeds command workflow/UI; infrastructure exception crosses port | S02: bridge CommandExecutionError to application-owned failure, retain public attributes/import/text and run signature | async command runner and command_runner_ui_failure_semantics suites |
| infrastructure/process/{runner,async_runner,streaming}.py | Central #354 subprocess owners; classify launch/timeout/nonzero and clean cancellation | Already structured infrastructure-private execution facts; preserve, no redesign. Adapter converts at port | tests.infrastructure.process.test_execution_contract |
| adapters/clients/lxc/command/{node_command,manager_shell_gateway,backend_cli}.py | LxcNodeCommandResult loses failure_hint; manager gateway generic RuntimeError reaches runtime/image/stack adapters | S03 preserve launch/timeout code and translate expected command errors; retain successful stdout data | clients.lxc.command.test_node_command plus gateway consumers |
| adapters/clients/{lxc_node_provider,lxc_container_docker_runtime,lxc_container_swarm_bootstrap,lxc_swarm_runtime,lxc_proxy_device_runtime,docker_swarm_runtime,docker_cli_runtime}.py and clients/lxc/{docker,swarm,images}/** | Provider/runtime facts and command outcomes feed platform reconciliation, deployment and artifact mutation | S03 retain domain condition codes; translate remaining expected infrastructure exceptions into declared port failures. Existing domain facts stay domain-only; S04/S05 aggregate | matching provider/runtime/stack/image suites |
| adapters/clients/{nexus_http_client,portainer_http_client,sonarqube_http_client,infisical_bootstrap_http_client,infisical_cli_client,infisical_playwright_client}.py; clients/lxc/services/** | Service readiness/bootstrap and secret/image steps; HTTP/process errors and capability-specific rejection types | S03 preserve existing typed port errors/rejection semantics; translate expected request/process failures still unclassified; no credential/browser behavior expansion | matching client tests and deployment service suites |
| adapters/update/lxc_runtime_observer.py; ports/update/port_update_runtime_observer.py | UpdateObservationError and UpdateObservationChanged are application owned; unsafe chained technical error possible | S03 attach safe context while preserving subtype and bounded reread behavior | tests.infrastructure.adapters.update.test_lxc_runtime_observer |
| adapters/update/json_state_store.py; ports/update/port_update_state_store.py | None for missing state; ValueError for corrupt state; OSError for storage failures; update catches these | S03 typed ValueError/OSError-compatible bridges, safe cause chain, atomic/private storage unchanged. S04 consume cause while preserving state_not_found blocking | tests.infrastructure.adapters.update.test_json_state_store; test_classic_update_workflow |
| adapters/configuration/configuration_sources.py; ports/configuration/**; composition_runtime.py::_FrozenConfigurationSource | Typed configuration errors plus parse/file failures feed preflight/setup | S03 compatible typed mapping at boundary; S04 preflight preserves underlying safe cause | configuration tests; test_preflight_service; test_composition_configuration |
| adapters/repositories/{desired_inventory_yaml_repository,node_provider_config_yaml_repository,port_registry_yaml_repository,compose_file_repository_yaml,secret_manifest_yaml_repository,installer_configuration_repository,command_repository_yaml}.py | #352 safe validation types; file/parser failures consumed by selected configuration validation | S03 retain existing defaults/missing-file contracts and domain validation errors; attach/translate only expected boundary failures needed by lifecycle, no parser change | existing repository tests, #352 valid/invalid fixtures |
| adapters/repositories/{observed_inventory_local_repository,verification_evidence_local_repository,routing_evidence_local_repository,performance_evidence_local_repository,project_filesystem_evidence_local_repository}.py; local_state_paths.py | Observe/state/evidence persistence called from workflows; expected filesystem failures may escape | S03 map expected storage failures at adapter; preserve protected paths, atomicity, redaction and stored schemas | matching local-repository tests |
| ports/file_management/port_local_file_storage.py; adapters/file_management/local_file_storage.py | Secret/config/evidence deployment uses read/write/scan/directory operations with filesystem errors | S03 new narrow typed storage bridge; preserve missing read semantics and cleanup | NEW tests.infrastructure.adapters.file_management.test_local_file_storage; deployment secret management |
| adapters/preflight/host_preflight_probe.py | Platform preflight reads memory/disk/environment; OSError from probes can escape | S03 safe expected probe failure mapping, no runtime policy changes; S04 application interpretation | tests.infrastructure.adapters.preflight.test_host_preflight_probe |
| adapters/preflight/artifact_readiness.py | Setup artifact contract guard maps broad exception to UNKNOWN | S03 distinguish expected safe cause versus unexpected failure while preserving UNKNOWN behavior | tests.infrastructure.adapters.preflight.test_artifact_readiness |
| adapters/preflight/{lxc_provider_preflight,artifact_source_readiness,secret_storage_probe,windows_wsl_bridge_state}.py; preflight/service_probes/** | Already return capability-specific preflight/readiness facts for setup guards | Preserve domain facts and guards; inventory expected leaks at execution, no new provider/UI behavior. Application maps existing facts in S04/S05; any necessary additional adapter edit needs reviewed scope | existing matching preflight tests |
| ports/network/port_wsl_socat_exposure.py; adapters/network/wsl_socat_exposure.py; composition_runtime.py::_WslSocatExposeStep | Platform exposure/setup consumes bool/status, losing transport cause | S03 retain successful bool compatibility, translate expected failures and expose static cause; no port-forward execution in tests or policy change | tests.infrastructure.adapters.network.test_wsl_socat_exposure; tests.infrastructure.test_composition |
| composition_probes.py::EndpointReadinessCheck/_endpoint_status | Already translates RequestException/Timeout to safe status evidence | Preserve safe domain evidence; explicit application mapping in S05. S03 edits only if required to retain classification, no retries/endpoint behavior change | tests.infrastructure.test_composition_probes |
| adapters/host/wsl_host_preparation.py; ports/host/port_host_preparation.py | Setup reaches legacy WindowsCommandRunner conversion via WslHostPreparation; OS/timeout failures may precede typed result | S03 translate at existing preparation boundary with compatible declared failure, no new Windows surface | tests.infrastructure.adapters.host.test_host_preparation |
| application/services/platform/workflow/{runtime,results,outcomes,update,verify,init,mutating,destructive}.py; platform/incus/lxc_docker_install.py; platform/preflight_service.py | Existing status families/broad catches, executed and domain evidence; recover observes convergence | S04 expected failure aggregation, truthful completed/pending/uncertain outcomes and verified rollback. Preserve lifecycle.py dispatch | platform workflows/lifecycle/classic_update/lxc_docker_install/preflight tests |
| application/services/artifacts/** | Prepare/bootstrap/verify wrappers with free reason/message and verification facts | S05 shared result and child-context propagation; preserve bootstrap prefix and mutation ordering | artifact workflows/readiness/ensure_image suites |
| application/services/deployment/** | Preparation/apply/verify, HTTP/secret/runtime steps and timeout outcomes | S05 shared result and typed failures; no dropped nested cause; existing preparation and verify ordering | deployment workflows and affected step suites |
| application/services/setup/** | Phases/group concurrency, broad caught failures, timeout/cancellation and nested results | S05 aggregate confirmed requested work and pending/uncertain effects, retain origin failures and deterministic group ordering | tests.application.services.setup.test_setup_workflow |
| __main__.py; installer.py; simple_installer.py; adapters/ui/install_reporter.py; ports/install_reporter.py | CLI completed->0, other returned workflow statuses->1, consent/confirmation->2; installer child/124/130; human output default | S06 additive structured opt-in and safe guidance; verified recovery completed/0 preserved; retain composition failures that currently propagate | package_entrypoint, classic_update_cli, installer, simple_installer, install_reporter suites |

All directory-wide scopes are restricted to these reachable operation-boundary
concerns. Unrelated client APIs, unused YAML compatibility, developer bootstrap tools,
network doctor/repair commands outside lifecycle, and process-runner internals are
not blanket migration targets. Domain validation/condition types are already explicit
facts: application maps them, never adds application imports into domain.

## Representative cause/action catalogue

S02 fixes the reusable catalogue; S03 adds inventory-specific constants with tests.
The following distinctions must survive (safe guidance is static per cause):

| Cause | Recoverability | Recommended action |
|---|---|---|
| launch_executable_missing | nonrecoverable until corrected | Install the required executable and retry after prerequisites pass. |
| launch_permission_denied | nonrecoverable until corrected | Check executable permissions and rerun prerequisite checks. |
| launch_os_error | unknown | Inspect local execution prerequisites before retrying. |
| process_timeout | unknown | Inspect operation state before retrying; effects may be incomplete. |
| process_exit_failed | unknown | Inspect redacted evidence and correct the failed operation. |
| filesystem_error | unknown | Check storage access and available space before retrying. |
| configuration_invalid / state_invalid | nonrecoverable until corrected | Correct the selected configuration or preserve invalid recovery state for diagnosis. |
| observation_unavailable / observation_changed | unknown | Refresh observed state before deciding whether to retry. |
| dependency_unavailable / request_failed | unknown | Check service readiness and connection settings. |
| verification_failed | unknown | Inspect verification evidence and actual target state. |
| refused / blocked | nonrecoverable until prerequisite/consent supplied | Review required consent or prerequisites before rerunning. |
| unexpected_failure | unknown | Inspect redacted diagnostic evidence; do not assume retry is safe. |

Recoverability expresses diagnosed potential, not authorization or an automatic
retry policy. Unknown must not be upgraded from raw exception class guessing.
Missing state file stays None; invalid stored state remains blocked/no mutation but
retains state_invalid. Existing observer changed subtype keeps its bounded behavior.

## Scope corrections reviewed during S355-01

Add to S355-03 only the file-management port/adapter/new tests, preflight host and
artifact probes/tests, WSL Socat port/adapter/tests, WSL host preparation port/adapter/tests,
and the named composition adapter helpers/tests. No runtime behavior expansion.
Architect accepts translation-only scope; final Four-Role inventory review gates
acceptance. No product edits occurred during discovery. If later inventory reveals
another required boundary, stop and obtain a similarly reviewed scope amendment.

## Verification and completion limits

S355-01 architecture gate: 26 tests PASS. Inventory is static source review, not
proof of future implementation. R355-01–15 remain OPEN until subsequent slices.
Final audit must reconcile every row with changed code/tests or documented existing
compliance. Original issue acceptance cannot be reduced to representative scaffolding.

## Final reachability refinements from Python review

The catalogue groups candidate boundary families; these explicit classifications
override any implication that every grouped file requires a change:

- desired_inventory_yaml_repository.py, observed_inventory_local_repository.py and
  performance_evidence_local_repository.py: no construction in current composition
  or runtime entrypoint. Out of default lifecycle migration; retain existing tests.
- docker_cli_runtime.py: no default construction; LXC runtime is wired. Legacy
  compatibility only. docker_swarm_runtime.py: transparent LXC delegation; verify
  translated failure passes through without a new wrapper.
- secret_manifest_yaml_repository.py: existing domain validation exception already
  translates parse/read failure. Preserve it; map at application/installer consumer.
- project_filesystem_evidence_local_repository.py: existing application-owned
  ProjectFilesystemEvidenceError. Preserve hierarchy; enrich only as needed.
- provider, container Docker/Swarm, proxy, provider preflight, artifact source,
  secret-storage and native-host preparation already produce explicit domain facts.
  Preserve and map at application aggregation; never import application into domain.
- EndpointReadinessCheck already produces safe endpoint evidence; no adapter edit
  is mandatory if application mapping preserves it.
- command_repository_yaml.py: optional compatibility surface. composition_platform.py
  constructs CommandWorkflow at line 155 and exposes it at line 398, but its repository
  factory is lazy and none of the four lifecycle workflow implementations uses
  .command_workflow. command_verification.py offers optional helpers only. Therefore
  it is not executed on default four-family paths; preserve its existing contract
  and tests. No FileManager/FileLoader migration is needed for this issue.
- Internal LXC args/backend_cli/diagnostics/node/profile/resource helpers stay internal;
  translate at their application-facing adapter, no blanket helper migration.
- host diagnostics and network doctor/repair are separate diagnostic commands.
  They do not require this lifecycle migration.

Known test naming: host uses test_host_preparation; LXC services use
clients.lxc.services.test_lxc_service_clients; inventory uses
repositories.test_inventory_repositories; command repository uses
repositories.test_command_repository_yaml_contract. LocalFileStorage test is new.

Additional edge cases: pgrep exit 1 means absent process, not launch failure;
missing update state returns None; changed observation preserves bounded reread;
existing bool readiness probes retain boolean contracts and require mapping of
safe known status rather than new exceptions for ordinary unready state.

## S355-03 implementation reconciliation

LXC command facts now retain available failure_hint; gateway, container, image and
service operations translate expected technical failures. Domain-returning
provider/Docker/Swarm/proxy facts retain existing collapsed classifications; S04/S05
map those truthfully and must not claim exact missing/permission causes that are
not available. Update observation preserves its changed subtype and originating
failure; state errors retain ValueError/OSError compatibility. HTTP/CLI/browser
remote data parsing uses safe capability errors. Configuration, evidence and local
storage translate expected failures without changing stored formats; atomic failure
preserves prior data and cleanup preserves active cancellation/control flow.
Host/preflight and Socat expected failures carry safe causes. Socat absence (pgrep 1)
remains false; composition catches typed startup failures and preserves counts/status.

Existing compliance/exclusions above remain: unreachable repositories, optional
command repository, domain secret-manifest validation, endpoint readiness facts
and transparent runtime delegation are preserved. This is not a claim of new
classification detail in unchanged domain facts.

Intentional diagnostic corrections: gateway timeout omits raw worker identity;
missing Portainer endpoint omits resource names; storage omits raw OS messages.
Numeric HTTP status and safe static JWT/Swarm messages are retained. Direct Socat
execution failures are now typed, with compatible workflow handling.

Test evidence: metadata targets (86, 84, 18), expanded adapter family (172),
configuration repositories (105); suites overlap. Named tests include
tests.infrastructure.adapters.exceptions.test_operation_failure_mapping,
tests.infrastructure.adapters.file_management.test_local_file_storage and
tests.infrastructure.test_composition; individual boundary coverage is backed by
the full gate and existing matching suites. Final application result aggregation
remains S04/S05; issue completion remains S07.
