"""Real weather provider: OpenWeatherMap (current + 5-day forecast) with safe fallback.

- If OPENWEATHER_API_KEY is missing/invalid/offline, raises RuntimeError
  and callers fall back to local simulation so the app NEVER crashes.
- Uses only stdlib urllib (no new dependency).
"""
import json
import urllib.request
import urllib.parse
from backend.config import OPENWEATHER_API_KEY


def _get(url: str, timeout: int = 12) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "supply-chain-mas/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def current_by_city(city: str) -> dict:
    """Live current weather for an Indian city. Returns normalized dict."""
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY not set - add it to .env (see .env.example)")
    q = urllib.parse.quote(city)
    url = (f"https://api.openweathermap.org/data/2.5/weather?q={q},IN&appid={OPENWEATHER_API_KEY}&units=metric")
    d = _get(url)
    rain = 0.0
    try:
        rain = float((d.get("rain") or {}).get("1h", 0) or 0)
    except Exception:
        rain = 0.0
    cond = ""
    try:
        cond = d["weather"][0]["main"]
    except Exception:
        cond = "Clear"
    return {
        "city": city,
        "temperature": float(d.get("main", {}).get("temp", 30.0)),
        "humidity": float(d.get("main", {}).get("humidity", 60.0)),
        "wind_speed": round(float(d.get("wind", {}).get("speed", 3.0)) * 3.6, 1),  # m/s -> km/h
        "rainfall_mm_last_hr": rain,
        "condition": cond,
        "description": (d.get("weather") or [{}])[0].get("description", ""),
        "source": "openweathermap",
    }


def forecast_by_city(city: str) -> list:
    """5-day / 3-hour forecast (returns simplified list of ~8 slots)."""
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY not set - add it to .env (see .env.example)")
    q = urllib.parse.quote(city)
    url = (f"https://api.openweathermap.org/data/2.5/forecast?q={q},IN&appid={OPENWEATHER_API_KEY}&units=metric&cnt=8")
    d = _get(url)
    out = []
    for item in d.get("list", [])[:8]:
        out.append({
            "time": item.get("dt_txt", ""),
            "temp": float(item.get("main", {}).get("temp", 0)),
            "condition": (item.get("weather") or [{}])[0].get("main", ""),
            "rain_mm": float(((item.get("rain") or {}).get("3h", 0)) or 0),
            "wind_kmh": round(float(item.get("wind", {}).get("speed", 0)) * 3.6, 1),
        })
    return out
