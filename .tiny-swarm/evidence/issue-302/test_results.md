# R06 verification results

- Full `python3 tools/quality_gate.py quality`: exit0, Python3.12.14; all six
  stages pass. 2,066 tests discovered, 18 explicit skips, 2,048 non-skipped;
  143.341 seconds test runtime. 18 architecture tests, three import contracts,
  674 typed files. See local-quality.json. Negative-case diagnostic text in
  unittest output is expected fixture behavior, not a failed final gate.
- `python3 tools/install_debugger.py`: exit0. Read-only `--live --env-file`
  diagnostics: exit0. `python3 tools/preflight.py` without loaded environment
  correctly fails missing required sources; protected configured repeat exit0.
  Exact c921 source, timing and non-secret result in cleanup-and-baseline.
- Deliberately failing unittest through canonical quality dispatch and the
  compatibility failure shell: both exit1, no downstream success marker. Local
  executed failure semantics; no synthetic hosted-quality execution claimed.
- Integrated main 69f040a7: Quality34729686799, Conda34729686818 and actual
  Sonar34729827923 PASS. Scanner SCM revision is verified from the log.
- Actual final blocked hosted dispatch34729909225 executes on restored runner23,
  fails the explicit approval guard, then skips mutation. Original successful
  lifecycle34725969899 and controlled block34727197058 retain their actual SHAs.
- All 271 referenced files in the current R01/R02/R03/R04/R05/R08 hash manifests
  matched before final audit. Final structural/link/redaction/manifest checks are
  recorded in audit-verification.json and final consolidation.

No extra live scenario is inferred from local quality or a missing/skipped gate.
The final evidence-publication PR and merged revision need their own checks;
their binding is recorded on GitHub after the actual revisions exist.
