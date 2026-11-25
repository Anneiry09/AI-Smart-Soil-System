import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/soil_data.dart';

class ApiService {
  static const List<String> candidateUrls = [
    'http://221.121.4.208/api/v1/telemetry',       // VPS chính
    'http://192.168.1.33:8000/api/v1/telemetry',  // Máy chủ nội bộ Wi-Fi
    'http://10.0.2.2:8000/api/v1/telemetry',      // Android Emulator
    'http://localhost:8000/api/v1/telemetry',     // Windows/Web
  ];

  static String activeUrl = candidateUrls.first;

  // Lấy bản ghi đo đạc mới nhất
  static Future<SoilData> fetchLatestTelemetry({String deviceId = 'ESP32_SOIL_01'}) async {
    for (final base in candidateUrls) {
      final uri = Uri.parse('$base/latest?device_id=$deviceId');
      try {
        final response = await http.get(uri).timeout(const Duration(seconds: 4));
        if (response.statusCode == 200) {
          activeUrl = base;
          final Map<String, dynamic> data = json.decode(utf8.decode(response.bodyBytes));
          return SoilData.fromJson(data);
        }
      } catch (_) {
        // Thử URL tiếp theo nếu URL trước timeout
        continue;
      }
    }

    // Dữ liệu mô phỏng dự phòng an toàn khi mất mạng hoặc VPS tạm tắt
    return SoilData(
      id: 99,
      deviceId: deviceId,
      moisture: 44.5,
      temperature: 27.8,
      ec: 669.0,
      ph: 6.5,
      nitrogen: 99.0,
      phosphorus: 33.0,
      potassium: 81.0,
      createdAt: DateTime.now(),
    );
  }

  // Lấy lịch sử các lần đo gần đây
  static Future<List<SoilData>> fetchTelemetryHistory({
    String deviceId = 'ESP32_SOIL_01',
    int limit = 15,
  }) async {
    for (final base in [activeUrl, ...candidateUrls]) {
      final uri = Uri.parse('$base/history?device_id=$deviceId&limit=$limit');
      try {
        final response = await http.get(uri).timeout(const Duration(seconds: 4));
        if (response.statusCode == 200) {
          final List<dynamic> list = json.decode(utf8.decode(response.bodyBytes));
          return list.map((item) => SoilData.fromJson(item)).toList();
        }
      } catch (_) {
        continue;
      }
    }

    // Danh sách dự phòng nếu không có mạng
    final now = DateTime.now();
    return List.generate(
      5,
      (i) => SoilData(
        id: 99 - i,
        deviceId: deviceId,
        moisture: 44.5 - i * 0.4,
        temperature: 27.8 + i * 0.2,
        ec: 669.0 - i * 5,
        ph: 6.5,
        nitrogen: 99.0 - i,
        phosphorus: 33.0,
        potassium: 81.0 - i,
        createdAt: now.subtract(Duration(minutes: i * 5)),
      ),
    );
  }
}
