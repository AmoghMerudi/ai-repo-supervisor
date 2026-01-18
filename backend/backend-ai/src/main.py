import sqlite3
import json
import os
import textwrap
import traceback
from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import logging
import urllib.request
import urllib.error
import urllib.parse

# New imports
from typing import Optional, Dict, Any, List, Any as _Any
try:
    import pymongo
    from pymongo import ReturnDocument
    from pymongo.errors import PyMongoError
    from pymongo.collection import Collection
except Exception:
    pymongo = None

# Load .env automatically
load_dotenv()

app = FastAPI()

# simple logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend-ai")

# GitHub token (optional). If set, server will post comments on PRs.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

# -----------------------------------
# Config
# -----------------------------------
USE_AI = os.getenv("USE_AI", "1") == "1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-3-flash-preview")

# Repo file search path (optional). If provided, AI will read files from here.
REPO_PATH = os.getenv("REPO_PATH", "")  # optional local checkout path

# Mongo config (optional). If not set, fallback to sqlite as before.
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DB = os.getenv("MONGODB_DB", "ai_repo_supervisor")

# -----------------------------------
# SQLite fallback DB (kept for backwards compatibility)
# -----------------------------------
conn = sqlite3.connect("health.db", check_same_thread=False)
conn.execute(
    """
CREATE TABLE IF NOT EXISTS repo_health (
    repo TEXT,
    timestamp TEXT,
    score INTEGER,
    reason TEXT
)
"""
)
conn.commit()

# -----------------------------------
# MongoDB setup (optional)
# -----------------------------------
mongo_client: Optional[_Any] = None
repo_collection: Optional[_Any] = None
repo_summary: Optional[_Any] = None
RECENT_LIMIT = 20
INITIAL_REPO_HEALTH = 100

if MONGODB_URI and pymongo:
    try:
        mongo_client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client[MONGODB_DB]
        repo_collection = db["repo_health"]
        repo_summary = db["repo_summary"]
        repo_collection.create_index([("repo", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])
        repo_summary.create_index([("repo", pymongo.ASCENDING)], unique=True)
        print("backend-ai: Connected to MongoDB:", MONGODB_DB)
    except PyMongoError as e:
        print("backend-ai: Warning: could not connect to MongoDB, falling back to sqlite:", str(e))
        mongo_client = None
        repo_collection = None
        repo_summary = None
else:
    if MONGODB_URI and not pymongo:
        print("backend-ai: pymongo not installed in this env; ignoring MONGODB_URI and using sqlite fallback")
    else:
        print("backend-ai: MONGODB_URI not set — using sqlite fallback (demo mode)")

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
# Helpers: read repo files for context
# -----------------------------------
def _read_candidate_file(path: str, max_chars: int = 2000) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars)
            if len(content) >= max_chars:
                content = content + "\n...[truncated]"
            return content
    except Exception:
        return None

def gather_repo_context_files() -> Dict[str, str]:
    """
    Look for README, package.json, requirements.txt, pyproject.toml, setup.py, Pipfile
    in REPO_PATH if provided, otherwise search upward from the backend-ai folder.
    Returns a dict filename -> content (truncated).
    """
    candidates = ["README.md", "README", "package.json", "requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]
    search_dirs = []
    if REPO_PATH:
        search_dirs.append(REPO_PATH)
    else:
        # start from this file's parent and walk up a few levels
        base = os.path.dirname(os.path.abspath(__file__))
        cur = base
        for _ in range(4):
            search_dirs.append(cur)
            cur = os.path.dirname(cur)
    found: Dict[str, str] = {}
    for d in search_dirs:
        for c in candidates:
            p = os.path.join(d, c)
            if os.path.isfile(p) and c not in found:
                txt = _read_candidate_file(p)
                if txt:
                    found[c] = txt
    return found

# -----------------------------------
# AI helper (OpenRouter / Gemini)
# -----------------------------------
def _build_ai_prompt(payload: PRRequest, repo_files: Dict[str, str]) -> str:
    """
    Construct a detailed prompt instructing the model to:
    - Infer repo goal/tech stack from files (if present)
    - Analyze the PR diff in context
    - Return ONLY valid JSON with required fields
    """
    intro = textwrap.dedent(
        """You are a senior repository supervisor and reviewer. You will:
1) Inspect the repository files provided to infer the project's goal and technologies.
2) Review the PR diff and state how the PR contributes to the repo goal.
3) Output ONLY a valid JSON object (no surrounding text) with these keys:
   - summary: string (summary of changes and how they relate to repo goal)
   - risks: array of strings (list of detected risk reasons)
   - suggestions: array of strings (actionable suggestions)
   - pr_score: integer 0-10 (10 = no risk; 0 = extremely risky)
   - health_delta: integer between -5 and +5 (-5 = very damaging, +5 = very beneficial)
   - reason: string (comma-separated brief reasons / same as joined risks)

Policy guidance for scoring:
- pr_score should reflect the PR quality; consider code quality, tests, docs, breaking changes.
- health_delta reflects the immediate impact on repo health; use negative for regression risk and positive for clear improvements.
- If repository metadata is missing, still analyze diff and be conservative in scoring.
"""
    )
    files_section = ""
    if repo_files:
        files_section += "\nRepository files (truncated if long):\n"
        for name, content in repo_files.items():
            files_section += f"\n=== {name} ===\n{content}\n"
    else:
        files_section += "\n(No repository files provided; infer only from the diff)\n"

    pr_section = textwrap.dedent(
        f"""
PR DETAILS:
Repo: {payload.repo}
PR Number: {payload.pr_number}
Author: {payload.author}
Additions: {payload.additions}
Deletions: {payload.deletions}
Changed files: {payload.changed_files}
Lint passed: {payload.lint_passed}

Diff:
{payload.diff}
"""
    )

    json_schema = textwrap.dedent(
        """
Return JSON exactly like:
{
  "summary": "...",
  "risks": ["...","..."],
  "suggestions": ["..."],
  "pr_score": 0,
  "health_delta": 0,
  "reason": "..."
}
"""
    )

    return intro + files_section + pr_section + json_schema

def run_ai_analysis(payload: PRRequest) -> Dict[str, Any]:
    """
    Call OpenRouter/Gemini. Returns parsed JSON dict. Raises on unrecoverable errors.
    """
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

    repo_files = gather_repo_context_files()
    prompt = _build_ai_prompt(payload, repo_files)

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    # OpenRouter returns choices[0].message.content
    raw = response.choices[0].message.content
    # Ensure we extract JSON if models include markdown fences
    # Try to find the first { ... } block
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        raw_json = raw[start:end]
    except Exception:
        raw_json = raw

    parsed = json.loads(raw_json)
    return parsed

# -----------------------------------
# Mongo helpers: atomic summary update (aggregation pipeline)
# -----------------------------------
def _update_repo_summary_mongo(doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Upsert/aggregate summary using aggregation pipeline update (supported operators only).
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

    new_recent_item = {
        "pr_number": pr_number,
        "score": pr_score,
        "timestamp": ts,
        "author": author,
        "overall_health_delta": health_delta,
    }

    try:
        pipeline_update = [
            {
                "$set": {
                    "repo": {"$ifNull": ["$repo", repo]},
                    "total_prs": {"$add": [{"$ifNull": ["$total_prs", 0]}, 1]},
                    "cumulative_score": {"$add": [{"$ifNull": ["$cumulative_score", 0]}, pr_score]},
                    "current_health": {"$add": [{"$ifNull": ["$current_health", INITIAL_REPO_HEALTH]}, health_delta]},
                    "last_score": pr_score,
                    "last_pr_number": pr_number,
                    "last_author": author,
                    "last_timestamp": ts,
                    "updated_at": datetime.utcnow().isoformat(),
                    "recent": {
                        "$slice": [
                            {"$concatArrays": [[new_recent_item], {"$ifNull": ["$recent", []]}]},
                            RECENT_LIMIT,
                        ]
                    },
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
            repo_summary.update_one({"repo": repo}, {"$set": {"avg_score": avg}})
            res = repo_summary.find_one({"repo": repo})
            return res
        return None
    except PyMongoError as e:
        print("backend-ai: Warning: failed to update repo_summary:", e)
        return None

# -----------------------------------
# API Endpoints
# -----------------------------------
@app.post("/analyze-pr")
@app.post("/analyze-pr/")
def analyze_pr(payload: PRRequest, request: Request = None):
    # simple request logging for debugging MVP
    client = None
    try:
        client = request.client.host if request and request.client else "unknown"
    except Exception:
        client = "unknown"
    logger.info("Received analyze-pr from %s repo=%s pr=%s additions=%s deletions=%s changed_files=%s",
                client, payload.repo, payload.pr_number, payload.additions, payload.deletions, payload.changed_files)

    # AI path (with fallbacks)
    if USE_AI:
        try:
            parsed = run_ai_analysis(payload)
            # Validate / coerce fields
            pr_score = int(parsed.get("pr_score", 0))
            if pr_score < 0:
                pr_score = 0
            if pr_score > 10:
                pr_score = 10
            health_delta = int(parsed.get("health_delta", 0))
            if health_delta < -5:
                health_delta = -5
            if health_delta > 5:
                health_delta = 5
            risks_arr = parsed.get("risks", [])
            if not isinstance(risks_arr, list):
                # if model returned a string, split by commas
                if isinstance(risks_arr, str):
                    risks_arr = [r.strip() for r in risks_arr.split(",") if r.strip()]
                else:
                    risks_arr = []
            reason = parsed.get("reason", ", ".join(risks_arr))
            summary = parsed.get("summary", "")
            suggestions = parsed.get("suggestions", [])
            # build doc for storage
            doc = {
                "repo": payload.repo,
                "timestamp": datetime.utcnow().isoformat(),
                "score": pr_score,  # legacy
                "pr_score": pr_score,
                "reason": reason,
                "risks": ",".join(risks_arr),
                "suggestions": suggestions,
                "pr_number": payload.pr_number,
                "author": payload.author,
                "additions": payload.additions,
                "deletions": payload.deletions,
                "changed_files": payload.changed_files,
                "health_delta": health_delta,
                "summary": summary,
            }

            # Build the comment (always present in response)
            comment_body = _format_comment(parsed, doc)

            wrote_to_db = False
            # Prefer MongoDB if configured
            if repo_summary is not None and repo_collection is not None:
                try:
                    # update repo_summary then set overall_health on doc
                    new_summary = _update_repo_summary_mongo(doc)
                    overall_health = None
                    if new_summary and isinstance(new_summary, dict):
                        overall_health = new_summary.get("current_health", INITIAL_REPO_HEALTH)
                    else:
                        overall_health = INITIAL_REPO_HEALTH + health_delta
                    doc["overall_health"] = overall_health
                    repo_collection.insert_one(doc)
                    wrote_to_db = True
                except Exception as e:
                    logger.warning("Mongo write failed, falling back to sqlite: %s", e)
                    # continue to sqlite fallback

            if not wrote_to_db:
                # sqlite fallback: store minimal fields (score = health_delta for compatibility)
                try:
                    conn.execute(
                        "INSERT INTO repo_health (repo, timestamp, score, reason) VALUES (?, ?, ?, ?)",
                        (payload.repo, datetime.utcnow().isoformat(), health_delta, ",".join(risks_arr)),
                    )
                    conn.commit()
                    doc["overall_health"] = INITIAL_REPO_HEALTH + health_delta
                except Exception:
                    doc["overall_health"] = INITIAL_REPO_HEALTH + health_delta

            # Try to post a PR comment from the server (best-effort)
            try:
                posted = _post_github_comment(payload.repo, payload.pr_number, comment_body)
                if not posted:
                    logger.info("Did not post comment for %s#%s (posting not configured or failed)", payload.repo, payload.pr_number)
            except Exception as e:
                logger.exception("Exception while attempting to post GitHub comment: %s", e)

            # Return the parsed analysis and the generated comment
            return {
                "summary": summary,
                "risks": risks_arr,
                "suggestions": suggestions,
                "pr_score": pr_score,
                "health_delta": health_delta,
                "reason": reason,
                "comment": comment_body,
            }
        except Exception as e:
            logger.exception("AI failed, falling back to deterministic logic: %s", e)
            print(traceback.format_exc())

    # Fallback deterministic logic (existing behavior)
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

    # pr_score mapping: 10 if no risks, else 0 (fallback deterministic policy)
    pr_score = 10 if not risks else 0
    # health_delta fallback: 0 if no risks, -5 if risky
    health_delta = 0 if not risks else -5

    # store (sqlite fallback)
    try:
        conn.execute(
            "INSERT INTO repo_health (repo, timestamp, score, reason) VALUES (?, ?, ?, ?)",
            (payload.repo, datetime.utcnow().isoformat(), health_delta, ",".join(risks)),
        )
        conn.commit()
    except Exception:
        pass

    # also try to persist to Mongo if available (minimal fields)
    if repo_collection is not None:
        try:
            doc = {
                "repo": payload.repo,
                "timestamp": datetime.utcnow().isoformat(),
                "score": pr_score,
                "pr_score": pr_score,
                "reason": ",".join(risks),
                "risks": ",".join(risks),
                "pr_number": payload.pr_number,
                "author": payload.author,
                "additions": payload.additions,
                "deletions": payload.deletions,
                "changed_files": payload.changed_files,
                "health_delta": health_delta,
                "summary": summary,
            }
            # update summary and insert
            new_summary = _update_repo_summary_mongo(doc)
            overall_health = new_summary.get("current_health") if new_summary else (INITIAL_REPO_HEALTH + health_delta)
            doc["overall_health"] = overall_health
            repo_collection.insert_one(doc)
        except Exception:
            doc = {
                "repo": payload.repo,
                "timestamp": datetime.utcnow().isoformat(),
                "score": pr_score,
                "pr_score": pr_score,
                "reason": ",".join(risks),
                "risks": ",".join(risks),
                "pr_number": payload.pr_number,
                "author": payload.author,
                "additions": payload.additions,
                "deletions": payload.deletions,
                "changed_files": payload.changed_files,
                "health_delta": health_delta,
                "summary": summary,
                "overall_health": INITIAL_REPO_HEALTH + health_delta,
            }

    # Ensure we build a comment for fallback and attempt posting (best-effort)
    comment_body = _format_comment({"summary": summary, "risks": risks, "suggestions": suggestions, "pr_score": pr_score, "health_delta": health_delta}, doc if "doc" in locals() else {})
    try:
        _post_github_comment(payload.repo, payload.pr_number, comment_body)
    except Exception as e:
        logger.exception("Exception while attempting to post GitHub comment (fallback): %s", e)

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "pr_score": pr_score,
        "health_delta": health_delta,
        "reason": ",".join(risks),
        "comment": comment_body,
    }


def _format_comment(analysis: Dict[str, Any], doc: Dict[str, Any]) -> str:
    """
    Build a markdown comment for the PR from analysis and stored doc.
    Truncate long sections to avoid exceeding API limits.
    """
    def _t(s: str, limit: int = 6000):
        if s is None:
            return ""
        s = str(s)
        return s if len(s) <= limit else s[:limit] + "\n\n...[truncated]"

    summary = _t(analysis.get("summary", doc.get("summary", "")), 8000)
    risks = analysis.get("risks", [])
    if isinstance(risks, list):
        risks_s = ", ".join(risks)
    else:
        risks_s = str(risks or "")
    suggestions = analysis.get("suggestions", [])
    if isinstance(suggestions, list):
        sugg_s = "\n".join(f"- {s}" for s in suggestions[:10])
    else:
        sugg_s = str(suggestions or "")

    pr_score = analysis.get("pr_score", doc.get("pr_score"))
    health_delta = analysis.get("health_delta", doc.get("health_delta"))
    overall_health = doc.get("overall_health")

    comment = []
    comment.append("**Automated AI PR Review**")
    comment.append("")
    comment.append(f"- **Score:** `{pr_score}`")
    comment.append(f"- **Health delta:** `{health_delta}`")
    if overall_health is not None:
        comment.append(f"- **Post-PR overall health:** `{overall_health}`")
    comment.append("")
    comment.append("**Summary:**")
    comment.append(summary or "_(no summary)_")
    comment.append("")
    if risks_s:
        comment.append("**Risks detected:**")
        comment.append(risks_s)
        comment.append("")
    if sugg_s:
        comment.append("**Suggestions:**")
        comment.append(sugg_s)
        comment.append("")
    comment.append("_This comment was posted automatically by the AI review service._")
    return "\n".join(comment)


def _post_github_comment(repo: str, pr_number: int, body: str) -> bool:
    """
    Post a comment to GitHub Issues API (PRs are issues). Returns True on success.
    Requires GITHUB_TOKEN env var to be set. Handles and logs errors.
    """
    if not GITHUB_TOKEN:
        logger.info("GITHUB_TOKEN not set; skipping posting comment for %s#%s", repo, pr_number)
        return False

    # ensure repo is owner/name
    if "/" not in repo:
        logger.warning("Invalid repo format for comment: %s", repo)
        return False

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "User-Agent": "ai-repo-supervisor/agent",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            resp_body = resp.read().decode("utf-8", errors="ignore")
            if 200 <= status < 300:
                logger.info("Posted GitHub comment to %s#%s (status=%s)", repo, pr_number, status)
                return True
            else:
                logger.warning("GitHub comment POST returned %s: %s", status, resp_body)
                return False
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            err_body = "<no body>"
        logger.warning("GitHub comment POST failed: %s %s", e.code, err_body)
        return False
    except Exception as e:
        logger.exception("Unexpected error posting GitHub comment: %s", e)
        return False


@app.get("/health")
def health():
    ok = True
    mongo_ok = repo_collection is not None
    return {"status": "ok", "mongo": mongo_ok}


@app.get("/health-history")
def health_history(repo: str):
    # Prefer Mongo if available
    if repo_collection is not None:
        try:
            cursor = repo_collection.find({"repo": repo}).sort("timestamp", pymongo.DESCENDING).limit(20)
            rows = []
            for r in cursor:
                rows.append(
                    {
                        "timestamp": r.get("timestamp"),
                        "pr_number": r.get("pr_number"),
                        "pr_score": r.get("pr_score", r.get("score")),
                        "health_delta": r.get("health_delta", 0),
                        "overall_health": r.get("overall_health"),
                        "reason": r.get("reason"),
                        "summary": r.get("summary"),
                    }
                )
            return {"repo": repo, "health": rows}
        except Exception:
            pass

    # sqlite fallback
    cur = conn.execute(
        "SELECT timestamp, score, reason FROM repo_health WHERE repo = ? ORDER BY timestamp DESC LIMIT 20",
        (repo,),
    )
    rows = [{"timestamp": r[0], "score": r[1], "reason": r[2]} for r in cur.fetchall()]
    return {"repo": repo, "health": rows}


@app.on_event("startup")
def _log_registered_routes():
    try:
        routes = sorted({r.path for r in app.routes})
        logger.info("backend-ai: registered routes: %s", routes)
    except Exception:
        logger.exception("backend-ai: failed to list routes")

@app.get("/")
def root():
    # quick health + route check for debugging
    routes = sorted({r.path for r in app.routes})
    return {"status": "ok", "routes": routes}
