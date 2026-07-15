# TASK-002 Versioned Save and Recoverable Random State ExecPlan

## 1. Objective

Add a versioned, validated, atomic JSON persistence adapter and a stable serializable random-source
implementation so the current headless state and random sequence can survive a process restart.

## 2. Scope

Included:

- JSON save envelope v1 with product, schema, state, random algorithm, algorithm version, and
  explicit random state;
- a deterministic `xorshift64*` v1 implementation of the TASK-001 `RandomSource` protocol;
- strict standard-library decoding with explicit version dispatch;
- structured persistence error codes;
- same-directory temporary writes, file flush/fsync, and atomic replacement;
- tests for round-trip, deterministic continuation, malformed and unsupported data, atomic failure,
  and domain boundaries;
- a persistence/RNG ADR and task, architecture, status, and developer documentation.

Excluded:

- changes to TASK-001 state, command, event, result, or engine semantics;
- event sourcing, transition logs, replay, real legacy fixtures, or implemented migrations;
- save slots, application services, HTTP endpoints, frontend behavior, databases, cloud saves,
  content systems, gameplay systems, or narrative content.

## 3. Existing context

P1 and P2 are complete. The Python 3.14 backend has strict Ruff, Pyright, and pytest checks. The
domain consists of frozen minimal state, typed commands, atomic accepted/rejected transitions, and
an injected `RandomSource` protocol. Static tests already enforce that `buxianxian.domain` imports
only the standard library and domain modules and has no filesystem dependency.

The target architecture explicitly reserves `buxianxian.infrastructure` for filesystem and storage
adapters. Accepted ADRs require Python authority, frontend projection, and system-before-narrative
discipline. The current API exposes only `/api/health`. The supplied workspace has no Git metadata,
so final review will use inventories and targeted scans rather than `git diff`.

The pre-change baseline passes Ruff format, Ruff lint, Pyright strict, and all ten existing tests.

## 4. Proposed design

### Save envelope and version boundary

The UTF-8 JSON v1 envelope contains exactly four root fields: `format`, `schema_version`, `state`,
and `random`. State contains `revision` and `counter`. Random data contains `algorithm`, `version`,
and `state`. The loader reads the identity and schema first, then selects a version-specific loader
from an explicit dispatch table. Only schema v1 exists; future versions may add a loader that
migrates an older representation into the current in-memory contracts.

Strict standard-library validation avoids coercion and an additional schema-framework coupling.
Booleans are not accepted as integers. Unknown or missing fields are invalid for v1, so compatible
shape changes require an intentional schema version decision.

### Random source

`XorShift64StarRandom` lives in infrastructure and implements the existing domain protocol without
changing it. Version 1 uses the published xorshift64* transition and multiplier with unsigned
64-bit masking. A nonzero 64-bit internal state is serialized as exactly 16 lowercase hexadecimal
digits. Inclusive bounded integers use rejection sampling to avoid modulo bias.

This algorithm is small, deterministic, independently specifiable, and easier to preserve than
Python runtime internals. It is not cryptographically secure and is not presented as a final
simulation-quality choice. PCG was considered but would add stream and seeding state not needed by
this persistence contract. Python `random` and pickle are rejected because their object/runtime
formats are not the project's versioned public contract.

### Repository and errors

`JsonFileSaveRepository` owns one explicit path and exposes `save(state, random_source)` and
`load() -> LoadedSave`. It is an infrastructure adapter, not a domain dependency or application
service. Expected load/save failures raise `SaveError` containing a stable `SaveErrorCode`.

The error taxonomy distinguishes missing files, malformed JSON, wrong product, unsupported save
schema, invalid envelope/domain data, unsupported random algorithm, unsupported random-state
version, invalid random state, and general I/O failure.

### Atomic write

The adapter serializes completely before touching the target, creates a temporary file in the same
directory, writes and flushes it, calls `fsync`, closes it, and calls `os.replace`. Same-directory
replacement avoids cross-filesystem moves and is the simplest common Windows/macOS/Linux strategy.
If writing or replacement fails, the temporary file is removed on a best-effort basis and the old
target is left untouched.

## 5. Milestones

### Milestone A: contracts and deterministic RNG

Affected files: `backend/src/buxianxian/infrastructure/__init__.py` and `random_source.py`.

Expected behavior: a same-seed source produces a frozen known sequence, implements the domain
protocol, and can export/restore a versioned nonopaque state.

Validation: focused Ruff, Pyright, and random-source tests.

Recovery: new infrastructure files are isolated and do not change domain code.

### Milestone B: save codec and filesystem adapter

Affected files: `backend/src/buxianxian/infrastructure/save_repository.py`.

Expected behavior: v1 saves round-trip state and RNG, reject invalid formats with structured codes,
and preserve an old valid save on replacement failure.

Validation: focused persistence tests using pytest temporary directories.

Recovery: all writes are confined to test temporary directories; replacement is atomic.

### Milestone C: decision records and final verification

Affected files: `docs/adr/ADR-004-versioned-snapshot-save-and-xorshift64star.md`, architecture and
status docs, READMEs, TASK-002 records, and this plan.

Expected behavior: documentation matches the shipped format and marks P3 as only partially
complete. Deferred replay, APIs, UI, and gameplay remain explicit.

Validation: complete backend checks, API and frontend boundary scans, dependency review, no-save
artifact inventory, and documentation status scan.

Recovery: documentation changes are declarative and no real save is created in the repository.

## 6. Progress log

- [x] 2026-07-15: Audited repository rules, architecture, roadmap, ADRs, TASK-001 implementation,
  tests, dependencies, CI, and definition of done.
- [x] 2026-07-15: Reported the bounded design and alternatives before editing.
- [x] 2026-07-15: Confirmed the pre-change backend baseline passes all checks.
- [x] 2026-07-15: Implemented and verified the concrete deterministic random source.
- [x] 2026-07-15: Implemented and verified the save codec, error model, and atomic file adapter.
- [x] 2026-07-15: Added ADR-004 and updated architecture, project status, and developer documentation.
- [x] 2026-07-15: Ran all backend quality gates and final scope review.

## 7. Discoveries and deviations

- No repository task file existed for TASK-002; the accepted user specification is recorded in
  `docs/tasks/TASK-002-versioned-save.md` before implementation.
- No new production dependency is expected; explicit standard-library validation is sufficient.
- P3 roadmap also names replay support, but TASK-002 explicitly limits this slice to snapshot and
  RNG persistence, so P3 must remain in progress after completion.
- The first strict Pyright pass identified `Unknown` members from `json.loads`. The decoder now uses
  an explicit recursive `JsonValue` alias; no `Any`, cast, suppression, or Pydantic coupling was
  introduced.
- Self-review found that invalid UTF-8 raises before JSON parsing. It is now mapped to the same
  structured corruption category as malformed JSON and has a focused regression test.

## 8. Verification

Completed on 2026-07-15:

- Pre-change full backend baseline: Ruff format, Ruff lint, Pyright strict, and ten tests passed.
- Initial focused infrastructure plus unchanged domain verification: Ruff and Pyright passed and
  twenty-eight tests passed. The later invalid UTF-8 regression case is included in the final full
  suite below.
- Full `ruff format --check .`: passed; fifteen Python files were already formatted.
- Full `ruff check .`: passed.
- Full `pyright`: passed with zero errors, warnings, or information messages.
- Full `pytest`: passed; twenty infrastructure tests, nine domain tests, and one health contract,
  thirty total.
- API route inspection: only `/api/health` remains under `/api/`.
- Dependency review: `backend/pyproject.toml` is unchanged and the lock still contains 26 packages.
- Scope scans: no infrastructure import from API/frontend, no persistence import in domain, no
  direct Python random state, pickle, replay implementation, type suppression, or shortcut.
- Artifact scan: no save or temporary file was left outside pytest temporary directories.

Git diff review remains unavailable because the supplied workspace has no Git metadata. Review used
explicit source inventories, dependency checks, import scans, API route inspection, and tests.

## 9. Completion summary

TASK-002 is complete. The repository now has a strict `buxianxian-save` JSON v1 snapshot, an explicit
version-loader boundary, recoverable xorshift64star v1 state, structured persistence failures, and
same-directory atomic replacement that preserves the old save on simulated replacement failure.

No domain contract, dependency, application service, API endpoint, frontend behavior, real player
save, database, replay/event-log system, migration fixture, content system, gameplay system, or
narrative content shipped. P3 remains in progress and requires separately scoped follow-up work.
