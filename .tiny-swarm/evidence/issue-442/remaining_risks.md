# Remaining risks and supported-scope limits — #442

- No prior installation-manifest schema was shipped. Only v1 identity migration
  is admitted; version 0/future/corrupt state is blocked, never guessed or reset.
- No new mutating CLI. Legacy installations remain usable via existing commands;
  new inspection reports adoption_required until complete verified inventory is
  available. Application adoption is an explicit integration boundary for W03/W04.
- Desired native image/build identities are known; upstream discovery, live image
  digest resolution and refreshed runtime observations are W05/W06 responsibilities.
  Unknown values remain null, and missing observations are not success.
- Resources report existing native declarations only, not qualified capacity.
  Fixed setup still couples Nexus/Traefik and service-access/Infisical; arbitrary
  optional omission is not claimed before W03/W04 integration.
- No qualified product/component/Portainer transitions are admitted by this
  catalog. W05–W08 own qualification and stateful backup/migration restrictions;
  image rollback cannot restore persistent data. No Incus host upgrade automation.
- Crash after replace but before directory fsync has uncertain durability and
  requires inspection; orphan temporary files are retained/diagnosed after kill.
  Writer concurrency uses a local advisory lock plus stale-token refusal; external
  manual writers must respect the contract. No live infrastructure was changed.
- Local checks use prepared Python 3.14.4 on WSL2; source retains Python 3.12
  syntax/APIs. This is not a claim of native/WSL2 installation/upgrade qualification.
  W09 owns exact-SHA/version/selection/host/command/result/redacted live evidence.
- Optional skipped/live/external checks remain non-pass; only executed default
  local checks support local implementation completion.
