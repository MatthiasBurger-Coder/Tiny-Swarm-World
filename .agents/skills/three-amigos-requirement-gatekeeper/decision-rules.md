# Decision Rules

## Stop Conditions

Stop immediately and return `REQUIRES_REFINEMENT` if:

- requirements are ambiguous
- ownership is unclear
- service boundaries are violated
- shared Java modules are introduced for microservice work
- acceptance criteria are missing or not testable
- APIs, schemas, event fields or graph labels are undefined
- workflows contain cyclic dependencies
- quality commands cannot be verified from `QUALITY.md` or build files
- evidence categories are collapsed or uncertain facts are presented as confirmed
- deployment impact or rollback expectations are relevant but missing
- required skills, roles or subagents cannot be found

## Refinement Rules

A ready requirement must contain:

- business goal
- technical goal
- scope
- non-goals
- affected systems or services
- API changes or explicit no API impact
- database or storage impact, or explicit no storage impact
- deployment impact, or explicit no deployment impact
- rollback strategy
- acceptance criteria
- required skills
- required subagents or role reviews
- requirement classification
- EPIC traceability status
- active workflow relationship, when an active workflow exists
- confidence level
- blocking questions status

For microservice migration work, a ready requirement must also contain:

- service boundary
- target service responsibility
- inputs and outputs crossing the boundary
- owned data
- allowed dependencies
- allowed communication mechanisms
- contract impact
- test impact
- risk level
- forbidden changes

Missing fields are blockers unless the user explicitly states they are not applicable.

If the user accepts a blocker-free assumption, record:

- the exact assumption
- the acceptance source
- the decision or slice affected by the assumption
- how the assumption will be verified or revisited

## Architecture Rules

Require:

- root `AGENTS.md` and `QUALITY.md` remain authoritative
- adapters and infrastructure depend inward on application and domain
- domain and application stay independent from concrete frameworks, storage, runtime tooling, LLM providers and build-tool APIs
- service-split work preserves independent deployability and no shared Java implementation modules
- microservice slices define service boundary, contract impact, data ownership,
  test impact, risk level and forbidden changes before implementation
- runtime, graph, replay, finding and LLM behavior preserve evidence provenance and uncertainty
- architecture decisions are made before implementation slices, not inside them

## Quality Rules

Require:

- acceptance criteria map to verification steps
- regression tests are planned for bug fixes
- architecture-sensitive changes identify import-linter, architecture-test or boundary checks
- quality commands are copied from `QUALITY.md` or verified build tasks
- external service checks are optional unless documented as required
- documentation synchronization surfaces are identified

Do not claim a quality gate exists unless its command or task has been verified.

## Dependency And Deadlock Rules

Reject or refine when:

- two slices need to edit the same files in parallel
- a slice depends on another slice's unstable API contract
- a service needs another service's private database or implementation classes
- target service ownership, service inputs, service outputs, allowed
  dependencies or allowed communication mechanisms are unclear
- two agents wait on each other's outputs
- rollback of one slice would leave another slice unrecoverable
- generated artifacts become inputs before their generation contract is stable

## Parallelization Rules

A slice may run in parallel only if:

- no shared file ownership exists
- no cyclic dependency exists
- API contract is stable
- data ownership is explicit
- outputs are deterministic
- verification can run independently
- merge order is documented when needed

## Decision Rules

Return `READY_FOR_WORKFLOW` only when the gate report contains no blockers and the next safe action is workflow authoring.

Return `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` only when confidence is from 70 to 89 percent, every remaining assumption is documented, non-blocking and accepted, and the next safe action is workflow authoring with those assumptions recorded.

Return `REQUIRES_REFINEMENT` when any blocker remains. Include precise questions or missing artifacts needed to unblock the gate.

Do not approve workflow authoring when:

- an active workflow may conflict with the new request
- EPIC drift cannot be classified
- provisional slices are still needed to explain missing ownership or contracts
