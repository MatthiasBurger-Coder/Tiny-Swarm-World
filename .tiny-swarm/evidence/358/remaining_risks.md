# Issue #358 remaining risks

- Runtime infrastructure and live provider behavior were not exercised because this issue changes local CLI orchestration and no live consent was provided. Local tests use mocks.
- The CLI compatibility exports and builder injection remain to preserve existing patch points for downstream Python callers. These are command-edge compatibility surfaces, not application workflow owners.
- A network-repair shell fixture outside the CLI path caused intermittent SIGPIPE under `pipefail`. The fixture now drains its fake producer; the final full quality run is the completion gate.
