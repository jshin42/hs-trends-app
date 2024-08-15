from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolUpdate
import logging
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)


def search_schools_by_name(db: Session, name: str, limit: int = 10) -> List[Dict]:
    schools = (
        db.query(School.id, School.name, School.city, School.state)
        .filter(func.lower(School.name).contains(func.lower(name)))
        .limit(limit)
        .all()
    )
    return [
        {"id": id, "name": name, "city": city, "state": state}
        for id, name, city, state in schools
    ]


def get_school(db: Session, school_id: str) -> Optional[School]:
    return db.query(School).filter(School.id == school_id).first()


def get_school_rankings(db: Session, school_id: str) -> List[Dict]:
    rankings = (
        db.query(School)
        .filter(School.id == school_id)
        .order_by(School.year.desc())
        .all()
    )

    logger.info(
        f"Retrieved {len(rankings)} rankings from database for school_id: {school_id}"
    )

    return [
        {
            "year": school.year,
            "national_rank": school.national_rank,
            "math_proficiency": school.math_proficiency,
            "reading_proficiency": school.reading_proficiency,
            "student_teacher_ratio": school.student_teacher_ratio,
            "college_readiness": school.college_readiness,
            "college_readiness_index": school.college_readiness_index,
            "grades": school.grades,
            "teachers": school.teachers,
            "students": school.students,
            "medal_awarded": school.medal_awarded,
        }
        for school in rankings
    ]


def get_school_overview(db: Session, school_id: str) -> Dict:
    school = get_school(db, school_id)
    if not school:
        return None

    rankings = get_school_rankings(db, school_id)

    return {"school": school, "rankings": rankings}


def create_school(db: Session, school: SchoolCreate) -> School:
    db_school = School(**school.dict())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school


def update_school(db: Session, db_school: School, school: SchoolUpdate) -> School:
    school_data = school.dict(exclude_unset=True)
    for key, value in school_data.items():
        setattr(db_school, key, value)
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school


def delete_school(db: Session, db_school: School) -> School:
    db.delete(db_school)
    db.commit()
    return db_school
