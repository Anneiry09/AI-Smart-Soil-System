#ifndef CONFIG_H
#define CONFIG_H

// --- Wi-Fi Configuration ---
#define WIFI_SSID       "YOUR_WIFI_SSID"
#define WIFI_PASSWORD   "YOUR_WIFI_PASSWORD"

// --- Backend API Configuration ---
#define API_SERVER_URL  "http://192.168.1.100:8000/api/v1/telemetry"
#define DEVICE_ID       "ESP32_SOIL_01"

// --- RS485 & Modbus Pinout (ESP32 DOIT DevKit V1) ---
#define RS485_RX_PIN    16 // ESP32 GPIO 16 (RX2) -> RS485 TXD
#define RS485_TX_PIN    17 // ESP32 GPIO 17 (TX2) -> RS485 RXD
#define RS485_BAUD      9600

// --- Sensor Modbus ID ---
#define SENSOR_SLAVE_ID 1

// --- Sampling Interval ---
#define READ_INTERVAL_MS 5000 // Đọc mỗi 5 giây

#endif // CONFIG_H
