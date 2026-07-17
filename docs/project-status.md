# Project status

## Current phase

**First operable web vertical slice complete; bounded P5/P6/P7 work remains in progress**

Status: `TASK-007-first-web-game-loop` completed and verified on 2026-07-17. A browser can now create
a character, atomically save a new game, reload it after process restart, inspect player/time state,
and submit revision-protected waiting. This is not a broader gameplay prototype.

## Completed tasks

- `docs/tasks/TASK-000-bootstrap.md`
- `docs/tasks/TASK-001-domain-kernel.md`
- `docs/tasks/TASK-002-versioned-save.md`
- `docs/tasks/TASK-003-persistent-session.md`
- `docs/tasks/TASK-004-read-only-content-compiler.md`
- `docs/tasks/TASK-005-authoritative-time.md`
- `docs/tasks/TASK-006-new-game-character-creation.md`
- `docs/tasks/TASK-007-first-web-game-loop.md`

## Implemented capabilities

- Locked backend/frontend engineering baseline, CI, formatting, linting, strict typing, tests, build,
  health endpoint, and local Vite proxy.
- Pure deterministic domain state/commands/events and transactional session commit semantics.
- Strict atomic `buxianxian-save` schema v3 with complete player/time/revision and recoverable
  xorshift64star v1 state.
- Deterministic server-authoritative character drafts and complete new-game transaction.
- One transport-independent `SingleGameRuntime` owning the repository, session, current draft,
  prototype catalog, and injected sources.
- One environment-configurable local save, with separate existence/loadability status and explicit
  overwrite consent.
- FastAPI state, draft, new-game, load, and wait routes with strict DTOs and stable errors.
- Vanilla TypeScript boot/start/creation/overview state machine with responsive accessible controls,
  busy guards, recoverable errors, explicit overwrite UI, and revision-conflict refresh.
- Eight pre-alpha display-only prototype traits; stable IDs may be stored but have no effects.
- Independent deterministic `buxianxian-content` v1 read-only-document compiler, still not loaded at
  runtime.

## Verification status

- Backend Ruff format/lint and Pyright strict pass; 125 tests pass.
- Fourteen API/config tests cover environment/default paths, status, drafts, anti-forgery,
  overwrite, save/load errors, waiting, conflict, persistence failure, secrecy, and restart recovery.
- Eight application-runtime tests cover headless lifecycle and exact state/RNG restart recovery.
- All prior domain, session, persistence, RNG, content, boundary, and health tests remain green.
- Frontend Prettier, ESLint, TypeScript, 18 transport/controller Vitest tests, and production build
  pass.
- Published-content validation passes with zero entries.
- Isolated Edge acceptance passes with fresh profiles: create, wait three days, restart the backend,
  continue from disk, and recover the same player, aptitudes, traits, elapsed days, and revision.

## Explicitly deferred

- Cultivation, inventory/storage, resources, money, locations, travel, tasks, events, combat, NPCs,
  relationships, progression, world simulation, and narrative.
- Trait effects, balance, rarity, conflicts, conditions, and production trait content.
- Calendar projections, age, lifespan, months, seasons, and automatic daily reactions.
- Multiple save slots, delete/import/export, autosave policy, backups, accounts, or networking.
- Multi-thread/process coordination, file locking, multiple Uvicorn workers, and database storage.
- Persistent or cross-process drafts, draft resumption, and authentication.
- Runtime content loading/readers, cross-content references, replay/event logs, and released-save
  migration tooling.
- UI framework, router, desktop wrapper, formal art/audio, browser automation, and LLM integration.

## Next phase entry

The next task requires a separate approved specification. The current vertical slice is sufficient
to validate API/client boundaries; it does not imply cultivation, inventory, location, content
reading, desktop packaging, or another gameplay system. A future task should select one bounded
capability or harden the local runtime based on explicit product priority.
