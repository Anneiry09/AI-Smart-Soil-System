from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import numpy as np

from app.core.database import get_db
from app.modules.telemetry.models import TelemetryRecord
from app.modules.soil_ai.evaluator import SoilAIEvaluator
from app.modules.soil_ai.weather_service import get_hcm_weather

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get(
    "/{device_id}",
    summary="Lấy chẩn đoán & khuyến nghị AI dựa trên trung vị các bản ghi ổn định gần nhất"
)
def get_recommendations_for_device(device_id: str, db: Session = Depends(get_db)):
    """
    Truy vấn 10 bản ghi gần nhất của thiết bị:
    - Kiểm tra trạng thái TRỰC TUYẾN / NGOẠI TUYẾN dựa trên thời gian đo đạc mới nhất (< 60s).
    - Kiểm tra lỗi phần cứng RS485 Lớp 0 trên bản ghi mới nhất.
    - Lọc lấy trung vị (median) của 3-5 mẫu hợp lệ gần nhất.
    - Kết nối dữ liệu thời tiết thực tế từ Open-Meteo API tại TP.HCM (nhiệt độ, độ ẩm, lượng mưa).
    - Chạy tầng AI chẩn đoán toàn diện 4 trụ cột và khử mâu thuẫn.
    """
    recent_records = db.query(TelemetryRecord)\
        .filter(TelemetryRecord.device_id == device_id)\
        .order_by(desc(TelemetryRecord.created_at))\
        .limit(10)\
        .all()

    if not recent_records:
        return JSONResponse(status_code=200, content={
            "status": "NO_DATA",
            "data": None,
            "message": f"Chưa có dữ liệu đo đạc nào cho thiết bị '{device_id}'",
            "device_id": device_id,
            "is_online": False
        })

    # 1. Tính toán trạng thái Trực tuyến / Ngoại tuyến của thiết bị (ngưỡng 60 giây)
    latest_record = recent_records[0]
    now_dt = datetime.now()
    rec_time = latest_record.created_at
    if rec_time:
        if hasattr(rec_time, "tzinfo") and rec_time.tzinfo is not None:
            now_dt = datetime.now(rec_time.tzinfo)
        age_seconds = abs((now_dt - rec_time).total_seconds())
    else:
        age_seconds = 999999.0

    is_online = bool(age_seconds <= 60.0)
    device_status = "ONLINE" if is_online else "OFFLINE"

    # Lấy thông tin thời tiết thực tế từ Open-Meteo API (cache 15 phút)
    weather = get_hcm_weather()

    # 2. Kiểm tra ngay nếu bản ghi mới nhất đang vi phạm lỗi phần cứng RS485 Lớp 0
    latest_err = SoilAIEvaluator.check_hardware_error(
        moisture=float(latest_record.moisture),
        temperature=float(latest_record.temperature),
        ec=float(latest_record.ec),
        ph=float(latest_record.ph),
        n=float(latest_record.nitrogen or 0.0),
        p=float(latest_record.phosphorus or 0.0),
        k=float(latest_record.potassium or 0.0)
    )
    if latest_err is not None:
        return {
            "device_id": device_id,
            "measured_at": str(latest_record.created_at),
            "is_online": is_online,
            "device_status": device_status,
            "last_seen_seconds": round(age_seconds, 1),
            "sample_count": 0,
            "weather": weather,
            "telemetry": {
                "moisture": latest_record.moisture,
                "temperature": latest_record.temperature,
                "ec": latest_record.ec,
                "ph": latest_record.ph,
                "nitrogen": latest_record.nitrogen,
                "phosphorus": latest_record.phosphorus,
                "potassium": latest_record.potassium
            },
            "ai_evaluation": latest_err
        }

    # 3. Lọc bỏ các bản ghi nhiễu/vi phạm Lớp 0 trong lịch sử để lấy 3-5 mẫu hợp lệ
    valid_records: List[TelemetryRecord] = []
    for r in recent_records:
        err = SoilAIEvaluator.check_hardware_error(
            moisture=float(r.moisture),
            temperature=float(r.temperature),
            ec=float(r.ec),
            ph=float(r.ph),
            n=float(r.nitrogen or 0.0),
            p=float(r.phosphorus or 0.0),
            k=float(r.potassium or 0.0)
        )
        if err is None:
            valid_records.append(r)
            if len(valid_records) >= 5:
                break

    # Nếu không có bản ghi hợp lệ nào
    if not valid_records:
        return {
            "device_id": device_id,
            "measured_at": str(latest_record.created_at),
            "is_online": is_online,
            "device_status": device_status,
            "last_seen_seconds": round(age_seconds, 1),
            "sample_count": 0,
            "weather": weather,
            "telemetry": {
                "moisture": latest_record.moisture,
                "temperature": latest_record.temperature,
                "ec": latest_record.ec,
                "ph": latest_record.ph,
                "nitrogen": latest_record.nitrogen,
                "phosphorus": latest_record.phosphorus,
                "potassium": latest_record.potassium
            },
            "ai_evaluation": latest_err
        }

    # 4. Tính trung vị (median) trên 3–5 bản ghi hợp lệ
    m_med = float(np.median([r.moisture for r in valid_records]))
    t_med = float(np.median([r.temperature for r in valid_records]))
    ec_med = float(np.median([r.ec for r in valid_records]))
    ph_med = float(np.median([r.ph for r in valid_records]))
    n_med = float(np.median([r.nitrogen or 0.0 for r in valid_records]))
    p_med = float(np.median([r.phosphorus or 0.0 for r in valid_records]))
    k_med = float(np.median([r.potassium or 0.0 for r in valid_records]))

    sample_count = len(valid_records)
    analysis_meta = {
        "device_id": device_id,
        "sample_count": sample_count,
        "analyzed_at": datetime.now().isoformat(),
        "aggregation": f"median_of_{sample_count}_valid_samples",
        "weather_source": weather.get("source", "open-meteo-live")
    }

    # 5. Chạy đánh giá toàn diện AI với dữ liệu thời tiết thật (hoặc fallback an toàn)
    evaluator = SoilAIEvaluator.get_instance()
    result = evaluator.evaluate(
        moisture=m_med,
        temperature=t_med,
        ec=ec_med,
        ph=ph_med,
        n=n_med,
        p=p_med,
        k=k_med,
        humidity=weather.get("humidity"),
        rainfall=weather.get("rainfall"),
        analysis_meta=analysis_meta
    )

    return {
        "device_id": device_id,
        "measured_at": str(valid_records[0].created_at),
        "is_online": is_online,
        "device_status": device_status,
        "last_seen_seconds": round(age_seconds, 1),
        "sample_count": sample_count,
        "weather": weather,
        "telemetry": {
            "moisture": round(m_med, 1),
            "temperature": round(t_med, 1),
            "ec": round(ec_med, 1),
            "ph": round(ph_med, 2),
            "nitrogen": round(n_med, 1),
            "phosphorus": round(p_med, 1),
            "potassium": round(k_med, 1)
        },
        "ai_evaluation": result
    }
