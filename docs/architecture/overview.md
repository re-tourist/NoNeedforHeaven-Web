# Architecture overview

## Target architecture

```text
Obsidian author workspace
        |
        | Markdown / YAML source material
        v
Content validation and compilation
        |
        | versioned runtime content package
        v
Python application
  - domain kernel
  - application services
  - persistence adapters
  - HTTP API
        |
        | commands and read models
        v
Browser frontend
  - rendering
  - player input
  - local presentation state
```

This is a target direction. P1 implements the engineering shell and connectivity smoke test. P2 adds the pure headless domain kernel. TASK-002 begins P3 with only versioned snapshot persistence and a recoverable deterministic random source; application services, replay, content, and gameplay layers remain deferred.

## Authority boundary

### Python owns

Eventually:

- authoritative game state;
- command validation;
- state transitions;
- random outcomes;
- time progression;
- persistence;
- content loading;
- world simulation;
- LLM orchestration and output validation.

### Frontend owns

- rendering;
- input collection;
- accessibility;
- transient UI state such as an open panel or pending request;
- error and loading presentation.

The frontend must not independently award resources, change relationships, advance time, or decide game outcomes.

## Planned backend layers

These directories are planned boundaries, not permission to implement them early:

```text
backend/src/buxianxian/
├─ domain/          # Pure rules and state transitions
├─ application/     # Use cases and orchestration
├─ infrastructure/  # Filesystem, storage, content, external services
└─ api/             # FastAPI transport
```

Dependency direction:

```text
api -> application -> domain
infrastructure -> application/domain contracts
domain -> Python standard library only
```

The domain layer must not import FastAPI, Pydantic transport models, filesystem code, or UI concerns.

## Current persistence boundary

`buxianxian.infrastructure` owns the TASK-002 local-file adapter and concrete deterministic random
source. Its dependency direction is:

```text
JSON/local filesystem adapter -> domain state constructors
concrete deterministic RNG    -> domain RandomSource protocol
domain                        -X-> infrastructure
```

The `buxianxian-save` v1 snapshot contains a complete authoritative `GameState` plus an explicitly
identified and versioned random state. Loading dispatches on the save schema version. Events are not
persisted or replayed. See `ADR-004-versioned-snapshot-save-and-xorshift64star.md` for the format,
compatibility, and atomic-write decisions.

## Planned frontend boundaries

```text
frontend/src/
├─ api/             # HTTP client and transport types
├─ views/           # Page-level rendering
├─ components/      # Reusable visual components
└─ main.ts          # Composition entrypoint
```

The first frontend uses vanilla TypeScript. A UI framework may be considered only after measured complexity justifies it.

## Data categories

The project must distinguish:

1. **Author source** — editable notes and drafts.
2. **Runtime content** — validated, compiled, versioned content.
3. **Save state** — mutable player/world state.
4. **Read models** — server-produced data shaped for presentation.
5. **Logs** — diagnostic and transition records.

No category should silently serve as another.

## Deferred decisions

Do not decide these during bootstrap:

- final game-state model;
- replay-log and event-persistence format;
- concrete migration policy after a real older save exists;
- content schema;
- content compiler implementation;
- database choice;
- desktop wrapper;
- distribution format;
- LLM provider or prompting architecture;
- exact UI layout;
- story structure.

They require evidence from later milestones.
