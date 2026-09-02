# Remaining Risks and Scope Boundaries: #282 / CRED-04

- Live Infisical, Incus, Docker Swarm, networking, WSL2, and native-Linux E2E
  execution was not authorized or run for this issue. CRED-07 / #285 owns that
  evidence.
- The post-bootstrap secure-source path is intentionally retained for the
  service-access lifecycle. Its effect on live stack consumers must be proven
  by the CRED-07 runtime matrix; this cleanup issue does not claim live vault
  precedence success.
- `TSW_BOOTSTRAP_SECRET_ENV_FILE` and the `TSW_BOOTSTRAP_STATE_DIR` alias remain
  explicit operator inputs defined by CRED-03. They are not generated state and
  are mutually exclusive; their protected WSL-native path rules remain active.
- Generic recovery terminology in workflow/UI code is operational failure
  guidance, not credential recovery persistence. It was not removed because it
  serves unrelated setup recovery behavior.
- The repository test run uses the local Linux/Python environment. The
  supported runtime contract remains Python 3.12 on Linux/WSL.
