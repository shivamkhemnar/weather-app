"""Real traffic provider: TomTom Traffic Flow with safe fallback.

- If TOMTOM_API_KEY is missing/invalid/offline, raises RuntimeError
  and callers fall back to simulated traffic so the app NEVER crashes.
- Uses only stdlib urllib (no new dependency).
"""
import json
import urllib.request
from backend.config import TOMTOM_API_KEY, CITY_COORDS


def flow_by_city(city: str) -> dict:
    """Live traffic flow near a city centre. Returns normalized dict."""
    if not TOMTOM_API_KEY:
        raise RuntimeError("TOMTOM_API_KEY not set - add it to .env (see .env.example)")
    lat, lon = CITY_COORDS.get(city, CITY_COORDS["Mumbai"])
    url = (f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
           f"?point={lat},{lon}&key={TOMTOM_API_KEY}")
    req = urllib.request.Request(url, headers={"User-Agent": "supply-chain-mas/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        d = json.loads(r.read().decode())
    seg = d.get("flowSegmentData", {})
    cur = float(seg.get("currentSpeed", 50.0))
    free = float(seg.get("freeFlowSpeed", 60.0)) or 60.0
    congestion = round(max(0.0, min(100.0, (1 - cur / free) * 100)), 1)
    return {
        "city": city,
        "current_speed_kmh": cur,
        "free_flow_kmh": free,
        "congestion_level": congestion,
        "road_closure": bool(seg.get("roadClosure", False)),
        "route_status": "Blocked" if seg.get("roadClosure") else ("Congested" if congestion > 60 else "Open"),
        "source": "tomtom",
    }
