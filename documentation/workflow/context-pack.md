# Workflow Context Pack

Workflow ID: `remove-port-vm-repository-yaml-v1.0.0`
Branch: `fix/workflow-remove-port-vm-repository-yaml-20260627`
Created: 2026-06-27

## Purpose

This context pack supports the workflow that safely removes the unused concrete `PortVmRepositoryYaml` infrastructure adapter after re-verifying that no runtime, test, or documentation dependency still requires it.

## Active Workflow

- Workflow file: `documentation/workflow/workflow.md`
- Execution profile: `FULL_PATH`
- Process strand: workflow create -> workflow execute
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior React Frontend Developer, Senior Tester
- Conditional roles: Senior Documentation Engineer, Quality Gate Orchestrator

## Affected Areas

- `src/tiny_swarm_world/infrastructure/adapters/repositories/vm_repository_yaml.py`
- `src/tiny_swarm_world/application/ports/repositories/port_vm_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/command_runner/command_workflow.py`
- `documentation/architecture/responsibility-separation-analysis.md`
- `documentation/arc42/02_constraints.adoc`
- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`

## Forbidden Areas

- Live LXD, Incus, LXC, Docker Swarm, compose, Portainer, Nexus, Jenkins, Pulsar, SonarQube, netplan, and socat operations.
- Java, Maven, Spring Boot, Gradle, JUnit, or ArchUnit project structure.
- Browser React frontend work.
- Application-to-infrastructure imports.
- Domain-to-application or domain-to-infrastructure imports.

## Quality Commands

```bash
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py quality
git diff --check
```

## Source Hashes

```text
AGENTS.md D1A58A10809EE76DC033180BB895A24F5FEE79D3203619BD72F1A96891FF033E
QUALITY.md 458E5F4D8FBDEDEA1C413E1FF135EC91392A4BB5A5AEA20300DCAC8E209414B6
.agents/skills/workflow-authoring/SKILL.md 5EF238CA8A98D08A3594906E5A30100649D4C09E64A01B377D690F6580B1CA03
.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md 23DE7D9AAC9D2694EAE26FAC2765D65F369C101AC348DAC24D5F3BBE9E2D3BA4
.agents/skills/execution-profile-router/SKILL.md B554FFD4C3C8DE9B313B55D8A9C99DEDA8C3BF3910F559105000E338680263E9
.agents/orchestrator/routing-rules.md BA3563181DB98DF3F6A1872D676006CF57CC1603C1B0B74D4C41CD3DB02A60A5
documentation/process/branch-governance.md 3332F0FB56E7A72FEE3A9B6E89C4D9D5C3BF1198B375CE4D2BBD5C7350588A83
documentation/arc42/02_constraints.adoc DE43DE687094637A82C22306F066AD4F9850619ED433724034F0FC10E2AB5C56
documentation/arc42/05_building_blocks.adoc C94B0A20A3264AA6F88F80BC6657E5921E4F6CDB9C151AE851AB7DBCA991633A
documentation/arc42/11_risks_and_debt.adoc CBA93D3929446C09B576141A7FADA9440BB467F7C8F95A26342E6CE3C1E4E504
documentation/epics/system-unification.md 25F81D22C36CFE61933681B2C3A9EF3FAEB4556947B22DA4FD66AEA6AC5B8DE4
```

## Staleness Rules

This context pack is stale when any recorded hash changes, when the active branch differs from `fix/workflow-remove-port-vm-repository-yaml-20260627`, or when execution discovers a real `PortVmRepositoryYaml` consumer.
