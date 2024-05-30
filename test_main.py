from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the City Suggestions API"}

def test_suggestions_without_geo():
    response = client.get("/suggestions?q=abb")
    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert len(suggestions) > 0
    assert suggestions[0]["name"] == "Abbotsford"

def test_suggestions_with_geo():
    response = client.get("/suggestions?q=air&latitude=51.0&longitude=-114.0")
    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert len(suggestions) > 0
    assert suggestions[0]["name"] == "Airdrie"

def test_suggestions_no_results():
    response = client.get("/suggestions?q=xyz")
    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert len(suggestions) == 0

def test_suggestions_invalid_query():
    response = client.get("/suggestions?q=")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert len(detail) > 0
    assert detail[0]["msg"] == "field required"
