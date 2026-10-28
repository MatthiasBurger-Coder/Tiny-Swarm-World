# S449-02F3 design record — symbolic Snap executable path classification

## Trigger

Committed S449-02F2 `9c311145e7b4a4ad5f588829fd9867776678e452` passed PC WSL verification. Its separately authorized native symbolic diagnostic returned `BLOCKED_UNKNOWN` for `snap.lxd.daemon.service`. The result did not expose the resolved executable path, as required.

## Requirement and scope

Classify the already-read resolved executable string in memory into a closed symbolic reason. Preserve `status=BLOCKED_UNKNOWN` and `identity=UNKNOWN`. For the fixed Snap LXD service, emit one of `SNAP_ROOT_PATH_MISMATCH`, `SNAP_EXECUTABLE_OUTSIDE_ROOT`, or `SNAP_EXECUTABLE_UNCLASSIFIABLE`. For other unknown services emit `EXECUTABLE_IDENTITY_BLOCKED`.

No new host command is added. The implementation must not emit or persist path, revision, basename, PID, package/version, raw output or exception text. It must not write an artifact, query endpoints/resources, change the executable allowlist, or claim native inventory/ownership success.

## Three-Amigos decision

- Requirement: GO for this narrow diagnostic extension; retain fail-closed identity state.
- Architecture: APPROVED; reuse the existing readlink result and existing module, no new dependency or service boundary.
- Security: APPROVED in principle; closed symbolic category only, no sensitive path-derived detail.
- Python Automation: APPROVED; Tester: APPROVED; both verified the exact v1.39 workflow/context/design hash tuple.
- Official Snap documentation describes `/snap/<snapname>/<revision>` mount points and an optional `current` symlink. This supports classifying path shape only; it does not prove executable identity or justify allowlist expansion: <https://snapcraft.io/docs/explanation/how-snaps-work/system-snap-directory/>.

## Acceptance checks

1. Each enum outcome is deterministic and exact; unknown identity remains blocked.
2. Empty/non-absolute values map to `SNAP_EXECUTABLE_UNCLASSIFIABLE`.
3. No path, revision, basename, PID or raw runner bytes appear in stdout, stderr, artifacts or command records.
4. No additional host command is issued; first-unknown stop and active-service recheck remain unchanged.
5. Normal inventory mode and existing admitted executable identities remain unchanged.
6. Focused inventory tests, full PC WSL quality gate, same-hash reviews and `git diff --check` pass before commit.

## Execution boundary

Sequential S449-02F3; no parallel streams. Obtain exact-hash reviews and a dedicated S3D plan before implementation. A separate post-commit S3D plan is required before any native rerun. Any allowlist change is out of scope.
