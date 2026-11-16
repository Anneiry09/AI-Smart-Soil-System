# Project: AI Smart Soil System (nongthinh.vn)
Repository: Anneiry09/ai-smart-soil-system

## 1. System Overview
Hệ thống AIoT giám sát và phân tích dinh dưỡng đất thời gian thực cho nông nghiệp tại Đồng Nai (nongthinh.vn).
- Edge Node: ESP32 đọc cảm biến đất 7-in-1 qua giao thức RS485 Modbus RTU.
- Backend & AI: Nhận dữ liệu qua HTTP REST API / MQTT, lưu trữ Database và chạy mô hình AI đánh giá độ phì nhiêu, đưa ra khuyến nghị tưới tiêu/bón phân.
- Frontend: Web Dashboard hiển thị thông số thời gian thực và cảnh báo.

## 2. Hardware Configuration (Phase 2 - Completed)
- MCU: DOIT ESP32 DEVKIT V1 (Arduino Core 3.3.12)
- Transceiver: TTL-to-RS485 Auto-Direction Module (HW-0519), powered at 3.3V
- Sensor: 7-in-1 Soil Sensor (Moisture, Temp, EC, pH, N, P, K) powered by 12V DC Adapter
- Wiring:
  - ESP32 GPIO 16 (RX2) -> RS485 TXD
  - ESP32 GPIO 17 (TX2) -> RS485 RXD
  - ESP32 3V3 -> RS485 VCC
  - ESP32 GND -> RS485 GND
- Tracked Metrics:
  1. Soil Moisture (%)
  2. Soil Temperature (°C)
  3. Electrical Conductivity - EC (us/cm)
  4. pH Level
  5. Nitrogen - N (mg/kg) [Inferred from EC]
  6. Phosphorus - P (mg/kg) [Inferred from EC]
  7. Potassium - K (mg/kg) [Inferred from EC]

## 3. Technology Stack & Architecture
- **Firmware:** ESP32 with PlatformIO (`firmware-esp32/`), Arduino framework, ModbusMaster & ArduinoJson.
- **Backend & AI:** Modular Monolith using Python FastAPI (`backend/`), SQLite/PostgreSQL, scikit-learn.
- **Client App:** Flutter (`mobile-app/`) supporting Android, iOS and Web.
- **Documentation:** Technical & sensor specs (`docs/`).

## 4. Milestones & Progress
- [x] Milestone 3.1: Tổ chức cấu trúc thư mục repo (`firmware-esp32/`, `backend/`, `mobile-app/`, `docs/`).
- [x] Milestone 4.1: Xây dựng Backend Telemetry Ingestion API & CSDL SQLite (Đã deploy thành công lên VPS `221.121.4.208:80`).
- [ ] Milestone 3.2: Hoàn thiện Firmware ESP32 (kết nối Wi-Fi, đọc cảm biến 7-in-1, lọc trung vị Median Filter và bắn dữ liệu lên VPS).
- [ ] Milestone 5.1: Xây dựng giao diện ứng dụng Flutter kết nối API xem số đo thời gian thực.
- [ ] Milestone 6.1 (Nghiên cứu riêng): Thu thập dataset thực tế từ cảm biến và huấn luyện mô hình AI đánh giá độ phì nhiêu của đất.

## 5. Live Server Endpoints (VPS wiservices)
- **Base URL:** `http://221.121.4.208`
- **Swagger Docs:** `http://221.121.4.208/docs`
- **Ingestion Endpoint (POST):** `http://221.121.4.208/api/v1/telemetry/`
- **Latest Record (GET):** `http://221.121.4.208/api/v1/telemetry/latest`
- **Export CSV (GET):** `http://221.121.4.208/api/v1/telemetry/export-csv`