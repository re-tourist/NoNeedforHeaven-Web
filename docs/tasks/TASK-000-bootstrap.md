# TASK-000: Bootstrap the engineering repository

## Role

You are the primary implementation agent for the first engineering task in the “不羡仙” repository.

This task creates the development environment only. It does not create a game engine or narrative demo.

## Read first

Before editing, read:

1. `AGENTS.md`
2. `docs/project-status.md`
3. `docs/product/vision.md`
4. `docs/architecture/overview.md`
5. `docs/roadmap.md`
6. `docs/quality/definition-of-done.md`
7. all accepted ADRs under `docs/adr/`
8. `docs/plans/PLANS.md`

Then inspect the repository and report any conflict between these documents and the actual files.

## Goal

Create a reproducible backend/frontend engineering skeleton for “不羡仙”.

After completion:

- the Python backend can start;
- the frontend can start;
- the frontend can call a backend health endpoint;
- formatting, linting, typing, tests, and builds run reliably;
- continuous integration verifies the repository;
- no game-domain or narrative code exists.

## Technical baseline

Use:

### Backend

- Python 3.14
- `uv` for environment and dependency locking
- FastAPI
- Pydantic
- pytest
- Ruff for formatting and linting
- Pyright for static type checking

### Frontend

- Node.js 24 LTS
- npm with a committed lockfile
- Vite
- vanilla TypeScript
- Vitest
- ESLint
- Prettier

Do not introduce a frontend framework.

## Required repository shape

Create a minimal structure consistent with:

```text
buxianxian/
├─ backend/
│  ├─ pyproject.toml
│  ├─ uv.lock
│  ├─ src/
│  │  └─ buxianxian/
│  │     ├─ __init__.py
│  │     └─ api/
│  │        ├─ __init__.py
│  │        └─ app.py
│  └─ tests/
├─ frontend/
│  ├─ package.json
│  ├─ package-lock.json
│  ├─ index.html
│  ├─ src/
│  └─ tests or colocated test files
├─ authoring/
│  └─ README.md
├─ docs/
├─ .github/
│  └─ workflows/
├─ .gitignore
├─ AGENTS.md
└─ README.md
```

Adjust minor details only when required by the chosen tools, and document the reason.

Do not create empty future domain/application/infrastructure modules merely to imitate the target architecture.

## Backend requirements

1. Use an application factory or otherwise separate app construction from process startup.
2. Provide `GET /api/health`.
3. Return a typed and validated response containing:
   - `status`;
   - `app_id`;
   - `app_name`;
   - `version`.
4. Required values:
   - `app_id = "buxianxian"`;
   - `app_name = "不羡仙"`.
5. Add tests for the successful health response and its contract.
6. Keep code small; this endpoint is a smoke test.
7. Do not create game state, commands, content models, saves, or domain abstractions.

## Frontend requirements

1. Use Vite vanilla TypeScript.
2. Display the product title `不羡仙`.
3. Call `GET /api/health` through one small API-client module.
4. Display a clear connected state that includes the backend application name.
5. Display a clear failure state when the backend is unavailable or returns invalid data.
6. Add a focused test for the API or UI behavior.
7. Do not create routing, global state management, game panels, scene buttons, character views, or narrative text.

## Developer experience

1. Document clean setup for Windows, macOS, and Linux where practical.
2. Document backend and frontend development commands.
3. Document all verification commands.
4. Configure local development so the frontend can reach the backend without hard-coding a production URL.
5. Commit both dependency lockfiles.
6. Add a GitHub Actions workflow that runs:
   - backend format check;
   - backend lint;
   - backend type check;
   - backend tests;
   - frontend format check;
   - frontend lint;
   - frontend type check;
   - frontend tests;
   - frontend production build.
7. Avoid Docker, Make, Just, shell-only scripts, or another globally required task runner.
8. Two-terminal local startup instructions are acceptable and preferred over a premature process supervisor.

## Constraints

Do not add:

- `GameState`;
- commands, conditions, effects, resources, tasks, relationships, progression, or RNG;
- save files;
- Markdown parsing or content compilation;
- named characters, factions, locations, cultivation concepts, or story scenes;
- Obsidian runtime integration;
- LLM integration;
- SQLite or another database;
- React, Vue, Svelte, Redux, Zustand, or similar;
- Electron, Tauri, pywebview, PyInstaller, installers, or packaging;
- authentication, telemetry, cloud deployment, or multiplayer.

Do not rename the product.

Do not use `文明online` in code or UI.

Do not suppress type or lint errors to pass checks.

## Work process

1. Inspect the repository.
2. Create `docs/plans/TASK-000-bootstrap-plan.md` using the ExecPlan contract.
3. Summarize the plan and intended file structure before implementation.
4. Implement milestone by milestone.
5. Update the ExecPlan with discoveries and actual progress.
6. Run all required checks.
7. Review the final diff for scope creep and naming consistency.
8. Produce the completion report required by `AGENTS.md`.

Do not begin TASK-001 or P2 work.

## Acceptance criteria

### Backend

- Clean dependency sync succeeds.
- Health endpoint starts successfully.
- Response is typed, validated, and tested.
- Backend format, lint, type, and test checks pass.

### Frontend

- Clean dependency install succeeds.
- Development server starts.
- Page title and body use `不羡仙`.
- Connected and disconnected states are understandable.
- Frontend format, lint, type, test, and build checks pass.

### Repository

- Lockfiles are committed.
- CI executes all essential checks.
- README instructions match actual commands.
- No forbidden game-domain or narrative code exists.
- Search confirms no unintended `文明online` product naming remains.
- Codex completion report identifies all dependencies and remaining limitations.

## Expected completion report

Report:

1. What was created.
2. Exact commands run and whether each passed.
3. Major configuration choices.
4. Files added or changed.
5. Dependencies added and their purpose.
6. Manual verification performed.
7. Remaining limitations.
8. Confirmation that no later-phase game or narrative feature was implemented.
