# TASK-004 Read-only Document Content Compiler ExecPlan

## 1. Objective

Establish the first strictly bounded, deterministic, versioned content compilation path for neutral
read-only Markdown documents while preserving the separation among published author source, private
author material, generated runtime content, test fixtures, player saves, and domain state.

## 2. Scope

Included:

- `authoring/published/documents/` as the only default publication input;
- a restricted scalar frontmatter parser and read-only-document validator;
- stable content ID validation and duplicate detection;
- structured source issues with file and optional line context;
- `buxianxian-content` JSON package schema v1;
- deterministic entry/key ordering, UTF-8/LF encoding, and atomic output replacement;
- standard-library validate/compile CLI commands;
- neutral dedicated test fixtures and required success/error/isolation/determinism tests;
- author documentation, ADR-005, architecture/status/README updates, and generated-output ignore rules.

Excluded:

- complete YAML support or a new YAML dependency;
- domain, state, save, session, API, or frontend integration;
- formal narrative content and all scene/gameplay/content-unlock systems;
- Wikilinks, HTML, localization, search, indexes, assets, watches, plugins, and LLM generation.

## 3. Existing context

The repository is clean on `main` at commit `53a5e69`. TASK-001 through TASK-003 provide domain,
save, RNG, and persistent-session capabilities with forty passing backend tests. The current
`authoring/` directory contains only its boundary README. `.gitignore` already excludes private and
draft author directories but has no publication or compiled-content path.

The architecture already distinguishes author source, runtime content, save state, read models, and
logs. ADR-001 makes Obsidian optional and requires explicit compilation; ADR-002 requires neutral
system fixtures before narrative. No YAML parser dependency exists. The target infrastructure layer
is the correct location for filesystem parsing and content compilation.

## 4. Proposed design

### Directory boundary

- `authoring/published/documents/`: explicitly publishable Markdown input only;
- `authoring/private/` and `authoring/drafts/`: ignored, non-input author material;
- `runtime-content/buxianxian-content.json`: generated default output, ignored by Git;
- `backend/tests/content/fixtures/`: neutral compiler-only fixtures.

The compiler receives the exact publication directory and recursively considers only `.md` files
within it. Directory symlinks are not followed and file symlinks are rejected. It never searches an
ancestor, sibling, home directory, or Obsidian vault.

### Restricted frontmatter

Version 1 accepts a leading `---` block containing exactly these unique scalar keys:

```yaml
schema_version: 1
id: document.alpha
type: read_only_document
title: "Document Alpha"
```

Lines use `key: value`. Values may be unquoted plain scalars or JSON-style double-quoted strings.
Blank metadata lines are allowed. Comments, arrays, mappings, anchors, multiline YAML, duplicate
keys, and unknown keys are rejected. This deliberate subset avoids a new dependency and YAML's
implicit type/coercion surface for four fields. PyYAML was considered but rejected at this size; if
metadata later needs real YAML, that is a separate compatibility and dependency decision.

### IDs and models

`ReadOnlyDocument` is a frozen dataclass containing entry schema version, content ID, fixed type,
title, and Markdown. IDs are explicit source metadata, never derived from title, filename, or path.
They are 1-128 ASCII characters matching lowercase alphanumeric segments separated by `.`, `_`, or
`-`, starting with a letter.

### Errors

`ContentIssueCode` is a stable enum. `ContentIssue` contains code, source `Path`, optional 1-based
line, and diagnostic detail. `ContentCompilationError` contains an ordered tuple of issues. The
compiler collects independent source errors where practical and adds duplicate-ID issues after
parsing. Expected validation failures do not rely on raw parser exceptions.

### Package and deterministic output

The package root has `format: buxianxian-content`, `schema_version: 1`, and `entries`. Each entry has
`schema_version`, `id`, `type`, `title`, and `markdown`; no source path or author metadata is emitted.
Entries sort by ID, JSON keys sort lexicographically, formatting is fixed at two spaces, UTF-8 uses
LF, and a single final newline is written.

`validate_content()` builds the complete in-memory package. `compile_content()` serializes only a
valid package, then writes to a same-directory temporary file, flushes/fsyncs, closes, and uses
`os.replace`. Validation failure cannot create a new output; replacement failure preserves an old
complete output and cleans the temporary file where possible.

### CLI

`python -m buxianxian.infrastructure.content validate` validates without output.
`python -m buxianxian.infrastructure.content compile` validates and writes the package. `argparse`
provides optional `--source` and `--output`; defaults are documented for commands run from backend.

## 5. Milestones

### Milestone A: source contracts and validation

Affected files: `backend/src/buxianxian/infrastructure/content/` model, errors, and parser modules.

Expected behavior: valid neutral Markdown becomes a typed document; every required invalid source
condition becomes a structured, path-aware issue.

Validation: focused Ruff/Pyright and parser/validator tests.

Recovery: new modules are isolated from domain/application/API and introduce no dependency.

### Milestone B: deterministic package, atomic output, and CLI

Affected files: compiler, CLI, package exports, fixtures, tests, and `.gitignore`.

Expected behavior: validated entries compile byte-stably in ID order, invalid input creates no
output, private siblings are excluded, and both CLI modes work cross-platform.

Validation: package-byte comparisons, failure/output tests, CLI tests and smoke commands.

Recovery: all outputs use pytest temporary directories or the ignored runtime-content path; atomic
replacement protects an existing complete output.

### Milestone C: content-format decision and final verification

Affected files: ADR-005, authoring/architecture/status/README docs, TASK-004 records, and this plan.

Expected behavior: active docs distinguish all four content categories, explain the format and
commands, and mark only the first P4 slice complete.

Validation: full backend checks, source/output/privacy scans, unchanged domain/save/session/API/
frontend checks, dependency review, and Git diff review.

Recovery: documentation is declarative; no formal narrative or generated package is committed.

## 6. Progress log

- [x] 2026-07-15: Audited Git status, repository rules, architecture, roadmap, ADRs, TASK-001 through
  TASK-003 source/tests/records, authoring contents, dependencies, CI, and quality contract.
- [x] 2026-07-15: Reported the bounded directories, restricted frontmatter, deterministic package,
  CLI, alternatives, and exclusions before editing.
- [x] 2026-07-15: Confirmed the pre-change backend checks and forty tests pass.
- [x] 2026-07-15: Implemented source models, structured errors, parser, validation, and discovery.
- [x] 2026-07-15: Implemented deterministic package serialization, atomic output, and CLI.
- [x] 2026-07-15: Added neutral fixtures and twenty-five focused tests.
- [x] 2026-07-15: Added ADR-005 and updated author, developer, architecture, status, and CI
  documentation.
- [x] 2026-07-15: Completed full backend verification and Git scope review.

## 7. Discoveries and deviations

- No TASK-004 record or content implementation existed; the accepted specification is recorded
  before code changes.
- No production dependency is needed because v1 deliberately supports only four scalar metadata
  fields rather than general YAML.
- TASK-004 begins the first P4 slice while P3 replay remains explicitly deferred; neither phase is
  declared complete by this task.
- Strict typing required the parser's issue-raising helper to return `Never`; this accurately
  describes the existing exception flow and avoids casts or ignored diagnostics.
- The active desktop shell does not expose `uv` on `PATH`. The repository `.venv` ran equivalent
  local commands successfully, while CI installs the pinned uv version before running the documented
  commands.
- CI previously tested compiler behavior but did not validate the real publication root. A bounded
  backend step now runs the content `validate` command on every push and pull request.

## 8. Verification

Pre-change baseline from `backend/`:

```text
.venv/Scripts/ruff format --check --no-cache .  -> 20 files formatted
.venv/Scripts/ruff check --no-cache .           -> passed
.venv/Scripts/pyright                           -> 0 errors
.venv/Scripts/python -m pytest -p no:cacheprovider -> 40 passed
```

Focused content verification:

```text
.venv/Scripts/ruff check --no-cache src/buxianxian/infrastructure/content tests/content
  -> passed
.venv/Scripts/pyright src/buxianxian/infrastructure/content tests/content
  -> 0 errors
.venv/Scripts/python -m pytest -p no:cacheprovider tests/content
  -> 25 passed
```

CLI smoke verification:

```text
.venv/Scripts/python -m buxianxian.infrastructure.content validate
  -> Validated 0 content entries.
.venv/Scripts/python -m buxianxian.infrastructure.content compile \
  --source tests/content/fixtures/published \
  --output ../runtime-content/task004-smoke.json
  -> Compiled 1 content entries; inspected valid v1 JSON; output removed.
```

Final backend verification:

```text
.venv/Scripts/ruff format --check --no-cache .  -> 29 files already formatted
.venv/Scripts/ruff check --no-cache .           -> passed
.venv/Scripts/pyright                           -> 0 errors, 0 warnings
.venv/Scripts/python -m pytest -p no:cacheprovider
  -> 65 passed
```

Scope review:

- `git diff --check` passed.
- Domain, application session, save adapter, API, frontend, and dependency manifests have no diff.
- Content source imports no protected runtime layer; protected runtime layers import no compiler.
- API route source and frontend remain unchanged.
- No runtime-content output, private author material, formal content, secret, or save artifact is
  present in the change set.
- `backend/pyproject.toml`, `backend/uv.lock`, and frontend dependency manifests are unchanged.

## 9. Completion summary

TASK-004 completed on 2026-07-15. The repository now has an explicit published Markdown boundary,
restricted read-only-document source contract, structured validation, deterministic and atomic
`buxianxian-content` v1 compilation, a standard-library CLI, CI validation, neutral tests, author
guidance, and ADR-005. No formal content or runtime integration was added. P4 reference validation,
additional schemas, package loading, API/frontend work, and all gameplay remain deferred.
