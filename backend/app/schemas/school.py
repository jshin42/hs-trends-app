from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SchoolBase(BaseModel):
    name: Optional[str] = None
    link: Optional[str] = None
    national_rank: Optional[int] = None
    student_teacher_ratio: Optional[str] = None
    college_readiness: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    district: Optional[str] = None
    reading_proficiency: Optional[str] = None
    grades: Optional[str] = None
    teachers: Optional[str] = None
    college_readiness_index: Optional[str] = None
    medal_awarded: Optional[str] = None
    math_proficiency: Optional[str] = None
    students: Optional[str] = None
    year: Optional[int] = None

    @validator("national_rank", "year", pre=True)
    def parse_integer(cls, value):
        logger.debug(f"Parsing integer value: {value}")
        if isinstance(value, str):
            if value.startswith("#"):
                return int(value[1:])
            try:
                return int(value)
            except ValueError:
                try:
                    return int(datetime.strptime(value, "%Y-%m-%d").year)
                except ValueError:
                    logger.error(f"Cannot parse {value} as an integer or date")
                    raise ValueError(f"Cannot parse {value} as an integer or date")
        return value


class SchoolCreate(SchoolBase):
    id: str


class SchoolUpdate(SchoolBase):
    pass


class School(SchoolBase):
    id: str

    class Config:
        from_attributes = True


class SchoolBasic(BaseModel):
    id: str
    name: str
    city: Optional[str]
    state: Optional[str]

    class Config:
        from_attributes = True


class SchoolRanking(BaseModel):
    year: int
    national_rank: int
    math_proficiency: Optional[str]
    reading_proficiency: Optional[str]
    student_teacher_ratio: Optional[str]
    college_readiness: Optional[str]
    college_readiness_index: Optional[str]
    grades: Optional[str]
    teachers: Optional[str]
    students: Optional[str]
    medal_awarded: Optional[str]

    @validator("year", pre=True)
    def parse_year(cls, value):
        logger.debug(f"Parsing year: {value}")
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").year
            except ValueError:
                logger.error(f"Invalid year format: {value}")
                raise ValueError(f"Invalid year format: {value}")
        return value

    @validator("national_rank", pre=True)
    def parse_rank(cls, value):
        logger.debug(f"Parsing national_rank: {value}")
        if isinstance(value, str):
            if value.startswith("#"):
                return int(value[1:])
            try:
                return int(value)
            except ValueError:
                logger.error(f"Invalid rank format: {value}")
                raise ValueError(f"Invalid rank format: {value}")
        return value

    class Config:
        from_attributes = True


class SchoolOverview(BaseModel):
    school: School
    rankings: List[SchoolRanking]

    class Config:
        from_attributes = True


logger.info("School schemas loaded successfully")
