# Context Pack: Live Greenpath Repair Loop

- workflow_id: live-greenpath-repair-loop-20260606
- workflow_version: 1.1.0
- branch: feature/live-greenpath-repair-loop-20260606
- execution_profile: FULL_PATH
- process_strand: Python automation, LXC-native runtime, Docker Swarm live verification, service-access browser verification, Vaultwarden credential inventory verification
- required_roles: Senior Workflow Architect, Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior React Frontend Developer, Senior Tester, Senior DevOps Engineer, Senior Documentation Engineer
- conditional_roles: Secrets and Config Management, Quality Gate owner, Root Architect escalation
- forbidden_areas: Java, Maven, Spring Boot, Ansible, Kubernetes-first migration, React frontend, safety guard weakening, dashboard password rendering, committed secrets
- quality_commands: `git diff --check`, targeted unittest, `python3 tools/quality_gate.py test`, `python3 tools/quality_gate.py quality`, `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1 PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live`

## Affected Areas

- `src/tiny_swarm_world/**`
- `infra/config/**`
- `tests/**`
- `tests/live/**`
- `documentation/workflow/**`
- `.tiny-swarm-world/evidence/**` as ignored local runtime evidence only

## Forbidden Areas

- Java, Maven, Spring Boot, React, TypeScript, Vite, TSX/JSX, Ansible, Terraform.
- Live infrastructure mutation without the workflow's explicit consent path.
- Password value display outside Vaultwarden's authenticated UI.
- Committed Vaultwarden admin tokens, service passwords, raw environment payloads, credential-bearing URLs, local IP addresses, or host-specific paths.

## Governing File Hashes

```text
d733bb2af3ebffc41b006039c318dc5253511839410f3cffebe4404b0ac51a34  AGENTS.md
458e5f4d8fbdedea1c413e1ff135ec91392a4bb5a5aea20300dcac8e209414b6  QUALITY.md
bcbafb53a543d66b660dc50fc9e85712fefcc07568388192fc8e89b3625d808a  .agents/prompts/workflow-create.md
c11b3df9e77717bad7caacb464b74db4566b00c7794cea53e2dbe39a8065e71a  .agents/orchestrator/routing-rules.md
087658240296e3b1ec74205c60a96a9a4c67a17cf653f7867e6f316bd9afa94e  .agents/skills/workflow-authoring/SKILL.md
23de7d9aac9d2694eae26fac2765d65f369c101ac348dac24d5f3bbe9e2d3ba4  .agents/skills/three-amigos-requirement-gatekeeper/SKILL.md
b554ffd4c3c8de9b313b55d8a9c99deda8c3bf3910f559105000e338680263e9  .agents/skills/execution-profile-router/SKILL.md
f9b4bcb8f950d1a52b1a4e29c14146966f325ad37656d38abf54bd9759f84eaf  .agents/skills/secrets-and-config-management/SKILL.md
dae7115594172e159c051c3ece15c0b535f1570efbb28fc67440aef0bbadc9c9  documentation/process/workflow-create.md
2d75afaced2c8c68fc8071a6b1c9782d6b3a931264562f2f43fdf05f0ced24f5  documentation/process/branch-governance.md
026a1c3349d19601b8b0d3733649206b9b53a0c5a0536b086dbe62feffbc6307  documentation/epics/autonomous-runnable-setup.md
9c93d460a92630f485c0672f26810ecb4832c69d21a8f6f0941dffa4aacd1606  documentation/epics/service-access-dashboard-vaultwarden.md
aa54aba46e870c27fe6c8cc80f64cf50100d7c8726f28de0b89beabbc86913c9  documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc
a8c9c30c39647377222643df06abe7bd2751e0814f70c4503fc9b6d73366b09c  documentation/arc42/09_architecture_decisions.adoc
0856922c1ab9967003993020f9ed932d1d119119055b09a8c047fdc6818d5fd4  documentation/arc42/10_quality_requirements.adoc
84d641cf72b49260f4baf4d4b81b3ba9fefbd83c8a8d57dcc9f4a192cc4dbb08  documentation/arc42/11_risks_and_debt.adoc
```

This context pack is a navigation aid only. Root `AGENTS.md`, `QUALITY.md`,
ADRs, arc42, and `documentation/workflow/workflow.md` remain authoritative.
The context pack is stale when any recorded hash changes, when governance
documents change, or when a conflict is detected.
