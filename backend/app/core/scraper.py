import asyncio
import aiohttp
from bs4 import BeautifulSoup
import structlog
import time
import random
import uuid
import json
import os
from datetime import datetime
from typing import List, Dict, AsyncGenerator, Optional
import databases
from sqlalchemy import MetaData, Table, Column, String
from ..db.base import engine
from ..core.config import settings
from ..db.base import Base
from pydantic import BaseModel, Field, validator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import chardet
from dataclasses import dataclass


@dataclass
class Settings:
    BASE_URL: str = settings.BASE_SCRAPER_URL
    INITIAL_URL: str = f"{BASE_URL}/web/20121231154127/http://www.usnews.com/education/best-high-schools/national-rankings/spp+100"
    DATABASE_URL: str = "sqlite:///schools4.db"
    CHECKPOINT_FILE: str = "scraper_checkpoint.json"
    LOG_FILE: str = "scraper.log"
    MAX_RETRIES: int = 5
    RETRY_DELAY: int = 2
    MAX_CONCURRENT_REQUESTS: int = 5
    CHECKPOINT_INTERVAL: int = 15 * 60  # 15 minutes
    RATE_LIMIT: float = 0.5  # requests per second


settings = Settings()


class School(BaseModel):
    id: str
    name: str
    link: str
    national_rank: str
    student_teacher_ratio: Optional[str] = Field(default="N/A")
    college_readiness: Optional[str] = Field(default="N/A")
    address: Optional[str] = Field(default="N/A")
    city: Optional[str] = Field(default="N/A")
    state: Optional[str] = Field(default="N/A")
    phone: Optional[str] = Field(default="N/A")
    district: Optional[str] = Field(default="N/A")
    reading_proficiency: Optional[str] = Field(default="N/A")
    grades: Optional[str] = Field(default="N/A")
    teachers: Optional[str] = Field(default="N/A")
    college_readiness_index: Optional[str] = Field(default="N/A")
    medal_awarded: Optional[str] = Field(default="N/A")
    math_proficiency: Optional[str] = Field(default="N/A")
    students: Optional[str] = Field(default="N/A")

    class Config:
        extra = "allow"

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v


database = databases.Database(settings.DATABASE_URL)
metadata = Base.metadata

schools = Table(
    "schools",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String),
    Column("link", String),
    Column("national_rank", String),
    Column("student_teacher_ratio", String),
    Column("college_readiness", String),
    Column("address", String),
    Column("city", String),
    Column("state", String),
    Column("phone", String),
    Column("district", String),
    Column("reading_proficiency", String),
    Column("grades", String),
    Column("teachers", String),
    Column("college_readiness_index", String),
    Column("medal_awarded", String),
    Column("math_proficiency", String),
    Column("students", String),
)


metadata.drop_all(engine)
metadata.create_all(engine)


async def save_school(school_data: dict):
    valid_keys = [c.name for c in schools.columns]
    filtered_data = {k: v for k, v in school_data.items() if k in valid_keys}
    query = schools.insert().values(**filtered_data)
    await database.execute(query)


structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


class AdaptiveRateLimiter:
    def __init__(
        self, initial_rate: float = 0.5, max_rate: float = 2.0, min_rate: float = 0.1
    ):
        self.current_rate = initial_rate
        self.max_rate = max_rate
        self.min_rate = min_rate

    async def wait(self):
        await asyncio.sleep(1 / self.current_rate)

    def adjust_rate(self, success: bool):
        if success:
            self.current_rate = min(self.current_rate * 1.1, self.max_rate)
        else:
            self.current_rate = max(self.current_rate * 0.9, self.min_rate)


class DynamicSemaphore:
    def __init__(self, initial_value: int, min_value: int, max_value: int):
        self.semaphore = asyncio.Semaphore(initial_value)
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = initial_value

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.release()

    async def acquire(self):
        await self.semaphore.acquire()

    def release(self):
        self.semaphore.release()

    def adjust(self, success: bool):
        if success and self.current_value < self.max_value:
            self.current_value += 1
            self.semaphore = asyncio.Semaphore(self.current_value)
        elif not success and self.current_value > self.min_value:
            self.current_value -= 1
            self.semaphore = asyncio.Semaphore(self.current_value)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 10, reset_timeout: int = 600):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = None

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

    def reset(self):
        self.failure_count = 0
        self.last_failure_time = None

    @property
    def is_open(self):
        if self.failure_count >= self.failure_threshold:
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.reset()
                return False
            return True
        return False


class SchoolScraper:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        rate_limiter: AdaptiveRateLimiter,
        semaphore: DynamicSemaphore,
        circuit_breaker: CircuitBreaker,
    ):
        self.session = session
        self.last_checkpoint = time.time()
        self.circuit_breaker = circuit_breaker
        self.rate_limiter = rate_limiter
        self.dynamic_semaphore = semaphore
        self.backoff_time = 60  # Start with a 1-minute backoff

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(aiohttp.ClientResponseError),
    )
    async def fetch_page(self, url: str) -> Optional[str]:
        while self.circuit_breaker.is_open:
            logger.warning(
                f"Circuit breaker is open. Waiting for {self.backoff_time} seconds before retrying."
            )
            await asyncio.sleep(self.backoff_time)
            self.backoff_time *= 2  # Exponential backoff
            if self.backoff_time > 3600:  # Cap at 1 hour
                self.backoff_time = 3600

        await self.rate_limiter.wait()
        async with self.dynamic_semaphore:
            try:
                async with self.session.get(url) as response:
                    if response.status == 404:
                        logger.warning("Page not found", url=url)
                        return None
                    if response.status == 403:
                        logger.warning("Access forbidden", url=url)
                        return None
                    response.raise_for_status()
                    content = await response.read()
                    encoding = chardet.detect(content)["encoding"]
                    self.rate_limiter.adjust_rate(True)
                    self.dynamic_semaphore.adjust(True)
                    return content.decode(encoding or "utf-8", errors="replace")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.circuit_breaker.record_failure()
                self.rate_limiter.adjust_rate(False)
                self.dynamic_semaphore.adjust(False)
                logger.error("Error fetching page", url=url, error=str(e))
                raise
            except Exception as e:
                logger.error("Unexpected error fetching page", url=url, error=str(e))
                raise

    def parse_rankings_page(self, html: str) -> List[School]:
        soup = BeautifulSoup(html, "html.parser")
        schools = []
        rows = soup.select("table.ranking-data tbody tr")

        for row in rows:
            try:
                rank_elem = row.select_one(
                    "td.column-first.column-odd.rank span.rankings-score"
                )
                name_elem = row.select_one("td.hs_display_name a")
                if rank_elem and name_elem:
                    school = School(
                        id=str(uuid.uuid4()),
                        name=name_elem.text.strip(),
                        link=settings.BASE_URL + name_elem["href"],
                        national_rank=rank_elem.text.strip(),
                        student_teacher_ratio=row.select_one(
                            "td.g_school_in_country_student_teachers_stacked .lead-value"
                        ).text.strip(),
                        college_readiness=row.select_one(
                            "td.g_school_in_country_college_readiness_index_stacked .lead-value"
                        ).text.strip(),
                    )
                    schools.append(school)
                else:
                    logger.warning(
                        "Could not find rank or name for a school in the list"
                    )
            except AttributeError as e:
                logger.error("Error parsing row in rankings page", error=str(e))
                continue

        return schools

    def get_next_page_url(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", class_="pager_link", string=">")
        if next_link and "href" in next_link.attrs:
            return settings.BASE_URL + next_link["href"]
        return None

    async def parse_school_page(self, school: School) -> School:
        html = await self.fetch_page(school.link)
        if not html:
            logger.error("Failed to fetch school page", school_name=school.name)
            return school

        soup = BeautifulSoup(html, "html.parser")

        try:
            # School Name and Basic Info
            name_elem = soup.find("h1")
            if name_elem:
                school.name = name_elem.text.strip()
            else:
                logger.warning(
                    "Could not find name for school", school_name=school.name
                )

            school_box = soup.find("div", id="schoolbox")
            if school_box:
                address = school_box.find_all("p")[0].text.strip()
                school.address = address
                city_state = address.split(",")[-2:]
                school.city = city_state[0].strip() if len(city_state) > 1 else "N/A"
                school.state = (
                    city_state[1].strip().split()[0] if len(city_state) > 1 else "N/A"
                )
                school.phone = (
                    school_box.find_all("p")[1]
                    .text.strip()
                    .replace("Phone:", "")
                    .strip()
                )

            # District
            district_elem = soup.find("p", id="district")
            if district_elem:
                school.district = district_elem.text.replace("District:", "").strip()

            # Ensure we have the national rank
            if school.national_rank == "N/A":
                rank_elem = soup.select_one(
                    'table.fields.rankings_awards td:contains("National Rankings") + td'
                )
                if rank_elem:
                    school.national_rank = rank_elem.text.strip()
                else:
                    logger.warning(
                        "Could not find national rank on detail page",
                        school_name=school.name,
                    )

            # Academic Indicators
            score_box = soup.find("div", id="scorebox")
            if score_box:
                indicators = score_box.find_all("dt")
                for indicator in indicators:
                    key = indicator.text.strip().lower().replace(" ", "_")
                    value = indicator.find_next("dd").text.strip()
                    setattr(school, key, value)

            # Academic Stats
            academic_stats = soup.find("ul", id="academic-stats")
            if academic_stats:
                stats = academic_stats.find_all("li")
                for stat in stats:
                    key = (
                        stat.find("span", class_="label")
                        .text.strip()
                        .lower()
                        .replace(" ", "_")
                    )
                    value = stat.find("strong").text.strip()
                    setattr(school, key, value)

            # Rankings / Awards
            rankings = soup.find("table", class_="fields rankings_awards")
            if rankings:
                rows = rankings.find_all("tr")
                for row in rows:
                    key_elem = row.find("td", class_="column-first")
                    value_elem = row.find("td", class_="column-last") or row.find(
                        "span", class_="rankings-score"
                    )
                    if key_elem and value_elem:
                        key = key_elem.text.strip().lower().replace(" ", "_")
                        value = value_elem.text.strip()
                        setattr(school, key, value)

            # Students / Teachers
            students_teachers = soup.find("table", class_="fields student_teachers")
            if students_teachers:
                rows = students_teachers.find_all("tr")
                for row in rows:
                    key_elem = row.find("td", class_="column-first")
                    value_elem = row.find("td", class_="column-last")
                    if key_elem and value_elem:
                        key = key_elem.text.strip().lower().replace(" ", "_")
                        value = value_elem.text.strip()
                        setattr(school, key, value)

            # Test Scores
            test_scores = soup.find("table", class_="fields test_scores")
            if test_scores:
                rows = test_scores.find_all("tr")
                for row in rows:
                    key_elem = row.find("td", class_="column-first")
                    value_elem = row.find("td", class_="column-last")
                    if key_elem and value_elem:
                        key = key_elem.text.strip().lower().replace(" ", "_")
                        value = value_elem.text.strip()
                        setattr(school, key, value)

            # School Data
            school_data = soup.find("table", class_="fields school_data")
            if school_data:
                rows = school_data.find_all("tr")
                for row in rows:
                    key_elem = row.find("td", class_="column-first")
                    value_elem = row.find("td", class_="column-last")
                    if key_elem and value_elem:
                        key = key_elem.text.strip().lower().replace(" ", "_")
                        value = value_elem.text.strip()
                        setattr(school, key, value)

            # District Data
            district_data = soup.find("table", class_="fields district")
            if district_data:
                rows = district_data.find_all("tr")
                for row in rows:
                    key_elem = row.find("td", class_="column-first")
                    value_elem = row.find("td", class_="column-last")
                    if key_elem and value_elem:
                        key = key_elem.text.strip().lower().replace(" ", "_")
                        value = value_elem.text.strip()
                        setattr(school, key, value)

        except AttributeError as e:
            logger.error(
                "Error parsing school page", school_name=school.name, error=str(e)
            )
        except Exception as e:
            logger.error(
                "Unexpected error parsing school page",
                school_name=school.name,
                error=str(e),
            )

        return school

    async def scrape_pages(self) -> AsyncGenerator[School, None]:
        current_url = self.load_checkpoint() or settings.INITIAL_URL
        page_number = 1
        max_retries = 5

        while current_url and page_number <= 49:
            for attempt in range(max_retries):
                try:
                    logger.info(f"Scraping page {page_number}", url=current_url)
                    html = await self.fetch_page(current_url)
                    if not html:
                        raise Exception("Failed to fetch page")

                    schools = self.parse_rankings_page(html)

                    for school in schools:
                        try:
                            yield await self.parse_school_page(school)
                        except Exception as e:
                            logger.error(
                                f"Error processing school",
                                school_name=school.name,
                                error=str(e),
                            )

                    next_url = self.get_next_page_url(html)
                    if not next_url:
                        logger.info("No more pages to scrape")
                        return

                    self.save_checkpoint(next_url)
                    current_url = next_url
                    page_number += 1
                    self.backoff_time = 60  # Reset backoff time on successful scrape
                    break
                except Exception as e:
                    logger.error(f"Error scraping page {page_number}", error=str(e))
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Max retries reached for page {page_number}. Moving to next page."
                        )
                        page_number += 1
                        current_url = self.get_next_page_url_by_number(page_number)
                    else:
                        await asyncio.sleep(30 * (attempt + 1))  # Wait before retrying

        logger.info("Finished scraping all pages")

    def get_next_page_url_by_number(self, page_number: int) -> str:
        return f"{settings.BASE_URL}/web/20121231154127/http://www.usnews.com/education/best-high-schools/national-rankings/spp+100/page+{page_number}"

    def save_checkpoint(self, current_url: str):
        if time.time() - self.last_checkpoint >= settings.CHECKPOINT_INTERVAL:
            checkpoint = {
                "current_url": current_url,
                "timestamp": datetime.now().isoformat(),
            }
            with open(settings.CHECKPOINT_FILE, "w") as f:
                json.dump(checkpoint, f)
            self.last_checkpoint = time.time()
            logger.info("Checkpoint saved", url=current_url)

    def load_checkpoint(self) -> Optional[str]:
        if os.path.exists(settings.CHECKPOINT_FILE):
            with open(settings.CHECKPOINT_FILE, "r") as f:
                checkpoint = json.load(f)
                return checkpoint.get("current_url")
        return None


async def main():
    await database.connect()
    async with aiohttp.ClientSession() as session:
        rate_limiter = AdaptiveRateLimiter(initial_rate=0.5, max_rate=2.0, min_rate=0.1)
        semaphore = DynamicSemaphore(initial_value=3, min_value=1, max_value=5)
        circuit_breaker = CircuitBreaker(failure_threshold=10, reset_timeout=600)
        scraper = SchoolScraper(session, rate_limiter, semaphore, circuit_breaker)

        try:
            async for school in scraper.scrape_pages():
                try:
                    validated_data = School(**school.dict())
                    await save_school(validated_data.dict())
                except ValueError as e:
                    logger.error(
                        "Data validation failed", school_name=school.name, error=str(e)
                    )
            logger.info("Data saved to database")
        except Exception as e:
            logger.error("Error in main function", error=str(e))
        finally:
            await database.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical("Unhandled exception", error=str(e))
