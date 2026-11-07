# Issue 363: node mutation evidence correction

Live worker recovery exposed an existing reporting defect: a stopped Incus node
actually returned to Running, while platform reconcile reported no_op. The
same producer omission existed at the historical RC1 candidate; it is not an
ARCH-03 typed-result regression.

The node adapter now marks successful, verified node creation and start as
applied. Existing workflow aggregation therefore reports converged and executed
true. Already-running nodes retain no_op and executed false. No provider command,
verification policy, API, resource configuration or service image changed.

A regression drives the real node provider result into the real platform workflow
result, covering created/started nodes followed by an unchanged repeat for both
existing backend enum values. All external commands are mocked. The old source
failed six assertions; the focused provider/platform suite passes98tests after
the two producer corrections. Full quality and both-host affected live reruns are
recorded in .tiny-swarm/evidence/issue-363-final-validation/.

Earlier functional installation/update/recovery/browser results remain attributed
to their executed revision. A reviewer-approved source impact assessment may
retain unaffected results; incorrect historical mutation summaries remain intact
and are superseded only by new source-qualified live reconciliation evidence.
