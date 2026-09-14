# Remaining Risks

- Full repository quality gates pass locally.
- Existing composition tests report an environment-level evidence-write
  warning for `deployment:effective-access-model-evidence`; this is unrelated
  to lifecycle dispatch and did not fail the focused tests.
- No live Incus, Docker, Swarm, or service deployment validation was requested
  or performed.
