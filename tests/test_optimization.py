"""Optimization: winner must be computed dynamically, never hardcoded."""
from backend.services import optimization_engine as oe


def test_best_is_dynamic():
    opts = oe.generate_options(base_cost=10000, base_delay=3.0, base_risk=87,
                               penalty_do_nothing=15000, shortage_units=10)
    assert len(opts) >= 3
    best = oe.select_best(opts)
    # Every option must have a score and best must be the minimum
    assert all("score" in o for o in opts)
    assert best["score"] == min(o["score"] for o in opts)


def test_low_risk_prefers_cheap_option():
    # Calm conditions: continuing should beat expensive alternates
    opts = oe.generate_options(base_cost=10000, base_delay=0.5, base_risk=10,
                               penalty_do_nothing=0, shortage_units=0)
    best = oe.select_best(opts)
    assert best["action"] == "Continue current route"


def test_score_option_weights():
    o = {"transport_cost": 14000, "penalty": 0, "delay": 1.0, "risk": 30.0, "shortage_units": 0}
    s = oe.score_option(o)
    assert s > 0
