import os
import sys
import traceback

# Ensure parent directory is in Python path so server.py and its assets can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from server import app
except Exception:
    err_tb = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    app = FastAPI()
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def show_startup_error(path: str = ""):
        return HTMLResponse(
            content=f"""
            <div style="font-family: monospace; padding: 20px; background: #fff5f5; color: #900; border: 1px solid #fcc; border-radius: 8px;">
                <h3>⚠️ Error during application startup:</h3>
                <pre style="white-space: pre-wrap;">{err_tb}</pre>
            </div>
            """,
            status_code=500
        )
