# Acceptance checklist

- [x] Architecture regression suite is wired into `arch-tests`, which CI runs through `quality`.
- [x] Synthetic prohibited dependency changes produce findings.
- [x] Findings identify file, line, violated rule, and imported module.
- [x] Legacy root exceptions use explicit reviewed modules and reject new edges.
- [x] Rules follow ARCH-03.02 package responsibilities.
- [x] Independent issue completion audit: PASS after package-child, composition-cycle, and wildcard findings were repaired and verified.
