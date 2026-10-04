"""D. LOGISTICS OPTIMIZATION AGENT - generates options and picks the best."""
import logging
from backend.services import optimization_engine as oe
from backend.services.decision_engine import build_explanation

log = logging.getLogger(__name__)


def optimize(shipment, risk: dict, finance: dict) -> dict:
    """Generate remediation strategies, score them, return best + explanation."""
    try:
        options = oe.generate_options(
            base_cost=shipment.transportation_cost or 10000.0,
            base_delay=finance.get("delay_days", 2.0),
            base_risk=risk.get("score", 50.0),
            penalty_do_nothing=finance.get("penalty", 0.0),
            shortage_units=finance.get("shortage_units", 0))
        best = oe.select_best(options)
        ranked = sorted(options, key=lambda x: x["score"])
        second = ranked[1] if len(ranked) > 1 else None
        explanation = build_explanation(
            shipment.shipment_id, risk.get("level", "MEDIUM"), risk.get("score", 0.0),
            risk.get("factors", []), best, second, finance.get("totals"))
        return {"best": best, "options": ranked, "explanation": explanation}
    except Exception as e:
        log.error(f"[optimization] failed: {e}")
        fallback = {"action": "Continue current route", "transport_cost": 10000.0,
                    "delay": 2.0, "risk": 50.0, "penalty": 0.0, "score": 0.0}
        return {"best": fallback, "options": [fallback],
                "explanation": f"Optimization fallback (error: {e})", "error": str(e)}
