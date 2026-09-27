# Issue #358 acceptance checklist

- [x] CLI modules contain no substantial infrastructure workflow orchestration.
- [x] Application behavior is invoked through explicit workflow services and use cases.
- [x] Presentation is separated from workflow semantics.
- [x] Command names and options are preserved.
- [x] Consent and destructive confirmations are preserved.
- [x] Exit semantics are preserved.
- [x] CLI regression tests cover declared commands and exit behavior.
- [x] Full local quality gate completed and recorded after final revisions.
- [x] Independent issue completion audit returned PASS.

## Three Amigos review

- Requirement Lead: The nine requirements above cover the issue goal, three scope bullets and five acceptance criteria. The parser registry remains the supported command source, and the frozen tuple prevents command removal or rename from passing unnoticed.
- System Architect Reviewer: PASS on the revised diff. Application actions own update/recovery validation and invocation, setup action and consent validation, host preflight ordering and setup plan data. Composition selects category builders and binds dependencies; CLI parsing, prompts, output and exits remain at the edge.
- Test / Evidence Reviewer: PASS. Frozen command names, mutating refusal exits, prior success/failure exits, host preflight ordering, architecture checks and final full quality gate are evidenced.

Independent Issue Completion Auditor decision: PASS. All nine requirements map to implementation and verification; the six required evidence files are present, and `git diff --check` is clean.
