import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.posts import router as posts_router
from app.routers.pages import router as pages_router
from app.routers.taxonomy import categories_router, tags_router
from app.routers.media import router as media_router
from app.routers.comments import router as comments_router
from app.routers.users import router as users_router
from app.routers.dashboard import router as dashboard_router

app = FastAPI(
    title="WP-Replacement API",
    description="RESTful API backed by the existing WordPress MySQL database.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────

PREFIX = "/api"

app.include_router(auth_router, prefix=PREFIX)
app.include_router(posts_router, prefix=PREFIX)
app.include_router(pages_router, prefix=PREFIX)
app.include_router(categories_router, prefix=PREFIX)
app.include_router(tags_router, prefix=PREFIX)
app.include_router(media_router, prefix=PREFIX)
app.include_router(comments_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(dashboard_router, prefix=PREFIX)

# ── Serve uploaded files ──────────────────────────────────────────────────────

uploads_dir = Path(settings.UPLOAD_DIR)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/wp-content/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
