---
name: protobuf-contracts
description: Use for Protobuf contract changes, ingestion messages, compatibility review, and schema-verification work.
---

# Protobuf

## Purpose

Guide Protobuf contract changes for ingestion and analysis payloads.

## Practices

- Verify current `.proto` files and generated consumers before changing fields.
- Preserve field numbers and names unless a task explicitly requires a contract change.
- Represent missing optional data explicitly.
- Keep evidence categories distinct in messages when practical.
- Document compatibility decisions and test them.

## Verification

- Run Protobuf generation or affected adapter tests when contracts change.
- Run full repository verification from `QUALITY.md` for public schema changes.
