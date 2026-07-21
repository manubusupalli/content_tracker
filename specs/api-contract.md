# Telusko Workflow Engine — Frontend/Backend API Contract

Derived strictly from `frontend/app.js`. This document specifies the exact
wire format the frontend sends and expects to receive for every backend
call it makes (auth + the four `api.*` task methods), plus the error
handling contract the backend must satisfy.

All task-API calls go through `apiFetch()`, which:
- Reads a JWT from `localStorage` key `telusko_token` and, if present,
  attaches header `Authorization: Bearer <token>`.
- Inspects the `content-type` response header; only parses the body as
  JSON if it contains `application/json` (non-JSON responses yield
  `data: null`).
- Treats HTTP status `401` specially (see Error Handling below) for
  *every* call made through `apiFetch` (i.e. all four task methods).

---

## Auth: `POST /api/auth/login`

(Not one of the four `api.*` task methods, but required context for
every other call — documented here because all task endpoints depend on
the token it returns.)

- **HTTP method / URL**: `POST /api/auth/login` (no path or query params)
- **Request headers**: `Content-Type: application/x-www-form-urlencoded`
- **Request body**: URL-encoded form (`URLSearchParams`), exactly two fields:
  - `username` (string, trimmed client-side before send)
  - `password` (string, sent as-is, not trimmed)
- **Success response body** (parsed as JSON): must contain
  - `access_token` (string) — the JWT. This is the only field the
    frontend reads (`data.access_token`).
- **Failure response body** (`!response.ok`): frontend does
  `response.json().catch(() => ({}))` and reads `err.detail` (string) as
  the human-readable error message shown in the login form. If parsing
  fails or `detail` is absent, frontend falls back to the literal string
  `"Invalid credentials. Please try again."`
- **JWT payload contract**: frontend decodes the JWT payload client-side
  (`parseJwtPayload`, base64url decode of the middle segment — display
  only, not verified/validated) and reads a `role` claim. Expected values
  and their mapping (`ROLE_MAP`):
  - `"admin"` → internal role `Admin`
  - `"content_team"` → internal role `Content`
  - `"video_editor"` → internal role `Editor`
  - `"uploader"` → internal role `Uploader`
  - Any other/missing value → frontend defaults to `Admin`.
- **Network failure** (fetch throws, e.g. server unreachable): frontend
  shows `` `Could not reach the server: ${err.message}` `` in the login
  error area.

---

## Auth: `POST /api/auth/users` (admin only)

(Not called by the frontend today — no UI exists for user management —
but implemented on the backend as an admin-only endpoint for creating
accounts. Documented here for completeness and future frontend work.)

- **HTTP method / URL**: `POST /api/auth/users` (no path or query params)
- **Authorization**: requires `Authorization: Bearer <token>` for a user
  whose JWT `role` claim is `admin`; any other role gets `403 Forbidden`.
- **Request headers**: `Content-Type: application/json`.
- **Request body** (JSON):
  ```json
  {
    "username": "string (non-empty)",
    "password": "string (non-empty, plaintext — hashed server-side)",
    "role": "string (one of admin|content_team|video_editor|uploader)"
  }
  ```
- **Success response body** (`201 Created`):
  ```json
  {
    "id": 5,
    "username": "string",
    "role": "string"
  }
  ```
  Note: `hashed_password` is never returned.
- **Failure response body**:
  - `401` — missing/invalid token (same shape as other endpoints:
    `{"detail": "Could not validate credentials"}`).
  - `403` — authenticated as a non-admin role:
    `{"detail": "role <role> is not permitted to perform this action"}`.
  - `409` — `username` already exists:
    `{"detail": "Username '<username>' is already taken"}`.

---

## Auth: `GET /api/auth/me`

(Not called by the frontend today, but implemented on the backend so a
client can look up the identity/role behind the current token without
decoding the JWT client-side.)

- **HTTP method / URL**: `GET /api/auth/me` (no path or query params)
- **Authorization**: requires `Authorization: Bearer <token>` for any
  authenticated user (all four roles permitted).
- **Request body**: none.
- **Success response body** (`200 OK`):
  ```json
  {
    "id": 1,
    "username": "string",
    "role": "string (admin|content_team|video_editor|uploader)"
  }
  ```
- **Failure response body**: `401` if the token is missing, invalid, or
  belongs to a username no longer present in the database:
  `{"detail": "Could not validate credentials"}`.

---

## `getTasks` — `GET /api/tasks`

- **HTTP method / URL pattern**: `GET /api/tasks`. No path or query
  parameters used.
- **Request body**: none.
- **Success response body**: a JSON array of task objects, returned
  as-is and assigned directly to the frontend's in-memory `tasks` array.
  Each task object is expected to have (based on all reads in
  `buildCard`, `buildColumn`, `renderStats`, `openModal`, and
  `advanceTask`/`deleteTask`/drag-drop lookups by `id`):
  - `id` — value used as a lookup key (`tasks.find(t => t.id === taskId)`)
    and rendered via `card.dataset.id = task.id`; also produced by
    `parseInt(form.dataset.editId, 10)` when round-tripped for edits,
    implying the frontend treats `id` as (or coerces it to) an integer.
  - `title` (string) — rendered via `escapeHtml(task.title)`.
  - `description` (string) — rendered via `escapeHtml(task.description)`.
  - `assignedRole` (string) — set into `form.elements['task-role'].value`
    on edit; must match one of the `<select>` option values in the form
    (not enumerated in app.js itself).
  - `state` (string) — must be one of the `STATE_KEYS`:
    `code_ready`, `recorded`, `editing`, `uploaded`, `published`. Used to
    bucket the task into a board column (`t.state === state.key`).
  - `createdAt` (string) — rendered as-is via
    `escapeHtml(task.createdAt)` (no date parsing/formatting is done by
    the frontend, so this must already be a display-ready string).
- **Query/path params**: none used.
- **Error handling specific to this call**: see "Error Handling" below —
  `getTasks` does NOT propagate generic errors to the caller; it catches
  them, toasts, and returns a fallback value instead (see below).

---

## `createTask` — `POST /api/tasks`

- **HTTP method / URL pattern**: `POST /api/tasks`. No path or query
  parameters.
- **Request headers**: `Content-Type: application/json`.
- **Request body** (JSON, from the Add/Edit modal form, only when adding
  a new task — i.e. `form.dataset.editId` is unset):
  ```json
  {
    "title": "string (trimmed, non-empty — validated client-side before submit)",
    "description": "string (trimmed, may be empty)",
    "assignedRole": "string (value of the task-role <select>)",
    "state": "string (one of code_ready|recorded|editing|uploaded|published; defaults to code_ready for new tasks)"
  }
  ```
  Note: no `id` and no `createdAt` are sent by the frontend on create —
  the backend is expected to generate both.
- **Success response body**: parsed JSON is returned as-is from
  `api.createTask()` to the caller. The caller (`handleFormSubmit`) does
  not read any fields from it directly — it discards the return value,
  closes the modal, and calls `renderBoard()` (which re-fetches via
  `getTasks`). Frontend therefore does **not** depend on the exact shape
  of the success body for this call, only that `response.ok` is true (a
  reasonable implementation would still return the created task object,
  consistent with the `getTasks` shape, but app.js does not require it).
- **Query/path params**: none.

---

## `updateTask` — `PUT /api/tasks/{id}`

- **HTTP method / URL pattern**: `PUT /api/tasks/{id}` — `{id}` is a
  **path parameter**, interpolated directly into the URL template
  literal: `` `/api/tasks/${id}` ``. The `id` value passed in is whatever
  type the task object's `id` field is (see `getTasks` note on `id`
  above) or, for edits from the modal, `parseInt(form.dataset.editId, 10)`
  (an integer).
- **Request headers**: `Content-Type: application/json`.
- **Request body**: `updateTask(id, updates)` sends `JSON.stringify(updates)`
  verbatim — the frontend calls this with **three distinct shapes**
  depending on the caller, so the backend must accept a **partial**
  update (not require all task fields on every PUT):
  1. Full-object update, from the Add/Edit modal when editing an existing
     task (`handleFormSubmit`):
     ```json
     {
       "title": "string",
       "description": "string",
       "assignedRole": "string",
       "state": "string"
     }
     ```
  2. State-only update, from drag-and-drop (Admin only, `buildColumn`'s
     `drop` handler):
     ```json
     { "state": "string (one of the STATE_KEYS)" }
     ```
  3. State-only update, from the "Move Forward" button (`advanceTask`):
     ```json
     { "state": "string (the next STATE_KEYS entry after the task's current state)" }
     ```
- **Success response body**: parsed JSON is returned as-is; none of the
  three call sites read fields off the returned object — each just
  toasts a success message and calls `renderBoard()` to re-fetch the
  authoritative list via `getTasks`.
- **Failure response body**: on `!response.ok`, the frontend throws an
  `Error` with `.status` (HTTP status code) and `.data` (the parsed JSON
  body, or `null` if not JSON) attached. All three call sites then read
  `err.data?.detail` (string) and, if present, show it in the toast
  (e.g. `` `Move blocked: ${detail}` ``, `` `Blocked: ${detail}` ``); if
  absent, they fall back to `` `Could not move/advance task: ${err.message}` ``.
  This means the backend should return a JSON body with a `detail` field
  describing the failure (matches FastAPI's default error shape).
- **Query params**: none. **Path param**: `id`.

---

## `deleteTask` — `DELETE /api/tasks/{id}`

- **HTTP method / URL pattern**: `DELETE /api/tasks/{id}` — `{id}` is a
  **path parameter**: `` `/api/tasks/${id}` ``.
- **Request body**: none sent.
- **Success response body**: the frontend does not read the response
  body at all — `api.deleteTask` just returns the boolean `true` once
  `response.ok` is confirmed. Any JSON body (or none) is acceptable on
  success; only the status code matters.
- **Failure response body**: same convention as `updateTask` — on
  `!response.ok`, an `Error` is thrown with `.status` and `.data`
  attached; `deleteTask()` (the UI action function, distinct from
  `api.deleteTask`) reads `err.data?.detail` and shows
  `` `Blocked: ${detail}` `` if present, else
  `` `Could not delete task: ${err.message}` ``. Same `detail`-field
  expectation as above.
- **Query params**: none. **Path param**: `id`.
- **Client-side gating** (not a backend contract requirement, but
  explains when this call fires): the frontend only invokes this for
  `currentRole === 'Admin'` and only after a `window.confirm()` dialog;
  the backend must still authorize this independently since the UI gate
  is not a security boundary.

---

## Error Handling

- **Status codes the frontend explicitly distinguishes**:
  - **`401`** — handled centrally in `apiFetch` for *every* call
    (login is a separate raw `fetch`, not routed through `apiFetch`, so
    login's own 401/failure path is handled separately as described in
    the Auth section above). On 401: clears the stored token
    (`clearToken()`), forces the login form back open
    (`showLoginForm()`), shows an error toast
    `"Session expired. Please sign in again."`, and throws
    `Error('Unauthorised — redirected to login')` which the caller must
    treat as terminal (see below).
  - Any other **non-2xx status** (`!response.ok`, e.g. `400`, `403`,
    `404`, `409`, `500`, etc.) is treated uniformly — the frontend does
    not special-case any specific non-401 code. It only distinguishes
    "ok" vs "not ok" vs "401" vs a genuine network/fetch exception.
- **`showToast(..., 'error')` is triggered for**:
  - 401 responses on any `apiFetch` call → `"Session expired. Please sign in again."`
  - `getTasks` failing for any *non*-401 reason (non-ok status, or a
    thrown network error) → `` `Failed to load tasks: ${err.message}` ``.
  - `createTask`/`updateTask`/`deleteTask` failures surfaced by their UI
    callers (`handleFormSubmit`, `advanceTask`, `deleteTask`, the
    drag-drop `drop` handler) → `` `Blocked: ${detail}` `` /
    `` `Move blocked: ${detail}` `` / `` `Save blocked: ${detail}` `` when
    the response body has a `detail` field, otherwise
    `` `Could not <advance/move/delete/Save> task: ${err.message}` ``.
  - Client-side-only validation errors not involving the backend at all
    (e.g. empty title, non-Admin attempting drag/delete, role not
    permitted to advance) also use `showToast(..., 'error')`, but these
    never reach the network.
  - Login failures use a dedicated inline error element
    (`showLoginError`), not `showToast`.
- **Does `getTasks` fail silently?** No. Per `api.getTasks()`:
  ```js
  try {
    const res = await apiFetch('/api/tasks');
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    return res.data;
  } catch (err) {
    if (err.message.includes('Unauthorised')) throw err;
    showToast(`Failed to load tasks: ${err.message}`, 'error');
    return structuredClone(tasks); // graceful degradation
  }
  ```
  - On a 401, the "Unauthorised" error is **re-thrown** (not swallowed) —
    it propagates up out of `renderBoard()` as well, since nothing
    catches it there.
  - On any other failure, it **does surface** an error toast
    (`"Failed to load tasks: ..."`) *and* degrades by returning a
    `structuredClone` of the last-known `tasks` array (or `[]` if no
    tasks have ever loaded) — it is not silent, just non-fatal to
    rendering.

---

## Discrepancies vs. CLAUDE.md

- DISCREPANCY: CLAUDE.md states "Tasks ... have `title`, `description`,
  `assignedRole`, `state`, and `createdAt`" but omits `id`. `app.js`
  clearly requires an `id` field on every task returned by `getTasks` —
  it is used as the DOM `data-id`, as the lookup key for
  drag/advance/delete/edit (`tasks.find(t => t.id === taskId)`), and is
  round-tripped through `PUT /api/tasks/{id}` and
  `DELETE /api/tasks/{id}`. The documented field list in CLAUDE.md should
  include `id`.
- DISCREPANCY (minor/type ambiguity): CLAUDE.md does not specify the
  type of `id`. `app.js` treats it inconsistently — task objects loaded
  from `getTasks` are compared with `===` against
  `parseInt(form.dataset.editId, 10)` (an integer) in `openModal`'s
  save path, implying the backend's `id` should be numeric, yet nothing
  in `app.js` coerces the `id` coming back from `getTasks` itself, so if
  the backend returned `id` as a string, the `===` comparisons used
  throughout (`tasks.find(t => t.id === taskId)`, `t.id === draggedTaskId`)
  would silently break. The backend must return `id` as a JS `number`
  (i.e. a JSON integer, not a string/UUID) for the frontend's identity
  comparisons to work.
- No other contradictions were found: the auth flow
  (`POST /api/auth/login`, `application/x-www-form-urlencoded` body of
  `username`/`password`, JSON response with `access_token`, JWT `role`
  claim decoded client-side and mapped via `ROLE_MAP`), the 401 handling
  (clear token + force re-login on any `apiFetch` call), and the
  graceful-degradation behavior of `getTasks` on non-auth errors all
  match what CLAUDE.md describes.
