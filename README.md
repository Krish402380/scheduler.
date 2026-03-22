# Mnemo — Knowledge Decay Tracker

> You don't forget things all at once. You forget them gradually, silently, until they're gone. Mnemo makes that process visible.

---

## What It Is

Mnemo is a personal knowledge retention system built for students who study complex, interconnected material. It tracks every concept you engage with, computes how much of it you're likely to retain right now, and surfaces what's fading before it's fully gone.

It doesn't generate flashcards. It doesn't quiz you. It gives you a live map of your knowledge state — and tells you where to look.

---

## The Core Idea: Knowledge Decay

Human memory follows an exponential decay curve. Retention drops after every study session and the rate of that drop depends on how well you understood the material in the first place.

Mnemo models this with the following formula:

```
retention = confidence_weight × e^(−λ × days_elapsed)
```

| Variable | Meaning |
|---|---|
| `confidence_weight` | Your self-rated understanding after the last session (1–5, normalized) |
| `λ` (lambda) | Decay constant — scales inversely with confidence. Weak topics decay faster. |
| `days_elapsed` | Days since you last logged a session on this topic |

This score is computed live on every request — never stored, always fresh. The result is a number between 0 and 100 that represents your estimated current retention for each topic.

---

## Features

### Decay Dashboard
The main screen. A card grid of all your tracked topics sorted by urgency — most decayed at the top. Each card shows the current decay score as a circular progress ring, days since last session, and your last confidence rating. Color signals state: green is fresh, amber is fading, red is critical.

A 60-day activity heatmap sits at the top of the dashboard — identical grammar to a GitHub contribution graph. Intensity maps to total study time per day.

### Session Logger
A fast-entry panel accessible from anywhere in the app. Log a topic, duration, confidence rating (1–5), and an optional note. Designed to take under 30 seconds — because if logging is slow, you won't do it.

### Decay Graph
Per-topic view. A line chart of retention over time with session events marked as upward inflection points. Shows you exactly when you studied something, how retention recovered, and how quickly it degraded afterward.

### Review Queue
Auto-generated list of topics that need attention. Sorted by decay score. Directly actionable — click any item to open the session logger pre-filled with that topic.

### Quick Reference Panel
A pinnable surface for formulas, mnemonics, and reference material you look up repeatedly. Not a notes app — a fast-access panel that keeps you inside the tool instead of switching tabs.

### Search
Full-text search across topics and session notes. Returns results inline without a page transition. The primary anti-context-switch feature.

---

## Tech Stack

### Frontend — Next.js + Tailwind CSS
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Auth**: Auth.js v5 (JWT-based, single user)
- **Charts**: Recharts — decay graphs and heatmap
- **State**: React state + SWR for server data fetching

The UI is dark glassmorphism — deep near-black backgrounds, frosted glass card surfaces via `backdrop-filter: blur()`, luminous borders, and a functional color system where color encodes decay state, not decoration.

### Backend — FastAPI + PostgreSQL
- **API**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: Prisma (via Prisma Client Python or a JS adapter depending on setup)
- **Search**: PostgreSQL full-text search (no external service)
- **Decay Engine**: Pure Python module — isolated from routing and database layers, independently tunable

The backend's primary responsibility is computing and serving accurate decay state on demand. The decay formula runs server-side on every topic fetch. The frontend receives derived state, not raw session history.

### Auth Flow
Auth.js v5 handles authentication at the Next.js layer. The JWT is forwarded to FastAPI on every protected request, validated there, and scoped to the requesting user's data.

---

## Data Model

### Topic
A single concept node — the atomic unit of the knowledge graph.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | string | Concept name |
| `subject` | string | Parent subject |
| `unit` | string | Unit within subject |
| `created_at` | timestamp | Creation date |

### Session
A study event — the only thing you actively input.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `topic_id` | UUID | Foreign key → Topic |
| `date` | date | Session date |
| `duration_minutes` | int | Duration |
| `confidence` | int | Self-rated understanding (1–5) |
| `notes` | text | Optional notes |

### Decay State (computed)
Not stored. Derived from the session history of a topic on every request.

| Output | Description |
|---|---|
| `score` | Current retention (0–100) |
| `days_since_last_session` | Days elapsed since most recent session |
| `status` | `fresh` / `fading` / `critical` — derived from score thresholds |

---

## Decay Constants

Default λ values by confidence rating:

| Confidence | λ | Approximate half-life |
|---|---|---|
| 5 | 0.05 | ~14 days |
| 4 | 0.07 | ~10 days |
| 3 | 0.10 | ~7 days |
| 2 | 0.14 | ~5 days |
| 1 | 0.20 | ~3.5 days |

These are stored as user-level settings and configurable without a code change.

---

## Project Structure

```
mnemo/
├── frontend/
│   ├── app/
│   │   ├── dashboard/         # Main decay dashboard
│   │   ├── topic/[id]/        # Per-topic decay graph + history
│   │   ├── log/               # Session logger
│   │   └── search/            # Full-text search
│   ├── components/
│   │   ├── DecayCard.tsx
│   │   ├── DecayGraph.tsx
│   │   ├── ActivityHeatmap.tsx
│   │   ├── SessionLogger.tsx
│   │   └── QuickReference.tsx
│   └── lib/
│       └── api.ts             # FastAPI client
│
├── backend/
│   ├── main.py                # FastAPI entrypoint
│   ├── routers/
│   │   ├── topics.py
│   │   ├── sessions.py
│   │   └── decay.py
│   ├── models/
│   │   └── schema.py
│   └── core/
│       └── decay_engine.py    # Isolated decay computation module
│
└── prisma/
    └── schema.prisma
```

---

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

### Database

```bash
npx prisma migrate dev
npx prisma generate
```

---

## Environment Variables

### Frontend (`.env.local`)
```
NEXTAUTH_SECRET=
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (`.env`)
```
DATABASE_URL=postgresql://user:password@localhost:5432/mnemo
JWT_SECRET=
```

---

## Design Philosophy

**Color is functional, not decorative.** The green-amber-red spectrum on decay cards communicates urgency at a glance. No additional interpretation required.

**Logging must be frictionless.** If the session logger takes more than 30 seconds, the data quality degrades. The entire UX is designed around minimizing entry cost.

**The decay formula must feel right.** If topics go critical too fast, the system creates anxiety and gets ignored. If too slow, it gives false confidence. Tune λ values after a week of real use — that's what the settings page is for.

---

## Roadmap

- [ ] Multi-subject support with custom λ per subject
- [ ] Export session history as CSV
- [ ] Weekly review digest (email or in-app)
- [ ] Topic dependency graph — mark prerequisites, propagate decay signals
- [ ] Offline support via PWA

---

## License

MIT
