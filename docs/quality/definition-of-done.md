# Definition of done

A task is complete only when all applicable conditions are met.

## Scope

- The assigned acceptance criteria are satisfied.
- No later-milestone feature was added.
- No unrelated refactor is mixed into the change.
- Naming follows `不羡仙` / `buxianxian`.

## Correctness

- New behavior has appropriate automated tests.
- Error paths are tested where material.
- Types are explicit.
- Required validation commands pass.
- Manual verification specified by the task was performed.

## Architecture

- Dependency boundaries remain intact.
- The frontend does not duplicate authoritative rules.
- Infrastructure concerns do not leak into the domain.
- Narrative content does not create core-engine special cases.
- New persisted or compiled formats are versioned and documented.

## Maintainability

- Code and documentation agree.
- Dependencies are justified.
- No unexplained TODO, placeholder, disabled test, ignored lint rule, or type suppression remains.
- Public behavior and contracts are understandable from tests or documentation.

## Delivery

- The diff contains no secrets, local saves, private author notes, generated caches, or unrelated formatting churn.
- The completion report lists changes, commands, results, risks, and dependencies.
- Failed or unverified work is described honestly.

“Code was written” is not a definition of done.
