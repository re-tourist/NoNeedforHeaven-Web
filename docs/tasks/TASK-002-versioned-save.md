# TASK-002: Versioned save and recoverable random state

## Goal

Implement the first P3 persistence slice for the TASK-001 headless kernel:

```text
domain state + deterministic random-source state
    -> explicit versioned JSON
    -> process restart and load
    -> equal domain state and the same random-sequence position
```

The state snapshot remains authoritative. This task does not adopt event sourcing or replay.

## Required public behavior

- A save identifies the product as `buxianxian-save` and carries an explicit schema version.
- The save contains the complete current `GameState` and a supported random algorithm,
  algorithm version, and explicit random state.
- A concrete deterministic random source implements the existing domain `RandomSource` boundary
  and can export and restore its state without Python `random` internals.
- File writes use a same-directory temporary file and atomic replacement so a failed replacement
  does not corrupt the previous valid save.
- Loading validates all persisted data and reports expected failures through stable structured
  error codes.
- Version dispatch has an explicit extension point for future migration, while v1 is the only
  supported format today.

## Acceptance checks

Tests must prove state round-trip, product and schema markers, deterministic RNG continuation,
continuous versus save-and-resume equivalence, all required error classes, old-save preservation
on replacement failure, and continued domain purity.

## Explicitly excluded

- event sourcing, transition logs, or replay;
- fictional legacy formats or implemented migrations;
- application services, save slots, API endpoints, frontend controls, databases, or cloud saves;
- content schemas, authoring integration, formal gameplay systems, or narrative content.

The synthetic `counter` remains only a kernel and persistence contract fixture.
