from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.crud import crud_school
from app.schemas import school as schemas
from app.api import deps
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/schools/search", response_model=List[schemas.SchoolBasic])
def search_schools(name: str = Query(...), db: Session = Depends(deps.get_db)):
    return crud_school.search_schools_by_name(db, name=name)


@router.get("/schools/{school_id}", response_model=schemas.School)
def get_school(school_id: str, db: Session = Depends(deps.get_db)):
    school = crud_school.get_school(db, school_id=school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.get("/schools/{school_id}/rankings", response_model=List[schemas.SchoolRanking])
def get_school_rankings(school_id: str, db: Session = Depends(deps.get_db)):
    rankings = crud_school.get_school_rankings(db, school_id=school_id)
    if not rankings:
        raise HTTPException(
            status_code=404, detail="School not found or no ranking data available"
        )

    logger.info(f"Retrieved {len(rankings)} rankings for school_id: {school_id}")

    try:
        validated_rankings = [schemas.SchoolRanking(**ranking) for ranking in rankings]
        logger.info(f"Successfully validated {len(validated_rankings)} rankings")
        return validated_rankings
    except Exception as e:
        logger.error(f"Validation error for school_id {school_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data validation error: {str(e)}")


@router.get("/schools/{school_id}/overview", response_model=schemas.SchoolOverview)
def get_school_overview(school_id: str, db: Session = Depends(deps.get_db)):
    school = crud_school.get_school(db, school_id=school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    rankings = crud_school.get_school_rankings(db, school_id=school_id)
    if not rankings:
        raise HTTPException(status_code=404, detail="No ranking data available")

    return schemas.SchoolOverview(
        school=schemas.School.from_orm(school), rankings=rankings
    )


@router.post("/schools/", response_model=schemas.School)
def create_school(school: schemas.SchoolCreate, db: Session = Depends(deps.get_db)):
    return crud_school.create_school(db=db, school=school)


@router.put("/schools/{school_id}", response_model=schemas.School)
def update_school(
    school_id: str, school: schemas.SchoolUpdate, db: Session = Depends(deps.get_db)
):
    db_school = crud_school.get_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return crud_school.update_school(db=db, db_school=db_school, school=school)


@router.delete("/schools/{school_id}", response_model=schemas.School)
def delete_school(school_id: str, db: Session = Depends(deps.get_db)):
    db_school = crud_school.get_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return crud_school.delete_school(db=db, db_school=db_school)
