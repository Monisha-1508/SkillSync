from __future__ import annotations

from typing import NamedTuple


class ProjectEntry(NamedTuple):
    title: str
    summary: str
    tracks: tuple[str, ...]
    difficulty: str               # beginner | intermediate | advanced
    estimated_hours: int
    stack: tuple[str, ...]
    skills_practiced: tuple[str, ...]
    stretch_goal: str


PROJECT_BANK: list[ProjectEntry] = [
    # ---- foundation / early portfolio pieces --------------------------------
    ProjectEntry(
        "Personal expense tracker (CLI)",
        "A command-line tool that logs spends to a local file, tags them by category, "
        "and prints a month-end summary - the smallest possible project that still "
        "touches input handling, file I/O and basic data shaping.",
        ("foundation",), "beginner", 12,
        ("Python", "CSV/JSON file storage"),
        ("control flow and functions", "file handling", "basic data structures"),
        "Add a simple budget-vs-actual chart using a plotting library.",
    ),
    ProjectEntry(
        "Markdown notes organiser",
        "A small script that scans a folder of markdown notes, builds a tag index, "
        "and generates a single browsable index page - practical enough to actually "
        "keep using afterwards.",
        ("foundation",), "beginner", 10,
        ("Python or JavaScript", "Markdown parsing", "filesystem APIs"),
        ("string processing", "file handling", "basic web page generation"),
        "Add full-text search across all notes from the generated index page.",
    ),
    ProjectEntry(
        "Quiz engine with scoring",
        "A small quiz runner that reads questions from a JSON bank, shuffles them per "
        "run, scores the attempt and stores results - a miniature, honest version of "
        "the checkpoint engine this very platform runs on.",
        ("foundation", "aptitude"), "beginner", 14,
        ("Python or JavaScript", "JSON data files"),
        ("data modelling", "control flow", "basic persistence"),
        "Add a simple difficulty curve that picks harder questions after a streak of correct answers.",
    ),

    # ---- software development engineer / capgemini tech analyst -------------
    ProjectEntry(
        "Task board API with auth",
        "A REST API for a Trello-style task board - boards, lists, cards, and a login "
        "flow with hashed passwords and tokens. The single most common 'prove you can "
        "build a backend' brief, and for good reason: it touches every layer at once.",
        ("sde", "capgemini_tech", "full_stack"), "intermediate", 28,
        ("Python (FastAPI) or Node (Express)", "PostgreSQL or SQLite", "JWT auth"),
        ("REST API design", "relational data modelling", "authentication", "input validation"),
        "Add role-based permissions so a board can have owners, editors and viewers.",
    ),
    ProjectEntry(
        "URL shortener with click analytics",
        "A service that turns long URLs into short codes, redirects on the way back "
        "out, and keeps a running count of clicks by day and referrer - small surface "
        "area, but real concurrency and indexing questions hide inside it.",
        ("sde", "capgemini_tech"), "intermediate", 18,
        ("Python or Node", "Redis or SQL for lookups", "basic charting on the frontend"),
        ("API design", "caching strategy", "database indexing", "rate limiting"),
        "Add expiry dates and a QR code endpoint for each shortened link.",
    ),
    ProjectEntry(
        "Job-application tracker",
        "A small full-stack app to log applications, statuses and follow-up dates - "
        "useful on its own terms for anyone deep in a placement search, and a clean "
        "vertical slice through a database, an API and a UI.",
        ("sde", "capgemini_tech", "full_stack"), "intermediate", 30,
        ("React or Next.js frontend", "FastAPI or Express backend", "PostgreSQL"),
        ("CRUD design", "form handling", "state management", "deployment basics"),
        "Add a weekly digest email summarising upcoming follow-ups.",
    ),
    ProjectEntry(
        "Rate-limited notification service",
        "A background worker that batches and sends notifications (email or webhook) "
        "while respecting per-user rate limits and retrying failures with backoff - "
        "the unglamorous plumbing that real systems spend most of their code on.",
        ("sde", "capgemini_tech"), "advanced", 26,
        ("Python or Node", "a queue (Redis/RQ or BullMQ)", "a mock email/webhook target"),
        ("asynchronous processing", "retry and backoff design", "rate limiting", "logging and observability"),
        "Add a small dashboard showing delivery rates and recent failures.",
    ),
    ProjectEntry(
        "In-memory key-value store with persistence",
        "A scaled-down Redis: a TCP server that handles GET/SET/DEL plus expiry, "
        "snapshots itself to disk, and reloads on restart - the project that makes "
        "data structures and networking stop being separate subjects.",
        ("sde",), "advanced", 32,
        ("Go, Python or Rust", "raw sockets", "a simple binary or JSON snapshot format"),
        ("data structures", "networking basics", "concurrency", "serialization"),
        "Add a simple replication mode where a second instance mirrors the first.",
    ),

    # ---- full stack -----------------------------------------------------------
    ProjectEntry(
        "Recipe-sharing community site",
        "A full-stack app where users post recipes, rate others' and save favourites - "
        "ordinary on the surface, but it forces real decisions about images, search, "
        "pagination and who-can-edit-what.",
        ("full_stack", "capgemini_tech"), "intermediate", 32,
        ("React/Next.js", "Node or FastAPI backend", "PostgreSQL", "image upload to local/object storage"),
        ("component design", "REST integration", "search and filtering", "authorization rules"),
        "Add a weekly 'trending recipes' view computed from recent ratings and saves.",
    ),
    ProjectEntry(
        "Real-time collaborative whiteboard",
        "A small drawing surface where multiple browser tabs see each other's strokes "
        "live - the project that makes WebSockets, conflict handling and state sync "
        "click in a way no slide deck can.",
        ("full_stack", "sde"), "advanced", 30,
        ("React", "WebSocket server (Socket.IO or native ws)", "a shared canvas library or raw canvas API"),
        ("real-time communication", "client-server state sync", "event-driven design"),
        "Add session rooms so different groups can draw on separate boards.",
    ),
    ProjectEntry(
        "Personal portfolio with a content API",
        "A portfolio site backed by a tiny content API rather than hard-coded pages - "
        "projects, posts and skills live in a database and render through the same "
        "components, so adding new work later is a form submission, not a redeploy.",
        ("full_stack", "capgemini_tech"), "beginner", 20,
        ("Next.js or React", "a small backend (FastAPI/Express) or a headless CMS", "SQLite or PostgreSQL"),
        ("static and dynamic rendering", "API integration", "responsive layout"),
        "Add a small admin page to add or edit entries without touching the database directly.",
    ),

    # ---- data analyst ----------------------------------------------------------
    ProjectEntry(
        "Placement outcomes dashboard",
        "An analysis of a public or synthetic placement dataset - offers by branch, "
        "package bands, timing trends - finishing in an interactive dashboard that "
        "answers the three questions a placement cell actually asks.",
        ("data_analyst", "capgemini_tech"), "intermediate", 24,
        ("Python (pandas)", "SQL for the heavier joins", "Plotly/Streamlit or Power BI for the dashboard"),
        ("data cleaning", "exploratory analysis", "SQL querying", "dashboard design"),
        "Add a simple filter so a viewer can slice the dashboard by branch or year.",
    ),
    ProjectEntry(
        "City transit on-time performance report",
        "A study of a public transit dataset - which routes run late, when, and by "
        "how much - written up as a short report with charts that a non-technical "
        "reader could act on.",
        ("data_analyst",), "intermediate", 22,
        ("Python (pandas, matplotlib/seaborn)", "Jupyter notebook"),
        ("data wrangling", "statistical summarising", "visual storytelling"),
        "Add a simple model that flags routes likely to run late on a given weekday.",
    ),
    ProjectEntry(
        "A/B test result analyser",
        "A small toolkit that takes two groups of conversion data, runs the right "
        "significance test, and writes a plain-language verdict - the exact skill a "
        "data analyst uses weekly, built once, end to end, by hand.",
        ("data_analyst", "data_scientist"), "advanced", 20,
        ("Python (pandas, scipy)", "a small CLI or notebook front end"),
        ("statistical testing", "experiment design reasoning", "clear written reporting"),
        "Add a sample-size calculator so a user can plan the next test before running it.",
    ),

    # ---- data scientist ---------------------------------------------------------
    ProjectEntry(
        "House-price prediction with model comparison",
        "The classic regression brief done properly: clean a real dataset, try three "
        "different model families, and write up which one wins and why - not which "
        "one scored highest on a leaderboard nobody asked about.",
        ("data_scientist", "data_analyst"), "intermediate", 26,
        ("Python (pandas, scikit-learn)", "Jupyter notebook", "matplotlib for diagnostics"),
        ("feature engineering", "model selection", "evaluation metrics", "result communication"),
        "Add a simple Streamlit front end where someone can enter a property's details and get an estimate.",
    ),
    ProjectEntry(
        "Resume-to-role matcher (mini version)",
        "A scaled-down sibling of this very platform's gap-mapping engine: take a "
        "resume and a target role's skill list, score the overlap, and explain the "
        "biggest gaps in plain language - small enough to finish, real enough to matter.",
        ("data_scientist", "sde", "capgemini_tech"), "advanced", 30,
        ("Python", "a simple text-similarity approach (TF-IDF or embeddings)", "a small skill taxonomy file"),
        ("text processing", "similarity scoring", "explainable output design"),
        "Add a short narrated summary of the match using a template-based explainer, the same pattern this platform uses for trust.",
    ),
    ProjectEntry(
        "Sentiment tracker for product reviews",
        "A pipeline that pulls in a batch of product reviews, scores their sentiment, "
        "and tracks how the mood shifts over time - the kind of small, end-to-end NLP "
        "build that turns 'I took an NLP course' into 'I shipped something with it'.",
        ("data_scientist",), "intermediate", 22,
        ("Python", "a pretrained sentiment model or a simple trained classifier", "pandas for the time series view"),
        ("text preprocessing", "model application", "trend visualisation"),
        "Add topic tagging so the dashboard can show sentiment broken down by what people are actually complaining about.",
    ),

    # ---- aptitude / interview-adjacent ------------------------------------------
    ProjectEntry(
        "Spaced-repetition flashcard CLI",
        "A tiny command-line clone of the FSRS-style revision engine this platform "
        "runs - cards, intervals, a review loop - useful for studying anything else "
        "afterwards, and a hands-on tour of an algorithm that is normally just a "
        "library import.",
        ("aptitude", "foundation"), "beginner", 16,
        ("Python", "a local file or SQLite for storage"),
        ("algorithmic thinking", "scheduling logic", "persistence"),
        "Add a small stats view showing retention rate over the last 30 days.",
    ),
    ProjectEntry(
        "Mock group-discussion timer and notes app",
        "A small tool that times group-discussion rounds, prompts rotating speaking "
        "turns, and lets a moderator jot quick notes per participant - built for a "
        "real placement-prep group to actually use.",
        ("aptitude", "capgemini_tech"), "beginner", 12,
        ("React or plain JavaScript", "local storage for notes"),
        ("UI state management", "timers and intervals", "form handling"),
        "Add a simple scoring rubric so notes turn into a comparable summary at the end.",
    ),
]


def projects_for_tracks(tracks: set[str]) -> list[ProjectEntry]:
    scored = [(len(set(entry.tracks) & tracks), index, entry) for index, entry in enumerate(PROJECT_BANK)]
    matching = [(score, index, entry) for score, index, entry in scored if score > 0]
    matching.sort(key=lambda row: (-row[0], row[1]))
    return [entry for _, _, entry in matching]
