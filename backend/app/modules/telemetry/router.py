from fastapi import APIRouter
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

class SoilTelemetryCreate(BaseModel):
    device_id: str
    moisture: float = Field(..., description="Độ ẩm đất (%)")
    temperature: float = Field(..., description="Nhiệt độ đất (°C)")
    ec: float = Field(..., description="Độ dẫn điện EC (us/cm)")
    ph: float = Field(..., description="Độ pH")
    nitrogen: Optional[float] = Field(None, description="Hàm lượng Nitơ (mg/kg)")
    phosphorus: Optional[float] = Field(None, description="Hàm lượng Photpho (mg/kg)")
    potassium: Optional[float] = Field(None, description="Hàm lượng Kali (mg/kg)")
    timestamp: Optional[datetime] = None

@router.post("/")
def ingest_telemetry(data: SoilTelemetryCreate):
    # Sẽ hoàn thiện ở Milestone 4.1
    return {"status": "received", "device_id": data.device_id}
