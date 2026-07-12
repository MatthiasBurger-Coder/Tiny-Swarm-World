# Routing Evidence Verification

- Runtime path: `.tiny-swarm-world/evidence/solid-typed-evidence/routing/effective-access-model.json`
- Producer: productive deployment pre-apply use case
- Runtime integration: final `deployment apply` exit 0
- Result: PASS

Verified required fields:

`evidence_kind`, `generated_at`, `service_profile`, `public_ports`, `gateway_public_ingress_ports`, `diagnostic_fallback_ports`, `service_access_preferred_url_source`, `routes`, `health_check_targets`, `service_access_links`, `skipped_routes`, and `result`.

Observed model:

- routes: 9
- service-access links: 9
- skipped routes: 4
- skipped reasons: `api`, `app`, `grafana`, and `prometheus` are `service_not_enabled`
- preferred links contain neither port 10080 nor 10443
- route, link, health-target, and skipped-route collections are deterministically sorted
- 15 loaded secret values were checked against serialized evidence and rendered dashboard; none occurred
- credential labels and Infisical item references remain available through the redacted model

`ROUTING_EVIDENCE_PASS routes=9 links=9 skipped=4 secret_values_checked=15`.
