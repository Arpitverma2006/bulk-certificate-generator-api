import os
# Force test database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db, engine
from main import app

# Recreate tables for test.db
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_generation_job():
    response = client.post(
        "/api/v1/certificates/generate",
        json={
            "recipients": [
                {"name": "Arpit Verma", "email": "arpit@example.com", "course_name": "Advanced Python"},
                {"name": "Jane Doe", "email": "jane@example.com", "course_name": "FastAPI Masterclass"}
            ]
        }
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"

def test_input_validation_failure():
    response = client.post(
        "/api/v1/certificates/generate",
        json={
            "recipients": [
                {"name": "Charlie", "email": "invalid-email-format", "course_name": "Python 101"}
            ]
        }
    )
    assert response.status_code == 422

def test_job_status_and_failure_handling():
    response = client.post(
        "/api/v1/certificates/generate",
        json={
            "recipients": [
                {"name": "Valid User", "email": "valid@example.com", "course_name": "SQL Basics"},
                {"name": "FAIL_TEST User", "email": "fail@example.com", "course_name": "Error Handling"}
            ]
        }
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status_response = client.get(f"/api/v1/certificates/jobs/{job_id}")
    assert status_response.status_code == 200
    job_data = status_response.json()
    assert job_data["total_recipients"] == 2
    assert job_data["successful_count"] == 1
    assert job_data["failed_count"] == 1