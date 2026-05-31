from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    "Test the /health endpoint to ensure it returns a 200 status code and the expected response."
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "online",
                               "message": 'AI Battle API is running'}