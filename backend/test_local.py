import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from app.core.database import Base, engine

# Ensure tables created
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_api():
    print("1. Testing health check...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("   -> OK:", res.json())

    print("2. Testing telemetry ingestion (POST /api/v1/telemetry)...")
    payload = {
        "device_id": "ESP32_SOIL_TEST",
        "moisture": 35.5,
        "temperature": 28.2,
        "ec": 650.0,
        "ph": 6.5,
        "nitrogen": 45.0,
        "phosphorus": 25.0,
        "potassium": 80.0
    }
    res = client.post("/api/v1/telemetry/", json=payload)
    assert res.status_code == 201, f"Ingestion failed: {res.text}"
    print("   -> OK:", res.json())

    print("3. Testing get latest (GET /api/v1/telemetry/latest)...")
    res = client.get("/api/v1/telemetry/latest?device_id=ESP32_SOIL_TEST")
    assert res.status_code == 200, f"Get latest failed: {res.text}"
    data = res.json()
    assert data["device_id"] == "ESP32_SOIL_TEST"
    assert data["ph"] == 6.5
    print("   -> OK:", data)

    print("4. Testing export CSV (GET /api/v1/telemetry/export-csv)...")
    res = client.get("/api/v1/telemetry/export-csv")
    assert res.status_code == 200, f"Export CSV failed: {res.text}"
    assert "moisture,temperature,ec,ph" in res.text
    print("   -> OK: CSV header & data generated correctly.")

    print("\nALL LOCAL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_api()
