# Test Findings

Required regression areas:

* `PlatformResetWorkflow` and `PlatformDestroyWorkflow` refuse without exact
  confirmation.
* Confirmed reset runs configured steps and verifies reset evidence.
* Already-missing managed resources are successful reset evidence.
* Reset failure prevents `setup run --live`.
* `install.sh` records reset, setup, artifact and deployment evidence.
* `install.sh` cannot report success when any selected artifact, deployment,
  or readiness target is blocked or failed.
* Existing update/reconcile tests remain valid.
* Portainer admin initialization stays redacted and safe around HTTP 409.
* Full guided setup acceptance covers service-access artifact image contracts,
  service stack contracts, service readiness targets and dashboard
  `index.html` packaging.

Tests must use fakes or mocked sessions. They must not execute live LXD,
Incus, LXC, Docker Swarm, compose, Portainer, Nexus, Jenkins, RabbitMQ,
SonarQube or service bootstrap commands.
