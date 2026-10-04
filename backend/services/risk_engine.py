"""Risk engine: transparent rule-based scoring (0-100) + tiny logistic ML fallback.

Rules (beginner-friendly, easy to explain to a professor):
- Heavy rain -> +risk | Traffic congestion -> +risk
- IoT temperature anomaly -> +risk | Supplier delay -> +risk
- Low inventory -> +risk | Near deadline -> +risk | Low reliability -> +risk
"""
import math
from datetime import datetime


def classify_risk(score: float) -> str:
    """Classify 0-100 score into LOW / MEDIUM / HIGH / CRITICAL."""
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def calculate_risk_score(
    rainfall: float = 0.0,
    congestion: float = 0.0,
    iot_temp: float = 5.0,
    iot_temp_limit: float = 8.0,
    supplier_delay_days: float = 0.0,
    reliability: float = 85.0,
    stock_ratio: float = 1.0,   # current_stock / reorder_point
    days_to_deadline: float = 5.0,
    accident: bool = False,
    wind_speed: float = 10.0,
) -> tuple:
    """Return (score 0-100, factors list of strings). Pure function - easy to test."""
    score = 5.0  # base background risk
    factors = []

    # 1. Rainfall (mm in last tick): >80 heavy, >40 moderate
    if rainfall >= 80:
        score += 25
        factors.append(f"Heavy rainfall ({rainfall:.0f}mm) increased route risk.")
    elif rainfall >= 40:
        score += 14
        factors.append(f"Moderate rainfall ({rainfall:.0f}mm) raised risk.")
    elif rainfall >= 15:
        score += 6
        factors.append(f"Light rainfall ({rainfall:.0f}mm) slightly raised risk.")

    # 2. Traffic congestion 0-100
    if congestion >= 80:
        score += 20
        factors.append(f"Severe traffic congestion ({congestion:.0f}%) on route.")
    elif congestion >= 55:
        score += 12
        factors.append(f"High traffic congestion ({congestion:.0f}%).")
    elif congestion >= 35:
        score += 6
        factors.append(f"Moderate traffic ({congestion:.0f}%).")

    if accident:
        score += 10
        factors.append("Road accident reported on route.")

    # 3. Wind
    if wind_speed >= 70:
        score += 10
        factors.append(f"High winds ({wind_speed:.0f} km/h).")
    elif wind_speed >= 45:
        score += 5
        factors.append(f"Strong winds ({wind_speed:.0f} km/h).")

    # 4. IoT temperature anomaly (cold chain)
    if iot_temp > iot_temp_limit + 4:
        score += 15
        factors.append(f"IoT temperature anomaly ({iot_temp:.1f}C vs limit {iot_temp_limit}C).")
    elif iot_temp > iot_temp_limit:
        score += 8
        factors.append(f"IoT temperature above limit ({iot_temp:.1f}C).")

    # 5. Supplier delay
    if supplier_delay_days >= 3:
        score += 18
        factors.append(f"Supplier delayed by {supplier_delay_days:.1f} days.")
    elif supplier_delay_days >= 1.5:
        score += 12
        factors.append(f"Supplier delay of {supplier_delay_days:.1f} days.")
    elif supplier_delay_days >= 0.5:
        score += 6
        factors.append(f"Minor supplier delay ({supplier_delay_days:.1f} day).")

    # 6. Supplier reliability (0-100, higher is better)
    if reliability < 60:
        score += 12
        factors.append(f"Low supplier reliability ({reliability:.0f}/100).")
    elif reliability < 75:
        score += 7
        factors.append(f"Below-average supplier reliability ({reliability:.0f}/100).")

    # 7. Inventory: stock_ratio < 1 means below reorder point
    if stock_ratio < 0.4:
        score += 12
        factors.append("Inventory critically low (below safety stock).")
    elif stock_ratio < 0.7:
        score += 8
        factors.append("Inventory below safety stock.")
    elif stock_ratio < 1.0:
        score += 4
        factors.append("Inventory below reorder point.")

    # 8. Deadline pressure
    if days_to_deadline <= 1:
        score += 12
        factors.append("Delivery deadline within 1 day - high urgency.")
    elif days_to_deadline <= 3:
        score += 7
        factors.append(f"Only {days_to_deadline:.1f} days left to deadline.")

    if not factors:
        factors.append("No major risk factors - conditions normal.")

    return max(0.0, min(100.0, round(score, 1))), factors


def predict_failure_probability(risk_score: float) -> float:
    """Tiny logistic model mapping risk score -> failure probability.

    This is a lightweight ML-style predictor (logistic curve).
    Rule-based fallback: if this function fails, callers use risk_score/100.
    """
    try:
        # Logistic: p = 1 / (1 + exp(-(a*x + b))), tuned so 50->0.5, 87->~0.9
        a, b = 0.09, -4.5
        p = 1.0 / (1.0 + math.exp(-(a * risk_score + b)))
        return round(p, 3)
    except Exception:
        return round(max(0.0, min(1.0, risk_score / 100.0)), 3)


def days_until(deadline_str: str) -> float:
    """Parse 'YYYY-MM-DD' deadline -> days remaining (negative if overdue)."""
    try:
        d = datetime.strptime(deadline_str[:10], "%Y-%m-%d")
        return (d - datetime.utcnow()).total_seconds() / 86400.0
    except Exception:
        return 5.0
