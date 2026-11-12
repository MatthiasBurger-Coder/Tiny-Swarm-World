# S440-06 prerequisite repair distribution

Baseline: c40d87ed81101dd582a112fe8b427d84372f36e2.
Branch: docs/workflow-issue440-acceptance-20261110.
Request: explicit operator instruction on 2026-11-11 to fix all three preflight
blockers. Architecture review s06_recovery_design ACCEPTS bounded implementation
of the existing cold restoration policy; no new ADR or support change.

S3/S3D: prerequisite S440-05 verified/pushed; S440-06 source repair must precede
live fixtures, S440-07 admission and all dependent scenarios. No dependency edge
changes. Source/test locks added in reviewed workflow amendment. No concurrent
runtime writer. Serial implementation; shared switch/bookmark/bridge semantics
make independent write streams unsafe. Root owns workflow/context/evidence and
final integration. One real specialist owns source/tests in isolated worktree
../Tiny-Swarm-World-worktrees/issue440-s06-recovery. No fallback.

Implementation ownership: switch/registration/bridge qualification PS sources,
switch/registration Python test wrappers and shared switch PowerShell fixture,
only as enumerated in S440-06. Worker must not run tests, live operations,
commits or pushes. Root reviews changes and independent auditor reviews final
scope/evidence. Test execution is NOT_RUN under the explicit development policy;
nearest targeted tests followed by full QUALITY.md quality gate require later
authorization on the designated SSH/Windows/WSL target.

No live GO, host interruption, resource deletion, fixture success or Epic
completion follows. Original listeners are preserved until separately approved
cold handoff. Full fixture-window preservation and exact zero-resource seal are
required; ambiguous pending effects keep their durable intent.
