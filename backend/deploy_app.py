"""Local deployment entrypoint: LicenzPol API plus the compiled React SPA."""
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server import app

BUILD_DIR = (Path(__file__).resolve().parent.parent / "frontend" / "build").resolve()
STATIC_DIR = BUILD_DIR / "static"

if not (BUILD_DIR / "index.html").is_file():
    raise RuntimeError(f"Frontend build is missing: {BUILD_DIR / 'index.html'}")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="frontend-static")


@app.get("/{path:path}", include_in_schema=False)
async def serve_frontend(path: str):
    """Serve real build assets when present; otherwise use the SPA shell."""
    candidate = (BUILD_DIR / path).resolve()
    if candidate.is_relative_to(BUILD_DIR) and candidate.is_file():
        return FileResponse(candidate)
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    return FileResponse(BUILD_DIR / "index.html")
