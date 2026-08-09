# Requirement Matrix — Issue #156

Source: [GitHub Issue #156](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/156)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-156-01 | Every directly published external Docker port resolves from the central port configuration. | functional | `infra/config/ports.yaml`, Compose repository/renderer | S156-02/S156-05 | registry-to-renderer contract tests | PLANNED |
| REQ-156-02 | Internal container target ports remain image-compatible and are not blindly replaced. | architecture | Compose definitions and resolver | S156-03/S156-04/S156-07 | target/published assertions | PLANNED |
| REQ-156-03 | Legacy hard-coded external defaults are classified and removed from the active direct-publish path. | functional | Compose/config/service metadata | S156-01/S156-06 | inventory and negative scan | PLANNED |
| REQ-156-04 | Direct URLs, smoke checks and health checks use the effective published port map. | functional | deployment/access model/readiness paths | S156-05/S156-07 | URL/health tests | PLANNED |
| REQ-156-05 | Evidence output includes the effective direct published-port map. | observability | evidence writer and deployment result | S156-05/S156-07 | serialized evidence assertion | PLANNED |
| REQ-156-06 | Pulsar remains the messaging service; RabbitMQ must not be reintroduced or published. | architecture | Pulsar Compose/config and negative checks | S156-04/S156-06/S156-07 | config scan and tests | PLANNED |
| REQ-156-07 | Jenkins publishes 11080 and 11050 while preserving image targets. | functional | Jenkins Compose | S156-03/S156-07 | Compose contract test | PLANNED |
| REQ-156-08 | SonarQube publishes 12000 while preserving its target. | functional | SonarQube Compose | S156-03/S156-07 | Compose contract test | PLANNED |
| REQ-156-09 | Nexus publishes 13081, and 13500/13501 when Docker ports are enabled. | functional | Nexus Compose | S156-03/S156-07 | Compose contract test | PLANNED |
| REQ-156-10 | Pulsar broker/admin/GUI use 14001/14080/14081 when direct access is enabled. | functional | Pulsar Compose | S156-04/S156-07 | Compose contract test | PLANNED |
| REQ-156-11 | Prometheus and Grafana use 15090 and 15300. | functional | observability Compose/config | S156-04/S156-07 | Compose contract test | PLANNED |
| REQ-156-12 | Gateway and Swagger direct ports use 10080/10443 and 16080/16081 as applicable. | functional | Traefik/Swagger Compose | S156-04/S156-07 | Compose contract test | PLANNED |
| REQ-156-13 | Scope excludes Incus/LXC setup, Docker installation, Swarm bootstrap, install order, Traefik routing redesign and local DNS. | non-goal | all touched files | S156-01/S156-08 | scope review and changed-files audit | PLANNED |
| REQ-156-14 | Quality gate passes or environment blockers are classified under `QUALITY.md`. | quality gate | repository gate | S156-07/S156-09 | targeted/full gate evidence | PLANNED |

