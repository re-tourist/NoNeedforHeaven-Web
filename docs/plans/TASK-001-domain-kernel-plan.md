# TASK-001 Headless Deterministic Domain Kernel ExecPlan

## 1. Objective

Create a pure, typed, deterministic Python state-transition kernel that accepts or rejects neutral synthetic commands atomically while preserving the Python authority boundary established by the accepted ADRs.

## 2. Scope

Included:

- immutable minimal state with revision and synthetic counter values;
- explicit typed commands and domain events;
- accepted and rejected result contracts;
- stable structured rejection reasons;
- an injected deterministic random-source boundary;
- minimal type-directed dispatch and focused command handlers;
- unit tests for success, rejection, immutability, events, dispatch, and deterministic randomness;
- task, plan, and project-status documentation.

Excluded:

- all formal gameplay systems, narrative concepts, content schemas, persistence, replay, migrations, application services, API changes, frontend changes, databases, authoring integration, and LLM behavior;
- a final RNG algorithm or RNG-state serialization;
- plugin discovery, reflective registration frameworks, dependency-injection containers, generic condition/effect languages, and event sourcing.

## 3. Existing context

TASK-000 is complete. The backend is a strict Python 3.14 project under `backend/`, currently containing only the `buxianxian.api` health endpoint and one API contract test. Ruff, Pyright strict mode, and pytest are already configured. No domain package exists and no production dependency is needed for TASK-001.

Architecture and ADRs require Python authority, a standard-library-only domain, frontend projection, system-before-narrative discipline, deterministic random boundaries, and no premature later-milestone code. The supplied directory still has no Git metadata, so review will use explicit file inventories and scope scans rather than `git diff`.

## 4. Proposed design

### Public contracts

Frozen, slotted dataclasses represent `GameState`, commands, events, `Accepted`, and `Rejected`. A `StrEnum` provides stable machine-readable rejection reasons. Public union aliases make the supported Command, DomainEvent, and TransitionResult sets explicit and statically exhaustible.

`GameState` validates its own non-negative invariants at construction. Command semantic validation remains in handlers so invalid requests use `Rejected` rather than exceptions as normal control flow.

### Dispatch and handlers

`DomainEngine.transition(state, command, random_source)` is the public execution boundary. A small exhaustive type match dispatches each supported command to a separate handler function. This avoids a business-logic megafunction while also avoiding dynamic registries, reflection, unsafe casts, and a plugin system.

Exact consumption validates the requested amount and available counter before constructing a new state. Random consumption validates its requested inclusive range, asks the injected source for the amount, and reuses the same atomic consumption helper.

### Random boundary

`RandomSource` is a standard-library `Protocol` with one inclusive integer method. Tests provide a small controlled implementation. Production code does not select an algorithm, import `random`, or serialize RNG state in P2.

### Alternatives considered

- Mutable dictionaries were rejected because they weaken type guarantees and make mutation/atomicity harder to prove.
- Pydantic was rejected inside the domain because it is a transport dependency and frozen dataclasses are sufficient.
- `singledispatch` or a handler registry was rejected at this scale because explicit exhaustive dispatch is easier for Pyright to verify and does not introduce registration mechanics.
- Event sourcing was rejected because the accepted state snapshot remains authoritative and events are explanatory facts only.

## 5. Milestones

### Milestone A: domain contracts

Affected files: `backend/src/buxianxian/domain/__init__.py`, `model.py`, and `random_source.py`.

Expected behavior: public state, command, event, result, rejection, and RNG contracts import without FastAPI or infrastructure.

Validation: Ruff and Pyright plus focused construction/equality tests.

Recovery: contracts are isolated in a new domain package; no existing API code is changed.

### Milestone B: engine and handlers

Affected file: `backend/src/buxianxian/domain/engine.py`.

Expected behavior: supported commands dispatch by type; valid transitions atomically return an independent revision-incremented state and event; invalid requests return the original state and reason.

Validation: focused domain unit tests for exact and random commands.

Recovery: handlers are pure functions with no side effects or external resources.

### Milestone C: verification and status

Affected files: `backend/tests/domain/`, `README.md`, `backend/README.md`, `docs/architecture/overview.md`, `docs/project-status.md`, and this plan.

Expected behavior: all ten TASK-001 completion claims are evidenced by tests or explicit scope scans, and P3+ work remains absent.

Validation: backend format, lint, strict type, focused tests, full tests, dependency/import scans, and final file inventory.

Recovery: documentation updates are declarative; no persisted data or migration exists.

## 6. Progress log

- [x] 2026-07-15: Read repository rules, status, architecture, roadmap, accepted ADRs, quality contract, TASK-000 plan, actual code, and tests.
- [x] 2026-07-15: Confirmed the existing backend baseline passes format, lint, strict type, and test checks.
- [x] 2026-07-15: Reported the intended TASK-001 scope, public design, and deferred boundaries before editing.
- [x] 2026-07-15: Implemented domain contracts and deterministic random boundary.
- [x] 2026-07-15: Implemented type-directed dispatch and atomic handlers.
- [x] 2026-07-15: Added focused contract, determinism, broken-source, and import-boundary tests.
- [x] 2026-07-15: Ran all backend checks and scope review.
- [x] 2026-07-15: Updated public documentation and project status to match P2 completion.

## 7. Discoveries and deviations

- No repository task file existed for TASK-001; the user-supplied accepted specification is recorded in `docs/tasks/TASK-001-domain-kernel.md` before implementation.
- No production or development dependency addition is required.
- The initial focused Pyright run required one explicit default branch in the AST-based import-boundary test; no production contract changed.
- TASK-000 documentation described the domain as absent. The root/backend READMEs and architecture status sentence were minimally updated so documentation matches the P2 repository state.

## 8. Verification

Completed on 2026-07-15:

- Baseline before editing: Ruff format, Ruff lint, Pyright strict, and the existing one-test pytest suite passed.
- Focused `ruff format --check`, `ruff check`, Pyright, and `pytest tests/domain`: passed after formatting one test helper and adding its explicit AST match default; nine domain tests passed.
- Full `ruff format --check .`: passed; ten Python files were formatted.
- Full `ruff check .`: passed.
- Full `pyright`: passed with zero errors, warnings, or information messages.
- Full `pytest`: passed; nine domain tests plus the unchanged API health test, ten total.
- API route inspection: only `/api/health` remains under `/api/`.
- Dependency review: `backend/pyproject.toml` and the 26-package lock remain unchanged.
- Static import-boundary tests: domain imports only standard library or `buxianxian.domain` modules and imports no filesystem modules.
- Scope review: no API/frontend domain integration and no persistence, content, gameplay, authoring, database, LLM, or narrative implementation was added.

Git diff review remains unavailable because the supplied directory has no Git metadata; review used a complete non-generated file inventory and targeted source scans.

## 9. Completion summary

TASK-001 is complete. The public kernel now supports immutable minimal state, explicit exact and controlled-random commands, atomic accepted transitions with events, structured expected rejection, exhaustive type-directed dispatch, and a deterministic random-source protocol.

No dependency, API endpoint, frontend behavior, persistence, content system, formal gameplay system, or narrative content shipped. RNG algorithm selection, RNG-state persistence, save/replay/version formats, and application/API integration remain intentionally unresolved for later separately approved milestones.
