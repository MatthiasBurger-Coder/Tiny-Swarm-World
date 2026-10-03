# RC1 behavioral applicability and rerun mapping

Historical product: c921e69533450fba86d908e2990c106bef87769a. Final runtime/test candidate:89357c4a1fd463bbe5ee2ae9dac074180513eace. Independent source assessment: documentation/evidence/issue-363-final-source-applicability-20261003.md. Every retained run keeps its actual revision.

| Stable ID | Historical scope invalidated by refactor | Successful replacement / evidence | State |
|---|---|---|---|
| S01 | Local quality/debugger/static preflight | Final code-equivalent gate2377PASS18existing skips; configured debugger/preflight in WSL phase ledger; native canonical diagnostics chain. local-verification.json. | VERIFIED |
| S02 | WSL pre-live diagnostics/bridge | Current canonical bridge preflight and actual nine Windows routed HTTPS checks with scoped current public CA. Default systemtrust and revocation availability explicitly unpassed. | VERIFIED scoped contract |
| S03 | WSL fresh installation | Clean1bd3 reset/emptyinventory/new3UUIDs/bootstrap18continuousservices/readiness; portable/wsl-fresh.json and reviewed unchanged runtime applicability. | VERIFIED |
| S04 | Post-install browser/API | WSL clean1bd3 and native cleanbdd immediate25live+7API, no failures/errors/skips; current893 native canonical chain. | VERIFIED |
| S05 | WSL reconcile | Clean1bd3 healthy reconcile no_op, stableUUIDs+25+7; final893affected worker converged then repeatno_op+25+7. | VERIFIED |
| S06 | WSL update | Actual distinct content-marked image A→B preview/apply, unchangedrepeatno_op, canonicalrecoveryA and25+7/persistedcomparisons under actualbddrevision. | VERIFIED |
| S07 | Representative prerequisite failclosed | Six relevant mocked modules122PASSzero skips/failures/errors; final fullgatepreflight regressions. No destructive live prerequisite fault required. | VERIFIED LOCAL |
| S08 | Partial/node recovery | Both hosts realexit73failedrollout→typedrollout_failed→recoverA→repeatno_op; final893stoppedworker convergence/repeat+25+7, preservedfixtures/identities. Originalfailures remainfailed. | VERIFIED |
| S09 | Selected distribution/native host restart | Actual isolated WSLdistribution PID1/namespacechange plus native changedbootID,≤600sreadiness and25+7/config/credentials/data/identity continuity. Final primary Ubuntu restoration also passed116.957seconds≤600 with25+7 and original application-data continuity. | VERIFIED |
| S10 | Native fresh installation | Cleanbdd canonicaldestroyemptyinventory→freshinstall/newUUIDs/immediate25+7; explicit resourcefixture18.73GiBhost8/6/3GiBnodes; reviewedphysicalapplicability. | VERIFIED |
| S11 | Native reconcile | Final893canonicalchain plus actualaffectedworker convergence→repeatno_op, stableidentities/config/specs and25+7. | VERIFIED |
| S12 | Native update | Final893distinctaccuratelyattributedB update+auth/recovery+auth, repeatedno_op, supplementalfault/recovery continuity. | VERIFIED |

All four credentialconsumer transition cases executed final893: bothhosts Vault-only and distinctoperator/Vault conflict LIVE_VERIFIED with verifiedrestoration. Unsupported platformstatusexit2 is retainedguard evidence; supportedstatus usesplatformverify. Both-hostmanagedcleanup/fresh proofs preserve trueexecutedcommands.

Historical hostedCI/Sonar/container scans and RC1 release decisions remain attributed to old candidates. Current external checks are NOT_APPLICABLE to this local behavioral completion task; manual current scenarios do not claim hosted execution or a newRC1_ACCEPTED.

## Independent final mapping review

Reviewer `/root/rc1_mapping`: PASS for behavioral applicability/mapping. Reviewed final2377/18-existing-skips local gate and122prerequisite fixtures, scoped Windows trust limits, true-revision retained physical evidence, both-host final affected worker/fault/CRED cases, actual WSLdistribution/nativehost reboot with representative application data, cleanfresh/reconcile/distinctupdate. No whole newRC1release/hostedCI/Sonar claim. Primary Ubuntu final restoration and portable checksum validation also passed; whole-issue independent audit remains the final authority.
