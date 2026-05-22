# Anti-Patterns

## Forbidden

- shared utility microservices
- undefined API contracts
- shared mutable state across services or slices
- cross-service database access
- frontend-driven backend architecture
- architecture decisions inside implementation slices
- multi-purpose mega-slices
- circular slice dependencies
- hidden compatibility wrappers
- undocumented fallback paths
- fabricated runtime, graph, replay or LLM evidence
- quality commands invented from memory

## Dangerous Patterns

- "Implement first, clarify later"
- "Temporary shared module"
- "We fix architecture later"
- "Single agent owns everything"
- "The API will be obvious during implementation"
- "Use static dependencies as runtime proof"
- "Let the LLM summarize evidence into facts"
- "Parallelize now and reconcile files later"

## Required Response

When one of these patterns appears:

1. Name the pattern.
2. Explain the concrete repository risk.
3. Return `REQUIRES_REFINEMENT`.
4. Ask for the smallest missing decision that would unblock workflow authoring.
