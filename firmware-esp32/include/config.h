#ifndef CONFIG_H
#define CONFIG_H

// ==========================================
// 1. Cấu hình Mạng Wi-Fi
// ==========================================
// Hãy điền tên Wi-Fi (SSID) của bạn vào đây (vd: Tên Wi-Fi nhà hoặc điểm phát sóng 4G điện thoại)
#define WIFI_SSID           "Pink Home"
#define WIFI_PASSWORD       "68686868"

// ==========================================
// 2. Cấu hình Backend Server (VPS wiservices)
// ==========================================
#define API_SERVER_URL      "http://221.121.4.208/api/v1/telemetry/"
#define DEVICE_ID           "ESP32_SOIL_01"

// ==========================================
// 3. Cấu hình Phần cứng RS485 & Cảm biến
// ==========================================
// ESP32 DOIT DEVKIT V1 kết nối module HW-0519
#define RS485_RX_PIN        16      // ESP32 GPIO 16 (RX2) -> Module RS485 TXD
#define RS485_TX_PIN        17      // ESP32 GPIO 17 (TX2) -> Module RS485 RXD
#define RS485_BAUD          9600    // Tốc độ Baud mặc định cảm biến đất

#define SENSOR_SLAVE_ID     1       // Modbus Slave ID mặc định (0x01)

// ==========================================
// 4. Cấu hình Bộ lọc trung vị & Chu kỳ gửi
// ==========================================
#define MEDIAN_SAMPLE_SIZE  5       // Số mẫu đọc liên tiếp để lọc trung vị (lấy số lẻ: 5 mẫu)
#define SAMPLE_DELAY_MS     150     // Khoảng cách giữa các lần đọc mẫu (ms)
#define SEND_INTERVAL_MS    5000    // Chu kỳ gửi dữ liệu lên VPS (5 giây / lần)

#endif // CONFIG_H
