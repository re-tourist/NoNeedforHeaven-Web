# 不羡仙 backend

This package contains the local authoritative Python runtime. The API retains the TASK-000 health
check and now exposes the bounded TASK-007 single-save game routes. Transport DTOs project existing
application/domain contracts; routes do not reimplement rules.

`buxianxian.infrastructure` implements the `buxianxian-save` JSON v3 file adapter and the versioned
`xorshift64star` random source. Schema v3 stores the complete player, revision, authoritative elapsed
days, and RNG state; experimental schemas v1/v2 are explicitly unsupported. Persistence depends on
the domain contract; the domain does not depend on persistence, JSON, Pydantic, or the filesystem.
Tests use pytest temporary directories and do not create player saves in the repository.

`buxianxian.application` implements the TASK-003 headless persistent session. A caller supplies an expected state revision; the session evaluates a command with a forked candidate RNG, saves accepted candidate state/RNG, and changes its official in-memory values only after the save succeeds. Conflict, domain rejection, and persistence failure are distinct result types. Application ports keep the session independent of FastAPI and the concrete JSON adapter.

TASK-006 adds `NewGameService` before that session boundary. It generates a private character-creation
draft on a forked RNG, revalidates the selected aptitude/name/trait IDs, saves the complete initial
state plus post-generation RNG, and creates a session only after save success. No formal trait
catalog or trait effects ship in production code.

TASK-007 adds `SingleGameRuntime`, which owns the one repository, active session, current opaque
draft, new-game service, prototype trait catalog, and injected production sources. FastAPI composes
this runtime and maps its typed results to stable DTO/error contracts. The default ignored save is
`../runtime-data/buxianxian.save.json`; set `BUXIANXIAN_SAVE_PATH` to override it. Drafts are memory
only and disappear on restart. Do not run multiple workers against the same save.

`buxianxian.infrastructure.content` implements the TASK-004 authoring compiler. It validates only an
explicit published Markdown directory, supports the restricted `read_only_document` v1 contract,
and atomically writes a deterministic `buxianxian-content` JSON v1 package. It has no domain,
application-session, save, FastAPI, frontend, Obsidian, or private-vault dependency.

TASK-005 defines the first formal mechanism: a bounded `AdvanceTime` command with a `TimeAdvanced`
event. TASK-006 extends the complete formal state to `GameState(revision, elapsed_days, player)`
without changing the time command. It does not define a calendar, age, lifespan, daily simulation,
or any other gameplay system. The session and new-game service are not exposed through an API or UI.

See the repository root `README.md` for setup, development, and verification commands.
