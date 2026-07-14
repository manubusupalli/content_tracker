# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This repo currently contains only the **frontend** — a static, vanilla JS/HTML/CSS single-page app (no build tooling, no `package.json`, no framework). It is designed against a backend API that does not exist yet in this repo.

The `.gitignore` anticipates a Python backend (`__pycache__/`, `.venv/`, `*.egg-info/`) using **Alembic** migrations (`backend/alembic/versions/*.pyc`) against a **SQLite** database (`*.db`, `*.db-shm`, `*.db-wal`). When adding the backend, follow this implied layout (`backend/` at repo root, with an `alembic/` migrations directory) unless told otherwise. The auth flow in `app.js` (`POST /api/auth/login` with `application/x-www-form-urlencoded` body of `username`/`password`, returning a JWT `access_token`) matches FastAPI's `OAuth2PasswordRequestForm` convention — assume FastAPI unless the user says otherwise.

There are no build, lint, or test commands yet — none are configured in this repo.

## Running the frontend locally

`frontend/index.html` makes relative `fetch` calls to `/api/...`, so opening the file directly (`file://`) will not work — it must be served, and in the absence of a backend those API calls will fail (the app degrades gracefully for `GET /api/tasks` but not for login, which is required to see the board). Once a backend exists, serve the frontend from the same origin as the API (or via a dev proxy) so `/api/*` resolves correctly.

## Architecture

### Domain model
The app is a Kanban board tracking video production through a fixed pipeline defined in `STATES` (`frontend/app.js`):

`code_ready → recorded → editing → uploaded → published`

Tasks (`GET/POST/PUT/DELETE /api/tasks`) have `title`, `description`, `assignedRole`, `state`, and `createdAt`. The board groups tasks into one column per state.

### Auth & roles
- JWT is stored in `localStorage` (`telusko_token`) and sent as `Authorization: Bearer <token>` on every API call via the `apiFetch` wrapper.
- The JWT payload's `role` claim (`admin`, `content_team`, `video_editor`, `uploader`) is decoded client-side (`parseJwtPayload` — display only, **not** a security boundary) and mapped through `ROLE_MAP` to an internal role key (`Admin`, `Content`, `Editor`, `Uploader`).
- `ROLE_CONFIG` defines which pipeline stages each role is allowed to advance a task from (`canAdvance`). This is a UI-level gate only — the real authorization must be enforced server-side once the backend exists.
- A 401 from any API call clears the token and forces re-login (`apiFetch` in `app.js`).
- Only `Admin` may drag-and-drop cards freely between columns or delete tasks; other roles use the "Move Forward" button, which only moves a task to the *next* state in the pipeline and only if their role permits it.

### Frontend structure (`frontend/app.js`)
Single-file app organized into clearly delimited sections (see the banner comments): Constants/Config → Token/Auth helpers → State → Login form → API wrapper (`api.*`) → Utility helpers → Rendering (`renderBoard`, `buildColumn`, `buildCard`, `renderStats`) → Task actions (`advanceTask`, `deleteTask`) → Add/Edit modal → Keyboard shortcuts → Init.

Rendering is a full re-render on every mutation: `renderBoard()` re-fetches all tasks and rebuilds the entire board DOM (no client-side diffing/virtual DOM). All user-supplied text is passed through `escapeHtml()` before being interpolated into `innerHTML`.

The `api` object is the single point of contact with the backend; every method surfaces failures via `showToast()` rather than failing silently, and `getTasks()` degrades gracefully to the last known `tasks` array on non-auth errors.

## Code Style
- Python: snake case for functions and variables
- Always use type hints
- schemas in /schemas folder and models in /models folder

## Rules
- NEVER modify files in frontend
- NEVER commit .env files
- Always create migration when changing