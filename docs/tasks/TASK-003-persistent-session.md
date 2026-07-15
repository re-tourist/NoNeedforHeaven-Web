# TASK-003: Persistent game session and atomic commit boundary

## Goal

Combine the TASK-001 domain transition and TASK-002 snapshot repository in a headless application
session with transaction-like semantics:

```text
current state + current RNG + command + expected revision
    -> candidate domain transition
    -> candidate state/RNG save
    -> commit everything or commit nothing
```

## Required public behavior

- A session can start from caller-provided state/RNG or a valid loaded save.
- Every submission includes an expected revision.
- A revision mismatch returns a structured conflict before domain execution, RNG use, or save I/O.
- Domain rejection returns a structured application result without committing candidate RNG use.
- An accepted transition is persisted before the session replaces its official state and RNG.
- Persistence failure returns a structured application result and preserves the previous in-memory
  state, RNG position, and valid save.
- Retrying after a failed save evaluates from the same official state and RNG position.

## Explicitly excluded

- HTTP endpoints, frontend integration, save menus, slots, and autosave policy;
- transition/event persistence, replay, event sourcing, and generic transaction frameworks;
- multithread, multiprocess, file-lock, database, or distributed concurrency;
- content schemas, formal gameplay systems, narrative content, Obsidian runtime behavior, and LLMs.

The current `counter` remains a neutral synthetic contract fixture.
