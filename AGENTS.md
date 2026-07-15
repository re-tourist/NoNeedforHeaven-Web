# Repository instructions for Codex

## Project identity

- Product name: `不羡仙`
- Stable code identifier: `buxianxian`
- Engineering repository: `NoNeedforHeaven-Web`
- This is an independent local web text game.
- Obsidian is an authoring environment only; it is not part of the runtime.

Do not use `文明online` as a product name, package name, UI label, save identifier, or test expectation.

## Start every task here

Before editing:

1. Read `docs/project-status.md`.
2. Read the assigned task file.
3. Read the architecture or ADR files referenced by that task.
4. Inspect existing code and tests.
5. State the intended scope before implementation.

The current milestone limits what may be implemented. Do not implement later milestones early.

## Architecture invariants

- Python is the sole authority for game state and game rules.
- The frontend renders server-provided state and submits commands.
- The frontend must not independently apply authoritative game effects.
- Domain code must not depend on FastAPI, filesystem, UI, or narrative content.
- Runtime state, static content definitions, and author notes are separate concerns.
- Random behavior must eventually use a deterministic project RNG abstraction; do not scatter direct random calls through domain code.
- LLM output must never directly mutate authoritative game state.

## System-before-narrative discipline

Until the roadmap explicitly reaches narrative integration:

- Use neutral fixtures such as `node_a`, `action_a`, `character_a`, and `resource_x`.
- Do not add named characters, factions, locations, cultivation systems, lore, or plot-specific branches.
- Do not introduce special cases justified by a future story scene.
- Do not create narrative content merely to demonstrate infrastructure.
- Core mechanisms must remain usable by a non-xianxia test game.

## Engineering rules

- Keep changes limited to the assigned task.
- Do not perform unrelated refactors.
- Do not add dependencies without explaining why they are required.
- Prefer the standard library or existing dependencies when reasonable.
- Use strict typing in Python and TypeScript.
- Do not use `Any`, `any`, unsafe casts, or ignored type errors as shortcuts.
- Add or update tests for behavior changes.
- Keep public contracts explicit and versionable.
- Never commit secrets, local saves, personal Obsidian vaults, generated caches, or private author notes.
- Do not claim completion while required checks fail.
- Do not silently weaken lint, type, or test configuration to make checks pass.

## Planning

Create or update an ExecPlan under `docs/plans/` before implementation when a task:

- changes a core domain contract;
- changes a persisted or compiled data format;
- introduces a migration;
- spans several modules or milestones;
- introduces a major dependency;
- is expected to require multiple implementation sessions.

Use `docs/plans/PLANS.md` as the planning contract.

## Verification

Run every command required by the assigned task.

When the repository bootstrap is complete, the normal baseline will include:

Backend:
- formatting check;
- lint;
- static type check;
- tests.

Frontend:
- formatting check;
- lint;
- TypeScript type check;
- tests;
- production build.

## Completion report

End each task with:

1. Scope completed.
2. Important design decisions.
3. Files changed.
4. Commands run and their results.
5. Remaining risks, limitations, or follow-up work.
6. Any dependency added and why.

Report failures honestly. Do not describe unverified behavior as working.
