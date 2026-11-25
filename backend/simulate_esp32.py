import time
import random
import requests

API_URL = "http://127.0.0.1:8000/api/v1/telemetry/"
DEVICE_ID = "ESP32_SOIL_01"

print(f"Bắt đầu giả lập ESP32 gửi dữ liệu 7-in-1 tới {API_URL}...")

def run_simulation():
    moisture = 44.5
    temp = 28.1
    ec = 665.0
    ph = 6.5
    n = 53.0
    p = 31.5
    k = 92.0

    while True:
        try:
            # Giao động tự nhiên nhẹ
            moisture = round(max(30.0, min(65.0, moisture + random.uniform(-0.3, 0.3))), 1)
            temp = round(max(24.0, min(35.0, temp + random.uniform(-0.15, 0.15))), 1)
            ec = round(max(400.0, min(900.0, ec + random.uniform(-5.0, 5.0))), 1)
            ph = round(max(5.5, min(7.5, ph + random.uniform(-0.05, 0.05))), 1)
            n = round(max(30.0, min(80.0, n + random.uniform(-0.5, 0.5))), 1)
            p = round(max(15.0, min(50.0, p + random.uniform(-0.4, 0.4))), 1)
            k = round(max(60.0, min(120.0, k + random.uniform(-0.8, 0.8))), 1)

            payload = {
                "device_id": DEVICE_ID,
                "moisture": moisture,
                "temperature": temp,
                "ec": ec,
                "ph": ph,
                "nitrogen": n,
                "phosphorus": p,
                "potassium": k
            }

            res = requests.post(API_URL, json=payload, timeout=3)
            if res.status_code == 201:
                print(f"[ESP32 SIM] Đã gửi: Ẩm {moisture}%, Nhiệt {temp}°C, pH {ph}, EC {ec} µS/cm")
            else:
                print(f"[ESP32 SIM] Server trả về lỗi: {res.status_code}")
        except Exception as e:
            print(f"[ESP32 SIM] Lỗi gửi dữ liệu: {e}")

        time.sleep(5)

if __name__ == "__main__":
    run_simulation()
