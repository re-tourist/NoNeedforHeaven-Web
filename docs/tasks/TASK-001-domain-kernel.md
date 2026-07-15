# TASK-001: Headless deterministic domain kernel

## Goal

Implement the smallest pure Python state-transition kernel that proves the P2 contracts without creating gameplay, persistence, API, content, or narrative systems.

The required transition semantics are:

```text
old state + typed command + controlled random source
    -> accepted(new state, domain events)
    or rejected(original state, structured reason)
```

## Required public behavior

- A minimal authoritative state contains `revision` and synthetic `counter` fields.
- A typed neutral command can request consumption of an exact counter amount.
- A second neutral command may use an injected random source solely to prove deterministic random behavior.
- Accepted transitions return an independent complete state, increment revision once, and emit a fact event.
- Expected invalid commands return a structured rejection without mutation, revision change, or success event.
- Command dispatch is type-directed and delegates to focused handlers.
- Domain code uses only the Python standard library and has no transport, filesystem, database, authoring, UI, LLM, or narrative dependency.

## Acceptance checks

Tests must prove:

1. consuming 2 from `GameState(revision=0, counter=5)` produces revision 1 and counter 3;
2. the accepted result contains a corresponding domain event and a distinct new state;
3. consuming 10 from the same state returns a recognizable rejection and preserves the original state;
4. success and rejection never mutate their input state;
5. identical state, command, and controlled random input produce equal results;
6. different controlled random inputs produce the expected different results;
7. domain tests run directly without starting FastAPI;
8. all backend format, lint, strict type, and test checks pass.

## Explicitly excluded

- scenes, nodes, navigation, condition/effect DSLs;
- time, action points, formal resources, inventory, tasks, relationships, progression, cultivation, combat, or NPC systems;
- saves, migrations, replay persistence, content schemas or compilers;
- new HTTP endpoints or frontend behavior;
- Obsidian, Markdown, LLM, database, packaging, or narrative integration.

The synthetic `counter` is a contract fixture, not a formal resource system.
