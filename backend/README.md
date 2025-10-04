# Backend v2 (FastAPI)
Features:
- Stable paragraph IDs & outline (`GET /api/outline/{file_id}`).
- Apply operations **anchored by after_paragraph_id**.
- Version snapshots (`GET /api/versions/{file_id}`).
- Redline-style compare (`GET /api/redline?base_id=...&revised_id=...`) -> downloads a `.docx` with visual inserts (green underline) and deletions (red strikethrough).

## Run
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...           # optional
export OPENAI_MODEL=gpt-4o-mini        # optional
uvicorn app:app --reload
```
The server serves the built Vite frontend from `../frontend/dist`.
