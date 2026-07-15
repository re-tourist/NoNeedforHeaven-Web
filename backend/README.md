# 不羡仙 backend

This package contains the local Python runtime. The API exposes only the TASK-000 engineering health check. The pure `buxianxian.domain` package implements the TASK-001 headless deterministic transition contract and is intentionally not exposed through HTTP yet.

`buxianxian.infrastructure` implements the TASK-002 `buxianxian-save` JSON v1 file adapter and the versioned `xorshift64star` random source. Persistence depends on the domain contract; the domain does not depend on persistence, JSON, Pydantic, or the filesystem. Tests use pytest temporary directories and do not create player saves in the repository.

`buxianxian.application` implements the TASK-003 headless persistent session. A caller supplies an expected state revision; the session evaluates a command with a forked candidate RNG, saves accepted candidate state/RNG, and changes its official in-memory values only after the save succeeds. Conflict, domain rejection, and persistence failure are distinct result types. Application ports keep the session independent of FastAPI and the concrete JSON adapter.

The current `revision` and `counter` state is a neutral synthetic contract fixture, not a formal gameplay or resource system. The session is not exposed through an API or UI.

See the repository root `README.md` for setup, development, and verification commands.
