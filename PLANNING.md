# PLANNING.md — Delivery Plan (Q4 2025)

> Assumes today is Oct 4, 2025 (Asia/Makassar). Adjust dates as needed.

## Milestones
- **M0 – Repo & Scaffolding (done):** MVP + v2 code scaffolds.
- **M1 – Anchor & Outline (Oct 6–Oct 17)**: Stable paragraph IDs, outline endpoint, anchor inserts.
- **M2 – Redline (Oct 13–Oct 24)**: Visual redline compare & download.
- **M3 – Frontend Vite+TS (Oct 6–Oct 24)**: Typed op schema, outline panel, redline UI, polish.
- **M4 – Hardening (Oct 27–Nov 7)**: Validation, limits, errors, observability, basic auth.
- **M5 – Pilot (Nov 10–Nov 21)**: Pilot with 5–10 users; fix critical issues; GA decision.

> M1–M3 run partially in parallel.

## Workstreams
1) **Backend Core**: ops, outline, redline, versions, validation.
2) **Frontend**: typed schema, outline UX, anchors, redline trigger, previews.
3) **LLM Orchestration**: tool schemas, prompt hardening, fallback heuristics.
4) **Security/Infra**: auth (basic), rate limits, storage, logs/metrics.
5) **QA**: unit/integration/E2E; example docs; regression suite.

## Deliverables per Milestone
- **M1**: `GET /api/outline/{file_id}` stable IDs; `after_paragraph_id` respected by all inserts; tests.
- **M2**: `GET /api/redline` returns downloadable `.docx`; diff covers line + word levels; tests.
- **M3**: Vite app with typed `Operation`; outline panel (copy anchor); plan/apply flow; helpful toasts.
- **M4**: Request validation, size limits, error UX; minimal auth; logs/metrics dashboard sketch.
- **M5**: Pilot plan, feedback form, bug triage, go/no‑go.

## QA Strategy
- **Unit**: op functions, outline builder, ID stability, diff composer.
- **Integration**: plan→apply roundtrip; multi-op sequences; large file bounds.
- **E2E**: create → plan → apply → download → redline (smoke test); cross‑browser.

## Risks & Mitigations
- **Anchor drift**: IDs recomputed; copyable anchors; document outline visible; add "insert after heading text" fallback.
- **Heuristic planning w/o LLM key**: Keep minimal rules; highlight limitation in UI.
- **Large docs**: cap & warn; streaming uploads later.
- **Security**: strict schema validation; sanitize inputs; rate limits.

## Analytics Plan
- Capture: plan/apply latencies; op types; success/error codes; redline attempts; downloads.
- Dashboard: p50/p95 latencies; success rates; DAU/WAU; ops/session.
