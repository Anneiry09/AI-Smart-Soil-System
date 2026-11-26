import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# Tọa độ mặc định: TP. Hồ Chí Minh
DEFAULT_LATITUDE = 10.8231
DEFAULT_LONGITUDE = 106.6297
CACHE_TTL_SECONDS = 900  # 15 phút (900 giây)
REQUEST_TIMEOUT_SECONDS = 3.0  # Timeout 3 giây

_cached_weather: Optional[Dict[str, Any]] = None
_cache_timestamp: float = 0.0

def get_hcm_weather(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Lấy dữ liệu thời tiết thực tế tại TP.HCM từ Open-Meteo API (không cần API Key).
    - Cache trên RAM 15 phút để tăng tốc phản hồi và tránh giới hạn gọi API.
    - Timeout tối đa 3 giây.
    - Tự động fallback nếu mất mạng, trả cờ rõ ràng 'source': 'open-meteo-live' hoặc 'fallback'.
    """
    global _cached_weather, _cache_timestamp

    now = time.time()
    if not force_refresh and _cached_weather is not None and (now - _cache_timestamp < CACHE_TTL_SECONDS):
        return _cached_weather

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={DEFAULT_LATITUDE}&longitude={DEFAULT_LONGITUDE}&"
        f"current=temperature_2m,relative_humidity_2m,precipitation&"
        f"daily=precipitation_sum&timezone=Asia%2FBangkok"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SmartSoilAI/1.0 (Agriculture Research System)"}
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                current = data.get("current", {})
                daily = data.get("daily", {})

                temp = float(current.get("temperature_2m", 29.5))
                humidity = float(current.get("relative_humidity_2m", 75.0))
                precip = float(current.get("precipitation", 0.0))

                # Tính toán lượng mưa mùa vụ ước lượng (mm) phục vụ Model B
                daily_sums = daily.get("precipitation_sum", [])
                if daily_sums:
                    week_sum = sum(daily_sums[:7])
                    rainfall_mm = round(max(60.0, min(300.0, 110.0 + week_sum * 3.5)), 1)
                else:
                    rainfall_mm = round(max(60.0, min(300.0, 140.0 + precip * 10.0)), 1)

                weather_data = {
                    "temperature": temp,
                    "humidity": humidity,
                    "rainfall": rainfall_mm,
                    "precipitation_now": precip,
                    "source": "open-meteo-live",
                    "location": "TP. Hồ Chí Minh",
                    "fetched_at": datetime.now().isoformat(),
                    "cache_ttl_remaining": CACHE_TTL_SECONDS
                }

                _cached_weather = weather_data
                _cache_timestamp = now
                logger.info("Đã cập nhật thời tiết thật từ Open-Meteo: %s°C, ẩm %s%%, mưa %s mm", temp, humidity, rainfall_mm)
                return weather_data

    except Exception as e:
        logger.warning("Không thể lấy thời tiết từ Open-Meteo (%s), chuyển sang fallback an toàn.", e)

    # Fallback nếu mạng ngắt hoặc timeout
    fallback_data = {
        "temperature": 29.5,
        "humidity": 75.0,
        "rainfall": 150.0,
        "precipitation_now": 0.0,
        "source": "fallback",
        "location": "TP. Hồ Chí Minh (Dữ liệu đặc trưng mùa vụ)",
        "fetched_at": datetime.now().isoformat(),
        "cache_ttl_remaining": 0
    }
    return fallback_data
