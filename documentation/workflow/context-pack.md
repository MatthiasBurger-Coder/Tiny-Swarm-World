# Context Pack: Replace RabbitMQ with Apache Pulsar

- Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`
- Workflow path: `documentation/workflow/workflow.md`
- Authoring branch: `feature/replace-rabbitmq-with-apache-pulsar-20260616`
- Required execution branch: `feature/replace-rabbitmq-with-apache-pulsar-20260616`
- Execution profile: `NORMAL_PATH` with serialized `LIVE_VALIDATION` slice.
- Status: `ACTIVE_RELEASED_FOR_WORKFLOW_EXECUTE`
- Dependencies: none
- Primary affected areas: `infra/config/**`,
  `src/tiny_swarm_world/domain/preflight/**`,
  `src/tiny_swarm_world/domain/deployment/**`,
  `src/tiny_swarm_world/domain/configuration/**`, `tests/**`,
  `documentation/**`, `README.md`, `AGENTS.md`, and
  `OPERATIONAL_READINESS_CHECKLIST.md`.
- Forbidden areas: Java/Maven/Spring Boot, React application setup,
  Kubernetes-first deployment, Multipass provider reintroduction,
  RabbitMQ compatibility fallback, Ansible, Windows-native behavior, committed
  secrets, and live infrastructure without explicit approval.
- Quality commands: `git diff --check`, `python3 tools/quality_gate.py test`,
  `python3 tools/quality_gate.py arch-tests`, and
  `python3 tools/quality_gate.py quality`.

Governing hashes are recorded in `context-pack.json`.
