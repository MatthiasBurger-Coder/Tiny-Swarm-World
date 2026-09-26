# Verification results

## Original worktree

Final `python3 tools/quality_gate.py quality`: all static gates PASS; 2179 tests,
2160 passed, 18 skipped, one pre-existing Windows Pester path-conversion failure.
Full output: quality.log. Baseline had the same failure before edits (2165 tests).
No changed-code failure remains. git diff --check: PASS.

Independent focused verification: 17 tests PASS (test_execution_contract and
spawn-boundary tests). Development focused sets of 109 and 23 tests also passed.

## Interop recovery

Earlier restricted executions could not see /run/WSL sockets and PowerShell
returned UtilAcceptVsock. After user changed to unrestricted execution, the
same socket and PowerShell invocation worked without restarting WSL.
The earlier conclusion that the host WSL environment itself was broken was
not established; it was based on a restricted filesystem view.

The unchanged Pester test was rerun in the existing mounted checkout and
PASSED: one test, 9.734 seconds. Test wrapper, test script and bridge script
were compared byte-for-byte before that retry.

## Full final verification

A byte-identical copy under /mnt/d is used because the existing Pester wrapper
supports mounted-drive paths only. final-verification-copy.json records all
input hashes; final-verification-result.json will record exit status and
post-run comparison to both copy and original. final-quality.log is authoritative.
Final result: PASS, exit 0. All six gates passed. 2179 tests ran in 242.816s;
2161 passed and 18 were skipped. Pester passed in the full suite. SHA-256
comparison after the run found no input differences between the candidate,
verification copy and original worktree. Earlier failed attempts above are
historical and do not describe the final verification status.

Earlier failed copy attempt: verification-copy-failed.log. That copy disappeared
during execution for an undetermined reason; its cascading failures are not
claimed as validation and do not override the final result.

LIVE_NOT_APPLICABLE: mocked source-refactor verification; no live infrastructure
execution requested or claimed.
At implementation verification time external gates were not applicable.
The subsequent explicit push auto authorizes publication; PR CI and configured
SonarCloud checks must pass before merge. Their results will be recorded on
the PR. Pester is part of the default local test suite.
