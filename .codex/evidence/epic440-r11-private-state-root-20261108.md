# Epic 440 R11: canonical first-writer state-root protection

## Authority and finding

Root authorized this narrow source correction after R10 PC discovery reported
3518 tests / 281.492 s, one failure and two errors (36 skips), log SHA256
`e565f83891ad1695d2fcc618300b39c0d21b892af2dd03d6c28b139801590fb6`.
The three package-entrypoint setup tests exposed a production ordering defect:
LoggerFactory created the fresh `.tiny-swarm-world` parent with the process
umask (normally 0755), before the real private installation lock required 0700.
R10's real journal guard delegate correctly exposed this defect; it is retained.

## Bounded implementation and locks

Seven production paths are in this Root-approved correction:

- `infrastructure/adapters/repositories/managed_state_directory.py`: shared
  descriptor-based no-follow ancestor walk, fresh private root creation and
  existing owner/mode validation; owned regular append-only log stream opening.
- `infrastructure/logging/logger_factory.py`: create fresh private state before
  logs, preserve FileHandler/public logger ABI and read-only no-write behavior.
- `infrastructure/adapters/lifecycle/manifest.py`: validate/create TinyRoot before
  the existing manifest persistence sequence.
- `infrastructure/adapters/repositories/observed_inventory_local_repository.py`.
- `infrastructure/adapters/repositories/verification_evidence_local_repository.py`.
- `infrastructure/adapters/repositories/routing_evidence_local_repository.py`.
- `infrastructure/adapters/repositories/project_filesystem_evidence_local_repository.py`.

Paths above are relative to `src/tiny_swarm_world/`. The last four writers retain
their existing child-directory/file/error contracts. Project-filesystem XDG
storage outside TinyRoot retains its previous policy. Read-only path resolution
never creates state. The three local-state repositories retain their original
lexical TinyRoot for write admission because their existing path resolver can
resolve an in-repository state-root symlink; resolved output must not erase the
original authority boundary. Root/project paths and existing public signatures
are retained.

Fresh TinyRoot is created 0700. Existing foreign-owned, wrong-mode, symlink or
non-directory TinyRoot is refused without chmod, adoption or migration. Logger
also refuses unsafe ancestors, symlink/hardlink/nonregular/foreign/writable log
files before writing. Existing ordinary owned log directories and files retain
their modes. Existing unsafe installation state remains BLOCKED and unchanged.
No installation guard, lease, consent, checkpoint, capability or host policy is
relaxed; Incus capability matrix remains unchanged/empty.

## Delivery regressions and honest fixtures

- `tests/infrastructure/logging/test_logger_factory.py`: actual logger under
  umask 022 followed by actual installation lease; retained unsafe state roots
  and log symlink, plus existing read-only test.
- `tests/infrastructure/adapters/repositories/test_managed_state_directory.py`:
  all five real first writers followed by actual private lock; wrong-mode roots
  refuse unchanged; resolved local-state paths cannot conceal original symlink.
- `tests/test_package_entrypoint.py`: the three setup tests use a real isolated
  fresh repository with actual infra/catalog and required repository markers.
  No pre-created state root, fake logger, fake private guard or changed assertion.
- `tests/infrastructure/adapters/repositories/test_routing_evidence_local_repository.py`:
  the existing atomic-replace failure fixture now explicitly creates its owned
  temporary TinyRoot 0700, so its intended os.replace failure is reachable.
  Its preservation/error assertions are unchanged.

## Verification state

Author verification is source-only AST parsing, exact unaffected R10 hash
comparison and Git whitespace checks. No project imports, tests, quality gates,
host commands or commits were executed by this author. Root must run independent
source review, focused logger/writer/package-entrypoint regressions and all
required PC gates on the exact R11 manifest. This is not live acceptance and does
not establish Epic completion.

## Root R12 concrete stream annotation

Actual R11 nearest91 tests and43 architecture checks passed, as did181 integration
focused tests. Typecheck then refused the abstract TextIO annotation assigned to
FileHandler.stream, which requires TextIOWrapper. The implementation already
returns the real os.fdopen text wrapper; annotate that concrete TextIOWrapper
without changing any call, flags, guard or handler behavior. No cast or ignore.
Retained type log29f87f32953700ed4d4c9a213dc58be69650ea84055c1c7b9a54c0d1a7cd2667.
R12 exact type/full gates remain pending.
