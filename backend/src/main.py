import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Use pymongo to talk to MongoDB Atlas
import pymongo
from pymongo.errors import PyMongoError

app = FastAPI()

# ---- MongoDB setup ----
MONGODB_URI = os.environ.get("MONGODB_URI", "").strip()
MONGODB_DB = os.environ.get("MONGODB_DB", "ai_repo_supervisor")

mongo_client: Optional[pymongo.MongoClient] = None
repo_collection = None

# In-memory fallback if Mongo is not configured or unavailable (keeps behavior in demos)
_in_memory_history: List[Dict[str, Any]] = []

if MONGODB_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client[MONGODB_DB]
        repo_collection = db["repo_health"]
        # index to speed up history queries
        repo_collection.create_index([("repo", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
        print("Connected to MongoDB:", MONGODB_DB)
    except PyMongoError as e:
        # Log and fall back to in-memory storage
        print("Warning: could not connect to MongoDB, falling back to in-memory store:", str(e))
        mongo_client = None
        repo_collection = None
else:
    print("MONGODB_URI not set — using in-memory history (demo mode)")

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
def analyze_pr(payload: PRRequest):
    # Basic deterministic "analysis" for demo purposes
    risks: List[str] = []
    if not payload.lint_passed:
        risks.append("Lint failures detected")
    if len(payload.diff or "") > 5000:
        risks.append("Very large diff")
    if (payload.additions - payload.deletions) > 500:
        risks.append("Many additions")

    suggestions: List[str] = []
    if not payload.lint_passed:
        suggestions.append("Fix lint issues")
    if not risks:
        suggestions.append("Add unit tests for changed code")

    summary = f"Mock analysis for {payload.repo} PR #{payload.pr_number} — {'issues found' if risks else 'low risk'}"

    # Store history in MongoDB (or fallback) with a simple score and reason
    score = 0 if risks else 10
    reason = ",".join(risks)

    doc = {
        "repo": payload.repo,
        "timestamp": datetime.utcnow().isoformat(),
        "score": score,
        "reason": reason,
        "pr_number": payload.pr_number,
        "author": payload.author,
    }

    if repo_collection:
        try:
            repo_collection.insert_one(doc)
        except PyMongoError as e:
            # don't crash analysis on DB write failure
            print("Warning: failed to write to MongoDB:", str(e))
    else:
        # in-memory fallback
        _in_memory_history.append(doc)
        # keep list bounded for memory safety in long-running demos
        if len(_in_memory_history) > 1000:
            _in_memory_history.pop(0)

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "health_delta": -5 if risks else 0
    }

@app.get("/health")
def health():
    return {"status": "ok", "mongo": bool(repo_collection)}

@app.get("/health-history")
def health_history(repo: str):
    """
    Returns the most recent 20 health records for the given repo.
    """
    try:
        if repo_collection:
            cursor = repo_collection.find({"repo": repo}).sort("timestamp", pymongo.DESCENDING).limit(20)
            rows = [{"timestamp": r.get("timestamp"), "score": r.get("score"), "reason": r.get("reason"), "pr_number": r.get("pr_number")} for r in cursor]
        else:
            rows = [r for r in reversed(_in_memory_history) if r.get("repo") == repo][:20]
        return {"repo": repo, "history": rows}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="DB error")
