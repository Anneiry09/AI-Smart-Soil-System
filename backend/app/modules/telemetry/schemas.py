from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TelemetryCreate(BaseModel):
    device_id: str = Field(..., example="ESP32_SOIL_01", min_length=1, max_length=50)
    moisture: float = Field(..., ge=0.0, le=100.0, description="Độ ẩm đất (%)")
    temperature: float = Field(..., ge=-40.0, le=80.0, description="Nhiệt độ đất (°C)")
    ec: float = Field(..., ge=0.0, le=20000.0, description="Độ dẫn điện EC (us/cm)")
    ph: float = Field(..., ge=0.0, le=14.0, description="Độ pH")
    nitrogen: Optional[float] = Field(None, ge=0.0, description="Hàm lượng Nitơ (mg/kg)")
    phosphorus: Optional[float] = Field(None, ge=0.0, description="Hàm lượng Photpho (mg/kg)")
    potassium: Optional[float] = Field(None, ge=0.0, description="Hàm lượng Kali (mg/kg)")
    timestamp: Optional[datetime] = None

class TelemetryResponse(BaseModel):
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

    class Config:
        from_attributes = True

class IngestionSuccessResponse(BaseModel):
    status: str = "success"
    message: str = "Data recorded successfully"
    record_id: int
    device_id: str


class TelemetryBatchCreate(BaseModel):
    records: List[TelemetryCreate] = Field(..., min_length=1, max_length=500)


class BatchSyncResponse(BaseModel):
    status: str = "success"
    inserted_count: int
    skipped_outliers: int = 0


class CalibrationSampleCreate(BaseModel):
    device_id: str = Field(..., example="ESP32_SOIL_01", min_length=1, max_length=50)
    environment_type: str = Field(
        ...,
        example="mineral_water",
        description="Môi trường test: mineral_water, naoh_alkaline, solvent_acid, distilled_water, standard_soil"
    )
    measured_ph: float = Field(..., ge=0.0, le=14.0)
    reference_ph: float = Field(..., ge=0.0, le=14.0)
    measured_ec: float = Field(..., ge=0.0, le=20000.0)
    reference_ec: float = Field(..., ge=0.0, le=20000.0)
    measured_moisture: Optional[float] = Field(None, ge=0.0, le=100.0)
    note: Optional[str] = Field(None, max_length=255)


class CalibrationSampleResponse(BaseModel):
    id: int
    device_id: str
    environment_type: str
    measured_ph: float
    reference_ph: float
    ph_offset: float
    measured_ec: float
    reference_ec: float
    ec_ratio: float
    measured_moisture: Optional[float]
    note: Optional[str]
    created_at: datetime
