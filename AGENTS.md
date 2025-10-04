# Repository Guidelines

## Project Structure & Module Organization
The workspace splits into `backend/` (FastAPI service) and `frontend/` (Vite + Vue 3 SPA). Backend entrypoint is `backend/app.py`, with document logic isolated inside `doc_ops.py`, Pydantic models in `models.py`, and shared helpers in `utils.py`. Generated `.docx` files and outlines persist under `storage/` (auto-created). Frontend source lives in `frontend/src` with `App.vue` as the root shell, `main.ts` for bootstrapping, and shared types in `types.ts`. Tailwind styles reside in `styles.css`; build artifacts land in `frontend/dist`.

## Build, Test, and Development Commands
Run the API with `python -m venv .venv && .\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Unix), then `pip install -r backend/requirements.txt` and `uvicorn app:app --reload` from `backend/`. The Vue client uses `npm install` followed by `npm run dev` in `frontend/`. Ship a production bundle with `npm run build`; FastAPI automatically serves `frontend/dist`.

## Coding Style & Naming Conventions
Python code follows PEP 8: four-space indents, `snake_case` functions, and type hints for request/response models. Keep business logic in `doc_ops.py` and surface-only routing in `app.py`. Vue files use `<script setup lang="ts">`, two-space indents, and `camelCase` refs. Prefer Tailwind utility classes; custom CSS stays in `styles.css`. Name new components or utilities with descriptive, hyphenated file names (e.g., `outline-panel.vue`, `doc-service.ts`).

## Testing Guidelines
Automated tests are not yet wired up. New features should introduce `pytest` suites under `backend/tests/` using realistic `.docx` fixtures, plus lightweight component or composable tests with `vitest` in `frontend`. Mirror file structure (e.g., `tests/test_doc_ops.py`) and exercise critical flows: outline generation, operation application, and planning fallbacks. Document manual QA steps when automated coverage is not feasible.

## Commit & Pull Request Guidelines
Commits should be small, imperative sentences referencing the area touched (e.g., `Add redline download link`). Include related issue IDs in the subject or body when applicable. Pull requests need: purpose summary, testing notes (`pytest`, `npm run build`, manual steps), screenshots or GIFs for UI changes, and callouts for schema or API adjustments.

## Security & Configuration Tips
Never commit secrets; load `OPENAI_API_KEY`, `OPENAI_MODEL`, or alternative `STORAGE_DIR` paths via environment variables. Verify that generated `.docx` artifacts in `storage/` stay out of version control and scrub sample documents of sensitive content before sharing.
