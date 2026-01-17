import sqlite3
import json
import os
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load .env automatically
load_dotenv()

app = FastAPI()

# -----------------------------------
# Config
# -----------------------------------
USE_AI = os.getenv("USE_AI", "1") == "1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-3-flash-preview")

# -----------------------------------
# Database setup
# -----------------------------------
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

# -----------------------------------
# Request model
# -----------------------------------
class PRRequest(BaseModel):
    repo: str
    pr_number: int
    author: str
    additions: int
    deletions: int
    changed_files: int
    diff: str
    lint_passed: bool

# -----------------------------------
# AI helper (OpenRouter)
# -----------------------------------
def run_ai_analysis(payload: PRRequest):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    prompt = f"""
You are a senior GitHub repository reviewer.

Analyze the pull request and return ONLY valid JSON.
No markdown. No explanations.

JSON schema:
{{
  "summary": string,            // concise explanation of what changed
  "risks": [string],            // potential reliability, security, or maintainability risks
  "suggestions": [string],      // actionable improvement suggestions
  "health_delta": number        // impact on repo health (-1.0 to +1.0)
}}

PR Context:
- Repo: {payload.repo}
- PR: #{payload.pr_number}
- Author: {payload.author}
- Additions/Deletions: +{payload.additions} / -{payload.deletions}
- Files changed: {payload.changed_files}
- Lint passed: {payload.lint_passed}

Diff:
{payload.diff}
"""

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content

# -----------------------------------
# API Endpoints
# -----------------------------------
@app.post("/analyze-pr")
def analyze_pr(payload: PRRequest):
    # -----------------------------------
    # AI-FIRST (with fallback)
    # -----------------------------------
    if USE_AI:
        try:
            ai_result = run_ai_analysis(payload)
            parsed = json.loads(ai_result)

            # Save basic health metric
            conn.execute(
                "INSERT INTO repo_health (repo, timestamp, score, reason) VALUES (?, ?, ?, ?)",
                (
                    payload.repo,
                    datetime.utcnow().isoformat(),
                    parsed.get("health_delta", 0),
                    ",".join(parsed.get("risks", [])),
                ),
            )
            conn.commit()

            return parsed
        except Exception as e:
            print("⚠️ AI failed, falling back to manual logic:", e)

    # -----------------------------------
    # FALLBACK: deterministic logic
    # -----------------------------------
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

    summary = f"Fallback analysis for {payload.repo} PR #{payload.pr_number}"

    score = -5 if risks else 0

    try:
        conn.execute(
            "INSERT INTO repo_health (repo, timestamp, score, reason) VALUES (?, ?, ?, ?)",
            (
                payload.repo,
                datetime.utcnow().isoformat(),
                score,
                ",".join(risks),
            ),
        )
        conn.commit()
    except Exception:
        pass

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "health_delta": score,
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health-history")
def health_history(repo: str):
    cur = conn.execute(
        "SELECT timestamp, score, reason FROM repo_health WHERE repo = ? ORDER BY timestamp DESC LIMIT 20",
        (repo,),
    )
    rows = [
        {"timestamp": r[0], "score": r[1], "reason": r[2]}
        for r in cur.fetchall()
    ]
    return {"repo": repo, "history": rows}
