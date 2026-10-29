# S449-CAPABILITY-G1 distribution and preflight

S3/S3D result: EXECUTION_PLAN, serial, at clean checkpoint
`eb7a57f7f4f9650892e268f27f32ab3c53c14500`, as handed off by the integration owner.
Workflow SHA-256: `b5b29d09475a5d39fdd05efe4176e421cd42593af269c7d067f1e6873b7097b1`.
Contract SHA-256: `e604ed56fdd75b2bd6f76b7330a31095590d810b3dbc2ae521ff8fe49c383f2d`.

The integration owner reports independent same-tuple GO decisions from Requirement,
Architecture, Security, Python, Tester and DevOps for this reviewed design. These
are planning decisions, not implementation or host qualification results.

Ownership is one sequential Python implementation stream with root integration;
no concurrent overlapping file, module, contract or architecture stream.
Locked files are `src/tiny_swarm_world/domain/lifecycle/incus_capability.py`,
`tests/domain/lifecycle/test_incus_capability.py`, the reviewed G1 contract,
this distribution record and G1 consolidation record. Contract, module and
architecture locks are those in workflow S449-CAPABILITY-G1.

The owner implements the typed domain classification and deterministic tests.
Independent code reviews, exact-source designated SSH PC WSL targeted tests,
Ruff and full quality gate follow before a checkpoint. No local Python tests,
runtime wiring, caller guard claim, live fixture or host operation is authorized
by this slice. The immutable supported-version set remains empty; legacy is
explicit classification only. Support qualification and caller integrations
remain future separately reviewed slices.

## Corrected candidate handoff

The original S3/S3D GO above binds the earlier contract bytes. The contract was
clarified to require an exact built-in string after a test review found that a
subclass could spoof its length. Corrected contract SHA-256:
`88a54329249894c8698f0c425dd5d861423e53ca70aea2a129a7e1b442a3fee3`.
Final candidate source SHA-256:
`235e03236ab1d46fa058ed852d8a21db551621aaa49dd9e26f2c96e4125debf1`.
Final candidate test SHA-256:
`092e288a4344dd5f5ecc4bd517498c4e351cc993530b85a7c0b5c1094f82b84b`.
The integration owner reports six same-source/contract GO decisions from
Requirement, Architecture, Security, Python, Tester and DevOps. DevOps
revalidated S3/S3D and returned GO for the corrected source, test and contract
hashes above. These decisions do not qualify a runtime caller or host.
