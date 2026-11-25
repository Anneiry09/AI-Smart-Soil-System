from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="", tags=["Actuators & System Configuration"])

# Trạng thái thiết bị phần cứng & Fuzzy Control
ACTUATORS_STATE = {
    "system_mode": "FUZZY_AUTO",  # FUZZY_AUTO hoặc MANUAL
    "fail_safe_locked": False,
    "fail_safe_reason": None,
    "pulse_pause": {
        "active_device": "Bơm Humic Kích Rễ",
        "pulse_duration_sec": 12,
        "pause_duration_sec": 90,
        "current_phase": "PULSE",  # PULSE hoặc PAUSE
        "elapsed_sec": 7,
        "remaining_sec": 5
    },
    "devices": [
        {
            "id": "humic_pump",
            "name": "Bơm định lượng Humic",
            "type": "Peristaltic Pump",
            "state": "ON",
            "pulse_timing": "Xung 12s - Nghỉ 90s",
            "rate": "15 ml/phút",
            "icon": "fa-droplet"
        },
        {
            "id": "npk_pump",
            "name": "Bơm định lượng NPK",
            "type": "Peristaltic Pump",
            "state": "OFF",
            "pulse_timing": "Xung 10s - Nghỉ 120s",
            "rate": "20 ml/phút",
            "icon": "fa-flask"
        },
        {
            "id": "fogging",
            "name": "Bơm phun sương cấp ẩm",
            "type": "High-Pressure Mist",
            "state": "OFF",
            "pulse_timing": "Xung 15s - Nghỉ 60s",
            "rate": "1.2 L/phút",
            "icon": "fa-cloud-rain"
        },
        {
            "id": "fan",
            "name": "Quạt thông gió đối lưu",
            "type": "Exhaust Fan",
            "state": "ON",
            "pulse_timing": "Chạy liên tục 65%",
            "rate": "1800 RPM",
            "icon": "fa-fan"
        },
        {
            "id": "grow_light",
            "name": "Đèn quang hợp toàn phổ",
            "type": "Full-Spectrum LED",
            "state": "OFF",
            "pulse_timing": "Hẹn giờ: 18:00 - 22:00",
            "rate": "200W",
            "icon": "fa-lightbulb"
        }
    ]
}

# Cấu hình vùng trồng & Ngưỡng cây trồng
CROP_CONFIG = {
    "current_node": "ESP32_SOIL_01",
    "crop_name": "Sầu riêng Monthong",
    "growth_stage": "Giai đoạn Nuôi trái non (Ngày 45 - 75)",
    "target_thresholds": {
        "moisture": {"min": 42.0, "max": 55.0},
        "ph": {"min": 6.2, "max": 6.8},
        "ec": {"min": 600.0, "max": 850.0}
    },
    "soil_type": "Đất đỏ bazan Đồng Nai (Độ xốp cao)"
}

NODES_LIST = [
    {
        "id": "ESP32_SOIL_01",
        "name": "Node Vườn Sầu Riêng Khu A",
        "crop": "Sầu riêng Monthong (Nuôi trái)",
        "status": "ONLINE",
        "battery": "94%",
        "wifi_rssi": "-62 dBm",
        "last_seen": "Vừa xong"
    },
    {
        "id": "ESP32_SOIL_02",
        "name": "Node Vườn Bưởi Da Xanh Khu B",
        "crop": "Bưởi Da Xanh (Làm đọt)",
        "status": "STANDBY",
        "battery": "88%",
        "wifi_rssi": "-71 dBm",
        "last_seen": "12 phút trước"
    },
    {
        "id": "ESP32_SOIL_03",
        "name": "Node Nhà Màng Nấm Linh Chi",
        "crop": "Nấm Linh Chi đỏ",
        "status": "STANDBY",
        "battery": "100% (Cắm nguồn)",
        "wifi_rssi": "-55 dBm",
        "last_seen": "35 phút trước"
    }
]

class ActuatorToggle(BaseModel):
    device_id: Optional[str] = None
    system_mode: Optional[str] = None
    new_state: Optional[str] = None

class CropConfigUpdate(BaseModel):
    crop_name: Optional[str] = None
    growth_stage: Optional[str] = None
    target_thresholds: Optional[Dict[str, Any]] = None

@router.get("/actuators/status")
def get_actuators_status():
    """Lấy trạng thái điều khiển rơ-le phần cứng, chu kỳ Xung-Nghỉ và còi cảnh báo."""
    return ACTUATORS_STATE

@router.post("/actuators/control")
def control_actuators(payload: ActuatorToggle):
    """Bật/tắt chế độ Fuzzy AI hoặc điều khiển cưỡng bức từng rơ-le."""
    if payload.system_mode:
        ACTUATORS_STATE["system_mode"] = payload.system_mode
        
    if payload.device_id:
        for dev in ACTUATORS_STATE["devices"]:
            if dev["id"] == payload.device_id:
                dev["state"] = payload.new_state or ("OFF" if dev["state"] == "ON" else "ON")
                break
                
    return {"status": "success", "state": ACTUATORS_STATE}

@router.post("/actuators/fail-safe")
def toggle_fail_safe(trigger: bool = True):
    """Mô phỏng kích hoạt / hủy bỏ cơ chế khóa an toàn chống tràn nước khi tuột cảm biến."""
    ACTUATORS_STATE["fail_safe_locked"] = trigger
    if trigger:
        ACTUATORS_STATE["fail_safe_reason"] = "Phát hiện cảm biến bị tuột hoặc cặn bám: Bơm đã chạy 2 chu kỳ nhưng độ ẩm không tăng. Đã ngắt điện toàn bộ máy bơm!"
        # Tắt toàn bộ máy bơm
        for dev in ACTUATORS_STATE["devices"]:
            if "pump" in dev["id"] or "fog" in dev["id"]:
                dev["state"] = "LOCKED_OFF"
    else:
        ACTUATORS_STATE["fail_safe_reason"] = None
        for dev in ACTUATORS_STATE["devices"]:
            if dev["state"] == "LOCKED_OFF":
                dev["state"] = "OFF"
                
    return {"status": "success", "fail_safe_locked": trigger, "state": ACTUATORS_STATE}

@router.get("/config/crop")
def get_crop_config():
    """Lấy cấu hình cây trồng và ngưỡng an toàn hiện tại."""
    return CROP_CONFIG

@router.post("/config/crop")
def update_crop_config(payload: CropConfigUpdate):
    """Cập nhật loại cây trồng, giai đoạn sinh trưởng và thanh trượt ngưỡng nông học."""
    if payload.crop_name:
        CROP_CONFIG["crop_name"] = payload.crop_name
    if payload.growth_stage:
        CROP_CONFIG["growth_stage"] = payload.growth_stage
    if payload.target_thresholds:
        CROP_CONFIG["target_thresholds"].update(payload.target_thresholds)
    return {"status": "success", "config": CROP_CONFIG}

@router.get("/config/nodes")
def get_sensor_nodes():
    """Danh sách các trạm cảm biến ESP32 trong mạng lưới."""
    return NODES_LIST
