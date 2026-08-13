# S150-01 Distribution Evidence

## Slice

Architecture, security boundary, route/auth decision, ADR and arc42 scope.

## Streams

The slice is intentionally serialized because route, authentication, secret
and ADR decisions share the same contract lock. A parallel implementation
stream would risk contradictory security decisions. Role-based fallback review
was performed by the workflow executor for Requirement Lead, System Architect,
Security/ASVS and Documentation owners.

## Result

- approved route: `Host(traefik.tsw.local)` on `websecure`;
- upstream: `api@internal`;
- authentication: BasicAuth users file from external Docker secret;
- no `api.insecure`, no extra dashboard port;
- Service Access and existing HTTPS ingress remain preserved;
- live/browser verification explicitly remains outside this slice.
