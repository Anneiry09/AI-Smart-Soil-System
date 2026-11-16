#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ModbusMaster.h>
#include "config.h"

// Khởi tạo ModbusMaster & Serial2
ModbusMaster node;

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("[ESP32] Smart Soil System - Starting...");

    // Cấu hình UART2 cho RS485 Modbus RTU
    Serial2.begin(RS485_BAUD, SERIAL_8N1, RS485_RX_PIN, RS485_TX_PIN);
    node.begin(SENSOR_SLAVE_ID, Serial2);

    Serial.println("[ESP32] Setup complete.");
}

void loop() {
    // Sẽ được hoàn thiện ở Milestone 3.2:
    // Đọc Modbus -> Lọc trung vị -> Đóng gói JSON -> Gửi HTTP POST
    delay(READ_INTERVAL_MS);
}
