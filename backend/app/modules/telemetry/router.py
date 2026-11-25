from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import io
import csv

from app.core.database import get_db, get_storage_info
from app.core.offline_sync import offline_buffer
from app.modules.telemetry.models import TelemetryRecord, CalibrationSample
from app.modules.telemetry.schemas import (
    TelemetryCreate,
    TelemetryResponse,
    IngestionSuccessResponse,
    TelemetryBatchCreate,
    BatchSyncResponse,
    CalibrationSampleCreate,
    CalibrationSampleResponse,
)

router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingestion"])


def _is_plausible_reading(payload: TelemetryCreate) -> bool:
    """Lọc nhiễu ngoại lai vật lý (tránh lưu các gói tin lỗi khi cảm biến tuột khỏi đất/dung dịch)."""
    if payload.ph <= 0.5 or payload.ph >= 13.8:
        return False
    if payload.temperature < -10.0 or payload.temperature > 65.0:
        return False
    return True


def _get_ph_calibration_offset(db: Session, device_id: str) -> float:
    """Tính sai số bù pH trung bình từ các mẫu hiệu chuẩn (nước khoáng / NaOH / dung môi)."""
    samples = (
        db.query(CalibrationSample)
        .filter(CalibrationSample.device_id == device_id)
        .order_by(desc(CalibrationSample.created_at))
        .limit(20)
        .all()
    )
    if not samples:
        return 0.0
    offsets = [s.reference_ph - s.measured_ph for s in samples]
    avg_offset = sum(offsets) / len(offsets)
    # Giới hạn biên độ bù an toàn trong khoảng [-1.5, +1.5] pH
    return round(max(-1.5, min(1.5, avg_offset)), 3)


def _build_telemetry_record(payload: TelemetryCreate, ph_offset: float = 0.0) -> TelemetryRecord:
    calibrated_ph = round(max(0.0, min(14.0, payload.ph + ph_offset)), 2)
    return TelemetryRecord(
        device_id=payload.device_id,
        moisture=round(payload.moisture, 2),
        temperature=round(payload.temperature, 2),
        ec=round(payload.ec, 2),
        ph=calibrated_ph,
        nitrogen=round(payload.nitrogen, 2) if payload.nitrogen is not None else None,
        phosphorus=round(payload.phosphorus, 2) if payload.phosphorus is not None else None,
        potassium=round(payload.potassium, 2) if payload.potassium is not None else None,
        created_at=payload.timestamp or None,
    )


@router.post(
    "/",
    response_model=IngestionSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tiếp nhận dữ liệu đo đạc thời gian thực từ ESP32"
)
def ingest_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    """
    Endpoint nhận dữ liệu JSON 7-in-1 từ ESP32, áp dụng hiệu chuẩn (nếu có) và ghi vào Database.
    """
    ph_offset = _get_ph_calibration_offset(db, payload.device_id)
    new_record = _build_telemetry_record(payload, ph_offset=ph_offset)

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
    response_model=TelemetryResponse,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chưa có dữ liệu đo đạc nào trong hệ thống"
        )
    return latest

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


@router.post(
    "/sync-batch",
    response_model=BatchSyncResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đồng bộ hàng loạt dữ liệu từ bộ đệm SQLite offline lên Server chính"
)
def sync_telemetry_batch(batch: TelemetryBatchCreate, db: Session = Depends(get_db)):
    """Nhận danh sách bản ghi từ SQLite cục bộ khi có mạng trở lại và ghi vào Database chính."""
    inserted = 0
    skipped = 0
    offset_cache: dict[str, float] = {}

    for item in batch.records:
        if not _is_plausible_reading(item):
            skipped += 1
            continue
        if item.device_id not in offset_cache:
            offset_cache[item.device_id] = _get_ph_calibration_offset(db, item.device_id)
        db.add(_build_telemetry_record(item, ph_offset=offset_cache[item.device_id]))
        inserted += 1

    db.commit()
    return BatchSyncResponse(status="success", inserted_count=inserted, skipped_outliers=skipped)


@router.get(
    "/storage-status",
    summary="Kiểm tra kiến trúc lưu trữ đa tầng (Primary MySQL/SQL Server & Secondary SQLite Offline)"
)
def get_multi_storage_status():
    info = get_storage_info()
    info["offline_queue_stats"] = offline_buffer.stats()
    return info


@router.get(
    "/offline-status",
    summary="Xem trạng thái hàng đợi SQLite lưu trữ phụ khi mất mạng"
)
def get_offline_buffer_status():
    return offline_buffer.stats()


@router.post(
    "/offline-enqueue",
    status_code=status.HTTP_201_CREATED,
    summary="Lưu tạm dữ liệu vào bộ đệm SQLite cục bộ khi mất mạng"
)
def enqueue_offline_telemetry(payload: TelemetryCreate):
    queue_id = offline_buffer.enqueue(payload.model_dump())
    return {"status": "queued_offline", "queue_id": queue_id, "stats": offline_buffer.stats()}


@router.post(
    "/offline-sync",
    summary="Đẩy dữ liệu từ SQLite phụ lên Server chính (VPS) khi có mạng"
)
def trigger_offline_sync(
    server_batch_url: str = Query(
        "http://221.121.4.208/api/v1/telemetry/sync-batch",
        description="URL endpoint /sync-batch của Server chính (VPS)"
    ),
    limit: int = Query(100, ge=1, le=500),
):
    return offline_buffer.sync_to_server(server_batch_url=server_batch_url, limit=limit)


@router.post(
    "/calibration-sample",
    response_model=CalibrationSampleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ghi nhận mẫu đo hiệu chuẩn (nước khoáng, NaOH, dung môi, đất chuẩn)"
)
def record_calibration_sample(payload: CalibrationSampleCreate, db: Session = Depends(get_db)):
    sample = CalibrationSample(
        device_id=payload.device_id,
        environment_type=payload.environment_type,
        measured_ph=round(payload.measured_ph, 2),
        reference_ph=round(payload.reference_ph, 2),
        measured_ec=round(payload.measured_ec, 2),
        reference_ec=round(payload.reference_ec, 2),
        measured_moisture=round(payload.measured_moisture, 2) if payload.measured_moisture is not None else None,
        note=payload.note,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)

    ph_offset = round(sample.reference_ph - sample.measured_ph, 3)
    ec_ratio = round(sample.reference_ec / sample.measured_ec, 3) if sample.measured_ec > 0 else 1.0

    return CalibrationSampleResponse(
        id=sample.id,
        device_id=sample.device_id,
        environment_type=sample.environment_type,
        measured_ph=sample.measured_ph,
        reference_ph=sample.reference_ph,
        ph_offset=ph_offset,
        measured_ec=sample.measured_ec,
        reference_ec=sample.reference_ec,
        ec_ratio=ec_ratio,
        measured_moisture=sample.measured_moisture,
        note=sample.note,
        created_at=sample.created_at,
    )


@router.get(
    "/calibration-summary",
    summary="Tổng hợp sai số và hệ số hiệu chuẩn theo từng môi trường test"
)
def get_calibration_summary(
    device_id: str = Query("ESP32_SOIL_01"),
    db: Session = Depends(get_db),
):
    samples = (
        db.query(CalibrationSample)
        .filter(CalibrationSample.device_id == device_id)
        .order_by(desc(CalibrationSample.created_at))
        .limit(50)
        .all()
    )
    if not samples:
        return {
            "device_id": device_id,
            "sample_count": 0,
            "recommended_ph_offset": 0.0,
            "environments": {},
        }

    env_groups: dict[str, list[CalibrationSample]] = {}
    for s in samples:
        env_groups.setdefault(s.environment_type, []).append(s)

    env_summary = {}
    for env_name, items in env_groups.items():
        avg_ph_err = sum(i.reference_ph - i.measured_ph for i in items) / len(items)
        avg_ec_err = sum(i.reference_ec - i.measured_ec for i in items) / len(items)
        env_summary[env_name] = {
            "count": len(items),
            "avg_ph_offset": round(avg_ph_err, 3),
            "avg_ec_diff": round(avg_ec_err, 2),
        }

    return {
        "device_id": device_id,
        "sample_count": len(samples),
        "recommended_ph_offset": _get_ph_calibration_offset(db, device_id),
        "environments": env_summary,
    }
