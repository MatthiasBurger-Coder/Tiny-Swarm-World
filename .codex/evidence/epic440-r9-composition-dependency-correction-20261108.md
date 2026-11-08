# F4 merged composition dependency correction (R9)

## Trigger and scope

Root reported R8 lint, typecheck and focused checks passed, followed by the
architecture gate refusing new composition cycle edges. The retained failing
architecture log has SHA256
`e60e220371b742269650330ed4664899b14a6863e6934ede695189839b4129de`.
This report does not change that failed gate into a pass.

Only two production dependency edges change. Component-update composition and
creation-completion verification now read the required Portainer secret from
`composition_configuration`, which defines the existing validation function.
They previously imported its compatibility re-export from
`composition_runtime`. Runtime already depends on selection/platform/deployment
composition, so the two unnecessary reverse imports made the new lifecycle and
management dependencies part of its existing compatibility cycle.

The actual secret function, missing-secret refusal, parameter names, public
function signatures, managed writer dispatch, current source/manifest checks,
private leases, profile admission and whole-selected task/API verification are
unchanged. `composition_runtime` keeps its public compatibility re-export.
There is no dynamic import workaround, architecture threshold change, new
exception, mock guard or replacement composition engine.

## Authored bytes and static verification

- `composition_lifecycle.py`: SHA256
  `41fc03b4f79fe280fd84134257ffa0e861836b6a4871733594ca586ea007872f`.
- `composition_management.py`: SHA256
  `40183411d379098d9cf130ab12275919a051596619688e348fc190fd18d62fa2`.
- All other 93 entries of the exact R8 95-file candidate remain byte-identical.
- An independent standard-library AST inspection of all 29 composition modules
  found no cyclic edge outside the unchanged reviewed baseline.
- `git diff --check` completed successfully.

No production module was imported for these checks. No tests, architecture
gate, quality gate, host query, live operation or commit ran in the authoring
agent. The existing architecture regression is the meaningful regression for
this dependency correction; Root must run it and the required full gate on the
SSH test host before integration acceptance. This is source-only authoring,
not independent approval of the author's earlier completion implementation and
not any native/WSL qualification or host-execution authority.
