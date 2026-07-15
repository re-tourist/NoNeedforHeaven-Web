# Project status

## Current phase

**P3 — Persistence, replay, and versioning in progress**

Status: `TASK-003-persistent-session` completed and locally verified on 2026-07-15. Snapshot/RNG
persistence and the single-session atomic commit boundary are complete; P3 as a whole is not.

## Completed tasks

- `docs/tasks/TASK-000-bootstrap.md`
- `docs/tasks/TASK-001-domain-kernel.md`
- `docs/tasks/TASK-002-versioned-save.md`
- `docs/tasks/TASK-003-persistent-session.md`

## Implemented capabilities

- The complete P1 engineering, locked-dependency, quality-check, CI, health, and connectivity
  baseline.
- The P2 pure deterministic domain kernel with immutable synthetic state, typed commands,
  accepted/rejected results, events, and injected randomness.
- The TASK-002 strict `buxianxian-save` JSON v1 snapshot, version dispatch, xorshift64star v1 state,
  structured persistence errors, and atomic same-directory file replacement.
- Application ports for a forkable deterministic RNG, structurally substitutable snapshot
  repository, and expected persistence errors.
- A headless `PersistentGameSession` initialized from explicit contracts or a valid save.
- Expected-revision protection before domain execution, RNG use, or save I/O.
- Candidate RNG execution with save-before-memory-commit ordering.
- Structured `CommitSucceeded`, `RevisionConflict`, `CommandRejected`, and `PersistenceFailed`
  outcomes.
- Complete rollback of official in-memory state/RNG on domain rejection or save failure, plus
  deterministic retry from the same candidate inputs.

The current `revision`, `counter`, commands, and event remain neutral contract fixtures. They are not
formal resources, actions, progression, or gameplay systems.

## Verification status

- All backend formatting, linting, Pyright strict type checks, and tests pass.
- Nine application tests prove explicit and loaded initialization, successful memory/disk commit,
  revision conflict short-circuiting, rejected-command RNG rollback, persistence-failure rollback,
  old-save preservation, retry determinism, and application dependency boundaries.
- The complete backend suite passes with forty tests: nine application, nine domain, twenty-one
  infrastructure, and the unchanged health contract.
- The application package imports only standard library, application contracts, and domain code.
- Existing domain boundary tests still prohibit application, infrastructure, filesystem, FastAPI,
  and other non-domain dependencies; TASK-003 did not modify the domain package.
- The API still exposes only `GET /api/health`; frontend behavior is unchanged.
- No production or development dependency was added, and no save artifact is stored in the
  repository.

## Explicitly deferred

- Event persistence, transition logs, replay, and event sourcing.
- Real legacy save migrations and compatibility with a future final state model.
- HTTP new/load/read/command endpoints and transport error schemas.
- Frontend command, save, load, conflict, or persistence-failure behavior.
- Multiple sessions, slots, backups, autosave, locks, file-level compare-and-swap, multi-process
  coordination, database transactions, and distributed consistency.
- Final game-state models and all formal gameplay systems.
- Content schemas, compilation, authoring tools, narrative content, Obsidian runtime integration,
  and LLM integration.

## Next phase entry

The next task requires a separate approved specification. It must not infer replay, HTTP, frontend,
content, or gameplay behavior from TASK-003. P3 remains in progress until its remaining explicitly
scoped requirements are completed or the roadmap is revised by an accepted decision.
