"""Risk history APIs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models

router = APIRouter()


@router.get("/risks")
def list_risks(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Risk).order_by(models.Risk.id.desc()).limit(limit).all()


@router.get("/risks/{risk_id}")
def get_risk(risk_id: int, db: Session = Depends(get_db)):
    r = db.query(models.Risk).filter_by(id=risk_id).first()
    if not r:
        raise HTTPException(404, "Risk not found")
    return r
