# S449-03 distribution

Code-only candidate: manifest v2, explicit verified migration, anchor installation
operation lock, optional typed journal intent and target-reader compatibility.
Implementation is isolated in `fix/epic440-manifest-v2-20261107` from `9a81972c`.
Root approved the exact design and necessary composition/runtime/catalog couplings;
architecture independently approved the design and single-journal clarification.
Root and architecture then required private delegation views for shared-object
concurrency. Source and authored regression tests remain subject to exact final
review and PC/WSL verification. Worker ran no tests, hosts or commits.

S02 acceptance, S04 scoped-profile implementation and S05 runtime policy admission
remain separate. Current writers fail closed on unsupported schema2 runtime policy.
