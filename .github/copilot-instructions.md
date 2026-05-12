# Copilot instructions for this repository

Purpose: Give Copilot sessions quick, actionable context (build/test/lint commands, high-level architecture, and repository-specific conventions).

---
Build / test / lint (location-specific)

- Backend (backend/)
  - Install: cd backend && pip install -r requirements.txt
  - Run dev server: cd backend && python api.py
  - Railway/Procfile examples: `web: python api.py` (simple) or `web: gunicorn api:app` (production)
  - Tests: no automated test suite detected. Run a single Python test file if/when pytest is added: `cd backend && pytest tests/test_x.py` or run ad-hoc scripts directly.

- Frontend (frontend/)
  - Install: cd frontend && npm install
  - Dev server: cd frontend && npm run dev
  - Build: cd frontend && npm run build
  - Preview: cd frontend && npm run preview
  - Lint: cd frontend && npm run lint (this delegates to lint:*). To lint only with eslint: `cd frontend && npm run lint:eslint -- <path/to/file>`
  - Type-check: cd frontend && npm run type-check
  - Single-file actions: pass a path after the script (npm run <script> -- <path>)

(If you add tests, include a `pytest`/`jest`/`vitest` script so Copilot can reference them directly.)

---
High-level architecture (big picture)

- Two main components:
  1. frontend/ — Vue 3 (Vite) single-page app (Pinia, axios). Node >=20 recommended. Serves UI and calls the backend API.
  2. backend/ — Python Flask API (api.py), SQLAlchemy + psycopg2 for PostgreSQL, simple token-based auth and history endpoints under `/api/*`.
- Data: PostgreSQL (DATABASE_URL). Database tables (users, history) are auto-created on first run or via `init_db()`.
- Deployment: backend targets Railway (Procfile examples in docs); frontend is built with Vite and can be deployed on Vercel/Railway.
- Env wiring: frontend reads VITE_API_BASE_URL; backend reads DATABASE_URL, DASHSCOPE_API_KEY, PORT.

---
Key repository conventions and notes

- Environment files: copy `.env.example` to `.env` in both `backend/` and `frontend/` and fill required keys. Important variables:
  - DASHSCOPE_API_KEY, DATABASE_URL, PORT (backend)
  - VITE_API_BASE_URL (frontend)

- Backend:
  - Uses `api.py` as entrypoint; starts a Flask app. DB schema created automatically on first run.
  - Passwords are hashed with werkzeug; tokens are simple and stored client-side (localStorage).
  - Common operations: `python api.py`, or use `gunicorn api:app` in production.

- Frontend:
  - package.json contains scripts: dev, build, preview, lint, format, type-check. Linting is split into `lint:oxlint` and `lint:eslint`.
  - `npm run dev` serves on default Vite port (5173). `VITE_API_BASE_URL` defaults to http://localhost:5000 for local dev.
  - Node engine constraint in package.json: node 20.x or >=22.12.0; use matching runtime in CI.

- No AI-assistant/agent config files detected (checked for CLAUDE.md, AGENTS.md, CONVENTIONS, .cursorrules, .windsurfrules, .clinerules). Add them if you want Copilot to follow organization-wide rules.

---
Quick pointers for Copilot sessions

- When asked to modify backend behavior, check `backend/api.py`, `backend/database.py`, and `backend/.env.example` for env expectations.
- When asked to change UI behavior, inspect `frontend/src/` (components, stores) and `frontend/package.json` scripts for local commands.
- For database-related changes, read `DATABASE_SETUP.md` (root) — contains schema, env examples and manual init instructions.

---
MCP servers

Would you like to configure any MCP servers (e.g. Playwright for end-to-end testing of the frontend)? Reply and I can add a sample `mcp` config and recommended test job.

---
Summary

Created concise guidance covering build/run/lint commands, the high-level architecture, and repository-specific conventions so future Copilot sessions can act accurately. Tell me if you want more details added (CI snippets, sample tests, or agent configs).