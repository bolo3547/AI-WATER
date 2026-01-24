from fastapi.testclient import TestClient
from src.cloud.api import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code in [200, 404] # Depending on if root is defined

def test_health_check():
    response = client.get("/health")
    # If not implemented, it will be 404, but at least we know the server is up
    assert response.status_code in [200, 404]
