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

## 4. Live Server Endpoints (VPS Ubuntu 22.04 - wiservices)
- **Base URL:** `http://221.121.4.208`
- **Swagger API Docs:** `http://221.121.4.208/docs`
- **Telemetry Ingestion:** `POST http://221.121.4.208/api/v1/telemetry/`
- **Latest Reading:** `GET http://221.121.4.208/api/v1/telemetry/latest`
- **CSV Dataset Export:** `GET http://221.121.4.208/api/v1/telemetry/export-csv`

## 5. Milestones & Progress Tracker
- [x] **Milestone 3.1:** Khởi tạo cấu trúc dự án chuẩn (`firmware-esp32/`, `backend/`, `mobile-app/`, `docs/`).
- [x] **Milestone 4.1:** Xây dựng Backend Ingestion API (FastAPI) & Database SQLite WAL, triển khai chạy nền 24/7 trên VPS `221.121.4.208`.
- [x] **Milestone 3.2:** Hoàn thiện Firmware ESP32: Đọc cảm biến 7-in-1 qua RS485, bộ lọc trung vị (Median Filter), kết nối Wi-Fi và đẩy dữ liệu lên VPS qua HTTP POST.
- [ ] **Milestone 3.3 (Thực địa):** Nạp code vào kit ESP32 thực tế, cắm cảm biến vào mẫu đất và xác nhận dữ liệu nhảy liên tục trên VPS.
- [ ] **Milestone 5.1:** Xây dựng giao diện ứng dụng (Flutter Mobile/Web) trực quan hóa thông số đất và cảnh báo từ API.
- [ ] **Milestone 4.2 (Giai đoạn sau):** Nghiên cứu & Huấn luyện mô hình AI phân tích dinh dưỡng đất từ tập dữ liệu thực tế thu thập được.