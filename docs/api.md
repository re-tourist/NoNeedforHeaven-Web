# Game API

The FastAPI adapter exposes the first local single-game vertical slice under `/api/game`. API DTOs
are presentation contracts; Python domain/application objects remain authoritative.

## Routes

### `GET /api/game`

Returns:

- `save_exists`: an entry occupies the configured path;
- `save_available`: that entry is a valid supported save;
- `session_active`: a session is active in this process;
- `state`: the current projected state only when a session is active;
- `error`: an optional stable save-inspection error.

### `POST /api/game/drafts`

Invalidates any previous server draft and returns a new `draft_id`, three aptitude options, six
prototype traits, and `required_trait_count: 2`. It never returns candidate RNG data.

### `POST /api/game/new`

Request:

```json
{
  "draft_id": "opaque server identifier",
  "name": "角色姓名",
  "aptitude_option_id": "aptitude_option_1",
  "trait_ids": ["prototype.calm", "prototype.steady"],
  "overwrite_existing_save": false
}
```

The server finds the retained draft and revalidates every value. If any save entry exists,
`overwrite_existing_save` must be true. Success atomically saves state plus post-generation RNG,
invalidates the draft, and creates the active session.

### `POST /api/game/load`

Loads the configured single save into the active session. Missing, corrupt, unsupported, and I/O
failures use different stable error codes.

### `POST /api/game/wait`

Request:

```json
{
  "days": 3,
  "expected_revision": 0
}
```

The API constructs the existing typed `AdvanceTime` command and delegates to the persistent
session. Success returns the complete new state. Revision conflict returns HTTP 409 plus the current
server state; the client refreshes and does not blindly retry.

## Error envelope

Expected failures use:

```json
{
  "error": {
    "code": "revision_conflict",
    "message": "游戏状态已经更新。界面已刷新。请重新确认操作。",
    "fields": []
  },
  "state": null
}
```

Current machine codes:

- `invalid_request`;
- `no_active_session`;
- `save_not_found`, `save_corrupt`, `save_unsupported`, `save_load_failed`;
- `draft_not_found`, `draft_creation_failed`;
- `invalid_name`, `invalid_aptitude_selection`, `invalid_trait_selection`;
- `save_overwrite_required`;
- `revision_conflict`, `time_command_rejected`;
- `persistence_failed`.

Responses never contain a local path, RNG state, internal exception type, or traceback.

## Runtime limits

The runtime supports one process, one session, one in-memory draft, and one configured save. Do not
run multiple Uvicorn workers against the same save. Drafts disappear after backend restart.

