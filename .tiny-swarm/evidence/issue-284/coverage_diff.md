# Change-Specific Coverage: #284 / CRED-06

After the issue branch is committed, run the full branch-aware suite and the
versioned diff utility from the repository root:

```text
python3 -m coverage erase
PYTHONPATH=src python3 -m coverage run --branch -m unittest discover -s tests -t .
python3 -m coverage json -o /tmp/tsw-cred06-coverage.json
python3 tools/coverage_diff.py --base main --coverage-json /tmp/tsw-cred06-coverage.json
```

The utility counts only executable production statement lines and source branch
arcs added by the branch diff. Documentation, test code, comments, imports,
multiline expression continuations, and deleted legacy lines are excluded.

Result: pending final branch-aware run on the committed CRED-06 branch.
