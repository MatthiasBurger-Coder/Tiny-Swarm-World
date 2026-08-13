# Issue #126 Remaining Risks

| Risk | State | Next owner/action |
| --- | --- | --- |
| Exact #150 dashboard route and authentication/authorization design | Open/future | #150 must decide and evidence the approved design before exposure. |
| Docker socket and admin-surface privilege | Open | Carry RISK-123-DOCKER-SOCKET into #150 and apply compensating controls. |
| Service-specific authn/authz and token rotation | Evidence pending | Verify per service under the later live-evidence contract. |
| TLS/route ownership and external exposure | Open | Preserve the Traefik HTTPS ADR and add only verified decisions. |
| ASVS runtime verification | Deferred | Use applicable local/live evidence; no certification claim is made here. |

These risks remain open or evidence-pending and are not accepted by the
existence of this mapping.
