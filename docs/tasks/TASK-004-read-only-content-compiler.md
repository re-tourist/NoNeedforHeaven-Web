# TASK-004: Read-only document content compiler foundation

## Goal

Create the first explicit author-to-runtime content path without connecting it to game state,
application sessions, HTTP, or the frontend:

```text
repository published Markdown
    -> restricted frontmatter parsing and validation
    -> deterministic compilation
    -> versioned buxianxian-content JSON package
```

## Required public behavior

- Only the dedicated repository publication directory is scanned; private notes and an entire
  Obsidian vault are never implicit inputs.
- Version 1 supports only `read_only_document` entries with explicit schema version, stable ID,
  player-visible title, and Markdown body.
- Validation reports structured issues with source file context for all required malformed,
  unsupported, duplicate, empty, encoding, and read failures.
- Compilation is deterministic, contains no source paths or private author metadata, and writes
  atomically only after every source passes validation.
- Developers have cross-platform validate and compile module commands.

## Explicitly excluded

- formal story, worldbuilding, character, location, faction, cultivation, or other narrative text;
- scenes, nodes, navigation, conditions, effects, tasks, state bindings, or unlock behavior;
- full YAML, Wikilinks, HTML rendering, search, localization, assets, file watching, or Obsidian
  plugins;
- domain, save, session, API, or frontend integration;
- LLM content generation.

Tests and committed examples use neutral synthetic documents only.

## Implemented contract

- `authoring/published/documents/` is the only default published input.
- `ReadOnlyDocument` and `ContentPackage` are immutable infrastructure contracts.
- `ContentIssueCode`, `ContentIssue`, and `ContentCompilationError` provide expected structured
  failures with source file and optional line context.
- `validate_content()` validates the full source set without writing.
- `compile_content()` emits a deterministic `buxianxian-content` JSON v1 package through atomic
  replacement only after complete validation.
- `python -m buxianxian.infrastructure.content validate|compile` is the cross-platform developer
  entry point.

## Completion

Completed on 2026-07-15. ADR-005 records the source/package identity, versioning, stable-ID,
Obsidian-isolation, restricted-frontmatter, and first-content-type decisions. P4 remains in progress;
runtime loading, reference validation, additional types, API/frontend integration, and formal
content are not part of this task.
