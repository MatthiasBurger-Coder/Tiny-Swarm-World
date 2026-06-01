# Workflow Context Pack

Workflow: `portainer-admin-init-rejection-v1.0.0`

Branch: `feature/workflow-portainer-admin-init-20260601`

Process strand: `S3D`

Execution profile: `NORMAL_PATH`

Affected areas:

- deployment Portainer admin access
- application Portainer admin client port
- LXC-native Portainer admin adapter
- explicit Multipass legacy Portainer admin adapter
- workflow governance
- arc42 runtime and quality documentation

Forbidden areas:

- live infrastructure execution
- browser or React frontend
- Java, Maven, or Spring Boot structure
- Kubernetes-first behavior
- Windows-specific behavior expansion

Required roles:

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester
- Senior DevOps Engineer

Conditional roles:

- Senior Documentation Engineer
- Release and Branch Governance

Quality commands:

```bash
git diff --check
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_portainer_admin_access
PYTHONPATH=src python3 -m unittest discover -s tests/infrastructure/adapters/clients
python3 tools/quality_gate.py quality
```

Freshness rule:

- This context pack is stale when the active branch differs from
  `feature/workflow-portainer-admin-init-20260601`, when governing files change
  after this workflow is created, or when a slice attempts to write outside its
  declared scope.
