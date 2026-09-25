# S352-01 configuration surface and mutation inventory

Verified baseline: ac011535; execution branch architecture/workflow-352-config-parsing-20260925.
Status: inventory accepted; implementation gaps remain OPEN.

| Surface | Loader and internal output | Consumer / earliest mutation | Classification and next slice |
|---|---|---|---|
| node-providers/provider_config.yaml | NodeProviderConfigYamlRepository.load -> NodeProviderConfig | composition_platform and composition_runtime; LxcNodeProvider rereads through _load_config for ensure/start/delete | Active typed boundary, coercion and stable-read hardening S03/S05 |
| inventory/desired_inventory.yaml | DesiredInventoryYamlRepository -> DesiredInventory.from_dict | No production caller found; repository tests only | Compatibility boundary S03; preserve missing/null defaults |
| ports.yaml | PortRegistryYamlRepository -> PortRegistry | Composition, Compose, provider exposure; separate installer line parser | Active typed boundary; reject bool-as-int/truthiness, unify installer owned-field reader S03 |
| services.yml | ComposeFileRepositoryYaml._enabled_service_names -> service-name set | Repository construction before deployment | Active selection input; silent filtering must fail closed S04 |
| installation-plan.yaml | No src/tools loader found; tests compare declarative contract | Runtime uses default_installation_plan in composition_setup | Declarative mirror, not unchecked application input; retain fixture compatibility |
| health-checks.yaml | Tests consume declarative readiness contract | No runtime filename reference found | Declarative mirror; no new runtime loader |
| validation-plan.yaml | Tests consume declarative evidence contract | No runtime filename reference found | Declarative mirror; no new runtime loader |
| secrets/infisical-secrets.yaml | LocalFileStorage.load_yaml -> raw PyYAML object -> SecretManifestRenderer | composition_deployment before secret synchronization; installer duplicates parsing/coercion | Active raw boundary; typed manifest model/port/adapter and both consumers S02 |
| selected compose/*/docker-compose.yml | ComposeFileRepositoryYaml -> StackDefinition / ComposeServiceDefinition | EnsureSwarmStack loads immediately before each deploy, after earlier mutators | Active typed boundary; reject malformed members S04, complete selection snapshot before mutation S05 |
| compose/traefik/dynamic/tls.yml | Traefik service input | Infrastructure/service-owned auxiliary payload | Pass-through, preserve provider schema ownership |
| compose/jenkins/image/casc.yaml | Jenkins service input | Image/service-owned auxiliary payload | Pass-through, no application interpretation |
| Operator environment / local shell file | EnvironmentConfigurationSource, ShellEnvFileConfigurationSource, CombinedConfigurationSource -> Mapping[str,str] | Configuration validation/composition; settings and required values before selected lifecycle mutation | Existing source parsing and precedence contract, audit S03/S05; validated typed mappings are allowed |
| simple_installer override files | load_operator_configuration -> shell source adapter | simple_installer before delegation | Existing mediated source; retain ownership/mode checks; no new simple_installer scope required |
| Retained command YAML | command_repository_yaml -> CommandEntity | command_workflow constructs repository before command execution | Dormant product catalogue, compatibility path still tested; validate whole input S03 |
| PortYamlRepository | Any create/load abstract methods | No source consumer/subclass found | Dormant contract; no active raw propagation demonstrated, do not remove gratuitously |
| Generic YAML builder | FluentYAMLBuilder / YAMLNode / YamlValue | Infrastructure utilities and tests, no external production consumer found | Infrastructure-only compatibility utilities |
| LXC profile/device output YAML | lxc/profile/policy.py and lxc_proxy_device_runtime.py | Observed command output within infrastructure | Runtime observation, not operator config; parser stays in infrastructure |
| LXC stack runtime YAML | lxc/swarm/swarm_stack_runtime.py parses StackDefinition.compose_content | Downstream typed opaque payload consumer | Validate TSW-owned fields earlier; S04/S05 protect stable content |

## Mutation boundaries and stable consumption

DeploymentApplyWorkflow runs prerequisite_checks, mutating pre_apply_steps,
pre_apply_checks, then individual apply steps. Static parsing must complete
before pre_apply_steps. Setup can mutate host/provider/network/artifacts before
its deployment phase, so deployment-only validation is insufficient. Setup
currently constructs separate Compose repositories for artifact preflight and
deployment; validation must freeze every selected consumer or share one snapshot.

Installer runs platform reset before setup run. Validate all selected static
configuration before reset, not only during setup. Dependency bootstrap and
sanitized evidence filesystem work are installation prerequisites, distinct
from managed lifecycle mutation; do not claim literally zero filesystem writes.
Runtime-dependent vault resolution retains its established readiness timing.

Provider ensure/start/delete rereads the shared configuration repository; a
validated snapshot mode within the repository, enabled by composition, can
prevent substitution without changing client internals. Operator settings and
selected Compose definitions likewise need stable consumption.

## Compatibility and scope decision

Preserve missing/null inventory and registry defaults, supported numeric
strings, environment precedence and safe shell parsing. Preserve Compose
extensions, anchors, interpolation and short/long port forms. Errors must not
expose raw secret values. No current application/domain ruamel import exists;
negative architecture probes should prevent future regression.

Requirement Engineer and System Architect independently accept the inventory.
No mandatory out-of-scope edit was found: S02–S05 contain the required model,
port, adapter, composition, installer and workflow files. A design requiring
LXC-client, artifact-composition, simple-installer, command-workflow or new
snapshot-file edits must stop for explicit reviewed scope correction. The
existing S04 stack_definition and port_compose_file_repository files can host
concrete snapshot contracts; no generic framework or new ADR is required.

R01/R03/R06/R10 have source-inspection evidence here; implementation and
behavior verification remain open until later slices. All R01–R11 must remain
represented in the issue matrix.
