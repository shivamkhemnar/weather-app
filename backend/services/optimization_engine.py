"""Optimization engine: generate remediation options, score them, pick the best.

Total objective (lower is better):
    score = cost*w_cost + delay*w_delay*SCALE + risk*w_risk*SCALE + inventory*w_inv*SCALE
NOT hardcoded: the winner is computed dynamically from weights + live inputs.
"""
from backend.config import COST_WEIGHT, DELAY_WEIGHT, RISK_WEIGHT, INVENTORY_WEIGHT

# Scale delays/risks to rupees so weights are comparable
DELAY_RUPEE_PER_DAY = 8000.0
RISK_RUPEE_PER_POINT = 100.0
INVENTORY_RUPEE_PER_UNIT = 50.0


def generate_options(base_cost: float, base_delay: float, base_risk: float,
                     penalty_do_nothing: float, shortage_units: int) -> list:
    """Build candidate strategies. Costs/delays are relative adjustments - dynamic, not fixed."""
    opts = [
        {"action": "Continue current route", "extra_cost": 0,
         "delay": base_delay, "risk": base_risk, "penalty": penalty_do_nothing},
        {"action": "Reroute shipment", "extra_cost": 4000,
         "delay": max(0.2, base_delay - 2.0), "risk": max(5, base_risk - 30), "penalty": 0},
        {"action": "Expedite shipment", "extra_cost": 7000,
         "delay": max(0.2, base_delay - 1.5), "risk": max(5, base_risk - 15), "penalty": 0},
        {"action": "Use alternate supplier", "extra_cost": 10000,
         "delay": 0.5, "risk": 25.0, "penalty": 0},
        {"action": "Split shipment", "extra_cost": 5000,
         "delay": max(0.3, base_delay - 1.0), "risk": max(5, base_risk - 20), "penalty": penalty_do_nothing / 2},
    ]
    for o in opts:
        o["transport_cost"] = round(base_cost + o["extra_cost"], 2)
        o["shortage_units"] = shortage_units if "Continue" in o["action"] or "Split" in o["action"] else 0
    return opts


def score_option(opt: dict, weights: dict = None) -> float:
    """Weighted objective score (lower = better)."""
    w = weights or {"cost": COST_WEIGHT, "delay": DELAY_WEIGHT,
                    "risk": RISK_WEIGHT, "inventory": INVENTORY_WEIGHT}
    cost_term = opt["transport_cost"] + opt.get("penalty", 0)
    delay_term = opt.get("delay", 0) * DELAY_RUPEE_PER_DAY
    risk_term = opt.get("risk", 0) * RISK_RUPEE_PER_POINT
    inv_term = opt.get("shortage_units", 0) * INVENTORY_RUPEE_PER_UNIT
    return round(w["cost"] * cost_term + w["delay"] * delay_term
                 + w["risk"] * risk_term + w["inventory"] * inv_term, 2)


def select_best(options: list, weights: dict = None) -> dict:
    """Score every option and return the lowest-score one (with scores attached)."""
    for o in options:
        o["score"] = score_option(o, weights)
    return min(options, key=lambda x: x["score"])
