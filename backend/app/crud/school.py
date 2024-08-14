from sqlalchemy.orm import Session
from app.models.school import School
from typing import List


def get_schools(db: Session, skip: int = 0, limit: int = 100) -> List[School]:
    """
    Retrieve a list of schools from the database.

    Args:
        db (Session): The database session.
        skip (int): Number of records to skip (for pagination).
        limit (int): Maximum number of records to return.

    Returns:
        List[School]: A list of School objects.
    """
    return db.query(School).offset(skip).limit(limit).all()


def get_school(db: Session, school_id: str) -> School:
    """
    Retrieve a single school by its ID.

    Args:
        db (Session): The database session.
        school_id (str): The ID of the school to retrieve.

    Returns:
        School: The School object if found, None otherwise.
    """
    return db.query(School).filter(School.id == school_id).first()
