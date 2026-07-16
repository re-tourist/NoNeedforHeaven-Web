# 不羡仙 backend

This package contains the local Python runtime. The API exposes only the TASK-000 engineering health check. The pure `buxianxian.domain` package implements the TASK-001 headless deterministic transition contract and is intentionally not exposed through HTTP yet.

`buxianxian.infrastructure` implements the `buxianxian-save` JSON v2 file adapter and the versioned
`xorshift64star` random source. Schema v2 stores revision and authoritative elapsed days; the
experimental counter-based schema v1 is explicitly unsupported. Persistence depends on the domain
contract; the domain does not depend on persistence, JSON, Pydantic, or the filesystem. Tests use
pytest temporary directories and do not create player saves in the repository.

`buxianxian.application` implements the TASK-003 headless persistent session. A caller supplies an expected state revision; the session evaluates a command with a forked candidate RNG, saves accepted candidate state/RNG, and changes its official in-memory values only after the save succeeds. Conflict, domain rejection, and persistence failure are distinct result types. Application ports keep the session independent of FastAPI and the concrete JSON adapter.

`buxianxian.infrastructure.content` implements the TASK-004 authoring compiler. It validates only an
explicit published Markdown directory, supports the restricted `read_only_document` v1 contract,
and atomically writes a deterministic `buxianxian-content` JSON v1 package. It has no domain,
application-session, save, FastAPI, frontend, Obsidian, or private-vault dependency.

TASK-005 defines the first formal mechanism: `GameState(revision, elapsed_days)` and a bounded
`AdvanceTime` command with a `TimeAdvanced` event. It does not define a calendar, age, lifespan,
daily simulation, or any other gameplay system. The session is not exposed through an API or UI.

See the repository root `README.md` for setup, development, and verification commands.
