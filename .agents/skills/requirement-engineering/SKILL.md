---
name: requirement-engineering
description: Use for EPIC lifecycle work, requirement drift detection, functional and non-functional requirement classification, architecture impact analysis, requirement traceability, constraint management, assumption tracking, and continuous comparison between implementation and EPIC assumptions.
---

# Skill: Requirement Engineering

## Purpose

Keep requirements, EPIC assumptions, architecture documentation, workflows, skills and roles synchronized with verified repository behavior.

LLM output, generated summaries and inferred plans are not requirements unless confirmed by explicit user input, EPIC text, architecture decisions or verified implementation behavior.

## Required Inputs

Inspect the relevant subset of:

- user request
- `AGENTS.md`
- `QUALITY.md`
- `documentation/epics`
- `documentation/arc42`
- `documentation/adr`
- `documentation/workflow`
- affected source, tests, schemas, examples or fixtures
- affected `.agents/skills` and `.agents/roles`

## EPIC Lifecycle

Before changing requirement-sensitive artifacts:

1. Identify the current EPIC source.
2. Verify whether implementation assumptions still match the EPIC.
3. Classify the requirement or drift.
4. Trace the change into arc42, ADR references, workflow slices and quality checks.
5. Document unresolved conflicts instead of choosing silently.

Ask internally:

```text
Does the implementation still match the EPIC?
```

## Requirement Classification

Classify requirements as one or more of:

- functional requirement
- non-functional requirement
- architecture constraint
- resilience requirement
- scalability requirement
- UX requirement
- observability requirement
- security or data-protection requirement
- quality-gate requirement
- assumption
- open question

## Drift Detection Checklist

Continuously verify whether:

- architecture changed
- runtime behavior changed
- responsibilities moved
- service ownership changed
- plugin versus server responsibility changed
- service boundaries changed
- new runtime assumptions appeared
- new orchestration assumptions appeared
- new persistence assumptions appeared
- new deployment assumptions appeared
- new UI assumptions appeared
- new resilience assumptions appeared
- scalability assumptions changed
- observability requirements changed
- UX requirements changed

## Drift Response

If drift is detected:

1. Update the EPIC when the requirement baseline changed, or document why the EPIC update is blocked.
2. Update arc42 when architecture, runtime, deployment or crosscutting behavior changed.
3. Review ADR references.
4. Regenerate or update `documentation/workflow` through `workflow-authoring`.
5. Review related skills and roles.
6. Document unresolved conflicts.

Do not hide drift with compatibility aliases, fallback paths or ambiguous wording.

## Traceability Rules

Every requirement-impacting change must trace to at least one of:

- requested task
- EPIC requirement
- verified implementation behavior
- architecture decision
- quality-gate rule
- documented project decision

If no trace can be established, stop and report.

## Stop Conditions

Stop and report if:

- the EPIC source cannot be identified
- EPIC, arc42 and implementation contradict each other
- implementation behavior cannot be verified
- service ownership is ambiguous
- resilience expectations are unclear
- a requirement would require guessing runtime facts
- a requirement would present planned behavior as implemented

## Expected Outputs

- requirement classification
- drift findings
- traceability notes
- required EPIC, arc42, ADR, workflow, skill or role updates
- unresolved conflicts and stop reports
