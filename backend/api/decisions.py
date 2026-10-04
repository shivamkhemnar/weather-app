"""Decision + alert history APIs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models

router = APIRouter()


@router.get("/decisions")
def list_decisions(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Decision).order_by(models.Decision.id.desc()).limit(limit).all()


@router.get("/decisions/{decision_id}")
def get_decision(decision_id: int, db: Session = Depends(get_db)):
    d = db.query(models.Decision).filter_by(id=decision_id).first()
    if not d:
        raise HTTPException(404, "Decision not found")
    return d


@router.get("/alerts")
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Alert).order_by(models.Alert.id.desc()).limit(limit).all()
