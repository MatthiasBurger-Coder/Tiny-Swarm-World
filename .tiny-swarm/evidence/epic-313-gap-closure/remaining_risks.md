# Remaining risks and verification limits

No known unmet implementation requirement in this remediation. The final local gate and independent architecture, security and Test/Evidence reviews passed; the independent Completion Auditor also returned PASS for all37requirements, with no open requirements (completion_audit.md).

Compatibility exports for existing root installer/renderer consumers remain intentionally explicit. Their implementation is canonical in infrastructure; protected inward imports cannot use those facades. Future removal requires consumer migration, as documented in the resulting architecture. Other documented capability debt remains subject to existing contracts/complexity guardrails; no new exception or provider redesign is introduced.

Live installer/provider/browser: NOT_APPLICABLE for this strict behavior-preserving extraction, as independently reviewed. No physical infrastructure mutation was executed. Existing #363 final-validation and #427 live results retain their original executed source revisions and host scopes; this changed tree is not declared LIVE_VERIFIED. No new RC1 qualification or SonarQube/CI result is claimed. External gates: NOT_RUN in this local request.

Default Linux quality uses Python 3.14. Python 3.12 stdlib-only bootstrap imports and 11 pure installation-service tests were executed; a full dependency-backed Python 3.12 gate was not executed because that interpreter lacks project dependencies. New code retains Python 3.12 syntax and supported dependency-light bootstrap semantics.

The repository ignores .tiny-swarm by default. Only this reviewed, secret-free EPIC package is explicitly included for review; generated caches and other private evidence are excluded.
