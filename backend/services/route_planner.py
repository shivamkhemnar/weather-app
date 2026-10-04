"""Route planner: origin -> destination estimate with cost/time/risk + best options.

Used by the map-style search ("mumbai to nashik"): returns distance, live
weather/traffic at both ends, risk score, and ranked options:
- recommended (balanced weighted score - the autonomous choice)
- cheapest (lowest transport + penalty)
- fastest (lowest delay)
Callers never crash: everything falls back to simulation defaults.
"""
import math
from backend.config import CITY_COORDS
from backend.services import risk_engine as re_
from backend.services import optimization_engine as oe
from backend.services import financial_engine as fe


def haversine_km(a: str, b: str) -> float:
    """Straight-line km between two tracked cities (fallback 250 km)."""
    try:
        lat1, lon1 = CITY_COORDS[a]
        lat2, lon2 = CITY_COORDS[b]
        R = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return round(2 * R * math.asin(math.sqrt(h)), 1)
    except Exception:
        return 250.0


def _live_weather_snapshot(city: str) -> dict:
    try:
        from backend.services import weather_provider as wp
        return wp.current_by_city(city)
    except Exception:
        return {"temperature": 32.0, "rainfall_mm_last_hr": 5.0, "wind_speed": 15.0,
                "condition": "Clear (simulated)", "source": "simulated"}


def _live_traffic_snapshot(city: str) -> dict:
    try:
        from backend.services import traffic_provider as tp
        return tp.flow_by_city(city)
    except Exception:
        return {"congestion_level": 35.0, "current_speed_kmh": 50.0,
                "route_status": "Open (simulated)", "source": "simulated"}


def plan_route(origin: str, destination: str, preference: str = "balanced") -> dict:
    """Plan origin->destination. preference: cheapest | fastest | balanced."""
    origin = origin.strip().title()
    destination = destination.strip().title()
    distance = haversine_km(origin, destination) if origin in CITY_COORDS and destination in CITY_COORDS else 250.0
    # Road distance ~30% more than straight line in India
    road_km = round(distance * 1.3, 1)

    w_o = _live_weather_snapshot(origin)
    w_d = _live_weather_snapshot(destination)
    t_o = _live_traffic_snapshot(origin)

    rain = max(float(w_o.get("rainfall_mm_last_hr", 0) or 0), 0.0)
    congestion = float(t_o.get("congestion_level", 35.0) or 35.0)
    wind = float(w_o.get("wind_speed", 15.0) or 15.0)

    score, factors = re_.calculate_risk_score(
        rainfall=rain, congestion=congestion, iot_temp=5.0,
        supplier_delay_days=0.5, reliability=80.0, stock_ratio=1.0,
        days_to_deadline=4.0, accident=False, wind_speed=wind)
    level = re_.classify_risk(score)

    base_cost = round(road_km * 65.0, 2)  # Rs ~65 per km all-in estimate
    base_delay = round(road_km / 400.0 + (score / 100.0) * 2.0, 1)  # ~400 km/day + risk buffer
    penalty = fe.contract_penalty(5000.0, base_delay, 5.0)

    options = oe.generate_options(base_cost=base_cost, base_delay=base_delay,
                                  base_risk=score, penalty_do_nothing=penalty,
                                  shortage_units=0)
    recommended = oe.select_best(options)  # balanced weighted winner
    cheapest = min(options, key=lambda o: o["transport_cost"] + o.get("penalty", 0))
    fastest = min(options, key=lambda o: o["delay"])

    if preference == "cheapest":
        pick, reason = cheapest, "Lowest total money (transport + penalty)."
    elif preference == "fastest":
        pick, reason = fastest, "Shortest delivery time."
    else:
        pick, reason = recommended, "Best balance of cost, time and risk (autonomous choice)."

    eta_hours = round(road_km / max(10.0, float(t_o.get("current_speed_kmh", 45.0) or 45.0)), 1)
    return {
        "origin": origin, "destination": destination,
        "distance_km": road_km, "eta_hours": eta_hours,
        "risk_score": score, "risk_level": level, "risk_factors": factors,
        "origin_weather": w_o, "destination_weather": w_d, "origin_traffic": t_o,
        "recommended": recommended, "cheapest": cheapest, "fastest": fastest,
        "picked": pick, "pick_reason": reason, "preference": preference,
        "options": sorted(options, key=lambda o: o["score"]),
        "map_url": f"https://www.google.com/maps/dir/{origin},India/{destination},India",
    }
