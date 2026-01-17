from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import sqlite3

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
@app.post("/analyze-pr")
def analyze_pr(pr: PRRequest):
    risks = []
    suggestions = []

    pr_size = pr.additions + pr.deletions
    risk_score = 0

    if pr_size > 500:
        risks.append("Large PR size")
        suggestions.append("Consider splitting this PR")
        risk_score += 3

    if pr.changed_files > 10:
        risks.append("Touches many files")
        risk_score += 2

    if not pr.lint_passed:
        risks.append("Lint checks failed")
        suggestions.append("Fix lint issues")
        risk_score += 2

    health_delta = -risk_score

    conn.execute(
        "INSERT INTO repo_health VALUES (?, ?, ?, ?)",
        (
            pr.repo,
            datetime.utcnow().isoformat(),
            health_delta,
            ",".join(risks)
        )
    )
    conn.commit()

    summary = (
        f"This PR changes {pr.changed_files} files "
        f"with {pr.additions} additions and {pr.deletions} deletions."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "health_delta": health_delta
    }

@app.get("/health-history")
def health_history(repo: str):
    rows = conn.execute(
        "SELECT timestamp, score FROM repo_health WHERE repo = ?",
        (repo,)
    ).fetchall()

    return [{"timestamp": r[0], "score": r[1]} for r in rows]
