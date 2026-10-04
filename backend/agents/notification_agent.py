"""F. NOTIFICATION / ALERT AGENT - alerts for HIGH and CRITICAL risks."""
import logging
from backend import models

log = logging.getLogger(__name__)


def maybe_alert(db, shipment_id: str, risk: dict) -> object:
    """Create an Alert row only for HIGH / CRITICAL. Returns the alert or None."""
    try:
        if risk.get("level") in ("HIGH", "CRITICAL"):
            msg = (f"{risk['level']} risk ({risk['score']}/100) on {shipment_id}: "
                   f"{(risk.get('factors') or [''])[0]}")
            alert = models.Alert(shipment_id=shipment_id,
                                 risk_level=risk["level"], message=msg[:500])
            db.add(alert)
            db.commit()
            return alert
        return None
    except Exception as e:
        db.rollback()
        log.error(f"[notification] alert failed: {e}")
        return None
