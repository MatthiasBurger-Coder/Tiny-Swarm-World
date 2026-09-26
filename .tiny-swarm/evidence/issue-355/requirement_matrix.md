# ARCH-03.12 requirement matrix

Source: GitHub #355 (goal, scope and all five acceptance bullets); R355-15 also derives from parent #313 and root governance. Authoring is complete only after review; implementation remains OPEN.

| ID | Requirement from issue | Type | Files likely affected / slices | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|---|---|
| R355-01 | Standardize expected lifecycle outcomes through explicit application-level results. | Functional / architecture | S355-02–05; exact paths in workflow metadata | PLANNED | PLANNED: Each of platform, artifacts, deployment and setup produces the common contract. | OPEN |
| R355-02 | Represent successful completion explicitly. | Functional | S355-02,04,05; exact paths in workflow metadata | PLANNED | PLANNED: Successful mutation, read-only operation and verified no-op. | OPEN |
| R355-03 | Represent failure explicitly. | Functional / resilience | S355-02–05; exact paths in workflow metadata | PLANNED | PLANNED: Failure before mutation and unsuccessful operation. | OPEN |
| R355-04 | Represent partial completion where applicable. | Functional / resilience | S355-04,05; exact paths in workflow metadata | PLANNED | PLANNED: Earlier confirmed work followed by failure; retain completed and pending work. | OPEN |
| R355-05 | Represent rolled-back outcome only after completed, verified restoration. | Functional / resilience | S355-02,04; exact paths in workflow metadata | PLANNED | PLANNED: Existing recover convergence; attempted, failed or planned rollback is never rolled_back. | OPEN |
| R355-06 | Failure details identify the operation. | Observability | S355-02–05; exact paths in workflow metadata | PLANNED | PLANNED: Stable operation identity survives nested propagation. | OPEN |
| R355-07 | Failure details identify the component. | Observability | S355-02–05; exact paths in workflow metadata | PLANNED | PLANNED: Affected component retained at adapter and workflow boundaries. | OPEN |
| R355-08 | Failure details identify a safe classified cause. | Security / observability | S355-02,03,06; exact paths in workflow metadata | PLANNED | PLANNED: Process, filesystem/configuration, HTTP/provider cases; secret-safe serialization and traceback. | OPEN |
| R355-09 | Failure details express recoverability. | Resilience | S355-02,03; exact paths in workflow metadata | PLANNED | PLANNED: Recoverable, nonrecoverable and unknown cases use evidence-based classification. | OPEN |
| R355-10 | Failure details provide a recommended action. | UX / resilience | S355-02,03,06; exact paths in workflow metadata | PLANNED | PLANNED: Safe concrete guidance, no unsupported automatic retry promise. | OPEN |
| R355-11 | Translate expected infrastructure exceptions at adapter boundaries. | Architecture | S355-02,03; exact paths in workflow metadata | PLANNED | PLANNED: External failures become application-owned failure values or typed port errors. | OPEN |
| R355-12 | Expected infrastructure failures do not leak arbitrary exceptions through orchestration. | Architecture / resilience | S355-03–05; exact paths in workflow metadata | PLANNED | PLANNED: Mocked boundary-to-workflow propagation; cancellation and programming defect policy. | OPEN |
| R355-13 | Preserve existing CLI exit/error behavior unless a correction is explicitly justified. | Compatibility / UX | S355-01,06; exact paths in workflow metadata | PLANNED | PLANNED: Legacy statuses, JSON keys, text, exits, installer and simple-installer regression coverage. | OPEN |
| R355-14 | Test representative failure mappings. | Quality | S355-02–07; exact paths in workflow metadata | PLANNED | PLANNED: Failure mapping catalogue tied to named tests and full local quality results. | OPEN |
| R355-15 | Preserve EPIC architecture, consent, destructive guards, redaction, deterministic evidence and Linux/WSL behavior. | Parent EPIC / governance | S355-01–07; exact paths in workflow metadata | PLANNED | PLANNED: Architecture and safety regression checks; independent completion audit. | OPEN |

Before execution, copy this matrix to `.tiny-swarm/evidence/issue-355/requirement_matrix.md` and replace planned entries with exact file/symbol/test evidence as slices complete. Every requirement must remain represented; inventory cannot silently narrow scope.

## S355-02 incremental evidence

Immutable safe operation contract, compatible application-owned command errors with cause preservation, and conservative real platform factory integration.
Targeted: 64 tests PASS. Full quality PASS: 2188 tests in 294.844s, 18 skipped. Partial evidence only; requirement rows remain OPEN until complete lifecycle coverage and final audit.

## S355-03 incremental evidence

Translated lifecycle adapter failures through compatible safe capability errors; preserved control flow, storage atomicity and legacy workflow status.
Targeted: metadata suites 86, 84, 18 PASS; regression repair 40 PASS; expanded 172 and repository 105 PASS (overlap). Full quality PASS: 2208 tests in 241.374s, 18 skipped. Partial evidence only; requirement rows remain OPEN until complete lifecycle coverage and final audit.

## S355-04 incremental evidence

Platform producers retain explicit requested progress, safe origins, uncertainty and verified recovery through the shared result contract.
Targeted: declared/helper 161 PASS; complete platform 221 PASS (overlap). Full quality PASS: 2227 tests in 241.428s, 18 skipped. Partial evidence only; requirement rows remain OPEN until complete lifecycle coverage and final audit.
