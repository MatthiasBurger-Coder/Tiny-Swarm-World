# Requirement Findings

Decision: `READY_FOR_WORKFLOW`

Confidence: 93 percent.

Findings:

* `install.sh` must mean fresh installation.
* Reset is mandatory before setup starts.
* After reset, `install.sh` must complete the selected setup profile rather
  than only reaching platform bootstrap.
* The default profile is `service-access`, so full install acceptance includes
  Portainer, Nexus, Jenkins, RabbitMQ, SonarQube, Swagger, and the
  service-access stack.
* The service-access dashboard `index.html` is part of the install acceptance
  path because it must be image-packaged into the dashboard service.
* Existing update/reconcile mechanisms should be preserved unless they block
  the fresh-install path.
* The Portainer HTTP 409 failure is treated as stale persisted state or
  credential mismatch evidence. The first response is therefore reset-before
  setup, not Portainer-only idempotency.
* Destructive behavior remains live-consent and confirmation gated.

Non-goals:

* No live infrastructure execution during workflow creation.
* No Multipass, Java/Spring, React, or Kubernetes-first scope.
