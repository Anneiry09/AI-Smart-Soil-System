#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ModbusMaster.h>
#include <algorithm>
#include "config.h"

// Khởi tạo đối tượng ModbusMaster
ModbusMaster node;

// Cấu trúc dữ liệu đo đạc cảm biến đất
struct SoilData {
    float moisture;     // Độ ẩm đất (%)
    float temperature;  // Nhiệt độ đất (°C)
    float ec;           // Độ dẫn điện (us/cm)
    float ph;           // Độ pH
    float nitrogen;     // Nitơ (mg/kg)
    float phosphorus;   // Photpho (mg/kg)
    float potassium;    // Kali (mg/kg)
    bool isValid;       // Trạng thái đọc thành công
};

// ================================================================
// HÀM QUẢN LÝ KẾT NỐI WI-FI (Tự động kết nối lại khi mất sóng)
// ================================================================
void ensureWiFiConnected() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.print("[Wi-Fi] Dang ket noi toi SSID: ");
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long startAttempt = millis();
    // Chờ tối đa 15 giây
    while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 15000) {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[Wi-Fi] Ket noi THANH CONG!");
        Serial.print("[Wi-Fi] IP Local ESP32: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n[Wi-Fi] Ket noi that bai, se thu lai o chu ky sau.");
    }
}

// ================================================================
// HÀM ĐỌC 1 MẪU THÔ TỪ MODBUS RS485 (Thanh ghi 0x0000 - 0x0006)
// ================================================================
SoilData readModbusSingleSample() {
    SoilData data;
    data.isValid = false;

    // Gửi lệnh Modbus Function Code 03 đọc 7 thanh ghi liên tiếp từ 0x0000
    uint8_t result = node.readHoldingRegisters(0x0000, 7);

    if (result == node.ku8MBSuccess) {
        // Chuyển đổi theo datasheet cảm biến 7-in-1
        data.moisture    = node.getResponseBuffer(0) / 10.0f;
        data.temperature = (int16_t)node.getResponseBuffer(1) / 10.0f; // int16_t hỗ trợ nhiệt độ âm
        data.ec          = (float)node.getResponseBuffer(2);
        data.ph          = node.getResponseBuffer(3) / 10.0f;
        data.nitrogen    = (float)node.getResponseBuffer(4);
        data.phosphorus  = (float)node.getResponseBuffer(5);
        data.potassium   = (float)node.getResponseBuffer(6);
        data.isValid     = true;
    } else {
        Serial.printf("[Modbus] Loi doc thanh ghi! Ma loi: 0x%02X\n", result);
    }

    return data;
}

// ================================================================
// BỘ LỌC TRUNG VỊ (MEDIAN FILTER) - Lọc sạch xung nhiễu đột biến
// ================================================================
SoilData readFilteredSoilData() {
    float moistArr[MEDIAN_SAMPLE_SIZE];
    float tempArr[MEDIAN_SAMPLE_SIZE];
    float ecArr[MEDIAN_SAMPLE_SIZE];
    float phArr[MEDIAN_SAMPLE_SIZE];
    float nArr[MEDIAN_SAMPLE_SIZE];
    float pArr[MEDIAN_SAMPLE_SIZE];
    float kArr[MEDIAN_SAMPLE_SIZE];

    int validCount = 0;
    int maxAttempts = MEDIAN_SAMPLE_SIZE + 3; // Cho phép thử tối đa nếu có 1-2 lần lỗi timeout

    for (int i = 0; i < maxAttempts && validCount < MEDIAN_SAMPLE_SIZE; i++) {
        SoilData sample = readModbusSingleSample();
        if (sample.isValid) {
            moistArr[validCount] = sample.moisture;
            tempArr[validCount]  = sample.temperature;
            ecArr[validCount]    = sample.ec;
            phArr[validCount]    = sample.ph;
            nArr[validCount]     = sample.nitrogen;
            pArr[validCount]     = sample.phosphorus;
            kArr[validCount]     = sample.potassium;
            validCount++;
        }
        delay(SAMPLE_DELAY_MS);
    }

    SoilData filtered;
    if (validCount < 3) {
        // Không đủ mẫu hợp lệ
        filtered.isValid = false;
        return filtered;
    }

    // Sắp xếp các mảng mẫu theo thứ tự tăng dần
    std::sort(moistArr, moistArr + validCount);
    std::sort(tempArr,  tempArr  + validCount);
    std::sort(ecArr,    ecArr    + validCount);
    std::sort(phArr,    phArr    + validCount);
    std::sort(nArr,     nArr     + validCount);
    std::sort(pArr,     pArr     + validCount);
    std::sort(kArr,     kArr     + validCount);

    // Lấy giá trị phần tử nằm chính giữa (Trung vị)
    int mid = validCount / 2;
    filtered.moisture    = moistArr[mid];
    filtered.temperature = tempArr[mid];
    filtered.ec          = ecArr[mid];
    filtered.ph          = phArr[mid];
    filtered.nitrogen    = nArr[mid];
    filtered.phosphorus  = pArr[mid];
    filtered.potassium   = kArr[mid];
    filtered.isValid     = true;

    return filtered;
}

// ================================================================
// HÀM ĐÓNG GÓI JSON & GỬI HTTP POST LÊN MÁY CHỦ VPS
// ================================================================
bool sendTelemetryToServer(const SoilData& data) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[HTTP] Khong the gui: Wi-Fi chua ket noi!");
        return false;
    }

    // Đóng gói JSON payload bằng ArduinoJson v7
    JsonDocument doc;
    doc["device_id"]    = DEVICE_ID;
    doc["moisture"]     = data.moisture;
    doc["temperature"]  = data.temperature;
    doc["ec"]           = data.ec;
    doc["ph"]           = data.ph;
    doc["nitrogen"]     = data.nitrogen;
    doc["phosphorus"]   = data.phosphorus;
    doc["potassium"]    = data.potassium;

    String jsonPayload;
    serializeJson(doc, jsonPayload);

    HTTPClient http;
    http.begin(API_SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000); // Timeout 5s

    Serial.print("[HTTP] Dang gui du lieu len VPS: ");
    Serial.println(jsonPayload);

    int httpCode = http.POST(jsonPayload);

    bool isSuccess = false;
    if (httpCode > 0) {
        String response = http.getString();
        Serial.printf("[HTTP] Server phan hoi (Ma %d): %s\n", httpCode, response.c_str());
        if (httpCode == 200 || httpCode == 201) {
            isSuccess = true;
        }
    } else {
        Serial.printf("[HTTP] Gui that bai! Ma loi: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
    return isSuccess;
}

// ================================================================
// SETUP
// ================================================================
void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n==========================================");
    Serial.println("  AI SMART SOIL SYSTEM - ESP32 NODE");
    Serial.println("  Ket noi VPS: " API_SERVER_URL);
    Serial.println("==========================================\n");

    // Khởi tạo Serial2 cho kết nối RS485
    // RX2 = GPIO 16, TX2 = GPIO 17
    Serial2.begin(RS485_BAUD, SERIAL_8N1, RS485_RX_PIN, RS485_TX_PIN);
    node.begin(SENSOR_SLAVE_ID, Serial2);
    Serial.println("[Hardware] RS485 Modbus RTU da san sang (RX: 16, TX: 17).");

    // Kết nối Wi-Fi
    ensureWiFiConnected();

    Serial.println("[System] Khoi dong hoan tat. Bat dau chu ky do đac.");
}

// ================================================================
// LOOP CHÍNH
// ================================================================
void loop() {
    // 1. Đảm bảo kết nối Wi-Fi ổn định
    ensureWiFiConnected();

    Serial.println("\n--- [BAT DAU CHU KY DOC CAM BIEN] ---");

    // 2. Đọc cảm biến qua bộ lọc trung vị (Median Filter 5 mẫu)
    SoilData soil = readFilteredSoilData();

    if (soil.isValid) {
        Serial.printf("[Cam bien] Am: %.1f%% | Nhiet: %.1f*C | EC: %.0f us/cm | pH: %.1f\n",
                      soil.moisture, soil.temperature, soil.ec, soil.ph);
        Serial.printf("[Dinh duong NPK] N: %.0f mg/kg | P: %.0f mg/kg | K: %.0f mg/kg\n",
                      soil.nitrogen, soil.phosphorus, soil.potassium);

        // 3. Gửi dữ liệu đã lọc sạch lên VPS
        sendTelemetryToServer(soil);
    } else {
        Serial.println("[Canh bao] Khong doc duoc du lieu tu cam bien (Kiem tra nguon 12V hoac day A/B RS485)!");
    }

    // 4. Nghỉ giữa các chu kỳ đo
    delay(SEND_INTERVAL_MS);
}
