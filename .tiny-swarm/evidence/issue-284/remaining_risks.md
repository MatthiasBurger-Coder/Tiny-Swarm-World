# Remaining Risks and Scope Boundaries: #284 / CRED-06

- Live WSL2 `/mnt/<drive>` and native-Linux installation proof was not
  authorized or run. CRED-07 / #285 owns that evidence and remains open.
- The catalog defaults are deliberately disposable `INTERNAL/TEST ONLY`
  values. Public, shared, or untrusted exposure requires an approved stronger
  override and the surrounding organization's identity and network controls.
- CRED-03's protected operator override and applicable Infisical lifecycle
  remain supported. Their live precedence and service behavior require the
  CRED-07 runtime matrix.
- Documentation and output are tested as repository text and mocked installer
  behavior. No browser, external service, Incus, Docker Swarm, or stack
  bootstrap success is claimed by this issue.
