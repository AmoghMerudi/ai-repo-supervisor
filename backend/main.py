import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent

BACKEND_API_DIR = BASE_DIR / "backend-api"
BACKEND_AI_DIR = BASE_DIR / "backend-ai"
BACKEND_DB_DIR = BASE_DIR / "backend-db"

for directory in (BACKEND_API_DIR, BACKEND_AI_DIR, BACKEND_DB_DIR):
    sys.path.insert(0, str(directory))


def _load_app(module_name: str, module_path: Path):
    if not module_path.exists():
        raise FileNotFoundError(f"Missing module at {module_path}")
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "app"):
        raise AttributeError(f"Module {module_name} does not expose app")
    return module.app


api_app = _load_app("backend_api_main", BACKEND_API_DIR / "src" / "main.py")
ai_app = _load_app("backend_ai_main", BACKEND_AI_DIR / "src" / "main.py")
db_app = _load_app("backend_db_main", BACKEND_DB_DIR / "src" / "main.py")

app = FastAPI(title="AI Repo Supervisor Backend")

app.mount("/api", api_app)
app.mount("/ai", ai_app)
app.mount("/db", db_app)


@app.get("/")
def root():
    return {
        "status": "ok",
        "services": {
            "api": "/api",
            "ai": "/ai",
            "db": "/db",
        },
    }
