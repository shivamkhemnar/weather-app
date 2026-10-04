"""Risk calculation tests."""
from backend.services.risk_engine import calculate_risk_score, classify_risk, predict_failure_probability


def test_low_risk_conditions():
    score, factors = calculate_risk_score(rainfall=0, congestion=10, iot_temp=4.0,
                                          supplier_delay_days=0, reliability=95,
                                          stock_ratio=1.5, days_to_deadline=10)
    assert score < 35
    assert classify_risk(score) == "LOW"


def test_critical_scenario_shp001():
    # SHP-001 demo scenario: heavy rain + congestion + anomaly + delay + low stock + deadline near
    score, factors = calculate_risk_score(rainfall=110, congestion=85, iot_temp=12.0,
                                          supplier_delay_days=2, reliability=82,
                                          stock_ratio=0.6, days_to_deadline=2, accident=True)
    assert score >= 80
    assert classify_risk(score) == "CRITICAL"


def test_classification_boundaries():
    assert classify_risk(10) == "LOW"
    assert classify_risk(40) == "MEDIUM"
    assert classify_risk(65) == "HIGH"
    assert classify_risk(87) == "CRITICAL"


def test_failure_probability_range():
    for s in [0, 30, 60, 87, 100]:
        p = predict_failure_probability(s)
        assert 0.0 <= p <= 1.0
    assert predict_failure_probability(87) > predict_failure_probability(20)
