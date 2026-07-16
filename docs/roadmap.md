# Development roadmap

The roadmap is ordered by dependency, not by entertainment value.

A later phase must not be pulled into an earlier task merely to make a demo look richer.

## P0 — Governance and project baseline

Deliverables:

- product identity;
- role and scope rules;
- architecture direction;
- milestone discipline;
- AGENTS.md;
- task template;
- definition of done.

Exit gate:

- all project documents agree on naming and phase order;
- the first Codex task is explicitly bounded.

## P1 — Engineering bootstrap

Deliverables:

- Python project;
- vanilla TypeScript frontend;
- locked dependencies;
- lint, formatting, typing, tests, and builds;
- CI;
- health endpoint;
- frontend connectivity smoke test.

Exit gate:

- a clean checkout can be set up and verified;
- no game-domain or narrative code exists.

## P2 — Headless deterministic domain kernel

Deliverables:

- minimal state representation;
- command abstraction;
- validation result;
- effect/transition result;
- pure deterministic engine;
- neutral synthetic fixtures;
- unit tests.

Exit gate:

- identical state, command, and RNG input produce identical output;
- invalid commands do not mutate state;
- domain has no web, filesystem, UI, or narrative dependency.

## P3 — Persistence, replay, and versioning

Deliverables:

- save envelope;
- atomic writes;
- corruption handling;
- version and migration boundary;
- deterministic RNG persistence;
- transition log or replay support.

Exit gate:

- state survives restart;
- failed writes do not destroy the previous valid save;
- old fixture saves can be migrated or rejected clearly.

## P4 — Content contract and compiler

Deliverables:

- minimal neutral content schema;
- source parser;
- structural validation;
- reference validation;
- compiled runtime package;
- precise source-location errors.

Exit gate:

- invalid content cannot enter a runtime build;
- author drafts remain separate;
- runtime does not parse an entire personal Obsidian vault.

## P5 — Application services and HTTP API

Deliverables:

- new/load/read/command use cases;
- transport schemas;
- error model;
- API integration tests.

Exit gate:

- the API cannot bypass domain validation;
- the frontend cannot directly modify authoritative state.

## P6 — Minimal game client

Deliverables:

- current node/read-model display;
- action buttons;
- loading and error states;
- basic status display;
- save/load controls when supported.

Exit gate:

- the browser can exercise the generic engine end to end using neutral content.

## P7 — Generic gameplay capabilities

Candidate capabilities, implemented one at a time:

- time;
- action points;
- resources;
- tasks;
- relationships;
- status effects;
- random event pools;
- checks and probability;
- progression;
- NPC state progression.

Each capability requires its own specification and tests. No named story content is required.

TASK-005 implements only the authoritative elapsed-day time item as an explicitly approved
foundational slice. It does not complete P7 or pull forward any other candidate capability.

## P8 — Authoring tools

Deliverables may include:

- templates;
- ID generation;
- duplicate and broken-reference checks;
- reachability analysis;
- branch visualization;
- content statistics;
- friendly Obsidian workflows.

Exit gate:

- ordinary content can be added without editing core engine code;
- errors point authors to the exact source location.

## P9 — System prototype

Use temporary but coherent non-final content to test:

- location movement;
- interaction;
- resource use;
- work/activity;
- progression;
- random event;
- day settlement;
- persistence.

This is the first stage where a short playable loop matters.

## P10 — Narrative integration

Only now introduce formal:

- world setting;
- named characters;
- factions;
- story branches;
- authored books and documents;
- final narrative tone.

Narrative requirements may reveal missing generic capabilities, but must not create hidden one-off rules.

## P11 — LLM assistance and distribution

Possible work:

- constrained dialogue presentation;
- event proposals;
- summaries;
- output validation;
- caching and cost controls;
- offline fallback;
- desktop wrapper;
- packaging and installers.

None of this is required for the core game to work.
