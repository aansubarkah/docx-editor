# PRD.md — Docx Agent (Create/Edit .docx via LLM)

## 1) Summary
A web app that lets users 1) **create** new Microsoft Word (`.docx`) documents and 2) **edit** existing ones by **asking an LLM**. The LLM acts as a planner and emits **bounded JSON operations**; the server executes those operations against `.docx` (no direct model write access). The app provides HTML previews, **section‑aware anchors** (stable paragraph IDs) for precise edits, versioning, and a **redline compare** download (visual diff inside a generated `.docx`).

**Tech:** FastAPI (Python) + `python-docx` for edits, Vite + Vue 3 + TypeScript + Tailwind for UI, Mammoth.js for previews. Optional OpenAI tool/function calling for planning.

---

## 2) Problem & Goals
**Problem:** Business users and teams spend time iterating Word docs. Editing is repetitive, brittle, and hard to delegate. "AI rewrite this section/add a table" is natural, but unsafe if the model writes files directly.

**Product Goal:** Provide a safe, predictable **agentic** workflow where users describe changes in natural language, the LLM proposes **structured ops**, and the server applies them deterministically with evidence (preview, versioning, redline).

**Non-Goals (v1):**
- Full fidelity WYSIWYG Word rendering in browser.
- Native Word **Track Changes** authoring (we provide a **visual** redline; native tracking is future scope).
- Complex Word features (content controls, macros).

---

## 3) Personas & Primary Use Cases
**Personas**
- **Contributor (primary):** edits or drafts docs via prompts; non-technical.
- **Power User (secondary):** uses precise anchors/IDs; expects reliability; semi-technical.
- **Reviewer/Manager (secondary):** wants redlines, history, rollbacks.

**Use Cases**
1. Draft a new engagement letter with headings and boilerplate.
2. Upload a `.docx`, then: "tighten section 2," "insert a 3×4 risks table under 'Risks'," "replace 'Foo Ltd' with 'Bar LLC'."
3. Copy an **anchor ID** from the outline and request: "insert paragraph after `h2-abc1234…`."
4. Download updated doc and **redline compare** vs a prior version.

---

## 4) Core Requirements
### 4.1 Functional (F)
- **F1 Create/Upload**: Create a new `.docx` from title/body; upload existing `.docx`.
- **F2 Plan Ops**: Given free‑text instruction, return **operations[]** (LLM tool calling or heuristic fallback).
- **F3 Apply Ops**: Execute ops server‑side with `python-docx`.
- **F4 Outline**: Return **stable paragraph IDs** with text & heading level; update after edits.
- **F5 Anchors**: Support `after_paragraph_id` to insert precisely after any paragraph/heading.
- **F6 Preview**: Client-side HTML preview via Mammoth.js (structure‑first, styling approximate).
- **F7 Versioning**: Snapshot versions on each apply.
- **F8 Redline Compare**: Generate a **visual** redline `.docx` (inserts = green underline; deletions = red strike).
- **F9 Download**: Provide URLs for current doc, redline output.

### 4.2 Non‑Functional (N)
- **N1 Reliability**: Lossless file persistence; corrupted file rate ~0%. Rollback via versions.
- **N2 Performance**: 95th‑percentile apply‑ops < 3s for documents ≤ 200 pages / 5 MB; plan‑ops < 8s with LLM.
- **N3 Safety**: Only whitelisted ops are executed. No direct model file I/O.
- **N4 Security**: Auth (phase 2), RBAC, rate limiting, audit logs, encrypted-at-rest storage.
- **N5 Observability**: Structured logs, request IDs, op counts, planning latency, apply latency, error rates.
- **N6 Accessibility**: Keyboard navigable; color‑contrast safe for critical affordances.

---

## 5) User Stories (selected)
- As a contributor, I can **create** a doc and immediately **preview** it in the browser.
- As a user, I can **ask**: "replace 'Lorem' with 'Introduction'" and see the ops JSON before applying.
- As a power user, I can **copy an anchor** from the outline and target my insert precisely.
- As a reviewer, I can **download a redline** to see exactly what changed.
- As a user, I can **revert** by downloading an older version.

Acceptance criteria are listed per epic in **TASKS.md**.

---

## 6) System Design
### 6.1 Architecture
- **Frontend** (Vite + Vue + TS + Tailwind): single-page app. Panels: Create/Upload, Plan/Apply, Outline & Redline.
- **Backend** (FastAPI): REST endpoints; file storage; outline builder; op executor; versioning; redline composer.
- **LLM** (optional): OpenAI tool/function calling to produce `operations[]`.

### 6.2 Data Model (conceptual)
- **File**: `{ file_id, path, created_at, updated_at }`
- **Version**: stored under `storage/versions/{file_id}/vN.docx`
- **OutlineItem**: `{ paragraph_id, text, level }` where `paragraph_id` = hash(normalized_text + level + index)
- **Operation** (TS/JSON):
```ts
export type OpType = "add_heading" | "add_paragraph" | "replace_text" | "insert_table";
export interface Operation {
  type: OpType;
  text?: string;
  level?: number;                // add_heading
  after_paragraph_id?: string;   // precise anchor
  after_heading_text?: string;   // legacy fallback
  find?: string;                 // replace_text
  replace?: string;              // replace_text
  rows?: number; cols?: number;  // insert_table
  data?: string[][];             // insert_table
}
```

### 6.3 API (initial)
- `POST /api/create` → `{ file_id, download_url }`
- `POST /api/upload` (multipart) → `{ file_id, download_url }`
- `POST /api/plan-ops` → `{ operations[] }` (LLM tool call or heuristic)
- `POST /api/apply-ops` → `{ file_id, download_url, outline[] }`
- `GET /api/download/{file_id}` → `.docx`
- `GET /api/outline/{file_id}` → `OutlineItem[]`
- `GET /api/versions/{file_id}` → `{ versions: string[] }`
- `GET /api/redline?base_id=...&revised_id=...` → `{ file_id, download_url }`

### 6.4 Preview
- Mammoth.js renders client‑side HTML for original/updated docs; fidelity is structural (not pixel‑perfect).

### 6.5 Redline (visual)
- Build a new `.docx` that line‑diffs paragraphs; word‑level diff within changed lines.
- **Insertions**: green + underline; **deletions**: red + strikethrough.
- Future: optional SDK for native Track Changes.

---

## 7) Risks & Mitigations
- **Model hallucinations** → schema‑validated ops; small op set; refuse unknown ops.
- **Imprecise anchors** → stable paragraph IDs; copy‑to‑clipboard in UI; outline recompute after edits.
- **Preview mismatch** → note Mammoth limitations; download real `.docx` for final check.
- **Large docs** → cap size; stream uploads; graceful error messages.
- **Security** → server‑side validation; deny file‑system traversal; rate limits; audit.

---

## 8) Metrics (minimum set)
- Plan‑ops success rate, planning latency (p50/p95), apply‑ops latency (p50/p95).
- Redline generation success rate.
- % operations applied without manual fix.
- Weekly active editors; documents created; average ops/session.

---

## 9) Rollout & Compliance
- **Phased**: Internal dogfood → Pilot users → GA.
- **Compliance** (future): Data retention policy; user deletion; PII guidance.

---

## 10) Acceptance Criteria (v1)
- Can create/upload `.docx`, plan ops, apply ops, anchor inserts with `after_paragraph_id`, preview changes, download current doc, list versions, generate **redline**.
- Error handling: friendly messages for missing anchors, invalid ops, large files.
- Basic observability: request logs and coarse metrics.
