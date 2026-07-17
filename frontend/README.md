# 不羡仙 frontend

The frontend is a vanilla TypeScript projection of the local FastAPI runtime. It does not own game
rules or mutate authoritative state locally.

## Structure

- `src/api/game.ts`: strict unknown-JSON validation and HTTP client;
- `src/app.ts`: testable boot/start/creation/overview state controller;
- `src/main.ts`: accessible DOM rendering and event wiring;
- `src/style.css`: responsive engineering-prototype presentation.

The controller may validate form completeness and keep transient selections. Aptitude outcomes,
elapsed days, revision, accepted traits, and command results always come from server responses.

## Development

From `frontend/`:

```text
npm ci
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`. Start the backend separately as documented in the
repository README.

Checks:

```text
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
```

Vitest exercises the HTTP contracts and pure controller. No DOM or browser-automation dependency is
required at this stage.
