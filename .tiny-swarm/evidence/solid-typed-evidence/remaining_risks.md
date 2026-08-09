# Issue #191 — Remaining Risks

- Live LXC/Incus and Docker/Swarm behavior remains unverified by design and
  requires explicit consent plus observable evidence.
- Browser/Selenium and external quality-system states remain not run and are
  not inferred from the local quality gate.
- Separate platform, deployment, artifact and Nexus evidence families retain
  their existing producer-owned contracts; this issue intentionally does not
  introduce a global evidence schema.
- A future intentional serialized-contract change would require a new
  compatibility decision and corresponding ADR review.
