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

This is the target direction. P1 implements the engineering shell and connectivity smoke test. P2
adds the pure headless domain kernel. TASK-002 begins P3 with versioned snapshot persistence and a
recoverable deterministic random source. TASK-003 adds the headless persistent-session commit
boundary. TASK-004 begins a separate P4 slice with published read-only-document compilation only;
TASK-005 adds the first bounded P7 capability, authoritative elapsed-day time. TASK-006 adds
deterministic pre-session character creation and a complete player-bearing state.
TASK-007 connects those bounded capabilities through one single-save application runtime, FastAPI
DTOs, and a vanilla TypeScript client. Runtime content loading, replay, and all other gameplay remain
deferred.

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

The `buxianxian-save` v3 snapshot contains a complete authoritative `GameState` plus an explicitly
identified and versioned random state. Loading dispatches on the save schema version. Events are not
persisted or replayed. Experimental schemas v1 and v2 are explicitly unsupported rather than
fictionally migrated. See ADR-004 for snapshot/RNG/atomic-write decisions, ADR-006 for authoritative
time and compatibility policy, and ADR-007 for player state and schema v3.

## Current authoritative time boundary

The complete current formal state is:

```text
GameState
├─ revision: non-negative integer
├─ elapsed_days: non-negative integer since game start
└─ player: PlayerCharacter
   ├─ name: normalized Unicode string
   ├─ aptitudes: five integers, each 1–10, total 25
   └─ trait_ids: two distinct stable IDs in canonical order
```

`AdvanceTime(days)` is validated and handled only in the pure domain. Success creates an independent
state, increments revision once, and emits `TimeAdvanced(previous, current, elapsed)`. Rejection
returns the unchanged input state. Time does not consume RNG, but the application session still
forks and saves the candidate RNG with the candidate state before committing official memory.

Elapsed days are the authority. Years, months, hours, seasons, named eras, age, lifespan, schedules,
and world reactions are neither stored nor inferred in TASK-005.

## Current new-game boundary

Character creation exists before formal session state:

```text
caller RNG
    |
    v
fork candidate RNG -> deterministic aptitude/trait candidates
    |
    v
player confirmation -> complete GameState(revision=0, elapsed_days=0, player)
    |
    v
atomic save of state + post-generation RNG
    |
    v
PersistentGameSession
```

Invalid generation or confirmation exposes no `GameState`. Save failure exposes no session. The
caller RNG remains unchanged; the draft owns the consumed candidate position and can be retried
without reversing random draws. Trait definitions are supplied explicitly to the service and are
not loaded from TASK-004 content packages.

`AdvanceTime` is only a direct time-skip command. Future commands that perform gameplay and consume
time must update both in one domain transition. Effects and time must never be persisted as two
separate commands.

## Current application commit boundary

`buxianxian.application` owns the TASK-003 single-session coordinator and its structural ports.
Infrastructure implements those ports; the application session imports only application contracts,
the domain, and the Python standard library.

```text
expected revision check
        |
        v
fork official RNG -> candidate RNG
        |
        v
pure domain transition
        |
        +-- Rejected -> discard candidate
        |
        v
save candidate state + candidate RNG
        |
        +-- persistence failure -> retain official memory
        |
        v
replace official in-memory state + RNG
```

This is transaction-like only within one process and one session. It does not provide locks,
multi-process coordination, database transactions, event persistence, or replay. The application
session is reached through the TASK-007 single-game runtime rather than directly from routes.

## Current web runtime boundary

```text
vanilla TypeScript controller
        |
        | strict JSON DTOs and stable API errors
        v
FastAPI route adapter
        |
        v
SingleGameRuntime
  - one configured JsonFileSaveRepository
  - zero or one active PersistentGameSession
  - zero or one opaque server CharacterCreationDraft
  - NewGameService, prototype trait catalog, injected sources
        |
        v
application/domain authority
```

The default save is `runtime-data/buxianxian.save.json`; `BUXIANXIAN_SAVE_PATH` is the only current
configuration override. The path and RNG state never enter DTOs. Status distinguishes save-file
existence from loadability so a corrupt file cannot produce a Continue action or be silently
overwritten.

New draft creation invalidates the previous server draft. Confirmation submits IDs only and uses
the retained draft for validation. Validation and save failures retain it; success and successful
load clear it. Restart loses it by design.

OS entropy creates only the initial nonzero seed. The deterministic xorshift64star source continues
from the exact post-generation position stored in the save. See ADR-008.

## Current published-content boundary

TASK-004 treats author source, generated runtime content, and mutable player saves as independent
versioned data categories:

```text
authoring/published/documents/*.md
        |
        | restricted frontmatter + Markdown, explicit source root
        v
infrastructure content validator/compiler
        |
        | deterministic UTF-8 JSON, atomic replacement
        v
runtime-content/buxianxian-content.json
```

Only the explicit publication root is scanned. Private/draft siblings and an entire Obsidian Vault
are never implicit inputs. Package v1 contains sorted `read_only_document` entries with an explicit
stable ID, display title, and Markdown body; it contains no source paths or author metadata.

The compiler is an infrastructure/authoring tool and does not import the domain, application
session, save adapter, API, or frontend. No runtime layer loads the package yet. See
`ADR-005-versioned-published-read-only-content.md` for format and compatibility decisions.

## Current frontend boundaries

```text
frontend/src/
├─ api/             # HTTP client and transport types
├─ api/             # HTTP client, unknown-JSON validation, transport types
├─ app.ts           # pure boot/start/creation/overview controller
├─ main.ts          # DOM projection and event wiring
└─ style.css        # responsive prototype presentation
```

The frontend uses vanilla TypeScript. It may keep transient form selection and busy/error state but
replaces authoritative state only from API responses. A UI framework may be considered only after
measured complexity justifies it.

## Data categories

The project must distinguish:

1. **Author source** — editable notes and drafts.
2. **Runtime content** — validated, compiled, versioned content.
3. **Save state** — mutable player/world state.
4. **Read models** — server-produced data shaped for presentation.
5. **Logs** — diagnostic and transition records.

No category should silently serve as another.

## Deferred decisions

Decisions still deferred:

- additional player/world state beyond the current identity, aptitudes, trait IDs, and time;
- replay-log and event-persistence format;
- concrete migration tooling for released save versions;
- additional content schemas and cross-entry reference validation;
- runtime content loading and read-model integration;
- database choice;
- desktop wrapper;
- distribution format;
- LLM provider or prompting architecture;
- exact UI layout;
- story structure.

They require evidence from later milestones.
