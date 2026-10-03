# Governing cache repair review

The README architecture navigation edit invalidated its recorded SHA256.
The registry conflict skill was read; README content was manually reviewed as
link-only, with no role, ownership, policy or STOP-rule changes. Only the
README.md hash field was updated using SHA256 over the current file bytes.

Independent reviewer confirmed deleting that field makes the parsed original
and current JSON identical, and the new uppercase hash matches README bytes.
All other recorded governance hashes remain unchanged.

Decision: hash-only repair accepted; registry integrity and skill discovery
checks substantiate revalidation, not reuse of the stale cache.
