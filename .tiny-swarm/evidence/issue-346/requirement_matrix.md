# Requirement Matrix — #346 / ARCH-03.03

Parent: #313 — EPIC 03

| ID | Requirement from issue | Type | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| REQ-001 | Inventory the current orchestration edge completely. | Architecture audit | `arch-03-03-orchestration-hotspot-ranking.md` scopes the three entrypoints and every `composition*.py` module. | AST inventory command and complete 15-surface table in `test_results.md`. | DONE |
| REQ-002 | Use objective signals including complexity, size, fan-out/dependencies, side effects, responsibility count, infrastructure imports, test setup difficulty, and change frequency where available. | Ranking method | Reproducible AST metrics, responsibility map, test-friction rubric, and change-frequency command are documented. | `git diff --check`; source metric command recorded in `test_results.md`. | DONE |
| REQ-003 | Classify each hotspot LOW, MEDIUM, HIGH, or CRITICAL. | Prioritization | Complete inventory assigns one severity to each surface. | Table review and acceptance checklist. | DONE |
| REQ-004 | Provide a proposed decomposition target for every HIGH/CRITICAL hotspot. | Remediation | Installer, CLI, runtime, deployment, and composition facade targets are explicit in the ranking and decomposition order. | Acceptance checklist and static document review. | DONE |
| REQ-005 | Do not use file size alone as the deciding metric. | Architecture constraint | Severity is explicitly based on combined coupling, effects, lifecycle, change frequency, and test friction; size is context only. | Documented scoring rule and checklist. | DONE |
| REQ-006 | Feed results into the remaining ARCH-03 implementation order. | Governance | P0–P4 order maps hotspots to ARC-02 through ARC-06 and calls for issue mapping confirmation. | Resulting implementation-order table and checklist. | DONE |
