# Web Platform 9.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit dashboard and separate API/MCP service topology with a professional unified web platform: one scheduler process plus one ASGI web process serving React, REST API, and MCP.

**Architecture:** The scheduler remains a separate long-running process. A new `job-search-web` ASGI entrypoint serves the React dashboard, `/api/*` REST routes, `/mcp` streamable HTTP, and `/health`. All surfaces use one application/query/command layer so API, MCP, and dashboard behavior cannot drift.

**Tech Stack:** Python 3.11, FastAPI/Starlette, FastMCP streamable HTTP, SQLite, ChromaDB, Vite, React, TypeScript, TanStack Query, TanStack Table, TanStack Virtual, shadcn/ui-style component primitives.

---

## Operating Rules

- Work on `release-9-web-platform`, never directly on `main`.
- Keep PRs/commits small enough to review.
- Every behavior change starts with a failing test.
- After each commit run the relevant focused tests, `pre-commit`, and a self-review of the commit diff.
- Before opening or updating the release PR, run the full Python suite, frontend quality checks, Docker build/smoke tests, and `gh pr checks`.
- Prefer deleting Streamlit code over keeping compatibility wrappers.
- Version target is `9.0.0` because the runtime surface and Docker topology intentionally change.

## Target Runtime

```text
job-search scheduler
job-search-web
  GET  /                         React dashboard
  GET  /assets/*                 React static assets
  GET  /health                   web health
  *    /api/*                    REST API
  *    /mcp                      MCP streamable HTTP
```

Docker Compose target:

```text
services:
  scheduler:
    command: ["job-search", "scheduler"]
  web:
    command: ["job-search-web"]
    ports:
      - "${JOB_SEARCH_WEB_BIND:-127.0.0.1}:${JOB_SEARCH_WEB_PORT:-8501}:8501"
```

API and MCP are enabled by the web server. Optional hard-disable environment flags may exist only if they simplify operational safety:

```text
JOB_SEARCH_API_ENABLED=true
JOB_SEARCH_MCP_ENABLED=true
```

Default should be enabled locally/LAN, bound to localhost by Compose.

## New/Changed File Map

### Python Application Layer

- Create `src/job_search_tool/application/__init__.py`
- Create `src/job_search_tool/application/models.py`
  - `JobListQuery`
  - `JobListResult`
  - `JobCommandResult`
  - `CleanupPreview`
  - `CleanupResult`
- Create `src/job_search_tool/application/jobs.py`
  - query jobs with SQL-backed filtering, sorting, pagination
  - get job detail
  - set bookmark/applied state idempotently
  - blacklist jobs
  - preview and run cleanup actions
- Modify `src/job_search_tool/database.py`
  - add repository methods used by `application/jobs.py`
  - keep low-level SQLite details here
  - remove broad `get_all_jobs()` usage from server surfaces where pagination/filtering is needed
- Modify `src/job_search_tool/job_service.py`
  - reduce to singleton wiring only or replace with application service wiring

### Unified Web Server

- Create `src/job_search_tool/web/__init__.py`
- Create `src/job_search_tool/web/app.py`
  - `create_app() -> FastAPI`
  - mount `/api`
  - mount `/mcp`
  - serve React static assets
  - expose `/health`
- Create `src/job_search_tool/web/api.py`
  - REST endpoints under `/api`
  - typed request/response models
  - token enforcement
- Create `src/job_search_tool/web/mcp.py`
  - FastMCP server construction
  - tool functions backed by application layer
  - expose `create_mcp_app()`
- Create `src/job_search_tool/web/static.py`
  - locate packaged frontend assets
  - fallback to API-only page in editable installs before frontend build
- Modify `pyproject.toml`
  - bump version to `9.0.0`
  - add `job-search-web = "job_search_tool.web.app:main"`
  - remove `job-search-api` and `job-search-mcp` entrypoints unless kept only for one release as hard aliases is explicitly rejected by this plan; no wrappers
- Remove or deprecate by deletion:
  - `src/job_search_tool/api_server.py`
  - `src/job_search_tool/mcp_server.py`
  - `src/job_search_tool/dashboard.py`

### React Frontend

- Create `frontend/package.json`
- Create `frontend/pnpm-lock.yaml` or use npm lock if pnpm is unavailable; prefer pnpm.
- Create `frontend/index.html`
- Create `frontend/vite.config.ts`
- Create `frontend/tsconfig.json`
- Create `frontend/src/main.tsx`
- Create `frontend/src/App.tsx`
- Create `frontend/src/api/client.ts`
- Create `frontend/src/api/types.ts`
- Create `frontend/src/features/jobs/JobsPage.tsx`
- Create `frontend/src/features/jobs/JobTable.tsx`
- Create `frontend/src/features/jobs/JobDetailPanel.tsx`
- Create `frontend/src/features/jobs/jobQueries.ts`
- Create `frontend/src/features/analytics/AnalyticsPage.tsx`
- Create `frontend/src/features/database/DatabasePage.tsx`
- Create `frontend/src/components/ui/*`
- Create `frontend/src/styles.css`

Frontend must support:

- large job lists via server pagination and virtualized rows
- filter bar: score range, site, company, status, remote, search text
- semantic search field
- detail drawer/panel with description
- idempotent actions: set applied/bookmarked
- blacklist single and selected jobs
- cleanup preview before cleanup execution
- CSV/XLSX export route or client-triggered download through API
- health/config status panel

### Docker and Release

- Modify `Dockerfile`
  - add Node/pnpm frontend build stage
  - copy built assets into Python package or `/opt/job-search-tool/frontend`
  - runtime contains only built static assets, not Node toolchain
- Modify `docker-compose.yml`
  - replace `dashboard`, `api`, `mcp` services with `web`
  - update ports/env names
- Modify `docker-compose.dev.yml`
  - web development override
  - optional separate frontend dev server only for development if needed
- Modify `.dockerignore`
  - include frontend build/cache rules
- Modify `.github/workflows/ci.yml`
  - add frontend install/build/test/typecheck
  - update Docker smoke tests for `job-search-web`
- Modify docs:
  - `README.md`
  - `docs/user/docker.md`
  - `docs/user/api.md`
  - `docs/user/mcp.md`
  - `docs/user/operations.md`
  - `docs/developer/architecture.md`
  - `docs/developer/testing.md`
  - `docs/developer/release.md`
  - `CHANGELOG.md`

## Task 0: Issue, Branch, and Baseline

- [x] Merge PR #11 into `main`.
- [x] Create branch `release-9-web-platform`.
- [x] Open GitHub issue titled `Release 9.0.0: unified web platform and React dashboard`: https://github.com/VincenzoImp/job-search-tool/issues/12
- [x] Add this plan file to the branch.
- [ ] Commit:

```bash
git add docs/developer/plans/2026-05-11-web-platform-9.md
git commit -m "docs: plan unified web platform release"
```

- [ ] Verify:

```bash
./.venv/bin/pytest -q tests/test_project_meta.py tests/test_docker_compose.py
./.venv/bin/pre-commit run --all-files
git diff --check
```

- [ ] Self-review:

```bash
git show --stat --oneline HEAD
git show --check HEAD
```

## Task 1: Define Shared Application Contracts

**Tests first:**

- Create `tests/test_application_jobs.py`.
- Add tests for:
  - list query filters by min/max score, site, company, bookmarked, applied
  - list query paginates and returns total count
  - list query sorts by score and date
  - `set_bookmarked(job_id, True)` is idempotent
  - `set_applied(job_id, True)` is idempotent
  - blacklist result reports blacklisted count
  - cleanup preview equals cleanup execution count before execution

Expected initial failure:

```bash
./.venv/bin/pytest -q tests/test_application_jobs.py
# ModuleNotFoundError: No module named 'job_search_tool.application'
```

Implementation:

- Create application package and models.
- Add SQL-backed repository methods to `JobDatabase`:
  - `query_jobs(...) -> tuple[list[JobDBRecord], int]`
  - `set_bookmarked(job_id: str, value: bool) -> bool`
  - `set_applied(job_id: str, value: bool) -> bool`
- Keep existing toggle methods only if still used internally by old tests during transition; remove after dashboard/API/MCP replacement.

Verification:

```bash
./.venv/bin/pytest -q tests/test_application_jobs.py tests/test_database.py
./.venv/bin/pre-commit run --all-files
git diff --check
```

Commit:

```bash
git add src/job_search_tool/application src/job_search_tool/database.py tests/test_application_jobs.py
git commit -m "feat: add shared job application layer"
```

Audit loop:

```bash
git show --stat --oneline HEAD
git show --check HEAD
./.venv/bin/pytest -q tests/test_application_jobs.py tests/test_database.py
```

## Task 2: Build Unified Web API

**Tests first:**

- Create `tests/test_web_api.py`.
- Add tests with `TestClient(create_app())` for:
  - `GET /health`
  - `GET /api/jobs`
  - `GET /api/jobs/{job_id}`
  - `PUT /api/jobs/{job_id}/bookmark` with JSON `{"bookmarked": true}`
  - `PUT /api/jobs/{job_id}/applied` with JSON `{"applied": true}`
  - `POST /api/jobs/blacklist` with JSON `{"job_ids": [...]}`
  - `GET /api/cleanup/preview`
  - `POST /api/cleanup/run`
  - token rejection when `JOB_SEARCH_API_TOKEN` is set

Expected initial failure:

```bash
./.venv/bin/pytest -q tests/test_web_api.py
# ModuleNotFoundError: No module named 'job_search_tool.web'
```

Implementation:

- Create `src/job_search_tool/web/api.py`.
- Create `src/job_search_tool/web/app.py`.
- Mount routes under `/api`.
- Keep `/health` at root for container health.
- Implement `main()` using `uvicorn.run(app, host="0.0.0.0", port=8501)`.
- Update `pyproject.toml` with `job-search-web`.

Verification:

```bash
./.venv/bin/pytest -q tests/test_web_api.py tests/test_application_jobs.py tests/test_project_meta.py
uv run mypy src/job_search_tool --ignore-missing-imports
./.venv/bin/pre-commit run --all-files
```

Commit:

```bash
git add src/job_search_tool/web src/job_search_tool/application pyproject.toml tests/test_web_api.py tests/test_project_meta.py
git commit -m "feat: add unified web API server"
```

## Task 3: Mount MCP in the Unified Web Server

**Tests first:**

- Create `tests/test_web_mcp.py`.
- Add tests for:
  - `create_mcp_server()` exposes tools
  - `list_jobs` returns same filtered fields as API summary
  - `set_bookmarked` is idempotent
  - `set_applied` is idempotent
  - `blacklist_jobs` returns count
  - `GET /mcp` path is mounted in `create_app()` route table

Expected initial failure:

```bash
./.venv/bin/pytest -q tests/test_web_mcp.py
# ImportError for job_search_tool.web.mcp
```

Implementation:

- Create `src/job_search_tool/web/mcp.py`.
- Build FastMCP server with tools backed by `application/jobs.py`.
- Return structured JSON strings for compatibility with current tool style.
- Mount `server.streamable_http_app()` at `/mcp` in `create_app()`.
- Remove old `src/job_search_tool/mcp_server.py` after tests are ported.

Verification:

```bash
./.venv/bin/pytest -q tests/test_web_mcp.py tests/test_mcp_server.py tests/test_web_api.py
uv run mypy src/job_search_tool --ignore-missing-imports
./.venv/bin/pre-commit run --all-files
```

Commit:

```bash
git add src/job_search_tool/web tests/test_web_mcp.py tests/test_mcp_server.py
git rm src/job_search_tool/mcp_server.py
git commit -m "feat: mount mcp tools in unified web server"
```

## Task 4: Remove Separate API Server

**Tests first:**

- Update tests to assert `job-search-api` no longer exists and `job-search-web` exists.
- Update API tests to target `job_search_tool.web.app`.

Expected initial failure:

```bash
./.venv/bin/pytest -q tests/test_project_meta.py tests/test_web_api.py
# console script mismatch until pyproject and tests align
```

Implementation:

- Delete `src/job_search_tool/api_server.py`.
- Remove `job-search-api` entrypoint.
- Ensure all API behavior is covered by `tests/test_web_api.py`.
- Remove stale `tests/test_api_server.py` or convert it fully to web API tests.

Verification:

```bash
./.venv/bin/pytest -q tests/test_web_api.py tests/test_project_meta.py
./.venv/bin/pre-commit run --all-files
```

Commit:

```bash
git add pyproject.toml tests
git rm src/job_search_tool/api_server.py tests/test_api_server.py
git commit -m "refactor: replace standalone api server with web server"
```

## Task 5: Scaffold React Dashboard

**Tests first:**

- Add frontend quality scripts:
  - `typecheck`
  - `test`
  - `build`
- Add a minimal React test that expects the app shell to render `Job Search`.

Expected initial failure:

```bash
pnpm --dir frontend test
# no frontend project yet
```

Implementation:

- Create Vite React TypeScript project under `frontend/`.
- Add minimal component primitives without overbuilding:
  - button
  - input
  - badge
  - tabs
  - drawer/sheet
  - table shell
  - toast
- Add API client with typed fetch helpers.
- Add TanStack Query provider.

Verification:

```bash
pnpm --dir frontend install
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
```

Commit:

```bash
git add frontend
git commit -m "feat: scaffold react dashboard"
```

## Task 6: Serve React Assets from Python Package

**Tests first:**

- Add `tests/test_web_static.py`.
- Test:
  - root path returns HTML when static assets exist
  - `/api/jobs` still works
  - static fallback does not swallow `/api` or `/mcp`

Implementation:

- Add frontend build output path to Python package data.
- Add `src/job_search_tool/web/static.py`.
- Update `Dockerfile` with frontend build stage.
- Ensure editable local backend still starts before frontend build with a useful message.

Verification:

```bash
pnpm --dir frontend build
./.venv/bin/pytest -q tests/test_web_static.py tests/test_web_api.py
docker build -t job-search-tool:9.0.0-local .
docker run --rm -v "$PWD/config/settings.example.yaml:/data/config/settings.yaml:ro" job-search-tool:9.0.0-local job-search-healthcheck
```

Commit:

```bash
git add Dockerfile pyproject.toml src/job_search_tool/web tests/test_web_static.py frontend
git commit -m "feat: serve react dashboard from web server"
```

## Task 7: Implement Jobs Dashboard

**Tests first:**

- Add frontend tests for:
  - jobs page renders rows from mocked API
  - filter updates query params
  - bookmark action sends PUT with explicit boolean
  - applied action sends PUT with explicit boolean
  - selected blacklist action sends selected IDs

Implementation:

- Implement `JobsPage`.
- Use TanStack Query for server data.
- Use TanStack Table for columns and state.
- Use TanStack Virtual for large result rendering.
- Use a detail panel for full description.
- Ensure every action invalidates relevant queries.

Verification:

```bash
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
./.venv/bin/pytest -q tests/test_web_api.py tests/test_application_jobs.py
```

Commit:

```bash
git add frontend src/job_search_tool/application tests
git commit -m "feat: implement jobs dashboard"
```

## Task 8: Implement Analytics and Database Operations

**Tests first:**

- Add backend tests for analytics endpoints if needed:
  - stats
  - distribution
  - cleanup preview
- Add frontend tests for:
  - analytics charts receive data
  - cleanup preview renders counts
  - cleanup execute calls backend only after explicit confirmation

Implementation:

- Add dashboard analytics page.
- Add database operations page.
- Add export controls.
- Add destructive-action confirmation dialogs.
- Add health/config status display.

Verification:

```bash
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
./.venv/bin/pytest -q tests/test_web_api.py tests/test_application_jobs.py tests/test_database.py
```

Commit:

```bash
git add frontend src/job_search_tool/application src/job_search_tool/web tests
git commit -m "feat: add analytics and database operations dashboard"
```

## Task 9: Remove Streamlit Runtime

**Tests first:**

- Update Docker Compose tests:
  - no `dashboard`, `api`, or `mcp` service
  - has `web` service
  - `web` command is `job-search-web`
  - web port uses `JOB_SEARCH_WEB_BIND` and `JOB_SEARCH_WEB_PORT`
- Update project meta tests:
  - no Streamlit entrypoint dependency

Implementation:

- Delete `src/job_search_tool/dashboard.py`.
- Remove Streamlit dependency from `pyproject.toml`.
- Update Docker Compose.
- Update Dockerfile comments.
- Update health check or smoke tests to target `job-search-web`.

Verification:

```bash
./.venv/bin/pytest -q tests/test_docker_compose.py tests/test_project_meta.py
uv lock
uv sync --locked
./.venv/bin/pre-commit run --all-files
```

Commit:

```bash
git add pyproject.toml uv.lock Dockerfile docker-compose.yml docker-compose.dev.yml tests
git rm src/job_search_tool/dashboard.py
git commit -m "refactor: remove streamlit dashboard runtime"
```

## Task 10: Documentation and Release Metadata

**Tests first:**

- Add/update docs consistency tests if practical:
  - README mentions `job-search-web`
  - docs do not mention `job-search-api`, `job-search-mcp`, or Streamlit as current runtime

Implementation:

- Update version to `9.0.0`.
- Update `CHANGELOG.md`.
- Update README interface table.
- Update Docker, API, MCP, operations, architecture, testing, release docs.
- Document breaking changes:
  - one `web` service replaces dashboard/api/mcp services
  - old entrypoints removed
  - API paths move under `/api`
  - MCP remains `/mcp`, now served by web
  - Streamlit dependency removed

Verification:

```bash
./.venv/bin/pytest -q tests/test_project_meta.py tests/test_docker_compose.py tests/test_settings_reference.py
pnpm --dir frontend build
./.venv/bin/pre-commit run --all-files
git diff --check
```

Commit:

```bash
git add README.md CHANGELOG.md docs pyproject.toml uv.lock tests frontend
git commit -m "chore: prepare 9.0.0 web platform release"
```

## Task 11: Full Release Verification

Run:

```bash
./.venv/bin/pytest --cov=job_search_tool --cov-report=xml --cov-fail-under=60
uv run mypy src/job_search_tool --ignore-missing-imports
./.venv/bin/pre-commit run --all-files
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
docker compose config
docker compose -f docker-compose.yml -f docker-compose.dev.yml config
docker build -t job-search-tool:9.0.0-local .
```

Smoke web container:

```bash
docker run --rm -d \
  --name job-search-web-smoke \
  -p 18501:8501 \
  -v "$PWD/config/settings.example.yaml:/data/config/settings.yaml:ro" \
  job-search-tool:9.0.0-local job-search-web

curl -fsS http://127.0.0.1:18501/health
curl -fsS http://127.0.0.1:18501/api/jobs
curl -fsS http://127.0.0.1:18501/
docker stop job-search-web-smoke
```

Open PR:

```bash
git push -u origin release-9-web-platform
gh pr create --title "Release 9.0.0 unified web platform" --body-file /tmp/job-search-9-pr.md
gh pr checks --watch --fail-fast
```

## Rollback Strategy

If the React dashboard blocks release quality:

- Keep the shared application layer and unified web API.
- Ship a minimal React UI that covers job list/detail/actions/cleanup.
- Do not keep Streamlit in the runtime; this plan intentionally removes it.

If MCP mounting inside FastAPI exposes an upstream FastMCP incompatibility:

- Keep one `web` Compose service.
- Run MCP as an internal mounted ASGI app only if stable.
- If not stable, use a sibling process inside the same container only as a temporary implementation detail, not as public service topology. Document and open a blocking follow-up issue before release.

## Completion Criteria

- `main` has 8.0.0 merged.
- `release-9-web-platform` PR is open.
- CI is green.
- Docker image builds.
- Runtime has only scheduler and web services.
- React dashboard fully replaces Streamlit.
- REST API is under `/api`.
- MCP is under `/mcp` on the same web server.
- No current docs mention Streamlit, standalone API, or standalone MCP as active runtime.
- All destructive commands have preview/confirmation behavior in dashboard and explicit command semantics in API/MCP.
