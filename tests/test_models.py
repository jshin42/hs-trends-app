import pytest
from app.crud.crud_school import create_school
from app.schemas.school import SchoolCreate


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to HS Trends API"}


def test_search_schools(client, db):
    # Create a test school
    school_data = SchoolCreate(
        id="test-id", name="Test School", national_rank="#1", year="2024"
    )
    create_school(db, school_data)

    response = client.get("/api/schools/search?name=Test")
    assert response.status_code == 200
    schools = response.json()
    assert len(schools) == 1
    assert schools[0]["name"] == "Test School"


def test_get_school_rankings(client, db):
    # Create a test school
    school_data = SchoolCreate(
        id="test-id", name="Test School", national_rank="#1", year="2024"
    )
    create_school(db, school_data)

    response = client.get("/api/schools/test-id/rankings")
    assert response.status_code == 200
    rankings = response.json()
    assert len(rankings) == 1
    assert rankings[0]["national_rank"] == 1
    assert rankings[0]["year"] == 2024


def test_school_not_found(client):
    response = client.get("/api/schools/nonexistent-id/rankings")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "School not found or no ranking data available"
    }
