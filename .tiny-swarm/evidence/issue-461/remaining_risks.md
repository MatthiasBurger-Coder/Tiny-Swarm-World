# Remaining risks and blockers

- Native test and isolated Hyper-V construction authorization now exists.
  Native clean snapshot/restore proof, explicit destructive reset consent and
  completed recoverable Windows installation remain missing.
- Operator identified local WSL and native SSH Ubuntu 26.04.1 targets; OS/kernel
  and Windows/WSL versions were observed read-only. No clean snapshot/restore
  method is established, no 24.04 target supplied, and runtime tool versions
  and selected-service capacity remain unverified.
- Existing local worktrees/live configuration do not authorize mutations.
- Restart, fault injection and destructive reset require scoped authorization;
  WSL host-wide shutdown could affect unrelated distributions.
- Resource boundaries depend on actual selected services and measured target
  capacity; mock/predecessor results do not qualify a capacity claim.
- Authentication requires protected operator credentials and redacted results.
- Historical #363 managed-state freshness is not fresh-OS evidence; changed
  bootstrap source prevents inheritance of W09 qualification.
- All required live AC1/AC2 product scenarios remain unexecuted. Issue is BLOCKED,
  not DONE. No release support guard or qualified list is changed.
- AC4 dependency security gate failed (exit 1): locked urllib3 2.7.0 has
  PYSEC-2026-4175, PYSEC-2026-4176 and PYSEC-2026-4177 according to the
  executed pip_audit result; reported fix version is 2.8.0. Dependency
  remediation and affected regression checks require a new committed runtime
  candidate before live qualification. No dependency change is represented
  by this evidence-only branch.

The original dependency finding is remediated in the working lock and a new
strict audit passed. A new committed candidate and passing full regression gate
are still required. The first mounted-checkout full run failed one 10-second
installer fixture timeout; supported-runtime verification is running in an
isolated Linux-native checkout. Windows media download and clean guest creation
are unfinished; full default WSL preparation additionally needs sufficient host
RAM for the 32-GiB guest. Prior audit/consent findings retain their historical
context and must not be read as the latest operator authorization state.
