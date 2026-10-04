"""FastAPI entrypoint: serves APIs + app UI, runs the 4-hour live refresh loop."""
import asyncio
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db, SessionLocal
from backend.services.simulation import load_seed_data, ensure_extra_routes
from backend.agents import orchestrator
from backend.config import SIMULATION_INTERVAL_SEC
from backend.api import shipments, risks, decisions, dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("supply-chain-mas")

app = FastAPI(title="Autonomous Multi-Agent Supply Chain Risk Monitoring",
              description="Professional live mode: real weather/traffic APIs + 4-hour refresh + simulation fallback",
              version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# REST APIs
app.include_router(shipments.router, prefix="/api", tags=["logistics"])
app.include_router(risks.router, prefix="/api", tags=["risks"])
app.include_router(decisions.router, prefix="/api", tags=["decisions"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "supply-chain-mas"}


async def refresh_loop():
    """Background task: refresh the whole fleet every SIMULATION_INTERVAL_SEC (default 4h)."""
    await asyncio.sleep(5)  # let startup finish
    from backend import models
    while True:
        try:
            if dashboard.simulation_state["running"]:
                db = SessionLocal()
                try:
                    ships = db.query(models.Shipment).all()
                finally:
                    db.close()
                for s in ships[:8]:
                    try:
                        result = orchestrator.run_cycle_for_shipment(s.shipment_id)
                        log.info(f"[refresh] {result}")
                    except Exception as e:
                        log.error(f"[refresh] {s.shipment_id} failed: {e}")
        except Exception as e:
            log.error(f"[refresh] loop error: {e}")
        await asyncio.sleep(SIMULATION_INTERVAL_SEC)


@app.on_event("startup")
def on_startup():
    init_db()  # create SQLite tables
    db = SessionLocal()
    try:
        seeded = load_seed_data(db)
        ensure_extra_routes(db)  # add all-India routes to older DBs
        log.info(f"[startup] seed loaded: {seeded}, refresh every {SIMULATION_INTERVAL_SEC}s "
                 f"({SIMULATION_INTERVAL_SEC/3600:.2f}h)")
        if seeded:
            for sid in ["SHP-001", "SHP-002", "SHP-003"]:
                try:
                    orchestrator.run_cycle_for_shipment(sid)
                except Exception as e:
                    log.error(f"[startup] pre-cycle failed: {e}")
    finally:
        db.close()
    asyncio.create_task(refresh_loop())


# Serve the app UI (frontend/index.html)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
