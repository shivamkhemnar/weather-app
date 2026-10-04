"""E. DECISION / ORCHESTRATOR AGENT - runs the full pipeline for one shipment."""
import json
import logging
import random
from backend import models
from backend.database import SessionLocal
from backend.agents import monitoring_agent, risk_agent, financial_agent, optimization_agent, notification_agent

log = logging.getLogger(__name__)


def run_cycle_for_shipment(shipment_id: str = None) -> dict:
    """One autonomous cycle: monitor -> risk -> finance -> optimize -> decide -> alert.

    Each step is wrapped so one bad event never crashes the loop.
    Returns a summary dict for logging/dashboard.
    """
    db = SessionLocal()
    try:
        # Pick a shipment (random if not specified)
        if shipment_id:
            shipment = db.query(models.Shipment).filter_by(shipment_id=shipment_id).first()
        else:
            shipments = db.query(models.Shipment).all()
            shipment = random.choice(shipments) if shipments else None
        if not shipment:
            return {"ok": False, "error": "no shipments in database"}

        events = monitoring_agent.collect_tick(db, shipment.shipment_id)
        lat = monitoring_agent.latest_events(db, shipment.shipment_id)
        risk = risk_agent.assess_shipment(db, shipment, lat["weather"], lat["traffic"], lat["iot"])
        finance = financial_agent.analyze(db, shipment, risk)
        opt = optimization_agent.optimize(shipment, risk, finance)

        best = opt["best"]
        # Persist the autonomous decision
        decision = models.Decision(
            shipment_id=shipment.shipment_id, risk_score=risk["score"],
            risk_level=risk["level"], selected_action=best["action"],
            total_cost=round(best.get("transport_cost", 0) + best.get("penalty", 0), 2),
            expected_delay_days=best.get("delay", 0),
            explanation=opt["explanation"],
            options_compared=json.dumps(opt["options"][:5], default=str)[:4000])
        db.add(decision)

        # Update shipment status from risk level
        if risk["level"] == "CRITICAL":
            shipment.current_status = "At Risk"
        elif risk["level"] == "HIGH":
            shipment.current_status = "Delayed" if finance.get("delay_days", 0) > 2 else "In Transit"
        db.commit()

        alert = notification_agent.maybe_alert(db, shipment.shipment_id, risk)

        return {"ok": True, "shipment_id": shipment.shipment_id,
                "risk_score": risk["score"], "risk_level": risk["level"],
                "action": best["action"], "total_cost": decision.total_cost,
                "alert": alert.message if alert else None}
    except Exception as e:
        log.error(f"[orchestrator] cycle failed: {e}")
        return {"ok": False, "error": str(e)}
    finally:
        db.close()
