# Slice 05 Consolidation

Workflow ID: `workflow-traefik-service-routing-20260627`
Slice ID: `05`
Slice title: Effective Access Evidence And Health-Check Model

Accepted changes:

- Corrected desired HTTPS ingress route overrides so Portainer, Jenkins,
  SonarQube, Nexus and Infisical use internal Traefik load-balancer target
  ports instead of direct diagnostic host ports.
- Added reusable static route/evidence assertions under
  `tests/integration/routing_contract.py`.

Verification:

- `PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state tests.domain.ingress.test_certificate`
- `python3 tools/quality_gate.py quality`

Result:

- Accepted. Domain ingress target ports now align with Issue #157 route
  semantics.
