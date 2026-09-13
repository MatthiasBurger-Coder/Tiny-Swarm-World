# Remaining Risks — ARCH-03.06

- The concrete transport remains LXC-backed because that is the supported
  platform direction. Podman and Kubernetes are intentionally out of scope.
- Live Docker Swarm behavior was not exercised; existing mocked adapter tests
  and the local quality gate are the verification authority for this slice.
