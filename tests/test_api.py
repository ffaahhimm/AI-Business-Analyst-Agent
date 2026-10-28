from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed


def setup_module():
    seed()


def test_schema_endpoint_exposes_approved_tables():
    response = TestClient(app).get("/api/schema")
    assert response.status_code == 200
    assert set(response.json()["tables"]) == {"orders", "order_items", "products", "regions"}


def test_analysis_endpoint_returns_evidence_contract():
    response = TestClient(app).post("/api/analyze", json={"question": "Which categories have the highest return rate?"})
    payload = response.json()
    assert response.status_code == 200
    assert payload["evidence"][0]["sql"].lstrip().lower().startswith("select")
    assert payload["evidence"][0]["row_count"] == 5
    assert payload["chart"]["type"] == "bar"


def test_analysis_endpoint_rejects_unsupported_questions():
    response = TestClient(app).post("/api/analyze", json={"question": "Show employee salaries"})
    assert response.status_code == 422
    assert "revenue" in response.json()["detail"]


def test_analysis_endpoint_validates_request_size():
    response = TestClient(app).post("/api/analyze", json={"question": "x"})
    assert response.status_code == 422
