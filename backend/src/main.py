import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

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
    # Basic deterministic "analysis" for demo purposes
    risks = []
    if not payload.lint_passed:
        risks.append("Lint failures detected")
    if len(payload.diff or "") > 5000:
        risks.append("Very large diff")
    if (payload.additions - payload.deletions) > 500:
        risks.append("Many additions")

    suggestions = []
    if not payload.lint_passed:
        suggestions.append("Fix lint issues")
    if not risks:
        suggestions.append("Add unit tests for changed code")

    summary = f"Mock analysis for {payload.repo} PR #{payload.pr_number} — {'issues found' if risks else 'low risk'}"

    # Optional: record a simple health metric to sqlite
    try:
        score = 0 if risks else 10
        conn.execute(
            "INSERT INTO repo_health (repo, timestamp, score, reason) VALUES (?, ?, ?, ?)",
            (payload.repo, datetime.utcnow().isoformat(), score, ",".join(risks))
        )
        conn.commit()
    except Exception:
        # ignore DB errors in demo mode
        pass

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "health_delta": -5 if risks else 0
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health-history")
def health_history(repo: str):
    cur = conn.execute("SELECT timestamp, score, reason FROM repo_health WHERE repo = ? ORDER BY timestamp DESC LIMIT 20", (repo,))
    rows = [{"timestamp": r[0], "score": r[1], "reason": r[2]} for r in cur.fetchall()]
    return {"repo": repo, "history": rows}
