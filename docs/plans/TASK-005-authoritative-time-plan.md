# TASK-005 Authoritative Game Time ExecPlan

## 1. Objective

Replace the TASK-001 synthetic counter state with the first formal authoritative gameplay fact,
elapsed non-negative game days, while preserving immutable deterministic transitions, versioned
snapshot persistence, recoverable RNG state, and TASK-003 save-before-memory-commit semantics.

## 2. Scope

Included:

- `GameState(revision, elapsed_days)` as the complete current formal state;
- typed `AdvanceTime` command, `TimeAdvanced` event, bounded validation, and structured rejection;
- type-directed domain dispatch and immutable atomic transitions;
- `buxianxian-save` schema v2 with strict `revision` and `elapsed_days` state;
- explicit rejection of experimental counter-based schema v1 without a fictional migration;
- updated domain, persistence, and application-session tests;
- ADR-006 and active architecture/status/developer documentation updates.

Excluded:

- any calendar projection, age, lifespan, action point, schedule, world update, or NPC behavior;
- cultivation, character, inventory, location, travel, task, event-pool, or other gameplay systems;
- API, frontend, save-slot, content integration, narrative, Obsidian runtime, or LLM work;
- changes to RNG algorithm/state format, atomic-write strategy, or session transaction ordering.

## 3. Existing context

The working tree contains completed but uncommitted TASK-004 content-compiler changes on top of
commit `53a5e69`. Those changes are preserved and are outside the TASK-005 production boundary.

The current domain has one frozen `GameState(revision, counter)`, two counter commands, one counter
event, three counter rejection reasons, and a type-directed `DomainEngine`. The save adapter strictly
loads/writes schema v1 with `revision` and `counter`; its version dispatch already rejects unknown
versions. The application session is state-shape agnostic and already forks RNG, transitions,
saves, and commits in the required order.

All pre-change backend checks pass with sixty-five tests. The content compiler, API, frontend, RNG
algorithm, dependency manifests, and author source require no TASK-005 production changes.

## 4. Proposed design

### Formal state and numeric invariants

`GameState` remains a frozen standard-library dataclass with exactly:

```text
revision: int
elapsed_days: int
```

Both fields require exact integers rather than `bool`. Revision and elapsed days are non-negative.
Elapsed days may not exceed `MAX_ELAPSED_DAYS = 2**63 - 1`, a portable storage/safety ceiling. No
calendar semantics are inferred from the stored count.

### Command, event, and rejection

`AdvanceTime(days)` expresses intent. The handler requires an exact positive integer, caps one
submission at `MAX_ADVANCE_DAYS = 1_000_000`, and rejects a transition that would exceed the total
ceiling. The cap prevents accidental pathological commands while remaining independent of any
year/month definition.

Accepted output creates a distinct `GameState(revision + 1, elapsed_days + days)` and one
`TimeAdvanced(previous_elapsed_days, current_elapsed_days, days_elapsed)` event. Expected failures
return the original state with either `INVALID_DAY_COUNT` or `DAY_COUNT_OUT_OF_RANGE` and no event.
The time handler never requests random input.

The counter field, commands, event, and counter-specific rejection reasons are removed rather than
retained as misleading formal gameplay contracts. RNG determinism remains covered by its concrete
known-vector, snapshot, restore, and fork tests.

### Save schema v2 and compatibility

The envelope identity remains `buxianxian-save`; the root schema becomes 2:

```json
{
  "format": "buxianxian-save",
  "schema_version": 2,
  "state": {"elapsed_days": 0, "revision": 0},
  "random": {
    "algorithm": "xorshift64star",
    "version": 1,
    "state": "0123456789abcdef"
  }
}
```

The strict v2 loader reconstructs the formal state. No v1 loader or counter-to-time assumption is
added: experimental v1 saves are explicitly unsupported. ADR-006 records that save compatibility
is not promised before the first externally playable version; after that point incompatible state
changes require an explicit migration/compatibility decision.

ADR-004 continues to govern snapshot authority, RNG compatibility, JSON safety, and atomic
replacement. ADR-006 supersedes only its current state-shape/schema-v1 statement.

### Application session

No session implementation change is expected. Tests submit `AdvanceTime` and prove successful
memory/disk agreement, revision conflict short-circuiting, rejected-command stability, save-failure
rollback, old-save preservation, unchanged official RNG state, and deterministic retry.

## 5. Milestones

### Milestone A: formal domain time

Affected files: domain model/engine/exports and domain tests.

Expected behavior: day zero is representable; legal time advances immutably; all invalid numeric
cases are structured rejections; no counter contract remains.

Validation: focused Ruff, Pyright, and domain tests.

Recovery: the changes are confined to the still-pre-alpha formal state contract; no persistence is
written until Milestone B updates the codec consistently.

### Milestone B: save v2 and transactional session coverage

Affected files: save repository, persistence tests, and session tests.

Expected behavior: time/RNG round-trip under schema v2; v1 is rejected; session success/failure/
conflict preserves existing transaction semantics with time.

Validation: focused infrastructure/application tests plus complete RNG tests.

Recovery: atomic-write code and RNG format remain unchanged; failed writes retain the prior v2 save.

### Milestone C: decisions, active docs, and final audit

Affected files: ADR-004 status note, ADR-006, architecture/status/README/backend README, TASK-005
record, and this plan.

Expected behavior: active docs describe only the formal time state and v2 save while preserving
historical TASK records.

Validation: full backend quality suite; counter/code scan; content/API/frontend/dependency diff
review; generated-artifact and Git diff checks.

Recovery: documentation records the shipped boundary; no unrelated layer is changed.

## 6. Progress log

- [x] 2026-07-16: Audited repository state, instructions, architecture, roadmap, accepted ADRs,
  TASK-001 through TASK-004 records, domain/save/session source, and all related tests.
- [x] 2026-07-16: Confirmed the pre-change backend baseline passes all checks and sixty-five tests.
- [x] 2026-07-16: Reported the formal state, bounded time command, schema-v2, no-migration, and
  preserved-session plan before editing production code.
- [x] 2026-07-16: Implemented the formal time domain contract and fourteen focused behavior tests.
- [x] 2026-07-16: Updated save schema v2 and transactional-session tests without changing the
  session coordinator or RNG implementation.
- [x] 2026-07-16: Recorded ADR-006, partially superseded ADR-004, and updated active documentation.
- [x] 2026-07-16: Completed final backend verification and scope audit.

## 7. Discoveries and deviations

- TASK-004 is complete but uncommitted. Its files are treated as existing user work and will not be
  reverted, reformatted outside normal full checks, or folded conceptually into TASK-005.
- The existing version-dispatch design supports a clean v2 cut without inventing migration
  infrastructure. Retaining schema version 1 with a different state shape was rejected because it
  would silently reinterpret persisted data.
- The application coordinator is already independent of concrete state fields and requires test
  updates rather than a production redesign.
- Equality with a union-typed session result did not narrow its static type for later attribute
  access. An explicit `isinstance(CommitSucceeded)` assertion preserves strict typing without a
  cast, ignored diagnostic, or production change.
- The final suite grew from sixty-five to seventy-six tests. Existing content, RNG, boundary, and
  API health tests all continue to pass.

## 8. Verification

Pre-change baseline from `backend/`:

```text
.venv/Scripts/ruff format --check --no-cache .  -> 29 files already formatted
.venv/Scripts/ruff check --no-cache .           -> passed
.venv/Scripts/pyright                           -> 0 errors, 0 warnings
.venv/Scripts/python -m pytest -p no:cacheprovider
  -> 65 passed
```

Focused verification:

```text
.venv/Scripts/python -m pytest -p no:cacheprovider tests/domain
  -> 16 passed, including 14 time tests and 2 boundary tests
.venv/Scripts/python -m pytest -p no:cacheprovider \
  tests/domain tests/infrastructure tests/application
  -> 50 passed
.venv/Scripts/pyright [changed domain/save/tests paths]
  -> 0 errors, 0 warnings
.venv/Scripts/ruff check --no-cache [changed domain/save/tests paths]
  -> passed
```

Final backend verification:

```text
.venv/Scripts/ruff format --check --no-cache .  -> 29 files already formatted
.venv/Scripts/ruff check --no-cache .           -> passed
.venv/Scripts/pyright                           -> 0 errors, 0 warnings
.venv/Scripts/python -m pytest -p no:cacheprovider
  -> 76 passed
.venv/Scripts/python -m buxianxian.infrastructure.content validate
  -> Validated 0 content entries
```

Scope review:

- `git diff --check` passed.
- Current production source contains no `counter` field, command, event, or rejection reason.
- The only test counter payloads are explicit invalid schema-v1 fixtures.
- Session coordinator, application ports, RNG implementation, API, frontend, and dependency
  manifests have no TASK-005 diff.
- All twenty-five TASK-004 content tests pass and the content compiler remains isolated.
- No runtime content package, player save, formal narrative, cache, type suppression, `Any`, unsafe
  cast, database, calendar framework, or new dependency was added.

## 9. Completion summary

TASK-005 completed on 2026-07-16. The authoritative state now contains revision and elapsed days;
bounded typed commands advance time immutably and emit complete facts; save schema v2 persists and
restores formal time plus the existing deterministic RNG; and the unchanged application session
preserves atomic commit/rollback semantics.

Experimental schema v1 is explicitly unsupported without migration. No calendar, daily reaction,
character, cultivation, resource, API, frontend, content integration, or narrative capability was
implemented. P7 remains in progress.
