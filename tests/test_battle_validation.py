from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_battle_rejects_invalid_category():
    """Battle should reject categories that arent in the valid set"""
    response = client.post("/battle/start", json={
        "category": "not_a_real_category",
        "models": ["llama3.2", "mistral"]
    })
    assert response.status_code == 400
    assert "Invalid category" in response.json()["detail"]

def test_battle_rejects_single_model():
    """A battle needs at least 2 models to compute"""
    response = client.post("/battle/start", json={
        "category": "reasoning",
        "models": ["llama3.2"]
    })
    assert response.status_code in [400]

def test_battle_rejects_missing_fields():
    """Pydantic should reject requests missing required fields"""
    response = client.post("/battle/start", json={
        "category": "reasoning"
        #missing model(s)
    })
    assert response.status_code in [400, 422]