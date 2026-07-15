# TASK-000 Engineering Bootstrap ExecPlan

## 1. Objective

Establish a reproducible backend and frontend engineering baseline for 不羡仙. A contributor must be able to install locked dependencies, start both development servers, verify backend connectivity from the browser, and run the same essential quality checks locally and in CI.

## 2. Scope

Included:

- a Python 3.14 project managed and locked with `uv`;
- a FastAPI application factory and typed `GET /api/health` response;
- a Vite vanilla TypeScript frontend with a small health API client;
- understandable loading, connected, and unavailable states;
- formatting, linting, strict type checking, automated tests, and a production build;
- GitHub Actions and cross-platform setup documentation.

Excluded:

- all game state, commands, rules, persistence, content, narrative, simulation, authoring integration, LLM features, databases, deployment, packaging, accounts, and telemetry;
- empty future `domain`, `application`, or `infrastructure` packages;
- frontend frameworks, routers, and state-management libraries.

## 3. Existing context

The inspected repository contains governance and architecture documents plus an authoring boundary README, but no implementation, dependency manifests, tests, CI configuration, or Git metadata. `AGENTS.md`, `docs/project-status.md`, `docs/architecture/overview.md`, accepted ADRs 001–003, and `docs/tasks/TASK-000-bootstrap.md` agree that Python is authoritative and the frontend is a presentation projection.

The local machine initially exposes Python 3.12.8 and Node.js 20.19.5; `uv` is not installed. TASK-000 requires Python 3.14 and Node.js 24 LTS, so configuration and CI will target those versions. Local verification must report honestly if the required runtimes cannot be provisioned.

## 4. Proposed design

### Backend boundary and contract

`buxianxian.api.app:create_app` constructs the FastAPI application, while a module-level `app` gives Uvicorn a conventional entrypoint. `GET /api/health` returns a Pydantic response with literal status and application identity fields plus the package version. No domain abstraction is introduced.

### Frontend data flow

Vite serves the browser application and proxies `/api` to the local backend during development. `src/api/health.ts` owns transport and runtime response-shape validation. `src/main.ts` owns only loading, connected, and unavailable presentation. The browser does not contain authoritative game behavior.

### Tooling choices

- Ruff provides Python formatting and linting in one fast tool.
- Pyright provides strict Python static analysis as required by TASK-000.
- pytest and FastAPI TestClient verify the HTTP contract.
- ESLint with typescript-eslint, Prettier, and TypeScript strict mode cover frontend static quality.
- Vitest tests the API client with an injected fetch function, avoiding a DOM emulator dependency for this small contract.
- Vite handles development and production builds without a UI framework.

Alternatives considered:

- CORS middleware was rejected because the Vite development proxy keeps requests same-origin and avoids extra runtime policy.
- A schema library for one four-field response was rejected; a narrow explicit type guard keeps dependencies and scope smaller.
- A monorepo task runner and process supervisor were rejected because two documented terminals are sufficient at this milestone.
- A new ADR was rejected because the key technologies and authority decisions are already mandated and accepted.

## 5. Milestones

### Milestone A: backend baseline

Affected files: `backend/pyproject.toml`, `backend/uv.lock`, `backend/src/buxianxian/`, and `backend/tests/`.

Expected behavior: the application starts and `/api/health` returns the exact typed identity contract.

Validation: `uv sync --locked`, Ruff format/lint checks, Pyright, pytest, and a live HTTP request.

Recovery: backend files are isolated under `backend/`; dependency or configuration failures can be corrected without affecting authoring or frontend files.

### Milestone B: frontend baseline

Affected files: `frontend/package.json`, `frontend/package-lock.json`, Vite/TypeScript/lint configuration, `frontend/index.html`, and `frontend/src/`.

Expected behavior: the page identifies 不羡仙 and reports backend connected or unavailable based on a validated health response.

Validation: `npm ci`, format check, lint, type check, Vitest, production build, and a live Vite request with the backend running.

Recovery: frontend transport and presentation stay in separate small modules, so either can be corrected without inventing shared game logic.

### Milestone C: repository workflow

Affected files: `.gitignore`, `.editorconfig`, `.github/workflows/ci.yml`, `README.md`, `docs/project-status.md`, and this plan.

Expected behavior: setup and verification commands match CI and generated artifacts/caches remain excluded.

Validation: inspect workflow syntax, run every documented essential command, scan names and forbidden concepts, and compare documentation against manifests.

Recovery: CI and documentation are declarative and can be revised without changing runtime behavior.

## 6. Progress log

- [x] 2026-07-15: Read repository instructions, task, architecture, roadmap, quality contract, and accepted ADRs.
- [x] 2026-07-15: Inspected repository contents and local Python/Node/uv/Git environment.
- [x] 2026-07-15: Reported scope, architecture interpretation, implementation plan, and risks before editing.
- [x] 2026-07-15: Implemented and locked the backend baseline.
- [x] 2026-07-15: Implemented and locked the frontend baseline.
- [x] 2026-07-15: Added CI, ignore rules, editor settings, and developer documentation.
- [x] 2026-07-15: Ran clean installs, all automated checks, production build, and live browser smoke verification.
- [x] 2026-07-15: Completed scope, naming, dependency, artifact, CI, and documentation review.

## 7. Discoveries and deviations

- The actual engineering root is `WebGameProject` beneath the supplied workspace directory; the sibling `Obsidian` directory is not part of the runtime repository.
- No `.git` metadata is present in or above the engineering root, so final review cannot rely on `git diff` or `git status` unless the user later initializes a repository.
- The available local runtimes are below the required baseline and `uv` is absent. Provisioning and verification results will be recorded here.
- The initially selected uv 0.8.22 provisioned Python 3.14.0rc3 because that uv release predates stable Python 3.14. PyPI showed uv 0.11.28 as current, so local tooling and CI were corrected to the fixed 0.11.28 release before environment verification.
- FastAPI 0.139 resolved Starlette 1.3, whose TestClient has moved from the deprecated `httpx` package to the maintained, typed `httpx2` successor. The dev dependency was corrected after pytest emitted Starlette's deprecation warning and Pyright exposed the old client's unknown types.
- The in-app browser controller did not return reliably for the localhost page. Manual acceptance therefore used installed Microsoft Edge in one-shot headless mode with separate fresh user-data directories, disabled cache, unique query parameters, and screenshots for connected and unavailable states.
- npm 11 reported that Vite's required `esbuild` postinstall script had not been reviewed. `npm approve-scripts esbuild` added a version-specific approval for only `esbuild@0.28.1`; a subsequent clean install completed without the warning and all checks still passed.

## 8. Verification

Completed on 2026-07-15:

- `uv 0.11.28`, `uv sync --locked`, and `uv run python --version`: passed with locked dependencies and Python 3.14.6.
- `uv run ruff format --check .`: passed; four Python files formatted.
- `uv run ruff check .`: passed.
- `uv run pyright`: passed in strict mode with zero errors or warnings.
- `uv run pytest`: passed; one backend contract test.
- Node.js 24.18.0 and npm 11.16.0 `npm ci`: passed; 156 packages installed and zero reported vulnerabilities.
- `npm run format:check`, `npm run lint`, and `npm run typecheck`: passed.
- `npm test`: passed; one test file and three API-client tests.
- `npm run build`: passed with Vite 7.3.6; production assets generated under ignored `frontend/dist/`.
- Live backend request: passed with HTTP 200, `application/json`, and the exact `buxianxian` / `不羡仙` / `0.1.0` contract.
- Live browser connected state: passed in a fresh, cache-disabled Edge profile; the page displayed `不羡仙` and `已连接到后端：不羡仙（0.1.0）`.
- Live browser unavailable state: passed after confirming port 8000 was unreachable and reloading in a second fresh, cache-disabled profile; the page displayed a clear backend-unavailable HTTP 500 message from the Vite proxy.
- Repository searches: no forbidden implementation terms in runtime code, no legacy name in code or UI, no unexpected temporary source files, and only ignored generated environments/caches/build output.
- CI workflow review: both jobs use the required runtime lines, locked installs, and every essential backend/frontend check documented in the root README.

GitHub Actions was not executed remotely because the supplied engineering directory has no `.git` metadata or configured remote. Its commands were all executed successfully in the required local runtime versions.

## 9. Completion summary

TASK-000 is complete. The repository now has a locked Python/FastAPI backend, a locked vanilla TypeScript/Vite frontend, a typed and tested health contract, clear connected and unavailable browser states, strict automated quality gates, a production build, CI configuration, and setup documentation.

No game-domain, persistence, content, authoring-runtime, narrative, simulation, database, LLM, deployment, or packaging capability shipped. P2 remains a separate future milestone that requires explicit approval and its own task or plan.
