# TASK-003 Persistent Game Session ExecPlan

## 1. Objective

Add the smallest headless application-layer coordinator that commits a domain transition only after
the corresponding state and deterministic RNG position have been saved successfully, with stale
revision protection and structured non-exceptional expected outcomes.

## 2. Scope

Included:

- initialization from explicit state/RNG or an existing valid TASK-002 repository;
- expected-revision validation;
- candidate RNG forking before domain execution;
- structured success, conflict, domain-rejection, and persistence-failure results;
- save-before-memory-commit ordering;
- application ports needed for structural repository/RNG substitution and expected persistence
  errors;
- focused tests for success, rollback, retry determinism, and dependency boundaries;
- TASK-003, architecture, backend README, and project-status updates.

Excluded:

- changes to domain state, commands, events, rejection semantics, or engine dispatch;
- save schema, RNG algorithm, random state format, migration, replay, and event logs;
- HTTP, frontend, multi-slot saves, autosave, databases, locks, distributed transactions, content,
  gameplay, narrative, Obsidian runtime, or LLM features.

## 3. Existing context

The repository is clean on `main` before TASK-003. P2 provides immutable `GameState`, typed commands,
atomic `Accepted`/`Rejected` results, and `DomainEngine`. TASK-002 provides mutable but snapshotable
`XorShift64StarRandom`, strict JSON v1 persistence, atomic file replacement, `LoadedSave`, and
structured `SaveError` values. All thirty existing backend tests and strict quality checks pass.

The existing RNG can already restore its position but has no application-facing clone operation.
The persistence error is currently defined in infrastructure, while the target dependency direction
requires infrastructure to implement application contracts rather than application importing the
file adapter.

## 4. Proposed design

### Application ports

`buxianxian.application.ports` defines:

- `TransactionalRandomSource`, extending the domain RNG protocol with `fork() -> Self`;
- generic structural loaded-save and repository protocols;
- `PersistenceError`, the expected save/load failure base caught by the application layer.

`SaveError` becomes a subclass of `PersistenceError` without changing its name, error codes, message,
or public infrastructure import. `XorShift64StarRandom.fork()` rebuilds an independent source from
its existing public snapshot. These are minimal backward-compatible extensions; the save format and
random algorithm are unchanged.

### Session and results

`PersistentGameSession[RandomT]` owns the official state and RNG. It can be created from explicit
values or by loading its repository. Its RNG inspection method returns a defensive fork so callers
cannot mutate the official source.

Submission returns one of four frozen result types:

- `CommitSucceeded(state, events)`;
- `RevisionConflict(expected_revision, actual_revision)`;
- `CommandRejected(state, reason)`;
- `PersistenceFailed(state, error)`.

The result type, not a string, controls caller branching. Contract violations and unexpected
programming errors continue to raise normally.

### Commit sequence

1. Compare the expected and current revisions. Return conflict immediately on mismatch.
2. Fork the official RNG.
3. Run `DomainEngine.transition` with the official immutable state and candidate RNG.
4. Discard the candidate on `Rejected` and return `CommandRejected`.
5. On `Accepted`, save the candidate state and candidate RNG.
6. Convert an expected `PersistenceError` into `PersistenceFailed` while retaining official memory.
7. Only after save success, replace official state/RNG and return `CommitSucceeded`.

No rollback-by-counting random draws, unit-of-work framework, or concurrency lock is introduced.

## 5. Milestones

### Milestone A: ports and candidate RNG

Affected files: `backend/src/buxianxian/application/ports.py`, infrastructure RNG and save error.

Expected behavior: the current concrete RNG and JSON repository satisfy the application contracts;
forks are independent and persistence errors remain backward compatible.

Validation: focused Ruff, Pyright, RNG and existing persistence tests.

Recovery: changes add methods/base types only and do not alter persisted bytes or domain behavior.

### Milestone B: persistent session and tests

Affected files: `backend/src/buxianxian/application/session.py`, package exports, and
`backend/tests/application/`.

Expected behavior: all four outcomes preserve the specified state/RNG/disk invariants, and retry
after failed persistence reproduces the same candidate.

Validation: focused application tests plus domain/application import-boundary checks.

Recovery: session is isolated below HTTP and above ports/domain; no existing entrypoint is changed.

### Milestone C: documentation and final verification

Affected files: TASK-003 records, architecture overview, backend README, project status, and this
plan.

Expected behavior: docs mark TASK-003 complete but P3 still in progress, with replay/API/UI deferred.

Validation: full backend checks, API/ frontend/scope scans, dependency check, Git diff review.

Recovery: documentation is declarative; tests use temporary directories only.

## 6. Progress log

- [x] 2026-07-15: Audited Git status, repository rules, P3 architecture/roadmap, all accepted ADRs,
  TASK-001/TASK-002 implementation records, source, tests, dependencies, and quality contract.
- [x] 2026-07-15: Reported the bounded design and the two minimal backward-compatible port changes.
- [x] 2026-07-15: Confirmed the pre-change backend baseline passes all checks and thirty tests.
- [x] 2026-07-15: Implemented application ports, RNG fork, and persistence-error base compatibility.
- [x] 2026-07-15: Implemented the session and all required behavioral/boundary tests.
- [x] 2026-07-15: Updated active architecture/status documentation.
- [x] 2026-07-15: Ran final backend checks and scope review.

## 7. Discoveries and deviations

- No repository TASK-003 record existed; the accepted user specification is recorded before code
  implementation.
- No new dependency, domain change, save-format change, or ADR is required.
- A candidate RNG can be implemented exactly from the existing public snapshot contract; no random
  draw counting or algorithm-specific rollback is needed.
- Pyright correctly required callers of the generic session classmethods to select the concrete RNG
  type explicitly. Tests and documentation use `PersistentGameSession[XorShift64StarRandom]`; no
  cast, `Any`, or weakened typing was introduced.
- The first application boundary test filename collided with the existing domain
  `test_boundaries.py` in pytest's non-package test layout. Renaming it to the unique
  `test_application_boundaries.py` fixed collection without changing behavior.
- One final API/frontend scope scan used an incorrect working-directory-relative frontend path. The
  scan was rerun from the repository root and passed.

## 8. Verification

Completed on 2026-07-15:

- Pre-change backend baseline: Ruff format, Ruff lint, Pyright strict, and all thirty existing tests
  passed.
- Focused application, domain, and infrastructure verification: Ruff and Pyright passed; thirty-nine
  tests passed after the boundary-test filename correction.
- Full `ruff format --check --no-cache .`: passed; twenty Python files were already formatted.
- Full `ruff check --no-cache .`: passed.
- Full `pyright`: passed with zero errors, warnings, or information messages.
- Full pytest without bytecode/cache artifacts: passed; nine application, nine domain, twenty-one
  infrastructure, and one API health test, forty total.
- API route inspection: only `/api/health` remains.
- Static boundary checks: application imports only standard library/application/domain; domain
  source is unchanged and existing domain purity tests pass.
- Dependency review: `backend/pyproject.toml` and `backend/uv.lock` are unchanged.
- Scope/artifact scans: no API/frontend session integration, replay/event log, formal gameplay,
  narrative system, save artifact, type suppression, `Any`, cast, or ignored error was added.
- `git diff --check`: passed.

## 9. Completion summary

TASK-003 is complete. The application layer now supports explicit and loaded session initialization,
stale-revision short-circuiting, candidate RNG execution, structured domain/persistence outcomes,
save-before-memory-commit ordering, complete official-memory rollback, old-save preservation, and
deterministic retry after persistence failure.

No domain contract, save schema, RNG algorithm/state format, dependency, API endpoint, frontend
behavior, replay/log system, concurrency framework, content system, gameplay system, or narrative
content shipped. P3 remains in progress. No new ADR was needed because the new ports and coordinator
are local, backward-compatible, and reversible application-layer choices.
