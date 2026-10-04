"""Financial impact + penalty tests."""
from backend.services import financial_engine as fe


def test_penalty_basic():
    assert fe.contract_penalty(5000, 3, 5) == 15000


def test_penalty_capped_at_max():
    assert fe.contract_penalty(5000, 10, 5) == 25000  # capped at 5 days


def test_penalty_no_delay():
    assert fe.contract_penalty(5000, 0, 5) == 0


def test_shortage_cost():
    assert fe.inventory_shortage_cost(20, 40) == 20 * 40 * 0.5
    assert fe.inventory_shortage_cost(0, 40) == 0


def test_disruption_totals_add_up():
    t = fe.disruption_totals(10000, 3, 15000, 2000, 87)
    assert t["total"] == 10000 + 3 * 2000 + 15000 + 2000 + 87 * 100
