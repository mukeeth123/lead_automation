from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service_catalog import CompanyService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/services", tags=["Services Catalog"])

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    keywords: List[str] = []
    is_excluded: bool = False

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    services = db.query(CompanyService).all()
    return services

@router.post("/", response_model=ServiceResponse)
def create_service(service: ServiceCreate, db: Session = Depends(get_db)):
    db_service = db.query(CompanyService).filter(CompanyService.name == service.name).first()
    if db_service:
        raise HTTPException(status_code=400, detail="Service with this name already exists")
    
    new_service = CompanyService(**service.dict())
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service

@router.delete("/{service_id}")
def delete_service(service_id: str, db: Session = Depends(get_db)):
    service = db.query(CompanyService).filter(CompanyService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    db.delete(service)
    db.commit()
    return {"status": "success", "message": "Service deleted"}
