# Remaining Risks: #280 / CRED-02

- The legacy installer still contains `generated`, `fixed`, and `infisical`
  modes and their persistence helpers. They are no longer selected by the
  normal `install.sh` path, but their final supported/removed status belongs
  to CRED-03 and CRED-04.
- The explicit compatibility file path is intentionally not assigned the full
  final override precedence here. CRED-03 must define secure/Infisical versus
  operator versus catalog precedence and the self-hosted bootstrap boundary.
- This issue proves local deterministic resolution and mocked orchestration,
  not live service login or Docker/Swarm lifecycle behavior. CRED-07 owns that
  evidence.
- The installer still prints the two intentional operator login credentials on
  successful completion. CRED-06 owns the final operator-output wording; no
  internal credential is added to diagnostics or durable evidence here.
