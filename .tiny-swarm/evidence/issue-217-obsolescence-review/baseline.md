# Current-Main Baseline — Issue #217

- Review ID: `issue-217-20260809:baseline`
- Repository: `MatthiasBurger-Coder/Tiny-Swarm-World`
- Current source baseline: `main` / `origin/main` at `ecdc71d94a72530905ecb0a41d2845921ad6debb`
- Workflow execution branch: `feature/workflow-review-obsolete-issues-20260809`
- Workflow commit at start: `125d7ea22a09544f9f786220d85e375d56506619`
- Workflow version: `issue-217-v1.0.0`
- Baseline captured: 2026-08-09, before any Issue #156/#163/#197 mutation

## S3/S3D result

- `S3_STATUS`: PASS; working tree was clean before Slice 01 write.
- `S3_BRANCH`: PASS; the declared workflow branch is active and its local ref
  exists.
- `S3_SCOPE`: PASS; Slice 01 is declared by the checked active workflow.
- `S3_CLASSIFY`: `documentation/governance/metadata`, explicitly allowed by
  the workflow.
- `S3D`: `EXECUTION_PLAN`; graph is acyclic with groups
  `[S217-01] -> [S217-02,S217-03,S217-04] -> [S217-05] -> [S217-06]`.

## Guard decisions

- No product source, configuration, test or deployment file was changed.
- No live Docker, LXC, Incus, Swarm, networking, Socat or Selenium command was
  run.
- No GitHub issue was closed, reopened, relabeled or rewritten in Slice 01.
- External Sonar state remains `EXTERNAL_GATE_UNAVAILABLE` unless a later slice
  observes an actual result.

## Baseline findings

- `infra/config/ports.yaml`, typed port loading and effective-access/Compose
  test surfaces exist and require the #156 end-to-end trace.
- The original #163 IP literals remain present in the named port-forwarding
  test fixture and require a current quality-state decision.
- The #197 Socat step and subprocess helpers remain in
  `src/tiny_swarm_world/infrastructure/composition.py` and require an
  architecture/test decision.

This file records the baseline only. It is not a completion decision for any
candidate issue.
