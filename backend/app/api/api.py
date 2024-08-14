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
