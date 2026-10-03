# Test results

Candidate: working tree fix/epic-03-orchestration-boundaries, baseline7e15d539. Changed Python file SHA256 values are in candidate_source_hashes.json. No product changes after final verification may inherit this result without revalidation. All34changed Python hashes remained unchanged during the gate.

- Final `python3 tools/quality_gate.py quality`: PASS, exit0. Verification-policy PASS; complexity280modules PASS; lint PASS; seven import contracts kept; architecture43tests PASS; mypy754source files PASS; full unit discovery2396tests PASS in277.529s with18existing skips. Executed output: quality.log.
- `python3 tools/quality_gate.py arch-tests`: PASS43tests; independent architecture reviewer also43PASS.
- `python3 tools/quality_gate.py typecheck`: PASS754source files after correcting typed AST visitor errors in the new test helper.
- Targeted CLI worker suite:89tests PASS; installer/simple/prepare/service/install-script worker suite156tests PASS. Independent security installer/service suite81PASS; independent Test/Evidence architecture/service24PASS. Final gate discovers integrated tests.
- `PYTHONPATH=src python3 -m unittest tests.architecture.test_architecture_regressions.TestOrchestrationEdgeGuards`:6PASS, includes deliberate positive/negative absolute/relative renderer imports, root regrowth and direct technology/state access. edge_guards.log.
- `PYTHONPATH=src python3.12 -S -m unittest tests.application.services.test_installation`:11PASS. python312_lifecycle.log.
- Python3.12 stdlib-only imports of installer, simple_installer and prepare_linux: PASS; third-party dependencies are not loaded before bootstrap. Product source parses under Python3.12. python312_bootstrap.log.
- `PYTHONPATH=src python3 -m tiny_swarm_world --list-workflows`: PASS19existing names. workflow_inventory.log.
- CLI AST parity:50moved definitions identical against baseline; cli_ast_parity.json.
- `git diff --check`: PASS.

Initial architecture integration failed because an old import scanner did not resolve package-member imports; exact resolved scanning repaired it. First full gate stopped at two new guard-test mypy errors; fixed AST visitor typing without weakening architecture behavior. Final gate result supersedes these intermediate checks, never inferred from the prior baseline.

Applicability: APPLICABLE_LOCAL. Live installer/provider/browser: NOT_APPLICABLE strict extraction (independent security/requirement review). Previous #363/#427 evidence retains original executed revisions and is historical scoped evidence, not this tree's LIVE_VERIFIED result. External/Sonar/CI: NOT_RUN. Existing18test skips must be reported as skips, not successful live runs.

Captured quality output has trailing spaces in the import-linter ASCII banner normalized for diff hygiene; substantive command/output content is unchanged. Original executed output was independently reviewed from /tmp/tsw-epic03-final-quality.log.
