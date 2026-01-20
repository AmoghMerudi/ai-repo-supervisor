import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute
from starlette.routing import Mount, Route

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


def _collect_routes(app_instance: FastAPI, prefix: str = ""):
    routes = []
    for route in app_instance.routes:
        if isinstance(route, Mount):
            mount_prefix = f"{prefix}{route.path}"
            if isinstance(route.app, FastAPI):
                routes.extend(_collect_routes(route.app, mount_prefix))
        elif isinstance(route, APIRoute):
            methods = sorted(m for m in (route.methods or []) if m not in {"HEAD", "OPTIONS"})
            routes.append(
                {
                    "path": f"{prefix}{route.path}",
                    "methods": methods,
                    "name": route.name,
                }
            )
        elif isinstance(route, Route):
            methods = sorted(m for m in (route.methods or []) if m not in {"HEAD", "OPTIONS"})
            routes.append(
                {
                    "path": f"{prefix}{route.path}",
                    "methods": methods,
                    "name": route.name,
                }
            )
    return routes


@app.get("/dashboard/routes", response_class=JSONResponse)
def dashboard_routes():
    routes = _collect_routes(app)
    routes.sort(key=lambda r: (r["path"], ",".join(r["methods"])))
    return {"routes": routes}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Backend Dashboard</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; color: #111; }
      h1 { margin-bottom: 4px; }
      .sub { color: #555; margin-bottom: 16px; }
      .row { display: flex; gap: 12px; flex-wrap: wrap; }
      label { display: block; font-weight: 600; margin-bottom: 6px; }
      select, input, textarea, button { font-size: 14px; padding: 8px; }
      textarea { width: 100%; min-height: 160px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
      .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-top: 16px; }
      .route-list { max-height: 280px; overflow: auto; border: 1px solid #eee; padding: 8px; border-radius: 6px; }
      .route-item { padding: 6px 4px; border-bottom: 1px solid #f0f0f0; }
      .route-item:last-child { border-bottom: none; }
      .pill { display: inline-block; padding: 2px 6px; background: #f2f2f2; border-radius: 6px; margin-right: 6px; font-size: 12px; }
      pre { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow: auto; }
      .muted { color: #666; font-size: 12px; }
    </style>
  </head>
  <body>
    <h1>Backend Dashboard</h1>
    <div class="sub">View and test backend endpoints.</div>

    <div class="card">
      <div class="row">
        <div style="min-width: 220px;">
          <label for="method">Method</label>
          <select id="method"></select>
        </div>
        <div style="flex: 1; min-width: 260px;">
          <label for="path">Endpoint</label>
          <select id="path" style="width: 100%;"></select>
          <div class="muted">Select an endpoint or type your own path below.</div>
        </div>
        <div style="flex: 1; min-width: 260px;">
          <label for="customPath">Custom Path</label>
          <input id="customPath" placeholder="/api/analyze-pr" style="width: 100%;" />
        </div>
      </div>
      <div style="margin-top: 16px;">
        <label for="query">Query Params (optional, e.g. repo=my-repo&limit=5)</label>
        <input id="query" style="width: 100%;" />
      </div>
      <div style="margin-top: 16px;">
        <label for="body">JSON Body (for POST/PUT/PATCH)</label>
        <textarea id="body">{}</textarea>
      </div>
      <div style="margin-top: 16px;">
        <button id="sendBtn">Send Request</button>
      </div>
    </div>

    <div class="card">
      <label>Response</label>
      <pre id="response">Waiting for request...</pre>
    </div>

    <div class="card">
      <label>Available Routes</label>
      <div id="routeList" class="route-list">Loading routes...</div>
    </div>

    <script>
      const methodEl = document.getElementById("method");
      const pathEl = document.getElementById("path");
      const customPathEl = document.getElementById("customPath");
      const queryEl = document.getElementById("query");
      const bodyEl = document.getElementById("body");
      const responseEl = document.getElementById("response");
      const routeListEl = document.getElementById("routeList");
      const sendBtn = document.getElementById("sendBtn");

      function setResponse(text, isError = false) {
        responseEl.textContent = text;
        responseEl.style.background = isError ? "#7f1d1d" : "#0f172a";
      }

      function buildUrl(path) {
        const query = queryEl.value.trim();
        if (!query) return path;
        return path.includes("?") ? `${path}&${query}` : `${path}?${query}`;
      }

      function getSelectedPath() {
        const custom = customPathEl.value.trim();
        if (custom) return custom;
        return pathEl.value || "/";
      }

      async function loadRoutes() {
        const res = await fetch("/dashboard/routes");
        const data = await res.json();
        const routes = data.routes || [];

        const uniqueMethods = new Set();
        routes.forEach(r => (r.methods || []).forEach(m => uniqueMethods.add(m)));
        methodEl.innerHTML = "";
        [...uniqueMethods].sort().forEach(m => {
          const opt = document.createElement("option");
          opt.value = m;
          opt.textContent = m;
          methodEl.appendChild(opt);
        });

        pathEl.innerHTML = "";
        routes.forEach(r => {
          const opt = document.createElement("option");
          opt.value = r.path;
          opt.textContent = `${r.path} (${(r.methods || []).join(", ")})`;
          pathEl.appendChild(opt);
        });

        routeListEl.innerHTML = "";
        routes.forEach(r => {
          const div = document.createElement("div");
          div.className = "route-item";
          const methods = (r.methods || []).map(m => `<span class="pill">${m}</span>`).join("");
          div.innerHTML = `${methods}<strong>${r.path}</strong> <span class="muted">${r.name || ""}</span>`;
          div.onclick = () => {
            pathEl.value = r.path;
            if (r.methods && r.methods.length) {
              methodEl.value = r.methods[0];
            }
          };
          routeListEl.appendChild(div);
        });
      }

      sendBtn.addEventListener("click", async () => {
        const method = methodEl.value || "GET";
        const path = getSelectedPath();
        const url = buildUrl(path);

        const options = { method, headers: { "Content-Type": "application/json" } };
        if (!["GET", "HEAD"].includes(method)) {
          const raw = bodyEl.value.trim();
          options.body = raw ? raw : "{}";
        }

        setResponse("Sending request...");
        try {
          const res = await fetch(url, options);
          const text = await res.text();
          let formatted = text;
          try {
            formatted = JSON.stringify(JSON.parse(text), null, 2);
          } catch (e) {}
          setResponse(`${res.status} ${res.statusText}\\n\\n${formatted}`);
        } catch (err) {
          setResponse(`Request failed: ${err}`, true);
        }
      });

      loadRoutes().catch(err => {
        routeListEl.textContent = `Failed to load routes: ${err}`;
      });
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)
