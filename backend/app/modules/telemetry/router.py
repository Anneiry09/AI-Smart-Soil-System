from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import io
import csv

from app.core.database import get_db
from app.modules.telemetry.models import TelemetryRecord
from app.modules.telemetry.schemas import (
    TelemetryCreate,
    TelemetryResponse,
    IngestionSuccessResponse
)

router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingestion"])

@router.post(
    "/",
    response_model=IngestionSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tiếp nhận dữ liệu đo đạc thời gian thực từ ESP32"
)
def ingest_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    """
    Endpoint nhận dữ liệu JSON 7-in-1 từ ESP32 và ghi vào Database.
    """
    new_record = TelemetryRecord(
        device_id=payload.device_id,
        moisture=round(payload.moisture, 2),
        temperature=round(payload.temperature, 2),
        ec=round(payload.ec, 2),
        ph=round(payload.ph, 2),
        nitrogen=round(payload.nitrogen, 2) if payload.nitrogen is not None else None,
        phosphorus=round(payload.phosphorus, 2) if payload.phosphorus is not None else None,
        potassium=round(payload.potassium, 2) if payload.potassium is not None else None,
    )
    if payload.timestamp is not None:
        new_record.created_at = payload.timestamp

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return IngestionSuccessResponse(
        status="success",
        message="Telemetry recorded",
        record_id=new_record.id,
        device_id=new_record.device_id
    )

@router.get(
    "/latest",
    summary="Lấy bản ghi đo đạc mới nhất"
)
def get_latest_telemetry(
    device_id: Optional[str] = Query(None, description="Lọc theo mã thiết bị (vd: ESP32_SOIL_01)"),
    db: Session = Depends(get_db)
):
    query = db.query(TelemetryRecord)
    if device_id:
        query = query.filter(TelemetryRecord.device_id == device_id)

    latest = query.order_by(desc(TelemetryRecord.created_at)).first()
    if not latest:
        return JSONResponse(status_code=200, content={
            "status": "NO_DATA",
            "data": None,
            "message": "Chưa có dữ liệu từ thiết bị"
        })

    # Trả dữ liệu thật – giữ nguyên cấu trúc phẳng TelemetryResponse để tương thích 100% với Flutter App & test cũ
    return TelemetryResponse.model_validate(latest)

@router.get(
    "/history",
    response_model=List[TelemetryResponse],
    summary="Lấy lịch sử dữ liệu đo đạc gần đây"
)
def get_telemetry_history(
    device_id: Optional[str] = Query(None, description="Lọc theo mã thiết bị"),
    limit: int = Query(50, ge=1, le=1000, description="Số lượng bản ghi tối đa"),
    db: Session = Depends(get_db)
):
    query = db.query(TelemetryRecord)
    if device_id:
        query = query.filter(TelemetryRecord.device_id == device_id)
    
    records = query.order_by(desc(TelemetryRecord.created_at)).limit(limit).all()
    return records

@router.get(
    "/export-csv",
    summary="Xuất toàn bộ dữ liệu đo đạc ra file CSV để phục vụ huấn luyện AI sau này"
)
def export_telemetry_csv(
    device_id: Optional[str] = Query(None, description="Lọc theo mã thiết bị nếu cần"),
    db: Session = Depends(get_db)
):
    query = db.query(TelemetryRecord).order_by(TelemetryRecord.created_at.asc())
    if device_id:
        query = query.filter(TelemetryRecord.device_id == device_id)
    
    records = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "device_id", "moisture", "temperature",
        "ec", "ph", "nitrogen", "phosphorus", "potassium", "created_at"
    ])

    for r in records:
        writer.writerow([
            r.id, r.device_id, r.moisture, r.temperature,
            r.ec, r.ph, r.nitrogen, r.phosphorus, r.potassium, r.created_at
        ])

    output.seek(0)
    filename = f"soil_telemetry_dataset_{device_id or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
