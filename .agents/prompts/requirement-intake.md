# Requirement Intake Prompt

Use before workflow authoring when a user introduces or changes a requirement.

## Required Flow

1. Load `three-amigos-requirement-gatekeeper`.
2. Normalize the requirement.
3. Separate confirmed facts from assumptions.
4. Validate business goal, technical goal, scope and non-goals.
5. Validate architecture fit.
6. Validate quality and testability.
7. Validate dependency and deadlock risks.
8. Validate required skills and role reviews.
9. Record confidence level and blocking questions.
10. Return `READY_FOR_WORKFLOW`, `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` or `REQUIRES_REFINEMENT`.

## Stop Conditions

Return `REQUIRES_REFINEMENT` when continuing would require guessing requirements, ownership, API contracts, data ownership, quality commands, architecture decisions, runtime facts or evidence semantics.

Return `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` only when confidence is from 70 to 89 percent, every assumption is documented, non-blocking and accepted, and no blocking question remains.
