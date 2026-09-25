# Workflow context pack

Workflow: issue-352-configuration-parsing-boundary; version 1.0; branch `architecture/workflow-352-config-parsing-20260925`.
Process: workflow execute; profile FULL_PATH; status BLOCKED_SCOPE_APPROVAL.
Implementation: see Execution Progress in workflow.md. Source baseline: `33aaafd5b80a3f316f4d650a9a831734dc7077e0`.

Affected areas: configuration adapters/models/ports, composition, selected
setup/platform/deployment and installer validation consumers. Forbidden: live
infrastructure, runtime/provider replacement, credential-policy changes,
unrelated work, Java/React/Kubernetes expansion.

Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester.
Conditional: DevOps for runtime contracts, security for secrets/error changes,
Console/status UI only for verified interaction/output impact.
Quality: `git diff --check`, `python3 tools/quality_gate.py quality`;
per-slice targeted commands are in workflow.md.

[context-pack.json](context-pack.json) records SHA-256 hashes for governing
files, checked architecture references and workflow artifacts. It is a navigation
aid, not authority. Any hash change, governance edit or conflict invalidates it;
reread changed authority and refresh only after review. Root AGENTS.md,
QUALITY.md, ADRs and skills remain authoritative.

Execution status: S352-01 through S352-04 accepted. S352-05 awaits approval of the two-file scope correction recorded in workflow.md; S352-06 remains unstarted.
