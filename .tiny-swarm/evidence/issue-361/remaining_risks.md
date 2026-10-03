# Issue #361 remaining risks

- AST branching is a source indicator, not a precise runtime control-flow or
  cognitive-complexity score. Exact normalized AST fingerprints miss semantic
  duplication written with different control flow. ARCH-03.17 remains the
  reviewed qualitative duplication inventory.
- The baseline protects named current hotspots by regression. It does not
  remove their existing complexity; EPIC #313 decomposition work owns that.
- The scope follows package-root modules, application services, composition,
  and all infrastructure adapters. New orchestration placed outside these
  locations requires architectural review and may need a coverage update.
  Existing import-linter and architecture tests remain the boundary authority.
- A contributor can propose a baseline or exception change in the same pull
  request. Reviewers must inspect that explicit change and its reason; the
  checker cannot substitute for human architecture review.

Verification applicability: local deterministic checks are `APPLICABLE_LOCAL`.
Live infrastructure and browser checks are `NOT_APPLICABLE`. SonarQube is
`APPLICABLE_EXTERNAL` to publication; its state is `EXTERNAL_GATE_UNAVAILABLE`
because no pull-request result was observed. This does not affect the local
implementation result.
