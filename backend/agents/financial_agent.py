"""C. FINANCIAL & CONTRACT ANALYSIS AGENT - cost of doing nothing vs acting."""
import logging
from backend import models
from backend.services import financial_engine as fe

log = logging.getLogger(__name__)


def analyze(db, shipment, risk: dict) -> dict:
    """Estimate delay, penalty, shortage and total disruption cost."""
    try:
        contract = fe.get_contract_for_supplier(db, shipment.supplier_id)
        inventory = db.query(models.Inventory).filter(models.Inventory.product_name == shipment.product).first()

        # Expected delay grows with risk: 0.5 day baseline up to ~4 days at score 100
        base_delay = round(0.5 + (risk["score"] / 100.0) * 3.5, 1)
        supplier_delay = risk.get("supplier_delay", 0.0)
        delay_days = round(max(base_delay, supplier_delay), 1)

        penalty = fe.contract_penalty(
            contract.penalty_per_day if contract else 5000.0,
            delay_days, contract.maximum_delay_days if contract else 5.0)

        shortage_units, unit_price = 0, 50.0
        if inventory:
            unit_price = inventory.unit_price or 50.0
            if inventory.current_stock < inventory.safety_stock:
                shortage_units = max(0, inventory.safety_stock - inventory.current_stock)
        shortage_cost = fe.inventory_shortage_cost(shortage_units, unit_price)

        totals = fe.disruption_totals(shipment.transportation_cost or 10000.0,
                                      delay_days, penalty, shortage_cost, risk["score"])
        return {"delay_days": delay_days, "penalty": penalty,
                "shortage_units": shortage_units, "shortage_cost": shortage_cost,
                "totals": totals,
                "contract_id": contract.contract_id if contract else "N/A"}
    except Exception as e:
        log.error(f"[financial] analysis failed: {e}")
        return {"delay_days": 1.0, "penalty": 0.0, "shortage_units": 0,
                "shortage_cost": 0.0, "totals": {"total": 0.0, "penalty": 0.0},
                "error": str(e)}
