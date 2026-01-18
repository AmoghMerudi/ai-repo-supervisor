import os
import sqlite3
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from src.ai.analyze_pull_request import analyze_pull_request

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

app = FastAPI()

# ---- Database setup ----
conn = sqlite3.connect("health.db", check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS repo_health (
    repo TEXT,
    timestamp TEXT,
    score INTEGER,
    reason TEXT
)
""")
conn.commit()

# ---- Request model ----
class PRRequest(BaseModel):
    repo: str
    pr_number: int
    author: str
    additions: int
    deletions: int
    changed_files: int
    diff: str
    lint_passed: bool

# ---- API Endpoints ----

# Public analyze endpoint (NO authentication for hackathon/demo)
@app.post("/analyze-pr")
def analyze_pr(payload: PRRequest):
    result = analyze_pull_request(payload.dict())
    if DEMO_MODE:
        result["summary"] = (
            result["summary"]
            or "This pull request introduces focused, high-impact changes."
        )

        result.setdefault("structural_signals", [])
        result.setdefault("semantic_insights", [])
        result.setdefault(
            "synthesis",
            "This change alters core behavior; review the critical paths carefully.",
        )

        if not result.get("risks"):
            result["risks"] = [
                "No major risks detected, but changes affect core logic."
            ]

        if not result.get("suggestions"):
            result["suggestions"] = [
                "Consider a quick manual review of the modified logic."
            ]

    # Optional: record a simple health metric to sqlite
    try:
        score = 0 if result.get("risks") else 10
        conn.execute(
            "INSERT INTO repo_health (repo, timestamp, score, reason) VALUES (?, ?, ?, ?)",
            (
                payload.repo,
                datetime.utcnow().isoformat(),
                score,
                ",".join(result.get("risks", [])),
            ),
        )
        conn.commit()
    except Exception:
        # ignore DB errors in demo mode
        pass

    return result

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health-history")
def health_history(repo: str):
    cur = conn.execute("SELECT timestamp, score, reason FROM repo_health WHERE repo = ? ORDER BY timestamp DESC LIMIT 20", (repo,))
    rows = [{"timestamp": r[0], "score": r[1], "reason": r[2]} for r in cur.fetchall()]
    return {"repo": repo, "history": rows}
