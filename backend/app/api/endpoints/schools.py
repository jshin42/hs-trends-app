from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=list[schemas.School])
def read_schools(db: Session = Depends(deps.get_db)):
    return crud.get_schools(db)


@router.get("/{school_id}", response_model=schemas.School)
def read_school(school_id: str, db: Session = Depends(deps.get_db)):
    db_school = crud.get_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school
