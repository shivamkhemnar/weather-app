"""Dashboard summary + live weather/traffic + settings + simulation controls."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import SessionLocal, get_db
from backend import models
from backend.agents import orchestrator
from backend.config import TRACKED_CITIES, OPENWEATHER_API_KEY, TOMTOM_API_KEY, SIMULATION_INTERVAL_SEC

router = APIRouter()

# In-memory flag so the dashboard can pause/resume the refresh loop
simulation_state = {"running": True}


@router.get("/dashboard/summary")
def dashboard_summary():
    db = SessionLocal()
    try:
        total = db.query(func.count(models.Shipment.id)).scalar() or 0
        active = db.query(func.count(models.Shipment.id)).filter(
            models.Shipment.current_status.in_(["In Transit", "Delayed", "At Risk"])).scalar() or 0
        delayed = db.query(func.count(models.Shipment.id)).filter(
            models.Shipment.current_status.in_(["Delayed", "At Risk"])).scalar() or 0
        latest = {}
        for r in db.query(models.Risk).order_by(models.Risk.id.desc()).limit(300).all():
            latest.setdefault(r.shipment_id, r)
        high = sum(1 for r in latest.values() if r.risk_level == "HIGH")
        critical = sum(1 for r in latest.values() if r.risk_level == "CRITICAL")
        fin = sum((d.total_cost or 0) for d in
                  db.query(models.Decision).order_by(models.Decision.id.desc()).limit(20).all())
        alerts = db.query(func.count(models.Alert.id)).filter(models.Alert.is_read == 0).scalar() or 0
        decisions = db.query(func.count(models.Decision.id)).scalar() or 0
        dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for r in latest.values():
            dist[r.risk_level] = dist.get(r.risk_level, 0) + 1
        recent_risks = [{"shipment_id": r.shipment_id, "score": r.risk_score,
                         "level": r.risk_level, "at": str(r.created_at)}
                        for r in db.query(models.Risk).order_by(models.Risk.id.desc()).limit(15).all()]
        recent_decisions = [{"id": d.id, "shipment_id": d.shipment_id,
                             "action": d.selected_action, "cost": d.total_cost,
                             "risk": d.risk_level, "at": str(d.created_at)}
                            for d in db.query(models.Decision).order_by(models.Decision.id.desc()).limit(10).all()]
        recent_alerts = [{"id": a.id, "shipment_id": a.shipment_id, "level": a.risk_level,
                          "message": a.message, "at": str(a.created_at)}
                         for a in db.query(models.Alert).order_by(models.Alert.id.desc()).limit(10).all()]
        last_wx = db.query(models.WeatherEvent).order_by(models.WeatherEvent.id.desc()).first()
        last_tf = db.query(models.TrafficEvent).order_by(models.TrafficEvent.id.desc()).first()
        return {"total_shipments": total, "active_shipments": active,
                "high_risk": high, "critical": critical, "delayed_shipments": delayed,
                "financial_impact": round(fin, 2), "active_alerts": alerts,
                "decisions": decisions, "risk_distribution": dist,
                "recent_risks": recent_risks, "recent_decisions": recent_decisions,
                "recent_alerts": recent_alerts, "simulation_running": simulation_state["running"],
                "refresh_interval_sec": SIMULATION_INTERVAL_SEC,
                "live": {"weather_key": bool(OPENWEATHER_API_KEY), "traffic_key": bool(TOMTOM_API_KEY),
                         "last_weather_at": str(last_wx.created_at) if last_wx else None,
                         "last_traffic_at": str(last_tf.created_at) if last_tf else None},
                "cities": TRACKED_CITIES}
    finally:
        db.close()


@router.get("/weather/live")
def weather_live(city: str = "Mumbai"):
    """Live current weather for a city (real API) with stored-data fallback."""
    try:
        from backend.services import weather_provider as wp
        return wp.current_by_city(city)
    except Exception as e:
        db = SessionLocal()
        try:
            last = db.query(models.WeatherEvent).order_by(models.WeatherEvent.id.desc()).first()
            return {"city": city, "source": "stored-fallback", "note": str(e),
                    "temperature": last.temperature if last else 30.0,
                    "rainfall_mm_last_hr": last.rainfall if last else 0.0,
                    "condition": last.weather_condition if last else "Unknown"}
        finally:
            db.close()


@router.get("/weather/forecast")
def weather_forecast(city: str = "Mumbai"):
    """5-day forecast (real API). Fails soft with a clear message when no key."""
    try:
        from backend.services import weather_provider as wp
        return {"city": city, "source": "openweathermap", "slots": wp.forecast_by_city(city)}
    except Exception as e:
        raise HTTPException(502, f"Forecast unavailable: {e}. Add OPENWEATHER_API_KEY to .env.")


@router.get("/traffic/live")
def traffic_live(city: str = "Mumbai"):
    """Live traffic flow for a city (real API) with stored-data fallback."""
    try:
        from backend.services import traffic_provider as tp
        return tp.flow_by_city(city)
    except Exception as e:
        db = SessionLocal()
        try:
            last = db.query(models.TrafficEvent).order_by(models.TrafficEvent.id.desc()).first()
            return {"city": city, "source": "stored-fallback", "note": str(e),
                    "congestion_level": last.congestion_level if last else 30.0,
                    "current_speed_kmh": last.average_speed if last else 50.0}
        finally:
            db.close()


@router.get("/settings/status")
def settings_status():
    """Show which live integrations are active (never exposes key values)."""
    return {"weather_live": bool(OPENWEATHER_API_KEY), "traffic_live": bool(TOMTOM_API_KEY),
            "refresh_interval_sec": SIMULATION_INTERVAL_SEC,
            "refresh_hours": round(SIMULATION_INTERVAL_SEC / 3600, 2),
            "cities": TRACKED_CITIES,
            "hint": "Copy .env.example to .env and paste keys, then restart the server."}


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(models.Alert).filter_by(id=alert_id).first()
    if not a:
        raise HTTPException(404, "Alert not found")
    a.is_read = 1
    db.commit()
    return {"ok": True, "id": alert_id}


@router.post("/simulation/start")
def sim_start():
    simulation_state["running"] = True
    return {"running": True}


@router.post("/simulation/stop")
def sim_stop():
    simulation_state["running"] = False
    return {"running": False}


@router.post("/simulation/tick")
def sim_tick(shipment_id: str = None):
    """Manually trigger one autonomous cycle (Refresh Now button)."""
    return orchestrator.run_cycle_for_shipment(shipment_id)


@router.get("/route/plan")
def route_plan(origin: str, destination: str, preference: str = "balanced"):
    """Map-style planner: cost/time/risk + cheapest/fastest/balanced pick."""
    try:
        from backend.services import route_planner as rp
        if preference not in ("cheapest", "fastest", "balanced"):
            preference = "balanced"
        return rp.plan_route(origin, destination, preference)
    except Exception as e:
        raise HTTPException(500, f"Route planning failed: {e}")


@router.post("/simulation/refresh-city")
def refresh_city(city: str):
    """Refresh one city now: run cycles for shipments linked to that city."""
    db = SessionLocal()
    try:
        ships = db.query(models.Shipment).filter(
            (models.Shipment.origin == city) | (models.Shipment.current_location == city)).all()
        if not ships:
            return orchestrator.run_cycle_for_shipment()
        return [orchestrator.run_cycle_for_shipment(s.shipment_id) for s in ships[:3]]
    finally:
        db.close()
