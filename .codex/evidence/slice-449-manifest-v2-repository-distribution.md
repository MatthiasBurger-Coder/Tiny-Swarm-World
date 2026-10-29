# S449-MANIFEST-V2-REPOSITORY — planned review distribution

One serial Python owner implements only the typed V2 record, new versioned port/isolated adapter and their tests. Preserve existing V1 repository, CLI/runtime wiring and other agents' edits. Requirement, Architecture, Security, Python, Tester and DevOps independently review identical workflow, closed wire contract, ADR reconciliation and source hashes; S3D must validate exact dependencies and locks. The proposed UNADOPTED wire format needs explicit ADR-owner acceptance; no review or execution result is asserted.

Reviewer NO-GO refinement: fixed staging root/file and nofollow/ownership/hardlink/budget rules, stable cooperating lock inode, exact-byte token and explicit ABA limitation, same-value no-op and post-replace UNCERTAIN semantics, explicit validation inputs and future operator/consumer/lock slices are now specified in the revised contract. Draft-persistence ADR and Security/owner decisions still need review; no acceptance or S3D is claimed.

Tester/Security/Python refinement: pre-replace preserves previous final, post-replace crash or directory-fsync failure yields UNCERTAIN and complete old-or-new state, no success/blind retry. Parser is bounded to 1 MiB, depth 32 and 50,000 items, rejects non-finite values and duplicates. Closed typed port results, distinct ABSENT token, persisted listen input and redacted repr/log/error contracts are explicit. ADR-owner decision remains pending.

## Reported ADR-owner handoff

The coordinator reports ADR-owner GO for the isolated UNADOPTED draft candidate reviewed at contract SHA-256 `425f3e735b27c655261e8762e4e87ec085162f864dd0ae261fbe78f8690c0107` and workflow SHA-256 `949b6d6578eeb0a38bac926040e935a4d746600ae44e3df79d1eadf7479d38d5`. This is a reported architectural review handoff, not a user decision, not acceptance of canonical admitted-v2 persistence and not a host GO. The current revision clarifies drift blocks without read-time rewriting, and version-bound migration/retention is mandatory before later production use. P1 affected selections require exact successful P1 recomputation, with service-access 8086 and Infisical-only 17080 roundtrip tests; mismatches block. Fresh role reviews and S3D are required for revised hashes.

## Final revised-contract review handoff

The execution coordinator reports independent Requirement, Architecture, Security, Python, Tester and DevOps GO, plus ADR Owner GO, on the identical revised contract SHA-256 `51f9d8d5b514a46714b5cb4a5f73ec455d1db9f76ac64d9fb5501b6292bf9edc` and workflow SHA-256 `7551302889998400cc454266a61ecda101fdc989b7f9bf081af47898b81d4eb1`. This is a reported contract/isolated-draft design decision, not S3D, product implementation, canonical admitted V2, host approval or live evidence.

Earlier reviewers returned NO-GO for unspecified safe path/lock/token/ABA/crash rules and ADR drift ambiguity. The revised contract records fixed isolated path and bounds, cooperating-only lock and bytehash ABA limit, closed CAS results, post-replace UNCERTAIN/read-only reconciliation, no read-time rewrite, production-use migration prerequisite and exact P1 8086 validation. Earlier reviews are not silently rewritten. Independent S3D EXECUTION_PLAN and exact-source quality remain pending.

## Implementation preflight

The integration owner reports serial S3/S3D EXECUTION_PLAN at clean checkpoint
`a75b592982b1af14fbce071ae106cd26eb76b157`, bound to the six-role and ADR-owner
reviewed workflow/contract tuple above. One serial implementation stream owns
the locked domain record, application port, isolated staging adapter, their
tests and evidence; root integrates. Independent final candidate review and
exact-source designated SSH PC WSL targeted tests, Ruff and full quality
remain pending. No canonical persistence, CLI/runtime integration, host
operation, admitted state or live qualification is authorized.

## Complexity-gate failure and proposed remediation

The initial full QUALITY run reported FAIL on four complexity guardrails in the new module/class/CAS/JSON parser. The proposed same-slice serial split introduces separately locked `versioned_manifest_json.py` and `versioned_manifest_fs.py`, preserves the facade and all safety/uncertainty checks, and does not change baselines, exceptions or thresholds. No pass is claimed; six-role same-hash review and S3D must approve revised locks before the worker continues.

## Complexity-remediation contract review

The execution coordinator reports independent Requirement, Architecture, Security, Python, Tester and DevOps GO on the identical revised contract SHA-256 `307e8b2ee45e8dd3f12dbc66e510e0ec05ed433ebfe6883c550e29c91147f36a` and workflow SHA-256 `c8a64ed887738d18880068110ced9b46a8ce3fceb8b04ec7f673a396e6dc5394`. The earlier full QUALITY complexity failure remains a failure; these are review decisions, not a new test pass. The new file locks require a fresh S3D plan before implementation resumes, and targeted/full SSH PC WSL quality must be rerun. No host or admission result follows.

## Remediation preflight and final candidate

The integration owner reports serial S3/S3D EXECUTION_PLAN for the amended
locks at clean checkpoint `9626d804d3272bae6208eecf9ecc97c3a196ef22`.
The exact task-only overlay was restored and source hashes verified before the
split. Security, Architecture, Tester, Requirement, Python and DevOps GO are
reported for the final facade, JSON, filesystem and adapter-test hashes below.
DevOps additionally reviewed task scope. These reports cover those four hashes,
not an asserted independent full seven-file tuple GO.

Final source and test SHA-256 values:
- `src/tiny_swarm_world/domain/lifecycle/manifest_v2_record.py`: `2501a16a5d287318a0ab8718c4217220c6cbb0ce6dc32ba8680dfb5abfe602b3`
- `src/tiny_swarm_world/application/ports/lifecycle/versioned_manifest.py`: `1d2a4a28e7bdcf0a867242fd9d8a061ba2269e61c1b1dbca44be96feac763779`
- `src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_repository.py`: `110e19570631b87629b487852dea38fb356dab1a48a8b765e21cae762c68f367`
- `src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_json.py`: `c3398a0231be0ddbacc8ba54dce0a795067560c9149231db2bc2cbd9d305a55e`
- `src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_fs.py`: `845e34af7717b7ab5e323bc3dd21fc9d43562cf15f539b8c3304d54af3400db5`
- `tests/domain/lifecycle/test_manifest_v2_record.py`: `0fc9a473a337c2cf5b37ded6467d40a5151f2ca8d90fd390bcb03acb88d32ca5`
- `tests/infrastructure/adapters/lifecycle/test_versioned_manifest_repository.py`: `60686ee2b23b855dd1c87f1d35311191996fe4b9b64964774e1a554a6bbc173c`

The integration owner reports exact-source designated SSH PC WSL targeted
tests, Ruff and full quality PASS using transferred candidate tar SHA-256
prefix `071ec104`; see consolidation. Python 3.12 and live host execution
were not tested. This isolated UNADOPTED primitive is not canonical installation
persistence or host qualification.
