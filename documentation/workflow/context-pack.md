# Context Pack — Issue #192

- Workflow: `issue-192-20260809`; chain order 06.
- Authoring branch: `feature/workflow-solid-refactor-chain-20260809`.
- Active workflow branch: `feature/separate-lxc-service-wrappers-solid`.
- Status: `COMPLETED_LOCAL_AUDITED`.
- Execution profile: `FULL_PATH`.
- Affected areas: LXC Portainer/Nexus wrappers, manager-IP resolver, local URL
  precedence, compatibility facade, composition and security tests.
- Forbidden areas: new HTTP API, live service access, browser React, deployment
  topology and unrelated DI/stack work.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester.
- Conditional roles: Senior Documentation Engineer, Senior Security Sandbox
  Engineer, Senior Execution Orchestrator.
- Quality commands: full local quality, targeted Python/architecture gates and
  `git diff --check`.
- Completion: all requirements are `VERIFIED_LOCAL`; Issue Completion Auditor
  result is `PASS`; #186 is the next serialized workflow.
