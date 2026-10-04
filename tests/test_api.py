"""Decision explanation + API health tests."""
from fastapi.testclient import TestClient
from backend.services.decision_engine import build_explanation


def test_explanation_contains_reasoning():
    best = {"action": "Reroute shipment", "transport_cost": 14000, "delay": 1.0,
            "penalty": 0, "score": 9000}
    exp = build_explanation("SHP-001", "CRITICAL", 87.0,
                            ["Heavy rainfall increased route risk."],
                            best, totals={"penalty": 15000})
    assert "SHP-001" in exp and "Reroute" in exp and "Heavy rainfall" in exp


def test_health_endpoint():
    from backend.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
