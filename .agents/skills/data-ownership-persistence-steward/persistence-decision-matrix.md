# Persistence Decision Matrix

| Store type | Use when | Do not use when | Required evidence |
| --- | --- | --- | --- |
| Relational Store | Entities need transactional consistency, constraints or tabular queries. | Relationships, traversals or semantic graph queries are primary. | Owner, schema, writer, migrations or migration plan. |
| Graph Store | Relationship traversal, dependency analysis or provenance graph queries are primary. | Runtime execution truth would be inferred from static relationships. | Node and edge semantics, provenance, deterministic ordering. |
| Event Store | Ordered facts or integration events must be replayed or projected. | Events are used as shared mutable state. | Event owner, ordering, idempotency, retention. |
| Vector Store | Similarity search over embeddings or generated representations is required. | Vector content would become verified evidence. | Source evidence link, embedding model, rebuild policy. |
| File/Object Store | Large artifacts, reports, snapshots or raw payloads need object identity. | Structured query semantics are required. | Object key, checksum, provenance, retention. |
| Runtime Trace Store | Observed runtime trace events need correlation and replay support. | Missing values would be fabricated or inferred. | Correlation IDs, ordering, completeness markers. |

## Decision Requirements

Every persistence decision must state:

- why this store fits the access pattern;
- who owns writes;
- who may read and how;
- how provenance is preserved;
- how deterministic output is verified;
- what security or data-protection review is needed.
