"""Pydantic schemas for API responses."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ShipmentOut(BaseModel):
    shipment_id: str
    product: str
    supplier_id: str = ""
    origin: str = ""
    destination: str = ""
    current_location: str = ""
    expected_delivery: str = ""
    current_status: str = ""
    quantity: int = 0
    transportation_cost: float = 0.0
    distance_km: float = 0.0

    class Config:
        from_attributes = True


class RiskOut(BaseModel):
    id: int
    shipment_id: str
    risk_score: float
    risk_level: str
    factors: str = ""
    failure_probability: float = 0.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DecisionOut(BaseModel):
    id: int
    shipment_id: str
    risk_score: float
    risk_level: str
    selected_action: str
    total_cost: float
    expected_delay_days: float
    explanation: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    shipment_id: str
    risk_level: str
    message: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SummaryOut(BaseModel):
    total_shipments: int
    active_shipments: int
    high_risk: int
    critical: int
    delayed: int
    financial_impact: float
    active_alerts: int
    decisions: int
