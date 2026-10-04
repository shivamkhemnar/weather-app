"""Simulation engine: generates realistic random logistics data + loads seed CSVs.

No external APIs needed - everything is simulated locally so the demo always works.
"""
import csv
import os
import random
from datetime import datetime, timedelta

from backend import models

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

ROUTES = {
    "SHP-001": ("Mumbai", "Nashik"), "SHP-002": ("Nashik", "Pune"),
    "SHP-003": ("Delhi", "Jaipur"), "SHP-004": ("Chennai", "Bangalore"),
    "SHP-005": ("Pune", "Mumbai"), "SHP-006": ("Hyderabad", "Chennai"),
    "SHP-007": ("Kolkata", "Delhi"), "SHP-008": ("Ahmedabad", "Mumbai"),
}
EXTRA_SHIPMENTS = [
    {"shipment_id": "SHP-006", "product": "Seafood", "supplier_id": "SUP-005",
     "origin": "Hyderabad", "destination": "Chennai", "current_location": "Vijayawada",
     "expected_delivery": "2026-10-05", "current_status": "In Transit",
     "quantity": 450, "transportation_cost": 16000, "distance_km": 520},
    {"shipment_id": "SHP-007", "product": "Grains", "supplier_id": "SUP-003",
     "origin": "Kolkata", "destination": "Delhi", "current_location": "Varanasi",
     "expected_delivery": "2026-10-06", "current_status": "In Transit",
     "quantity": 1200, "transportation_cost": 22000, "distance_km": 1500},
    {"shipment_id": "SHP-008", "product": "Dairy Products", "supplier_id": "SUP-004",
     "origin": "Ahmedabad", "destination": "Mumbai", "current_location": "Surat",
     "expected_delivery": "2026-10-04", "current_status": "In Transit",
     "quantity": 350, "transportation_cost": 14000, "distance_km": 530},
]
WEATHERS = ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Thunderstorm", "Heatwave"]


def _csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_seed_data(db):
    """Load CSVs into SQLite on first startup (idempotent - skips if data exists)."""
    try:
        if db.query(models.Shipment).count() > 0:
            return False
        for row in _csv(os.path.join(DATA_DIR, "suppliers.csv")):
            db.add(models.Supplier(
                supplier_id=row["supplier_id"], supplier_name=row["supplier_name"],
                reliability_score=float(row["reliability_score"]), capacity=int(row["capacity"]),
                current_delay_days=float(row["current_delay_days"]),
                contract_id=row["contract_id"], location=row.get("location", "")))
        for row in _csv(os.path.join(DATA_DIR, "shipments.csv")):
            db.add(models.Shipment(
                shipment_id=row["shipment_id"], product=row["product"],
                supplier_id=row["supplier_id"], origin=row["origin"],
                destination=row["destination"], current_location=row["current_location"],
                expected_delivery=row["expected_delivery"], current_status=row["current_status"],
                quantity=int(row["quantity"]), transportation_cost=float(row["transportation_cost"]),
                distance_km=float(row.get("distance_km", 200))))
        for row in _csv(os.path.join(DATA_DIR, "inventory.csv")):
            db.add(models.Inventory(
                product_id=row["product_id"], product_name=row["product_name"],
                current_stock=int(row["current_stock"]), reorder_point=int(row["reorder_point"]),
                safety_stock=int(row["safety_stock"]), daily_demand=int(row["daily_demand"]),
                unit_price=float(row["unit_price"])))
        for row in _csv(os.path.join(DATA_DIR, "contracts.csv")):
            db.add(models.Contract(
                contract_id=row["contract_id"], supplier_id=row["supplier_id"],
                penalty_per_day=float(row["penalty_per_day"]),
                maximum_delay_days=float(row["maximum_delay_days"]),
                contract_value=float(row["contract_value"]), product=row.get("product", "")))
        db.commit()
        ensure_extra_routes(db)
        return True
    except Exception as e:
        db.rollback()
        print(f"[simulation] seed load failed: {e}")
        return False


def ensure_extra_routes(db):
    """Add all-India shipments to existing DBs (idempotent upsert)."""
    try:
        for row in EXTRA_SHIPMENTS:
            exists = db.query(models.Shipment).filter_by(shipment_id=row["shipment_id"]).first()
            if not exists:
                db.add(models.Shipment(**row))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[simulation] extra routes failed: {e}")


def random_weather(shipment_id: str) -> dict:
    """Random weather reading; occasionally extreme to trigger HIGH/CRITICAL risks."""
    extreme = random.random() < 0.30  # 30% chance of bad weather for demo visibility
    if extreme:
        condition = random.choice(["Heavy Rain", "Thunderstorm"])
        rainfall = round(random.uniform(60, 140), 1)
        wind = round(random.uniform(40, 90), 1)
        severity = "high" if rainfall < 100 else "critical"
    else:
        condition = random.choice(WEATHERS)
        rainfall = round(random.uniform(0, 30) if condition in ("Clear", "Cloudy") else random.uniform(10, 60), 1)
        wind = round(random.uniform(5, 40), 1)
        severity = "low" if rainfall < 15 else "medium"
    return {"shipment_id": shipment_id, "temperature": round(random.uniform(22, 42), 1),
            "rainfall": rainfall, "wind_speed": wind,
            "weather_condition": condition, "severity": severity}


def random_traffic(shipment_id: str) -> dict:
    congestion = round(random.uniform(10, 98), 1)
    accident = "Yes" if random.random() < 0.15 else "No"
    return {"shipment_id": shipment_id, "congestion_level": congestion,
            "average_speed": round(max(8, 80 - congestion * 0.6 + random.uniform(-5, 5)), 1),
            "route_status": "Blocked" if congestion > 90 else ("Congested" if congestion > 60 else "Open"),
            "accident_reported": accident}


def random_iot(shipment_id: str) -> dict:
    anomaly = random.random() < 0.20
    temp = round(random.uniform(9, 16), 1) if anomaly else round(random.uniform(2, 7.5), 1)
    o, d = ROUTES.get(shipment_id, ("Mumbai", "Nashik"))
    return {"shipment_id": shipment_id, "temperature": temp,
            "humidity": round(random.uniform(40, 95), 1),
            "vibration": round(random.uniform(0.1, 3.5), 2),
            "gps_position": f"{o} -> {d} @ {random.randint(5, 95)}%",
            "sensor_status": "Anomaly" if anomaly or temp > 8 else "Normal"}
