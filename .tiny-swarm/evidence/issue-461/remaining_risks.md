# Remaining risks and blockers

- Native tests and the isolated Windows VM are authorized. The native supplied
  host is an existing installation without a clean OS snapshot/restore proof;
  it cannot establish fresh-host or safe injected-failure recovery results.
- Native Python preparation succeeded in the owned source, preserving existing
  protected scopes and three nodes. Network preparation refused the existing
  IPv6-enabled bridge policy. Preserve that policy; installation needs a
  compatible separately recoverable target.
- No native Ubuntu 24.04 target is supplied. The isolated Windows guest now has
  observed Windows 11 Enterprise Evaluation 26H2 build 26300.9457 and a verified
  clean pre-WSL checkpoint restore. WSL/distro/tool installation and full selected
  service capacity are still unverified.
- The 24-GiB Windows OS-only phase is distinct from the full 32-GiB guest. RAM
  was set/observed 32 GiB while off; a 34-GiB free-host guard precedes its boot.
  Do not infer effective WSL limits or service capacity from VM settings.
- Explicit destructive WSL reset consent remains missing. Existing local WSL
  distributions and native resources are preserved. Host-wide shutdown/reset
  or native fault/reboot injection must not be inferred from access details.
- All required AC1/AC2 product fresh/rerun/recovery, ordinary WSL preservation,
  reset isolation, routes and authentication results remain open. No release
  support guard or qualified list is changed; #461 remains BLOCKED.
- AC4 is verified locally: urllib3 2.8.0 strict audit and complete Python 3.12
  quality passed at the frozen runtime candidate. Historical failed audit and
  mounted-checkout timeout remain in test_results.md.
- Historical #363 source/scenario results do not qualify this new candidate.
- Authentication requires protected credentials and redacted evidence. Raw
  VM files, credentials, paths and logs remain private ignored artifacts.
- The source-bound Windows dry-run measured only file hashes and selected
  registry fields; it is partial S13 evidence, not comprehensive no-write proof.

No product quality rule, source guard or selected-service capacity requirement
was weakened. Windows OS provisioning at 24 GiB does not qualify WSL capacity.

The first feature-only UAC launch was canceled; the authorized retry confirmed
features but returned exit 4 PARTIAL when the effect checkpoint replacement
failed. The pending checkpoint and effect records are preserved. A separate
owned-guest reboot was verified and fresh source-bound inventory requests
install_wsl. The revised NullString fix has a passing Windows PowerShell 5.1
filesystem regression, and the full Python 3.12 quality retry passes. Frozen
source and corrected live application are still pending. The operator-installed
Ubuntu registration must be preserved; its observed WSL allocation needs
21-GiB/8-processor reconciliation. Do not upgrade the original partial result.
