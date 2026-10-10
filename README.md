# HeadsUp

HeadsUp solves one problem: **you missed lectures, and the next lecture assumes you were there.**

You show up to lecture 11. The professor writes an equation on the board and says "as we saw last
week" — except last week is the lecture you skipped, and the week before that too. You have two
hours before class. What is the *minimum* you need to understand to follow along?

That minimum is not "everything from the missed lectures." It is the specific chain of concepts the
upcoming lecture actually depends on, taught in dependency order, fitted to the time you have.

## Status: Stage 1 of 8 (foundation)

Stage 1 delivers the persistent course/lecture model and the UI to track where you stand.
**The knowledge bridge engine does not exist yet** — it is Stage 5, the most important stage.
Nothing in this repository should be read as a working product claim.

| Stage | Scope | Status |
| ----- | ----- | ------ |
| 1 | Course/lecture model, status tracking, position summary, basic UI | **Done** |
| 2 | Material ingestion + extraction | Not started |
| 3 | Concept extraction + explicit dependency graph | Not started |
| 4 | Student knowledge-state tracking | Not started |
| 5 | **Minimum knowledge bridge algorithm** | Not started |
| 6 | Time-budget-aware heads-up | Not started |
| 7 | Readiness checks + polish | Not started |
| 8 | Testing/reliability/docs/deployment hardening | Not started |

## Why a generic AI chatbot isn't the answer

Asking an AI to "summarize the missed lectures" fails in a specific, predictable way:

- **Completeness, not continuity.** A summary covers everything in the material. A student walking
  into the next lecture doesn't need everything — they need the dependency chain of that lecture.
- **No persistent state.** A chatbot doesn't know which lectures you understood, which you missed,
  or what's coming next. Every conversation starts from zero.
- **No ordering guarantee.** Understanding "TCP Congestion Control" requires "Reliable Data
  Transfer" *first*. Summaries have no notion of what must be learned before what.
- **No time-budget semantics.** "Explain it in 5 minutes" is not the same knowledge as "explain it
  in 20" with the hard parts shortened. The content itself must change with the budget.

HeadsUp keeps the narrow claim: persistent course continuity plus automatic minimum-prerequisite
determination. It is not a general tutor, and it does not try to be.

## Core insight

The bridge is a graph computation, not a generation task:

```
required = prerequisite_closure(upcoming lecture's concepts)
known    = concepts from lectures marked UNDERSTOOD
bridge   = required − known, ordered by the dependency graph
```

Everything deterministic (statuses, ordering, closure, subtraction, time allocation) stays in
application code and is unit-testable without any AI system. LLMs are used only where language
understanding is genuinely required (extracting concepts, proposing prerequisite edges, generating
explanations) — and their proposals are stored as *evidence-backed, reviewable* graph data, never
consumed blindly.

## How it works (Stage 1)

1. Create a course and add lectures in the order the course teaches them.
2. Mark each lecture: **Understood**, **Missed**, **Upcoming**, or leave it unmarked.
3. HeadsUp derives your position server-side:
   - *Understood through* — the highest-numbered understood lecture (your knowledge frontier).
   - *Preparing for* — the single lecture marked Upcoming.
   - *Missed* — the gap between the frontier and the upcoming lecture. Missed lectures after the
     upcoming one are out of scope.
   - *Unmarked before upcoming* — surfaced explicitly, because an unmarked lecture is treated as
     **not known**, never silently as known.
4. The *Get me ready* action is a visible placeholder until Stage 5 ships the bridge.

## Architecture

```
frontend/          React + Vite + TypeScript, Tailwind CSS, react-router
  src/api/         typed API client (fetch wrapper, no framework)
  src/components/  SituationPanel, LectureRow, AddLectureForm, GetReadyCard
  src/pages/       CoursesPage, CoursePage
  src/test/        vitest + Testing Library component tests

backend/           Python + FastAPI + SQLAlchemy 2 + Alembic
  app/models/      Course, Lecture (status enum), shared base
  app/schemas/     pydantic v2 request/response models incl. derived CourseSummary
  app/services/    domain logic; summary.py is a pure function (no DB, no I/O)
  app/api/         thin route layer
  alembic/         schema migrations
  scripts/         seed_demo.py
```

Design rules:

- **Deterministic vs LLM separation.** Stage 1 is 100% deterministic. Later stages must keep
  graph storage, closure, ordering, and budget allocation in application code; LLM output only
  ever enters as extracted, evidence-tagged data.
- **One upcoming lecture per course**, enforced by the service layer (marking a new upcoming
  lecture unmarks the previous one).
- **Derived, not stored.** The student's position is computed from statuses on every read
  (`app/services/summary.py`), so it can never drift out of sync.
- **Postgres-ready, SQLite-capable.** Configure via `DATABASE_URL`. A `docker-compose.yml` ships a
  Postgres 16 instance; without Docker, the default SQLite file database works with zero setup.
- **Deliberately excluded:** chat, flashcards, generic summaries, quizzes, planners, calendars,
  social, gamification. If a feature doesn't improve understanding of the *next* lecture, it
  doesn't go in.

## The bridge algorithm (Stage 5, not yet implemented)

The algorithm this codebase is built toward:

1. Take the upcoming lecture's concepts (Stage 3 graph).
2. Compute the prerequisite closure over the explicit dependency graph.
3. Subtract every concept already covered by understood lectures (Stage 4 knowledge state).
4. Order the remainder by the dependency graph (roots first).
5. Allocate the student's chosen time budget (2/5/10/20 min) — changing *what* is taught, not just
   compressing it; uncertain dependencies are handled conservatively and labeled as such.

The invariant the tests will enforce: if L1 introduced A; L2 introduced B (depends on A) and C
(depends on A); L3 teaches D (depends on B) — and the student understood L1, missed L2, and L3 is
upcoming — the bridge is **B only, not B and C**.

## Setup

Prerequisites: Python 3.12+, Node 20+.

```bash
# Backend
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt   # on Windows
# .venv/bin/pip install -r requirements-dev.txt     # on macOS/Linux
cp .env.example .env
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

# Optional demo data (understood L1-8, missed L9-10, upcoming L11)
.venv/Scripts/python.exe scripts/seed_demo.py
```

```bash
# Frontend
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to :8000
```

PostgreSQL instead of SQLite: start `docker compose up -d` and set
`DATABASE_URL=postgresql+psycopg://headsup:headsup@localhost:5432/headsup` in `backend/.env`.

## Screenshots

<!-- TODO: replace with real screenshots after Stage 7 polish -->

- Course list — _placeholder_
- Course page with position panel and lecture statuses — _placeholder_
- Get-ready card with time budgets — _placeholder_

## Testing

```bash
# Backend (44 tests)
cd backend && .venv/Scripts/python.exe -m pytest
cd backend && .venv/Scripts/python.exe -m ruff check .

# Frontend (18 tests)
cd frontend && npx vitest run
cd frontend && npm run lint && npm run build
```

What Stage 1 tests cover:

- Course CRUD, list counts, validation.
- Lecture append/order, status updates, invalid input rejection.
- The **single-upcoming invariant** (a new upcoming lecture unmarks the old one).
- Delete with order renumbering under the unique `(course_id, order_index)` constraint.
- The pure position-derivation function: gap detection, missed-after-upcoming exclusion,
  unmarked-before-upcoming surfacing, no-upcoming behavior, unsorted input.
- UI: situation panel content, status-change flow, budget chips, confirm-guarded delete,
  empty-input guards, API error surfacing.
