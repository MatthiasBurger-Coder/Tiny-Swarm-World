# Issue 363: credential transition runner login correction

Current live Jenkins login includes a hidden Jenkins-Crumb field. The canonical
credential transition runner omitted it, so its cookie-session precondition
failed despite successful Basic authentication with the same credentials.
Submitting the actual form fields with those credentials authenticated the
cookie session in the bounded diagnostic; the original failed run and successful
restoration remain separate evidence.

The runner now parses hidden fields only from the matching local authentication
form using the standard HTML parser and submits them through the same session.
Explicit supplied username/password override any hidden field values. Missing or
foreign authentication forms fail before submission. No form tokens are logged;
server CSRF checks, subsequent identity checks, cookie invalidation assertions,
TLS settings and restoration logic are unchanged.

Regression evidence: original helper failed three assertions in six tests; the
corrected helper passes all six. Final canonical local gate passes2377tests with
18existing skips. Both-host Vault-only and conflicting-operator live scenarios
must execute on the committed corrected runner; no old failure is relabeled.
Full scenario evidence belongs to .tiny-swarm/evidence/issue-363-final-validation/.
