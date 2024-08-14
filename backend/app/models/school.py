from sqlalchemy import Column, String, Integer
from app.db.base import Base


class School(Base):
    __tablename__ = "schools"

    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    link = Column(String)
    national_rank = Column(Integer)  # Changed to Integer
    student_teacher_ratio = Column(String)
    college_readiness = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    phone = Column(String)
    district = Column(String)
    reading_proficiency = Column(String)
    grades = Column(String)
    teachers = Column(String)
    college_readiness_index = Column(String)
    medal_awarded = Column(String)
    math_proficiency = Column(String)
    students = Column(String)
    year = Column(Integer)  # Add this line
