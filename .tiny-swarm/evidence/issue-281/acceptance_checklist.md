# Acceptance Checklist: #281 / CRED-03

- [x] Precedence is implemented once in the domain resolver and documented.
- [x] Self-hosted Infisical is unavailable as a bootstrap source for its own startup inputs.
- [x] Explicit operator values override deterministic defaults.
- [x] Applicable secure values win in the post-bootstrap phase.
- [x] External Infisical is explicitly distinguished and rejected in this self-hosted RC1 scope.
- [x] Conflicting or unsupported source, path, provider, and metadata combinations fail safely.
- [x] Evidence and installer context report only credential key/source labels.
- [x] Legacy mode semantics are inventoried and separated for CRED-04 cleanup.
- [x] Tests cover defaults, operator/file/process overrides, Vault precedence, bootstrap behavior, conflicts, external references, and reruns.
- [x] Branch-aware diff coverage is 100% for the measured changed production lines and therefore above the 95% threshold.
- [x] `python3 tools/quality_gate.py quality` passes.
- [x] Live infrastructure was not run; the local-only verification state is recorded and live proof remains assigned to CRED-07/#285.
