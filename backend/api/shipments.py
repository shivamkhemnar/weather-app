"""Shipment / inventory / supplier / contract / event read APIs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models

router = APIRouter()


@router.get("/shipments")
def list_shipments(db: Session = Depends(get_db)):
    return db.query(models.Shipment).all()


@router.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    s = db.query(models.Shipment).filter_by(shipment_id=shipment_id).first()
    if not s:
        raise HTTPException(404, "Shipment not found")
    return s


@router.get("/inventory")
def list_inventory(db: Session = Depends(get_db)):
    return db.query(models.Inventory).all()


@router.get("/suppliers")
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(models.Supplier).all()


@router.get("/contracts")
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).all()


@router.get("/weather")
def list_weather(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.WeatherEvent).order_by(models.WeatherEvent.id.desc()).limit(limit).all()


@router.get("/traffic")
def list_traffic(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.TrafficEvent).order_by(models.TrafficEvent.id.desc()).limit(limit).all()


@router.get("/iot")
def list_iot(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.IoTEvent).order_by(models.IoTEvent.id.desc()).limit(limit).all()
