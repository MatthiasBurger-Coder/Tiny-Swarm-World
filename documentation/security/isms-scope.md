# ISMS-light Scope

## Purpose

ISMS-light makes Tiny Swarm World's security scope, assets, trust boundaries,
risks, controls, incidents, secret handling and risk acceptance explicit. It is
a local governance document and does not claim ISO/IEC 27001 certification or
prove that a control is deployed.

## In scope

- The repository, source/configuration artifacts and workflow evidence.
- The local Linux/WSL operator environment and generated local evidence.
- The Docker Swarm-first service-access stack.
- Infisical, Portainer, Nexus, Jenkins, SonarQube, Apache Pulsar,
  Swagger/NGINX and Traefik surfaces.
- LXC/LXD/Incus provider interactions, node identity, network and host metadata.
- Credentials, tokens, managed cryptographic material, local environment files, logs and
  redacted screenshots/evidence.
- Dependencies, container images and artifact sources.

## Out of scope

Unrelated host resources, production cloud deployment and an enterprise identity
provider are outside this scope unless a later approved workflow adds them.
A local configuration file or compose definition is not evidence that an
external service is running or secured.

## Asset classes

| Class | Examples | Protection concern |
| --- | --- | --- |
| Source and configuration | Python, YAML, compose, workflow and ADR files | integrity, review and path safety |
| Credentials and secrets | Infisical bootstrap material, catalog/admin credentials, tokens and managed cryptographic material | confidentiality, rotation and redaction |
| Infrastructure control surfaces | Docker socket, Incus/LXC provider, Traefik, Portainer | unauthorized mutation and privilege |
| Service data/metadata | Nexus, Jenkins, Pulsar, SonarQube, Swagger and access metadata | access control, integrity and exposure |
| Evidence artifacts | logs, summaries, screenshots, checksums and audit records | redaction, provenance and retention |
| Suppliers and images | dependencies, registries and container images | vulnerability and provenance |

## Trust boundaries

The S123-01 matrix records the detailed six-boundary model. The principal
boundaries are operator-to-automation, automation-to-provider, host-to-Docker
socket, Traefik-to-service ingress, secret-source-to-service/evidence and
repository-to-supplier/image. Each boundary requires explicit treatment and
evidence state; none is assumed secure merely because its configuration exists.

## Local-only assumptions

The supported operating model is Linux/WSL-only, Docker Swarm-first and managed
LXC through Incus as the provider direction. Live actions require explicit
consent and fail closed when consent, prerequisites or evidence are missing.
Security documentation stays compatible with the System Unification EPIC and
the existing Traefik HTTPS ADR. The EPIC is architectural context; #120 and
#123 remain issue authorities.

## Ownership and review

The Security Owner maintains risks and residual treatment. The Lead Architect
owns boundary decisions. The Senior Tester owns evidence review. The Workflow
Executor owns process gates. #126 owns the detailed ASVS/admin-surface
decision, and #150 may implement only an approved resulting design.
