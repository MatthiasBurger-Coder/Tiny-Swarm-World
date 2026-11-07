# WSL Q16 source-admission previews — R52

Status: **VERIFIED BOUNDED subcases; Q16 remains PARTIAL.** This records two
read-only product-preview refusals on WSL2. It does not qualify a product
upgrade or claim that WSL runtime state was observed or preserved.

## Candidate identity

The controller was copied from current workspace base HEAD
`6d2f25ee843a01066fcdcfe4855666849513ff06`, including its exact current dirty
Python source tree and lock. The source archive SHA-256 is
`d8a79a5d91fa4762c1960610184d720403628560f1281dec11439edc4bb4b6d6`; its 554
file source/metadata manifest SHA-256 is
`64bbb92f33e17c91a18e5f33155bfca26a0ff5299f55bc69d30fedf0306f6d10`.
`requirements.lock` SHA-256 is
`ac9474784f50b87087e5e24a5a3163118aaf1f2845597d07f7dfa86eb713ff08`, and the
`product_admission.py` SHA-256 is
`195953d6fe420281617d0f62b599c4cb7cd689b4ba0ac7276d22befbe13cb86d`. The
controller used Python 3.12.15 on `approved WSL2 test host` WSL2.

## Preview cases

Both fixtures were separate owner-only temporary Git repositories. The dirty
case had the official credential-free origin and one untracked sentinel. The
clean case had origin `https://example.invalid/tsw-449-q16-origin.git`. No
remote fetch was needed. Both used the exact command:

```text
python -m tiny_swarm_world product upgrade --to 0.5.0 --preview --json
```

| Case | Result | Standard-output SHA-256 | Standard-error SHA-256 | Fixture state |
|---|---|---|---|---|
| Dirty checkout, official origin | Exit 1, `blocked`; dirty-checkout diagnostic | `2790b48971d704a0cb27ae348b7f5cca6ddec4df23085049fcf03c21b75516c6` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | HEAD, tree, origin and porcelain status unchanged; sentinel remained the sole untracked file |
| Clean checkout, unofficial origin | Exit 1, `blocked`; official-repository diagnostic | `c27c41bbf2cc92711be8fc8e8ab3f890eab9be981de94173ccfa536b51521579` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | HEAD, tree, origin and porcelain status unchanged; remained clean |

`TSW_INFRA_ROOT`, credentials, adoption, live, recovery and consent inputs were
absent. Git global/system configuration was isolated. A local null proxy blocked
external release-resolution requests if the source guards had failed open.
Static inspection of the exact candidate confirmed the dirty/origin checks run
before manifest and release resolution. No manifest, journal or state root was
created. No Incus, Docker, Swarm or Portainer operation ran.

## Evidence boundary

Requirements, Architecture and Test/Evidence independently accepted these two
bounded subcases. The private local bundle is under
`.tiny-swarm/evidence/issue-449/q16-wsl-r52/`: run-record JSON SHA-256
`8dc86e47e92764beea051f4dcc5c0546842f25a1f83bf528caa4e09c5712a90b`, fixture
archive SHA-256
`96c7c43e8d8effed4cd710abd9ae0d290bcfe215a5b198ee27fc5a426f4e4771`, and the
controller source archive above. The run record preserves the parsed
diagnostics and stdout/stderr hashes; raw stdout files were not retained. The
fixture archive and source archive are local ignored artifacts, so this report
is the versionable summary and the private bundle is not a versioned W10
handoff.

Q16 remains **PARTIAL**. Moved-source semantics, other dirty/unknown source
cases, runtime drift, old/mixed tasks and remaining cross-host applicability
are still open. No runtime-preservation or release-resolution claim follows
from these previews.
