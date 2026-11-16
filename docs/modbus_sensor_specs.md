# Tài liệu Kỹ thuật Cảm biến Đất 7-in-1 (RS485 Modbus RTU)

## 1. Thông số Kỹ thuật
- **Nguồn cấp:** 9V - 24V DC (Khuyên dùng Adapter 12V 1A)
- **Giao tiếp:** RS485 Modbus RTU
- **Tốc độ Baud:** 9600 bps (8 data bits, 1 stop bit, no parity)
- **Slave ID mặc định:** 1 (`0x01`)

## 2. Bảng thanh ghi Modbus (Function Code 03 - Read Holding Registers)

| Địa chỉ (Hex) | Địa chỉ (Dec) | Thông số đo | Dải đo | Đơn vị | Hệ số nhân / Chia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0x0000` | 0 | Độ ẩm đất (Soil Moisture) | 0 - 100% | % | Chia cho 10 (vd: 355 -> 35.5%) |
| `0x0001` | 1 | Nhiệt độ đất (Soil Temp) | -40 - 80°C | °C | Chia cho 10 (vd: 285 -> 28.5°C) |
| `0x0002` | 2 | Độ dẫn điện (EC) | 0 - 20000 | $\mu\text{S/cm}$ | Giá trị thực |
| `0x0003` | 3 | Độ pH | 3 - 9 pH | pH | Chia cho 10 (vd: 68 -> 6.8 pH) |
| `0x0004` | 4 | Nitơ (N) | 1 - 1999 | mg/kg | Giá trị thực (nội suy từ EC) |
| `0x0005` | 5 | Photpho (P) | 1 - 1999 | mg/kg | Giá trị thực (nội suy từ EC) |
| `0x0006` | 6 | Kali (K) | 1 - 1999 | mg/kg | Giá trị thực (nội suy từ EC) |

## 3. Khung truyền mẫu đọc 7 thanh ghi liên tiếp
- **Request (8 bytes):**
  `01 03 00 00 00 07 04 08`
- **Response (19 bytes):**
  `01 03 0E [Data 14 bytes] [CRC 2 bytes]`
