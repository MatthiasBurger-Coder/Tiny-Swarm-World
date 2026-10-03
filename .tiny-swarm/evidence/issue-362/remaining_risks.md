# Remaining risks

- A static scan resolves `from package import name` against source module paths. Dynamically generated module imports that have no source file cannot be resolved without executing product code; the architecture contract and import-linter provide additional protection.
- Existing cyclic composition edges remain as reviewed debt. The suite blocks new cyclic edges and permits removal as ARC-04 work progresses.
- Runtime dynamic imports (`importlib`, `__import__`) are outside the AST import rule. Existing product code is not changed by this issue.
- CI execution after publication is pending; local `quality` is the available verification authority for this branch.
