"""SQLAlchemy ORM models - one table per entity in the spec."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from backend.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(String, unique=True, index=True)
    supplier_name = Column(String)
    reliability_score = Column(Float, default=80.0)
    capacity = Column(Integer, default=1000)
    current_delay_days = Column(Float, default=0.0)
    contract_id = Column(String, default="")
    location = Column(String, default="")


class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, unique=True, index=True)
    product = Column(String)
    supplier_id = Column(String, default="")
    origin = Column(String, default="")
    destination = Column(String, default="")
    current_location = Column(String, default="")
    expected_delivery = Column(String, default="")
    current_status = Column(String, default="In Transit")
    quantity = Column(Integer, default=100)
    transportation_cost = Column(Float, default=10000.0)
    distance_km = Column(Float, default=200.0)


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True, index=True)
    product_name = Column(String)
    current_stock = Column(Integer, default=100)
    reorder_point = Column(Integer, default=200)
    safety_stock = Column(Integer, default=80)
    daily_demand = Column(Integer, default=50)
    unit_price = Column(Float, default=50.0)


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(String, unique=True, index=True)
    supplier_id = Column(String, default="")
    penalty_per_day = Column(Float, default=5000.0)
    maximum_delay_days = Column(Float, default=5.0)
    contract_value = Column(Float, default=500000.0)
    product = Column(String, default="")


class WeatherEvent(Base):
    __tablename__ = "weather_events"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, default="")
    temperature = Column(Float, default=30.0)
    rainfall = Column(Float, default=0.0)  # mm
    wind_speed = Column(Float, default=10.0)  # km/h
    weather_condition = Column(String, default="Clear")
    severity = Column(String, default="low")
    created_at = Column(DateTime, default=datetime.utcnow)


class TrafficEvent(Base):
    __tablename__ = "traffic_events"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, default="")
    congestion_level = Column(Float, default=20.0)  # 0-100
    average_speed = Column(Float, default=60.0)  # km/h
    route_status = Column(String, default="Open")
    accident_reported = Column(String, default="No")
    created_at = Column(DateTime, default=datetime.utcnow)


class IoTEvent(Base):
    __tablename__ = "iot_events"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, default="")
    temperature = Column(Float, default=5.0)
    humidity = Column(Float, default=60.0)
    vibration = Column(Float, default=0.5)
    gps_position = Column(String, default="")
    sensor_status = Column(String, default="Normal")
    created_at = Column(DateTime, default=datetime.utcnow)


class Risk(Base):
    __tablename__ = "risks"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, index=True)
    risk_score = Column(Float, default=0.0)  # 0-100
    risk_level = Column(String, default="LOW")  # LOW/MEDIUM/HIGH/CRITICAL
    factors = Column(Text, default="")  # human-readable explanation
    failure_probability = Column(Float, default=0.0)  # 0-1 (simple ML/logistic)
    created_at = Column(DateTime, default=datetime.utcnow)


class Decision(Base):
    __tablename__ = "decisions"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, index=True)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="LOW")
    selected_action = Column(String, default="")
    total_cost = Column(Float, default=0.0)
    expected_delay_days = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    options_compared = Column(Text, default="")  # JSON string of evaluated options
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String, default="")
    risk_level = Column(String, default="HIGH")
    message = Column(String, default="")
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
