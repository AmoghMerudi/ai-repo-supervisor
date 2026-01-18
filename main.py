from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.main import app as backend_app

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_OUT_DIR = BASE_DIR / "frontend" / "ai-repo-supervisor" / "out"

app = FastAPI(title="AI Repo Supervisor")

# Backend API mounted under /api
app.mount("/api", backend_app)

# Frontend static build (Next.js export) if available
if FRONTEND_OUT_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_OUT_DIR, html=True), name="frontend")
else:
    @app.get("/", response_class=HTMLResponse)
    def root():
        return """
        <h1>AI Repo Supervisor</h1>
        <p>Backend available at <code>/api</code>.</p>
        <p>Frontend build not found. Run a Next.js build/export to generate
        <code>frontend/ai-repo-supervisor/out</code>.</p>
        """
