# CRED-09 executed verification

Actual candidate: 81443e80aad88cf4a9a647cb3241486f06c43e43.
Four clean runs passed: WSL Vault-only 20260912T071242Z (140.439 s), WSL distinct
sources 071614Z (138.717 s), native Vault-only 071903Z (63.548 s), native distinct
sources 072101Z (63.631 s). Each proves selected Vault login, old/non-effective
HTTP 401, observed cookie invalidation after update plus task replacement,
reconcile/redeployment/one replacement, unrelated-state equality and restoration.
Both restored targets passed 37 checks: eight live HTTP/API/TLS and 29 static,
not 37 browser logins. Full local gate: 1,934 tests, 18 explicit skips; 161 focused
checks. Exact commands, timestamps, original failures and original CI links are
in the [published completion report](../../../documentation/evidence/cred09-source-precedence-completion.md)
and its [JSON](../../../documentation/evidence/cred09-source-precedence-20260912.json).
R06 source comparison and current full gate review applicability; no old run is
renamed as c921 or final documentation SHA.
