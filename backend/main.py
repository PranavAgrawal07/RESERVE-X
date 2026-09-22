"""RESERVE-X backend — FastAPI application entry point.

Run with:  uvicorn backend.main:app --reload
Swagger:   http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.engine.option_manager import expire_stale_options
from backend.api.resources import router as resources_router
from backend.api.options import router as options_router
from backend.api.system import router as system_router
from backend.api.simulation import router as simulation_router


# ── Background expiration sweep ──────────────────────────────────

SWEEP_INTERVAL_SECONDS = 5


async def _expiration_sweep() -> None:
    """Periodically expire stale options."""
    while True:
        expire_stale_options()
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background sweep on startup, cancel on shutdown."""
    task = asyncio.create_task(_expiration_sweep())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ── FastAPI app ──────────────────────────────────────────────────

app = FastAPI(
    title="RESERVE-X",
    description="Contingent resource reservation system for concurrent autonomous AI agents.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow everything for hackathon (dashboard will call from localhost:3000+)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api/v1
API_PREFIX = "/api/v1"
app.include_router(resources_router, prefix=API_PREFIX)
app.include_router(options_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(simulation_router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {
        "name": "RESERVE-X",
        "version": "0.1.0",
        "docs": "/docs",
        "api": "/api/v1",
    }
