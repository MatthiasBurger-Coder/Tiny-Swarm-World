# Portainer upgrade ownership guard — distribution

PROPOSED. ADR owner, Requirements and Security must decide checkpoint/recovery semantics before implementation, then Architecture, Python, Tester and DevOps and S3D. No product, host or quality result is claimed.

Tester/Python/DevOps NO-GO addressed in revised candidate: explicit recovery stage matrix, read-only runtime port, checkpoint consumer regression locks. ADR owner/Architecture conditional GO concerns prior design direction only; exact matrix requires fresh reviews and S3D.

Tester NO-GO addressed: a failed pending save may leave either old or new complete checkpoint after replace/fsync uncertainty; reopen read-only, classify actual valid state and never repeat effects or claim save success. Fresh exact-hash ADR/Architecture and role reviews remain required.

Final exact-hash handoff: Requirement, Architecture, Security, Python, Tester and DevOps and the ADR owner reported GO for contract SHA256 `ebbd10a3f3333d5d93253a982d4350e37a9c7254a233cf91f18339a2ed8a60a1` and workflow SHA256 `e4f42f20c4a6d85841ba52f40000161cd72b02f2b888dd5cf577b9a9950a31d7`. Earlier Tester NO-GO on post-replace/fsync save uncertainty is addressed by old-or-new complete state and read-only reconciliation without blind replay or success on error. This approves the contract only: implementation, S3D, quality, host operation and ownership admission are not claimed.

After making the Ruff command executable, Requirement, Architecture, Security, Python, Tester, DevOps and ADR owner reported GO rebind for workflow SHA256 `04287aa16b55123be93e607450b33a5f98d3466cccf75ad0375bb20c56770c1d` and unchanged contract SHA256 `ebbd10a3f3333d5d93253a982d4350e37a9c7254a233cf91f18339a2ed8a60a1`. S3D and implementation/quality evidence remain separate.

S3D EXECUTION_PLAN on clean base `da61b2d0a21422d8eccdd11727e99226960800a0`, workflow v1.71, contract SHA256 `ebbd10a3f3333d5d93253a982d4350e37a9c7254a233cf91f18339a2ed8a60a1`. Requirement, Architecture, Security, Python, Tester, DevOps and ADR owner reported GO for the design; one serial worker owns declared locks. No ownership admission, host action or verification pass follows from design approval. Implementation and SSH PC WSL tests are pending.

## Candidate verification handoff

The integration owner reports final Security GO on service `65ab3eb17d9b0cd6a844e9e58a63c1bf205e82e5317f0c832c1b5dddcde1058c` and runtime `171ed9823087a7f8b8a021fa03e4ad948d3552f1e1a9bc7cbaed46d97cb128ba`; Tester GO on application tests `96569feb0dfe2702065085650810675a626c4ce6467e27c75fcb4566a8427364` and runtime tests `7dcdc856baf7f3d11393375f0d8300bb5a26122abae876bf79964eb5a38fd179`. Requirement, Architecture, Python and DevOps also reported final GO on these four hashes; DevOps additionally reviewed the slice scope. These final rebinds are limited to the stated hashes and scope, not all changed files.

Exact-candidate tar SHA-256 prefix `42e2b4e9` on designated SSH PC WSL Python 3.14: 83 targeted tests and Ruff PASS; full quality exit 0, 3,453 tests run, 37 skipped, 204.360 seconds. Earlier targeted execution failed one fixture assertion because the component journal was written to a different directory than the canonical shared lock; the fixture now uses the same directory and retains its guard assertion. A subsequent full gate failed Ruff F401 on an unused `PortainerCheckpoint` import; the import was removed and the later exact-candidate full gate passed. Python 3.12 and live host execution were not tested.
