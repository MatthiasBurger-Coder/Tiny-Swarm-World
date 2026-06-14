# Issue 4 Swarm Stack Validation Baseline

## Decision

Issue #4 is implemented as repository-level validation of product compose stack
files loaded through `ComposeFileRepositoryYaml`.

The selected rule is:

- a stack compose file must define a mapping-valued top-level `services`
  section;
- each service in that mapping must define a mapping-valued `deploy` section;
- invalid stack compose files fail before deployment clients or live Docker
  commands are reached.

This is stricter than checking that a file contains one `deploy:` token. It
matches Docker Swarm stack intent better because each deployable service should
carry stack deployment metadata.

## Repository Evidence

Current product compose files:

- `infra/config/compose/infisical/docker-compose.yml`
- `infra/config/compose/jenkins/docker-compose.yml`
- `infra/config/compose/nexus/docker-compose.yml`
- `infra/config/compose/portainer/docker-compose.yml`
- `infra/config/compose/rabbitmq/docker-compose.yml`
- `infra/config/compose/service-access/docker-compose.yml`
- `infra/config/compose/sonarqube/docker-compose.yml`
- `infra/config/compose/swagger/docker-compose.yml`
- `infra/config/compose/traefik/docker-compose.yml`

All current product stack files already include `deploy:` sections. Existing
tests for `ComposeFileRepositoryYaml` already parse these files and assert
service names, published ports, stack contracts, Traefik labels, and packaged
service-access assets.

## Implementation Target

Add validation at the infrastructure repository boundary that reads structured
YAML and returns `StackDefinition`. This keeps YAML parsing in infrastructure,
keeps deployment application services dependent on ports, and fails before
Portainer or Swarm runtime adapters can apply an invalid stack file.

## Non-Goals

- No live Docker, Docker Swarm, Portainer, Nexus, or LXC operation.
- No compose file rewrite unless a fixture or product file is proven invalid.
- No Java, Maven, Spring Boot, React, Kubernetes-first, Multipass, or
  Windows-native behavior.

## Next Slice

Slice 02 should add the validation behavior and focused tests for:

- missing top-level `services`;
- non-mapping `services`;
- a service missing `deploy`;
- a service with non-mapping `deploy`;
- current committed stack files remaining valid.
