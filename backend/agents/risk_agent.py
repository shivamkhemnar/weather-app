"""B. RISK DETECTION / PREDICTION AGENT - scores shipment risk 0-100."""
import logging
from backend import models
from backend.services.risk_engine import calculate_risk_score, classify_risk, predict_failure_probability, days_until

log = logging.getLogger(__name__)


def assess_shipment(db, shipment, weather, traffic, iot) -> dict:
    """Combine live events + business data into a risk score; persist a Risk row."""
    try:
        supplier = db.query(models.Supplier).filter_by(supplier_id=shipment.supplier_id).first()
        inventory = db.query(models.Inventory).filter(models.Inventory.product_name == shipment.product).first()

        rainfall = getattr(weather, "rainfall", 0) or 0
        wind = getattr(weather, "wind_speed", 10) or 10
        congestion = getattr(traffic, "congestion_level", 20) or 20
        accident = (getattr(traffic, "accident_reported", "No") == "Yes")
        iot_temp = getattr(iot, "temperature", 5.0) or 5.0
        delay = supplier.current_delay_days if supplier else 0.0
        reliability = supplier.reliability_score if supplier else 85.0
        stock_ratio = (inventory.current_stock / inventory.reorder_point) if inventory and inventory.reorder_point else 1.0
        days_left = days_until(shipment.expected_delivery or "")

        score, factors = calculate_risk_score(
            rainfall=rainfall, congestion=congestion, iot_temp=iot_temp,
            supplier_delay_days=delay, reliability=reliability,
            stock_ratio=stock_ratio, days_to_deadline=days_left,
            accident=accident, wind_speed=wind)
        level = classify_risk(score)
        prob = predict_failure_probability(score)

        db.add(models.Risk(shipment_id=shipment.shipment_id, risk_score=score,
                           risk_level=level, factors="\n".join(factors),
                           failure_probability=prob))
        db.commit()
        return {"score": score, "level": level, "factors": factors,
                "failure_probability": prob, "days_left": days_left,
                "stock_ratio": stock_ratio, "supplier_delay": delay}
    except Exception as e:
        db.rollback()
        log.error(f"[risk] assessment failed: {e}")
        return {"score": 0.0, "level": "LOW", "factors": [f"Risk engine error: {e}"],
                "failure_probability": 0.0, "error": str(e)}
