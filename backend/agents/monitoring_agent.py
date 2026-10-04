"""A. DATA MONITORING AGENT - collects real API data first, simulation fallback."""
import logging
from backend import models
from backend.services import simulation

log = logging.getLogger(__name__)


def _city_for_shipment(db, shipment_id: str) -> str:
    try:
        s = db.query(models.Shipment).filter_by(shipment_id=shipment_id).first()
        return (s.current_location or s.origin or "Mumbai") if s else "Mumbai"
    except Exception:
        return "Mumbai"


def _real_weather(city: str, shipment_id: str):
    """Try OpenWeatherMap; return WeatherEvent kwargs or None."""
    try:
        from backend.services import weather_provider as wp
        live = wp.current_by_city(city)
        condition = live.get("condition", "Clear")
        rain = float(live.get("rainfall_mm_last_hr", 0) or 0)
        severity = "critical" if rain >= 50 else ("high" if rain >= 20 else ("medium" if rain >= 5 else "low"))
        if condition.lower() in ("thunderstorm", "tornado"):
            severity = "critical"
        return {"shipment_id": shipment_id, "temperature": float(live.get("temperature", 30.0)),
                "rainfall": rain, "wind_speed": float(live.get("wind_speed", 10.0)),
                "weather_condition": f"{condition} ({city}, live)",
                "severity": severity, "_source": "live-openweathermap"}
    except Exception as e:
        log.info(f"[monitoring] live weather unavailable for {city}: {e}")
        return None


def _real_traffic(city: str, shipment_id: str):
    """Try TomTom; return TrafficEvent kwargs or None."""
    try:
        from backend.services import traffic_provider as tp
        live = tp.flow_by_city(city)
        return {"shipment_id": shipment_id,
                "congestion_level": float(live.get("congestion_level", 30.0)),
                "average_speed": float(live.get("current_speed_kmh", 50.0)),
                "route_status": live.get("route_status", "Open") + f" ({city}, live)",
                "accident_reported": "Yes" if live.get("road_closure") else "No",
                "_source": "live-tomtom"}
    except Exception as e:
        log.info(f"[monitoring] live traffic unavailable for {city}: {e}")
        return None


def collect_tick(db, shipment_id: str, prefer_live: bool = True) -> dict:
    """One refresh: real APIs first (if keys set), else simulation. Always persists."""
    try:
        city = _city_for_shipment(db, shipment_id)
        w, t = None, None
        if prefer_live:
            w = _real_weather(city, shipment_id)
            t = _real_traffic(city, shipment_id)
        if w is None:
            w = simulation.random_weather(shipment_id)
        if t is None:
            t = simulation.random_traffic(shipment_id)
        i = simulation.random_iot(shipment_id)  # IoT stays simulated (truck sensors)
        w_clean = {k: v for k, v in w.items() if not k.startswith("_")}
        t_clean = {k: v for k, v in t.items() if not k.startswith("_")}
        db.add(models.WeatherEvent(**w_clean))
        db.add(models.TrafficEvent(**t_clean))
        db.add(models.IoTEvent(**i))
        db.commit()
        return {"weather": w, "traffic": t, "iot": i,
                "mode": "live" if ("_source" in (w or {}) or "_source" in (t or {})) else "simulated",
                "city": city}
    except Exception as e:
        db.rollback()
        log.error(f"[monitoring] tick failed for {shipment_id}: {e}")
        return {"weather": {}, "traffic": {}, "iot": {}, "error": str(e)}


def latest_events(db, shipment_id: str) -> dict:
    """Fetch the most recent stored events for a shipment."""
    w = db.query(models.WeatherEvent).filter_by(shipment_id=shipment_id).order_by(models.WeatherEvent.id.desc()).first()
    t = db.query(models.TrafficEvent).filter_by(shipment_id=shipment_id).order_by(models.TrafficEvent.id.desc()).first()
    i = db.query(models.IoTEvent).filter_by(shipment_id=shipment_id).order_by(models.IoTEvent.id.desc()).first()
    return {"weather": w, "traffic": t, "iot": i}
