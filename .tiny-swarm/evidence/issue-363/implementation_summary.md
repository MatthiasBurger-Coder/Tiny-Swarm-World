# Implementation summary

Issue #363 is a verification campaign for the integrated ARCH-03 refactor.
The initial live attempt revealed that the Classic runner labelled a setup
resource gate as `LIVE_FAILED_AFTER_MUTATION`, despite the preflight stopping
before mutation. The runner now classifies this observed shape as
`LIVE_BLOCKED_BEFORE_MUTATION`, with a regression test. The first protected
artifact remains unchanged as defect evidence; a second guarded run confirmed
the corrected state. A third run confirmed both the live state and the nested
`resource_gated` operation result after the summary parser was corrected. The
source baseline was
`2a74134e1a39cd3dab27bbc43de1803844a9a004`, plus the current branch diff.

The focused regression set and canonical local quality gate passed on WSL2.
The final gate after the preflight change passed 2,343 tests with 18 skips.
The runner's 13 focused tests and the Python 3.12 targeted set also passed.
The Classic live runner was inspected: it covers diagnostics, setup, platform
verification, post-install browser checks, authenticated acceptance,
reconcile, update and recovery. Fresh installation, restart, and scoped
destroy/cleanup require separate scenarios. After the runner correction, WSL2
setup passed preflight and reached deployment apply, where separate Traefik
and Infisical failures stopped two runs. On native Linux, a complete rerun
after installing browser dependencies passed all 14 Classic operations,
including authenticated browser/API checks, reconcile, update and recovery.
A separate Jenkins task restart and post-restart authentication passed;
confirmed destroy removed the managed nodes. After stopping an idle conflicting
LXD daemon on the disposable VM, the guarded native installer rebuilt the
managed platform from empty state with exit 0. The repository's quality gate
ran only in local mode.

The fresh native install then exposed a Jenkins image defect: its Groovy
initialization file was `600 root:root`, so the Jenkins process could not
read it. The Dockerfile now copies that file as `jenkins:jenkins` with mode
`0644`. A rebuilt candidate image was inspected at `644 jenkins:jenkins`,
published to the VM's local registry and deployed through the guarded update
workflow. The replacement task logged successful Jenkins setup, and the
post-update authenticated suite returned `LIVE_VERIFIED` (8+8 readiness,
9 browser checks, 7 API checks, zero failures, errors or skips). This validates
the image correction after a managed-state reinstall; the native host had
already been prepared, so it is not factory-clean first-install evidence.

Existing September 2026 RC1 and issue #427 results predate later installer,
CLI, platform and composition refactors in the current branch. They remain
historical observations and cannot establish compatibility for this commit.
The operator approved the usual live campaign and clarified that WSL2
preflight had worked with the current memory setting. A later global resource
floor change had regressed that path. The service-access floor is now 16 GiB
for WSL2 and remains 20 GiB for native Linux; real read-only preflight passed
on both hosts. The temporary `.wslconfig` increase was reverted to the
original 20 GB value without a WSL restart. The Ubuntu 26.04 VM was accessed
using operator-provided credentials, and an isolated candidate archive was
used for native testing. No `LIVE_VERIFIED` claim is made for issue #363.
