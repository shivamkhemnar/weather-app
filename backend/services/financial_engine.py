"""Financial engine: penalties, shortage cost, total disruption cost (pure functions)."""
from backend import models


def get_contract_for_supplier(db, supplier_id: str):
    """Find contract row for a supplier (via supplier.contract_id or supplier_id match)."""
    supplier = db.query(models.Supplier).filter_by(supplier_id=supplier_id).first()
    if supplier and supplier.contract_id:
        c = db.query(models.Contract).filter_by(contract_id=supplier.contract_id).first()
        if c:
            return c
    return db.query(models.Contract).filter_by(supplier_id=supplier_id).first()


def contract_penalty(penalty_per_day: float, delay_days: float, max_days: float) -> float:
    """Penalty = per-day rate x capped delay days. Never negative."""
    try:
        return round(max(0.0, penalty_per_day * min(max(0.0, delay_days), max_days)), 2)
    except Exception:
        return 0.0


def inventory_shortage_cost(shortage_units: int, unit_price: float, factor: float = 0.5) -> float:
    """Lost-margin proxy: shortage_units x unit_price x factor."""
    try:
        return round(max(0, shortage_units) * max(0.0, unit_price) * factor, 2)
    except Exception:
        return 0.0


def disruption_totals(base_transport: float, delay_days: float, penalty: float,
                       shortage_cost: float, risk_score: float) -> dict:
    """Total cost of doing nothing: transport + delay overhead + penalty + shortage + risk cost."""
    delay_overhead = round(max(0.0, delay_days) * 2000.0, 2)  # holding/fuel/driver per day
    risk_cost = round(risk_score * 100.0, 2)  # risk monetised: 1 point = Rs 100
    total = round(base_transport + delay_overhead + penalty + shortage_cost + risk_cost, 2)
    return {
        "transport": round(base_transport, 2),
        "delay_overhead": delay_overhead,
        "penalty": round(penalty, 2),
        "shortage_cost": round(shortage_cost, 2),
        "risk_cost": risk_cost,
        "total": total,
    }
