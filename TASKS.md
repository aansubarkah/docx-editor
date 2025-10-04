# TASKS.md — Epics & Backlog

## Epic A — Backend Core
- **A‑01 Outline builder**: compute `{paragraph_id,text,level}`; persist after each apply.
  - *Acceptance*: `GET /api/outline/{file_id}` returns stable IDs; IDs persist across no‑op apply.
- **A‑02 Anchor insertions**: support `after_paragraph_id` for `add_heading`, `add_paragraph`, `insert_table`.
  - *Acceptance*: Inserting after a given anchor places content at `anchor+1` index.
- **A‑03 Replace text**: simple string replace per paragraph.
  - *Acceptance*: Exact matches replaced; no side effects on other paragraphs.
- **A‑04 Versioning**: snapshot `vN.docx` after each apply; list versions.
  - *Acceptance*: `GET /api/versions/{file_id}` returns increasing `vN`.
- **A‑05 Redline compare (visual)**: line + word diff; generate `.docx` with colored styles.
  - *Acceptance*: Insertions visible (green underline); deletions visible (red strike); works for typical docs.
- **A‑06 Validation**: schema validation for `Operation[]`; unknown ops rejected; size limits.
  - *Acceptance*: 400 with helpful message on invalid ops/oversized files.

## Epic B — Frontend (Vite + Vue + TS + Tailwind)
- **B‑01 Typed schema**: `types.ts` for `Operation`, `OutlineItem`.
  - *Acceptance*: Type‑checked usage across components; build passes.
- **B‑02 Outline panel**: list items; copy anchor to clipboard.
  - *Acceptance*: Clicking ID copies to clipboard; visual hierarchy by level.
- **B‑03 Plan → Apply flow**: textarea → plan ops (LLM or heuristic) → show JSON → apply.
  - *Acceptance*: Operations show as JSON; apply updates doc; outline refreshes.
- **B‑04 Redline UI**: choose base+revised; generate & download.
  - *Acceptance*: Button returns redline `.docx` link; handles errors gracefully.
- **B‑05 Preview UX**: keep Mammoth preview note; show toasts/spinners; error banners.
  - *Acceptance*: Clear UX states for loading/errors; accessible to keyboard users.

## Epic C — LLM Orchestration
- **C‑01 Tool schema**: expose `propose_operations` with the typed parameters.
  - *Acceptance*: Model emits valid `operations[]`; unknown fields ignored server‑side.
- **C‑02 Prompt guardrails**: system message restricting to tool calls; refuse free‑form edits.
  - *Acceptance*: Non‑tool replies are rejected and retried; logs show reason.
- **C‑03 Fallback heuristic**: basic replace/append when key absent.
  - *Acceptance*: Heuristic returns at least one valid op for common instructions.

## Epic D — Security & Observability
- **D‑01 Request validation**: strict Pydantic models; length caps.
- **D‑02 Rate limiting** (basic): IP/user caps on plan/apply.
- **D‑03 Logging/Metrics**: request IDs, latency, error codes, op counts.
- **D‑04 Audit events**: who did what (create/upload/apply/redline).

## Epic E — Pilot Readiness
- **E‑01 Minimal Auth**: email‑magic link or demo password.
- **E‑02 Bug triage**: severity labels & SLAs for pilot period.
- **E‑03 Feedback loop**: in‑app link to form; tag sessions with consent.

## Icebox / Future
- Native **Track Changes** authoring via commercial SDK adapter.
- Image insertion, headers/footers, style controls, page breaks.
- RTF/PDF input, export to PDF.
- Multi‑tenant storage on S3/GCS, signed URLs.
- Doc outline tree with drag‑to‑reorder sections.

## Task Matrix (sample)
| ID | Task | Epic | Depends | Est. | Owner | Acceptance |
|---|---|---|---|---|---|---|
| A‑01 | Outline builder | A | — | 3 | TBA | Returns stable IDs; persisted |
| A‑02 | Anchor insertions | A | A‑01 | 5 | TBA | Inserts after anchor |
| A‑03 | Replace text | A | — | 2 | TBA | Paragraph‑level replace works |
| A‑04 | Versioning | A | — | 2 | TBA | vN snapshots list correctly |
| A‑05 | Redline compare | A | A‑04 | 5 | TBA | Visual diffs in `.docx` |
| B‑01 | Typed schema | B | — | 1 | TBA | TS build passes |
| B‑02 | Outline panel | B | B‑01 | 2 | TBA | Copy anchor works |
| B‑03 | Plan→Apply flow | B | B‑01 | 3 | TBA | Ops apply & refresh |
| B‑04 | Redline UI | B | B‑03,A‑05 | 2 | TBA | Download link works |
| C‑01 | Tool schema | C | A‑01 | 2 | TBA | Valid ops from LLM |
| C‑02 | Prompt guardrails | C | C‑01 | 2 | TBA | Non‑tool replies rejected |
| D‑01 | Validation | D | A‑03 | 2 | TBA | 400 on invalid ops |
| D‑03 | Logging/Metrics | D | — | 2 | TBA | p50/p95 dashboards |
| E‑01 | Minimal Auth | E | D‑01 | 3 | TBA | Login gate in front |

> *Est.* are rough story‑points; adjust in sprint planning.
