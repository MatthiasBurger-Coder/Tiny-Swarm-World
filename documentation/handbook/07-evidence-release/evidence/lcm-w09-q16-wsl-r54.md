# WSL Q16 relocated-checkout characterization — R54

Date: 2026-10-26. Result: **bounded characterization only; not a Q16 pass**.

The WSL2 preview used the exact R52 candidate source archive
(`d8a79a5d91fa4762c1960610184d720403628560f1281dec11439edc4bb4b6d6`) and a
disposable clean Git fixture. The fixture was recorded at path A, moved to path
B, and had the same synthetic HEAD `92dc2f0425eb07222bb2aca26205fd5780276a68`,
tree `6429dc10e834241e96cad615e0b5da1a27f4ea65`, official-origin URL and clean
porcelain state before and after the move.

The command was `product upgrade --to 0.5.0 --preview --json`, Python 3.12.15,
candidate controller cwd `/tmp/tsw449-q16-wsl-r52/controller`. It exited 1 with
`status=blocked` and the later diagnostic `Legacy installation needs an
explicitly inventoried --adoption-manifest; no state inferred.` Raw stdout is
included in the private run bundle; stderr was empty. The result is consistent
with the source guard not refusing the relocated checkout, but the run record
omits the `TSW_REPOSITORY_ROOT` value and the runner script is absent, so
invocation binding is not independently proven. The command did not reach release
resolution, resource validation or runtime, so this is not a successful product
preview, source/manifest continuity result, runtime preservation check, or
moved-source refusal pass.

Private archive:
`.tiny-swarm/evidence/issue-449/q16-wsl-r54-relocation.tar.gz`,
SHA-256 `61919d665113360fcafa037fd23427cf45af642912614245b9fb314c69983aad`.
The run record lists `TSW_REPOSITORY_ROOT` as an environment key but omits its
value; the runner script and an explicit path-binding assertion are not in the
archive. Therefore independent review could not bind the invocation to path B
with the required strength. No runtime state or credentials were read and no
`TSW_INFRA_ROOT` was set. Q16 moved-source semantics remain open pending
clarification whether “moved” means a moved official release reference or a
relocated clean checkout. See the private Three-Amigos follow-up and R52 report.
