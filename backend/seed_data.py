import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, Base, engine
from app.modules.telemetry.models import TelemetryRecord

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check existing data for ESP32_SOIL_01
    existing_count = db.query(TelemetryRecord).filter(TelemetryRecord.device_id == "ESP32_SOIL_01").count()
    if existing_count >= 10:
        print(f"ESP32_SOIL_01 already has {existing_count} records. Adding fresh latest record...")
        latest_record = TelemetryRecord(
            device_id="ESP32_SOIL_01",
            moisture=45.2,
            temperature=28.4,
            ec=680.0,
            ph=6.5,
            nitrogen=55.0,
            phosphorus=32.0,
            potassium=95.0,
            created_at=datetime.utcnow()
        )
        db.add(latest_record)
        db.commit()
        db.close()
        print("Latest record inserted successfully!")
        return

    print("Seeding realistic telemetry records for ESP32_SOIL_01...")
    now = datetime.utcnow()
    records = []
    
    for i in range(25, -1, -1):
        record_time = now - timedelta(minutes=i * 5)
        # Add slight natural variation
        moisture = round(44.0 + random.uniform(-2.5, 3.5), 1)
        temp = round(28.0 + random.uniform(-1.0, 1.5), 1)
        ec = round(670.0 + random.uniform(-30.0, 40.0), 1)
        ph = round(6.5 + random.uniform(-0.3, 0.3), 1)
        n = round(52.0 + random.uniform(-5.0, 8.0), 1)
        p = round(30.0 + random.uniform(-3.0, 5.0), 1)
        k = round(90.0 + random.uniform(-8.0, 12.0), 1)
        
        record = TelemetryRecord(
            device_id="ESP32_SOIL_01",
            moisture=moisture,
            temperature=temp,
            ec=ec,
            ph=ph,
            nitrogen=n,
            phosphorus=p,
            potassium=k,
            created_at=record_time
        )
        records.append(record)
        
    db.add_all(records)
    db.commit()
    print(f"Successfully seeded {len(records)} records for ESP32_SOIL_01!")
    db.close()

if __name__ == "__main__":
    seed()
