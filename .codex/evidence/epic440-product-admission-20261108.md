# Product acceptance admission: closed credentials and actual host proofs

SOURCE_ONLY / NOT_RUN. Exact base a81456f0; isolated worktree
`tsw440-product-admission`. Root approved six paths: native suite/source test,
previously frozen WSL suite/source test/record and this shared correction record.
Original WSL394a10 remains unchanged in its original worktree. No public product
files, new shared module, capability entries, target promotion or host actions.

## Findings and implemented boundary

P1: WSL merged arbitrary parsed TSW_* values after its fixed scope; native also
admitted arbitrary TSW path/policy/authority keys beyond its four fixed paths.
Both omitted an explicit owned TLS state root, allowing the ingress resolver to
use /root/.local/state/tiny-swarm-world/tls/traefik. The correction rejects rather
than forwards unapproved operator settings, assigns fixed scope last, and points
TLS exclusively at the protected current case journal/tls directory.

Allowed credential keys are exactly:

- TSW_PORTAINER_ADMIN_PASSWORD;
- TSW_NEXUS_ADMIN_PASSWORD;
- TSW_JENKINS_ADMIN_PASSWORD;
- TSW_SONARQUBE_ADMIN_PASSWORD;
- TSW_POSTGRES_PASSWORD;
- TSW_SONARQUBE_POSTGRES_PASSWORD;
- TSW_PULSAR_TOKEN_SECRET_KEY;
- TSW_PULSAR_ADMIN_TOKEN;
- TSW_PULSAR_MANAGER_ADMIN_PASSWORD;
- TSW_INFISICAL_LOGIN_EMAIL;
- TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD;
- TSW_INFISICAL_ENCRYPTION_KEY;
- TSW_INFISICAL_AUTH_SECRET;
- TSW_INFISICAL_POSTGRES_PASSWORD;
- TSW_INFISICAL_REDIS_PASSWORD;
- TSW_TRAEFIK_GUI_USERS_HTPASSWD.

This literal set matches the active canonical credential catalog and contract
secret material plus the explicit login email. It does not grow automatically
with catalog changes. Inactive optional credentials, all Infisical URL/provider/
seed selectors, images, secret-name selectors, CA/TLS file paths, profile,
selection, policy, authority and consent controls are not credentials. Legacy
username overrides only feed optional Infisical seed behavior; that selector is
not allowed. Non-TSW assignments are ignored by the existing canonical parser
and never forwarded. No shell execution, plaintext expansion or default test
credential injection occurs.

The canonical parser receives an immutable byte-backed read interface with the
two existing exists/read_text operations; its Path interface cast is narrowly
confined to that adapter call. The parser consumes EXACT bytes already approved
by checksum/tree hash, not a second filesystem read. Native checks its approved
operator checksum at child construction. WSL immediately rechecks its entire
approved bounded configuration tree before every public setup/add/helper
construction, retains the operator bytes from that same pass, then parses and
validates them. Credential values are nonempty strings<=8192 with no NUL/CR;
provided values pass the restricted existing ConfigurationContract, and supplied
htpasswd uses the actual semantic validator. Public selected-service validation
still determines required credentials. Controller reasons do not echo values.
Fixed scope and own TLS path are assigned after credential/transport values.

P2: a native PASS artifact could be copied under the WSL label because neither
suite checked actual target_host. The shared pure validator now requires exact
host keys, receipt schema/source/hash, distinct actual file hashes, PASS and
literal33/native_linux versus58/wsl2, server6.0.5, exact admitted fixture runner
SHA and a real GO SHA shape. This is still validation of actual protected input
artifacts, not a creator or signer of qualification. Each suite independently
reads the actual private bytes and resolves the admission source revision AND
both artifact source revisions to the admitted fixture blob before proceeding.
No moving-ref, platform-label or fake-context fallback.

## Verification authored, not executed

- Actual canonical catalog/contract active-key equality and allowed credential
  byte preservation; Path.read_text cannot be used for a second parse read.
- Unknown/reserved authority/path/policy/Infisical/image/TLS selectors refuse;
  invalid htpasswd refuses and errors do not echo supplied values.
- Native checksum drift before parser; WSL operator or other config-byte drift
  before parser/Popen; reserved values with an otherwise approved tree refuse.
- Both scope environments retain fixed anchors/TLS last even if an injected test
  credential-loader regression tries to override them; native uses a real gated
  harmless subprocess for environment/first-output verification.
- Actual canonical_tls_state_root takes the explicit own path without Path.home;
  symlink TLS paths refuse instead of chmod or mkdir on an external target.
- Genuine two-host fixture-shaped unit inputs pass; copied native data, wrong or
  missing targets, wrong captured source/runner, wrong admission source blob and
  wrong captured source blob fail through BOTH real prerequisite functions.

All host, SCM, package, Git/provenance and fixture transports in these unit cases
are faked; fixture-shaped unit data are not actual qualification artifacts. The
actual matrix remains EMPTY and neither native nor WSL product cases ran.
Author checks: Python AST parsing, new-file whitespace scan and git diff --check.
No production imports, PowerShell, tests, hosts or commits. Root independently
reviews and executes exact-source PC focused/full gates; live effects still
require real both-host admission and their own source/host/case GOs.

Root PC R1 nearest found a synthetic graph alias: five distinct API used_by
arrays shared one Python list, so appending the allowed pool image reference
also changed foreign project/profile/network references. R2 gives each array
its own list, matching separately decoded real JSON. Production projection
remains unchanged; an added negative assertion verifies the same image reference
on a network still causes preservation drift rather than being stripped.

## Root PC verification and integration

Frozen R4 six-path manifest8f76e9a8c2f866e45e7c45ad4a5ae8fcb7e4c3460159aa7bb2395052432c4058
was independently staged/verified on PC WSL base128c5e62. Root R3 fixed missing
child pipe narrowing before permit. R4 split21 test semicolons only; AST and
non-layout tokens unchanged. Focus54 PASS0.164s; affected lint PASS.
Final SERIAL-R2 originalumask022/isolatedHOME full QUALITY all7 PASS:43architecture,
type980,3661discovery/36skips/268.924s. Allsix pins rechecked afterward.
Quality68848c08e79aa5f8e0768b68ed925fe7e290917fec3dcdd05901d8ede990a48c;
lint82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18;
focused ad47eb3e0a49a2a3995a95983bbda666e3f34ebd991b1abcf5704bf559d4c69d.
Private ext4 logs were copied600 and hash verified. This record-only append
follows exact tested executing bytes. No live product cases or capability promotion.

Earlier failures remain private: R1 test fake shared Python list alias (corrected
to independent JSON-shaped arrays); R2 type narrowing; R3 lint21E702. Initial R4
full failed a preexisting product migration capture. A bounded actual test
reproduced strict ancestor mtime/ctime sensitivity under own/tmp sibling churn,
while dev/inode/uid/mode stayed fixed; the historical exact failed predicate is
NOT proven. Target/module tests passed. The first serial retry used an incorrect
globalumask077 and failed the public-directory test;022PASS versus077FAIL proved
that launcher error. No production guard/test expectation was weakened. Final
serial022 all7 PASS is the accepted result; earlier failures are not erased.
