"""Route planner tests: Mumbai->Nashik must return cost/time/risk + ranked options."""
from backend.services import route_planner as rp


def test_plan_mumbai_nashik():
    r = rp.plan_route("Mumbai", "Nashik", "balanced")
    assert r["origin"] == "Mumbai" and r["destination"] == "Nashik"
    assert r["distance_km"] > 50  # real road distance, not a stub
    assert 0 <= r["risk_score"] <= 100
    assert r["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert len(r["options"]) >= 3
    assert r["picked"]["action"] in [o["action"] for o in r["options"]]


def test_cheapest_is_cheapest():
    r = rp.plan_route("Delhi", "Jaipur", "cheapest")
    costs = [o["transport_cost"] + o.get("penalty", 0) for o in r["options"]]
    assert r["picked"]["transport_cost"] + r["picked"].get("penalty", 0) == min(costs)


def test_fastest_is_fastest():
    r = rp.plan_route("Chennai", "Bangalore", "fastest")
    delays = [o["delay"] for o in r["options"]]
    assert r["picked"]["delay"] == min(delays)


def test_route_api():
    from fastapi.testclient import TestClient
    from backend.main import app
    c = TestClient(app)
    r = c.get("/api/route/plan?origin=Mumbai&destination=Nashik&preference=balanced")
    assert r.status_code == 200
    assert r.json()["distance_km"] > 50
