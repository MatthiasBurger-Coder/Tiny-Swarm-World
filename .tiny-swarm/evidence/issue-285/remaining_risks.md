# Remaining Risks and Scope Boundaries: #285 / CRED-07

- The required live acceptance has not run. This is not a live pass.
- The current workspace is WSL2 under `/mnt/d`; it is not native Linux.
- No native-Linux VM/host, disposable target, rollback path, evidence root, or
  target-owner reference was supplied.
- Running the canonical installer performs a governed reset and can create or
  alter Incus-managed nodes, Docker Engine, Swarm state, stacks, networking,
  and service data. It must remain opt-in and scoped.
- Custom credentials must be provided through a protected WSL-native file or
  approved secret source. Raw credentials, tokens, headers, and private
  endpoints must not be committed or written to durable evidence.
- `LIVE_CONSENT_MISSING` and `LIVE_PREREQUISITE_MISSING` remain the authoritative
  states until the operator supplies the missing approval and target.
