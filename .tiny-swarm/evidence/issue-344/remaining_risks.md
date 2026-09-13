# Remaining Risks — #344 / ARCH-03.01

- The audit documents the composition cycle but does not remove it. Breaking
  the cycle is ARC-04 work and must preserve compatibility patch points.
- Root-level boundary bypasses remain until ARC-02 and ARC-03 introduce and
  enforce explicit CLI and installer ownership.
- The existing architecture gate protects the inner hexagonal layers more
  strongly than the executable edge. ARC-05 should add root-boundary contracts
  before structural extraction begins.
- The five-module cycle was identified by a source-level AST graph. Runtime
  import behavior and compatibility patch semantics should be covered by
  targeted tests during ARC-04.
- Full local verification does not provide live Linux, Incus, Docker, browser,
  or SonarQube evidence. Those states remain outside this issue's scope.
