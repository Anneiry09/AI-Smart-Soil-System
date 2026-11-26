from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class TelemetryCreate(BaseModel):
    device_id: str = Field(..., examples=["ESP32_SOIL_01"], min_length=1, max_length=50)
    moisture: float = Field(..., ge=0.0, le=100.0, description="Độ ẩm đất (%)")
    temperature: float = Field(..., ge=-40.0, le=80.0, description="Nhiệt độ đất (°C)")
    ec: float = Field(..., ge=0.0, le=20000.0, description="Độ dẫn điện EC (us/cm)")
    ph: float = Field(..., ge=0.0, le=14.0, description="Độ pH")
    nitrogen: Optional[float] = Field(None, ge=0.0, description="Hàm lượng Nitơ (mg/kg)")
    phosphorus: Optional[float] = Field(None, ge=0.0, description="Hàm lượng Photpho (mg/kg)")
    potassium: Optional[float] = Field(None, ge=0.0, description="Hàm lượng Kali (mg/kg)")
    timestamp: Optional[datetime] = None

class TelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    moisture: float
    temperature: float
    ec: float
    ph: float
    nitrogen: Optional[float]
    phosphorus: Optional[float]
    potassium: Optional[float]
    created_at: datetime

class IngestionSuccessResponse(BaseModel):
    status: str = "success"
    message: str = "Data recorded successfully"
    record_id: int
    device_id: str
