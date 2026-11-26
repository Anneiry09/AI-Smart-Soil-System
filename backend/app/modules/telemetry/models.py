from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    moisture: Mapped[float] = mapped_column(Float, nullable=False)        # Độ ẩm đất (%)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)     # Nhiệt độ (°C)
    ec: Mapped[float] = mapped_column(Float, nullable=False)              # Độ dẫn điện (us/cm)
    ph: Mapped[float] = mapped_column(Float, nullable=False)              # Độ pH
    nitrogen: Mapped[Optional[float]] = mapped_column(Float, nullable=True)     # N (mg/kg)
    phosphorus: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # P (mg/kg)
    potassium: Mapped[Optional[float]] = mapped_column(Float, nullable=True)    # K (mg/kg)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_device_created_at", "device_id", "created_at"),
    )
