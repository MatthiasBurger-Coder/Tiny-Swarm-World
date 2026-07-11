# Dependency Scan Policy

Runtime dependency audits use the hashed `requirements.lock` file and fail on
known vulnerabilities or incomplete collection:

```bash
python3 tools/security_gate.py dependencies
```

Regenerate the lock from the declared ranges with the supported Python 3.12
runtime only, and only after reviewing the resolved versions:

```bash
python3.12 -m piptools compile --generate-hashes --strip-extras \
  --output-file=requirements.lock requirements.txt
```

CI performs a clean Python 3.12 install with `--require-hashes`, installs the
editable project with `--no-deps`, and runs `pip check` before quality gates.

Do not edit a vulnerable package out of the audit, weaken strict mode, or add an
ignore identifier without a documented risk decision. Development tools are
not runtime dependencies and are maintained separately in
`requirements-dev.txt`.
