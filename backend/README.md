# 不羡仙 backend

This package contains the local Python runtime. The API exposes only the TASK-000 engineering health check. The pure `buxianxian.domain` package implements the TASK-001 headless deterministic transition contract and is intentionally not exposed through HTTP yet.

`buxianxian.infrastructure` implements the TASK-002 `buxianxian-save` JSON v1 file adapter and the versioned `xorshift64star` random source. Persistence depends on the domain contract; the domain does not depend on persistence, JSON, Pydantic, or the filesystem. Tests use pytest temporary directories and do not create player saves in the repository.

The current `revision` and `counter` state is a neutral synthetic contract fixture, not a formal gameplay or resource system. Save/reload is not exposed through an application service, API, or UI in this task.

See the repository root `README.md` for setup, development, and verification commands.
