# Changed files

Evidence scope is `.tiny-swarm/evidence/issue-461/`:
requirement_matrix.md, qualification_matrix.md, implementation_summary.md,
changed_files.md, test_results.md, remaining_risks.md, acceptance_checklist.md.
commit_readiness.md records local source-freeze readiness.
completion_audit.md records the independent read-only review.
Additional scope: requirements.lock, narrow urllib3 security remediation for
AC4. No existing workflow, source, test, configuration or historical evidence
edits. Ignored local VM scripts/images/logs/credentials are not commit content.

Portable redacted live observations: native_preflight_result.json and
native_python_result.json. No raw remote logs or credentials are included.

windows_image_result.json records the actual successful image/boot steps and
RAM-guarded stop; guest boot/checkpoint was unverified at that historical attempt; later Windows
OS-only boot and checkpoint restoration are now verified.

windows_resume_result.json and windows_image_diagnostic.json preserve the
failed resume attempt and read-only owned-image observations.

windows_provision_only_result.json records actual 24-GiB first boot and the
checkpoint ACL failure, with private error paths excluded.

Continuation records: windows_checkpoint_attempt.json,
windows_checkpoint_inventory.json, windows_guest_dry_run_unbound.json,
windows_guest_dry_run_source_bound.json, windows_pre_wsl_restore_result.json.
Historical failed attempts and actual successful environment checks remain
separate; private helper scripts and credentials are excluded.

windows_feature_elevation_result.json records the actual host elevation failure
and absence of guest feature execution.

R461-22 live blocker remediation: tools/windows/preparation/Adapters.ps1 uses explicit PowerShell NullString for the existing atomic state replacement; tests/windows/prepare-windows.Tests.ps1 adds real create/replace IO regression with isolated mocked ACL boundaries; documentation/user_guide/windows-preparation.md explains retained pending evidence after persistence failure. No source qualification guard or atomic-write requirement is relaxed. New portable evidence includes feature apply, partial inspection, recovery reboot and disposable writer diagnosis.
