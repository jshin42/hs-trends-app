from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.school import School
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)


def search_schools_by_name(
    db: Session, name: str, limit: int = 10
) -> List[Tuple[str, str]]:
    return (
        db.query(School.id, School.name)
        .filter(func.lower(School.name).contains(func.lower(name)))
        .limit(limit)
        .all()
    )


def get_school_rankings(db: Session, school_id: str) -> List[Dict]:
    rankings = (
        db.query(
            School.year,
            School.national_rank,
            School.math_proficiency,
            School.reading_proficiency,
            School.student_teacher_ratio,
        )
        .filter(School.id == school_id)
        .all()
    )

    logger.info(
        f"Retrieved {len(rankings)} rankings from database for school_id: {school_id}"
    )

    # Convert to list of dicts for easier manipulation
    return [
        {
            "year": year,
            "national_rank": national_rank,
            "math_proficiency": math_proficiency,
            "reading_proficiency": reading_proficiency,
            "student_teacher_ratio": student_teacher_ratio,
        }
        for year, national_rank, math_proficiency, reading_proficiency, student_teacher_ratio in rankings
    ]
