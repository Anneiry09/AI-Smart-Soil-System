from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from datetime import datetime
from app.core.database import Base

class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    moisture = Column(Float, nullable=False)        # Độ ẩm đất (%)
    temperature = Column(Float, nullable=False)     # Nhiệt độ (°C)
    ec = Column(Float, nullable=False)              # Độ dẫn điện (us/cm)
    ph = Column(Float, nullable=False)              # Độ pH
    nitrogen = Column(Float, nullable=True)         # N (mg/kg)
    phosphorus = Column(Float, nullable=True)       # P (mg/kg)
    potassium = Column(Float, nullable=True)        # K (mg/kg)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_device_created_at", "device_id", "created_at"),
    )


class CalibrationSample(Base):
    """Lưu mẫu đo đối chứng trên từng môi trường chuẩn (nước khoáng, NaOH, dung môi, đất mẫu) để hiệu chuẩn cảm biến."""
    __tablename__ = "calibration_samples"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    environment_type = Column(String(40), nullable=False, index=True)  # mineral_water, naoh_alkaline, solvent_acid, standard_soil
    measured_ph = Column(Float, nullable=False)
    reference_ph = Column(Float, nullable=False)
    measured_ec = Column(Float, nullable=False)
    reference_ec = Column(Float, nullable=False)
    measured_moisture = Column(Float, nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
