# Project status

## Current phase

**First cultivation vertical slice complete; bounded P5/P6/P7 work remains in progress**

Status: `TASK-008-wheel-seeking-cultivation` completed and verified on 2026-07-17. A browser can
create or load a character, enter the cultivation page, seek the wheel for bounded days, atomically
persist time/insight/status/RNG, and resume after restart. The slice ends at suspected sighting; it
is not a complete cultivation system.

## Completed tasks

- `docs/tasks/TASK-000-bootstrap.md`
- `docs/tasks/TASK-001-domain-kernel.md`
- `docs/tasks/TASK-002-versioned-save.md`
- `docs/tasks/TASK-003-persistent-session.md`
- `docs/tasks/TASK-004-read-only-content-compiler.md`
- `docs/tasks/TASK-005-authoritative-time.md`
- `docs/tasks/TASK-006-new-game-character-creation.md`
- `docs/tasks/TASK-007-first-web-game-loop.md`
- `docs/tasks/TASK-008-wheel-seeking-cultivation.md`

## Implemented capabilities

- Locked backend/frontend engineering baseline, CI, formatting, linting, strict typing, tests, build,
  health endpoint, and local Vite proxy.
- Pure deterministic domain state/commands/events and transactional session commit semantics.
- Strict atomic `buxianxian-save` schema v4 with complete player/time/revision/cultivation and
  recoverable xorshift64star v1 state.
- Deterministic server-authoritative character drafts and complete new-game transaction.
- One transport-independent `SingleGameRuntime` owning the repository, session, current draft,
  prototype catalog, and injected sources.
- One environment-configurable local save, with separate existence/loadability status and explicit
  overwrite consent.
- FastAPI state, draft, new-game, load, and wait routes with strict DTOs and stable errors.
- Immutable `SeekWheel` state transition with centralized pre-alpha integer rules, two fixed RNG
  calls per actual day, early stopping at 100 insight, and one aggregate event.
- FastAPI cultivation route returning complete authoritative state and action summary.
- Vanilla TypeScript boot/start/creation/overview/cultivation state machine with responsive
  accessible controls, busy guards, recoverable errors, and revision-conflict refresh.
- Eight pre-alpha display-only prototype traits; stable IDs may be stored but have no effects.
- Independent deterministic `buxianxian-content` v1 read-only-document compiler, still not loaded at
  runtime.

## Verification status

- Backend Ruff format/lint and Pyright strict pass; 150 tests pass.
- API tests cover environment/default paths, status, drafts, anti-forgery, overwrite, save/load
  errors, waiting, cultivation, conflict, persistence failure, secrecy, and restart recovery.
- Application-runtime tests cover headless lifecycle, cultivation commit, and exact state/RNG
  restart recovery.
- All prior domain, session, persistence, RNG, content, boundary, and health tests remain green.
- Frontend Prettier, ESLint, TypeScript, 25 transport/controller Vitest tests, and production build
  pass.
- Published-content validation passes with zero entries.
- Isolated Edge acceptance covers create/load, cultivation navigation, one- and seven-day seeking,
  authoritative progress/time/revision refresh, backend restart, complete state recovery, and
  continued seeking.

## Explicitly deferred

- The three sighting trials, seeking completion, later cultivation stages, multiple methods,
  cultivation resources, injuries, and trait effects.
- Inventory/storage, resources, money, locations, travel, tasks, events, combat, NPCs,
  relationships, broader progression, world simulation, and narrative.
- Trait effects, balance, rarity, conflicts, conditions, and production trait content.
- Calendar projections, age, lifespan, months, seasons, and automatic daily reactions.
- Multiple save slots, delete/import/export, autosave policy, backups, accounts, or networking.
- Multi-thread/process coordination, file locking, multiple Uvicorn workers, and database storage.
- Persistent or cross-process drafts, draft resumption, and authentication.
- Runtime content loading/readers, cross-content references, replay/event logs, and released-save
  migration tooling.
- UI framework, router, desktop wrapper, formal art/audio, browser automation, and LLM integration.

## Next phase entry

The next task requires a separate approved specification. The current slice establishes the atomic
cultivation/time/RNG pattern but does not imply the three trials, later realms, inventory, location,
content reading, desktop packaging, or another gameplay system. A future task should select one
bounded capability and preserve the same domain/application/API authority boundaries.
