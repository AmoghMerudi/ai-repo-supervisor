import os
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError

# Use pymongo to talk to MongoDB Atlas
import pymongo
from pymongo.errors import PyMongoError
from pymongo.collection import Collection
from pymongo import ReturnDocument

app = FastAPI()

# ---- MongoDB setup ----
MONGODB_URI = os.environ.get("MONGODB_URI", "").strip()
MONGODB_DB = os.environ.get("MONGODB_DB", "ai_repo_supervisor")

mongo_client: Optional[pymongo.MongoClient] = None
repo_collection: Optional[Collection] = None
repo_summary: Optional[Collection] = None

# In-memory fallback if Mongo is not configured or unavailable (keeps behavior in demos)
_in_memory_history: List[Dict[str, Any]] = []
_in_memory_summary: Dict[str, Dict[str, Any]] = {}  # keyed by repo

RECENT_LIMIT = 20  # keep last N PRs in summary.recent
INITIAL_REPO_HEALTH = 100  # base health for new repos

if MONGODB_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client[MONGODB_DB]
        repo_collection = db["repo_health"]
        repo_summary = db["repo_summary"]
        # indexes
        repo_collection.create_index([("repo", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
        repo_summary.create_index([("repo", pymongo.ASCENDING)], unique=True)
        print("Connected to MongoDB:", MONGODB_DB)
    except PyMongoError as e:
        print("Warning: could not connect to MongoDB, falling back to in-memory store:", str(e))
        mongo_client = None
        repo_collection = None
        repo_summary = None
else:
    print("MONGODB_URI not set — using in-memory history (demo mode)")

# ---- Request model ----
class PRRequest(BaseModel):
    repo: str
    pr_number: int = 0
    author: str = "unknown"
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    diff: str = ""
    lint_passed: bool = True

    class Config:
        extra = "ignore"  # ignore unexpected fields, don't fail with 422

# ---- Helper functions for summary maintenance ----
def _update_in_memory_summary_with_doc(doc: Dict[str, Any]) -> None:
    repo = doc["repo"]
    s = _in_memory_summary.setdefault(
        repo,
        {
            "repo": repo,
            "total_prs": 0,
            "cumulative_score": 0,
            "avg_score": 0.0,
            "current_health": INITIAL_REPO_HEALTH,
            "last": None,
            "recent": [],
            "updated_at": None,
        },
    )

    pr_score = int(doc.get("pr_score", doc.get("score", 0)))
    health_delta = int(doc.get("health_delta", 0))

    s["total_prs"] += 1
    s["cumulative_score"] += pr_score
    s["avg_score"] = s["cumulative_score"] / s["total_prs"] if s["total_prs"] else 0.0

    # apply delta to current health
    s["current_health"] = s.get("current_health", INITIAL_REPO_HEALTH) + health_delta

    s["last"] = {"pr_number": doc.get("pr_number"), "score": pr_score, "author": doc.get("author"), "timestamp": doc.get("timestamp"), "overall_health": s["current_health"]}
    s["recent"].insert(0, {"pr_number": doc.get("pr_number"), "score": pr_score, "timestamp": doc.get("timestamp"), "author": doc.get("author"), "overall_health": s["current_health"]})
    if len(s["recent"]) > RECENT_LIMIT:
        s["recent"].pop()
    s["updated_at"] = datetime.utcnow().isoformat()

def _update_repo_summary(doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Atomically upsert/aggregate per-repo summary in repo_summary collection using an
    aggregation-pipeline update without unsupported stages like $setOnInsert.
    Returns the updated summary document or None on failure.
    """
    if repo_summary is None:
        return None

    repo = doc["repo"]
    pr_score = int(doc.get("pr_score", doc.get("score", 0)))
    health_delta = int(doc.get("health_delta", 0))
    pr_number = doc.get("pr_number")
    author = doc.get("author")
    ts = doc.get("timestamp", datetime.utcnow().isoformat())

    # small helper doc inserted into recent
    new_recent_item = {
        "pr_number": pr_number,
        "score": pr_score,
        "timestamp": ts,
        "author": author,
        "overall_health_delta": health_delta,
    }

    try:
        # Aggregation-pipeline update using only supported stages/operators.
        pipeline_update = [
            {
                "$set": {
                    # ensure repo field exists
                    "repo": {"$ifNull": ["$repo", repo]},
                    # increment counters safely even if document absent
                    "total_prs": {"$add": [{"$ifNull": ["$total_prs", 0]}, 1]},
                    "cumulative_score": {"$add": [{"$ifNull": ["$cumulative_score", 0]}, pr_score]},
                    # initialize current_health from INITIAL_REPO_HEALTH if missing, then add delta
                    "current_health": {"$add": [{"$ifNull": ["$current_health", INITIAL_REPO_HEALTH]}, health_delta]},
                    # last-* fields set to current PR values
                    "last_score": pr_score,
                    "last_pr_number": pr_number,
                    "last_author": author,
                    "last_timestamp": ts,
                    "updated_at": datetime.utcnow().isoformat(),
                    # prepend new_recent_item and keep RECENT_LIMIT
                    "recent": {
                        "$slice": [
                            {"$concatArrays": [[new_recent_item], {"$ifNull": ["$recent", []]}]},
                            RECENT_LIMIT,
                        ]
                    },
                    # keep avg_score computed after update (separate write below)
                }
            }
        ]

        res = repo_summary.find_one_and_update(
            {"repo": repo},
            pipeline_update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        if res:
            total = res.get("total_prs", 0)
            cumulative = res.get("cumulative_score", 0)
            avg = (cumulative / total) if total else 0.0
            # ensure avg_score is set
            repo_summary.update_one({"repo": repo}, {"$set": {"avg_score": avg}})
            # return the latest doc
            res = repo_summary.find_one({"repo": repo})
            return res

        return None
    except PyMongoError as e:
        print("Warning: failed to update repo_summary:", str(e))
        return None

def _coerce_payload(payload_raw: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce common field types from strings to expected types."""
    p = dict(payload_raw)  # shallow copy
    # ints
    for key in ("pr_number", "additions", "deletions", "changed_files"):
        if key in p:
            try:
                p[key] = int(p[key])
            except Exception:
                # leave default handling to Pydantic, but ensure not None
                p[key] = p.get(key, 0)
    # lint_passed truthy strings
    if "lint_passed" in p:
        v = p["lint_passed"]
        if isinstance(v, str):
            p["lint_passed"] = v.lower() in ("1", "true", "yes", "y", "t")
        else:
            p["lint_passed"] = bool(v)
    return p

# ---- API Endpoints ----

@app.post("/analyze-pr")
async def analyze_pr(request: Request):
    # Accept raw JSON and validate/coerce to avoid 422 on client mistakes.
    try:
        payload_json = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    if not isinstance(payload_json, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")

    # attempt coercion of common types then validate with pydantic
    coerced = _coerce_payload(payload_json)
    try:
        payload = PRRequest.parse_obj(coerced)
    except ValidationError as e:
        # return helpful 400 with validation errors instead of 422
        raise HTTPException(status_code=400, detail=f"Invalid request payload: {e}")

    # now proceed with analysis logic (protected with general try/except to avoid 500 on unexpected errors)
    try:
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

        summary_text = f"Mock analysis for {payload.repo} PR #{payload.pr_number} — {'issues found' if risks else 'low risk'}"

        # pr_score: descriptive metric stored per-PR; health_delta: signed impact (policy)
        pr_score = 0 if risks else 10
        health_delta = -5 if risks else 0
        reason = ",".join(risks)

        # create base doc (we will attach overall_health shortly)
        doc: Dict[str, Any] = {
            "repo": payload.repo,
            "timestamp": datetime.utcnow().isoformat(),
            "score": pr_score,          # legacy field kept
            "pr_score": pr_score,       # explicit per-PR score
            "reason": reason,
            "pr_number": payload.pr_number,
            "author": payload.author,
            "additions": payload.additions,
            "deletions": payload.deletions,
            "changed_files": payload.changed_files,
            "health_delta": health_delta,
        }

        # Update summary first to compute new current_health atomically (if DB is available)
        new_summary_doc = None
        wrote_to_db = False
        if repo_summary is not None:
            new_summary_doc = _update_repo_summary(doc)
        else:
            # in-memory summary update will compute current_health
            _update_in_memory_summary_with_doc(doc)
            new_summary_doc = _in_memory_summary.get(doc["repo"])

        # overall_health should reflect the updated current_health after applying this PR
        overall_health = None
        if new_summary_doc is not None:
            overall_health = new_summary_doc.get("current_health") if isinstance(new_summary_doc, dict) else None
            if overall_health is None:
                overall_health = new_summary_doc.get("current_health", INITIAL_REPO_HEALTH) if isinstance(new_summary_doc, dict) else INITIAL_REPO_HEALTH
        else:
            # fallback: use in-memory summary if available
            s = _in_memory_summary.get(doc["repo"])
            overall_health = s.get("current_health") if s else INITIAL_REPO_HEALTH

        doc["overall_health"] = overall_health

        # Now insert PR doc into repo_health if collection available
        if repo_collection is not None:
            try:
                repo_collection.insert_one(doc)
                wrote_to_db = True
            except PyMongoError as e:
                print("Warning: failed to write PR doc to MongoDB, falling back to in-memory:", str(e))
                _in_memory_history.append(doc)
                if len(_in_memory_history) > 1000:
                    _in_memory_history.pop(0)
        else:
            _in_memory_history.append(doc)
            if len(_in_memory_history) > 1000:
                _in_memory_history.pop(0)

        # Return analysis including health_score_impact
        return {
            "summary": summary_text,
            "risks": risks,
            "suggestions": suggestions,
            "health_score_impact": health_delta,
            "health_delta": health_delta,
            "pr_score": pr_score,
            "overall_health": overall_health,
        }
    except Exception:
        # Log stack for debugging, but return safe 500 response
        print("Unhandled error in /analyze-pr:", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

@app.get("/health")
async def health():
    return {"status": "ok", "mongo": repo_collection is not None}

@app.get("/health-history")
async def health_history(repo: str, limit: int = 20):
    """
    Returns the most recent `limit` health records for the given repo.
    Each record now contains overall_health (repo health at the time of that PR).
    """
    try:
        if repo_collection is not None:
            try:
                cursor = repo_collection.find({"repo": repo}).sort("timestamp", pymongo.DESCENDING).limit(limit)
                rows = [
                    {
                        "timestamp": r.get("timestamp"),
                        "pr_number": r.get("pr_number"),
                        "pr_score": r.get("pr_score", r.get("score")),
                        "health_delta": r.get("health_delta", 0),
                        "overall_health": r.get("overall_health"),
                        "reason": r.get("reason"),
                    }
                    for r in cursor
                ]
            except PyMongoError as e:
                print("Warning: error querying MongoDB:", str(e))
                raise HTTPException(status_code=500, detail="DB query error")
        else:
            rows = [
                {
                    "timestamp": r.get("timestamp"),
                    "pr_number": r.get("pr_number"),
                    "pr_score": r.get("pr_score", r.get("score")),
                    "health_delta": r.get("health_delta", 0),
                    "overall_health": r.get("overall_health"),
                    "reason": r.get("reason"),
                }
                for r in reversed(_in_memory_history) if r.get("repo") == repo
            ][:limit]
        return {"repo": repo, "history": rows}
    except PyMongoError:
        raise HTTPException(status_code=500, detail="DB error")

@app.get("/repo-summary")
async def repo_summary_endpoint(repo: str):
    """
    Return the summary document for a repo (from repo_summary collection or in-memory).
    Contains current_health (current overall health) and stats.
    """
    # DB-backed summary
    if repo_summary is not None:
        try:
            doc = repo_summary.find_one({"repo": repo})
            if not doc:
                return {"repo": repo, "total_prs": 0, "cumulative_score": 0, "avg_score": 0.0, "current_health": INITIAL_REPO_HEALTH, "recent": []}
            # ensure avg_score present
            if "avg_score" not in doc:
                total = doc.get("total_prs", 0)
                cumulative = doc.get("cumulative_score", 0)
                doc["avg_score"] = (cumulative / total) if total else 0.0
            # remove internal _id for cleaner API response
            doc.pop("_id", None)
            return doc
        except PyMongoError:
            raise HTTPException(status_code=500, detail="DB error")

    # In-memory summary fallback
    s = _in_memory_summary.get(repo)
    if not s:
        # synthesize from in-memory history if no summary entry exists
        rows = [r for r in reversed(_in_memory_history) if r.get("repo") == repo]
        total = len(rows)
        cumulative = sum(r.get("pr_score", r.get("score", 0)) for r in rows)
        avg = (cumulative / total) if total else 0.0
        recent = rows[:RECENT_LIMIT]
        current_health = s.get("current_health") if s else INITIAL_REPO_HEALTH
        return {"repo": repo, "total_prs": total, "cumulative_score": cumulative, "avg_score": avg, "current_health": current_health, "last": recent[0] if recent else None, "recent": recent}
    return s
