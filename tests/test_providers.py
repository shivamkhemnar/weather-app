"""Live providers: must fail soft (no crash) when keys are missing."""
import os


def test_weather_provider_requires_key():
    from backend.services import weather_provider as wp
    if os.getenv("OPENWEATHER_API_KEY"):
        return  # skip when a real key is configured
    try:
        wp.current_by_city("Mumbai")
        assert False, "should have raised without key"
    except RuntimeError as e:
        assert "OPENWEATHER_API_KEY" in str(e)


def test_traffic_provider_requires_key():
    from backend.services import traffic_provider as tp
    if os.getenv("TOMTOM_API_KEY"):
        return
    try:
        tp.flow_by_city("Mumbai")
        assert False, "should have raised without key"
    except RuntimeError as e:
        assert "TOMTOM_API_KEY" in str(e)


def test_live_endpoints_fallback():
    from fastapi.testclient import TestClient
    from backend.main import app
    c = TestClient(app)
    w = c.get("/api/weather/live?city=Mumbai")
    assert w.status_code == 200
    assert w.json()["source"] in ("stored-fallback", "openweathermap")
    t = c.get("/api/traffic/live?city=Mumbai")
    assert t.status_code == 200
    s = c.get("/api/settings/status")
    assert s.status_code == 200
    assert "refresh_hours" in s.json()
