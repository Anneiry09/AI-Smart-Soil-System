import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/soil_data.dart';

class ApiService {
  static const String primaryUrl = 'http://smartsoil.duckdns.org/api/v1/telemetry';
  static const String fallbackUrl = 'http://221.121.4.208/api/v1/telemetry';

  // Lấy bản ghi đo đạc mới nhất từ VPS
  static Future<SoilData> fetchLatestTelemetry({String deviceId = 'ESP32_SOIL_01'}) async {
    try {
      final uri = Uri.parse('$primaryUrl/latest?device_id=$deviceId');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return SoilData.fromJson(data);
      }
    } catch (_) {
      // Thử lại qua IP nếu DuckDNS gặp độ trễ
    }

    try {
      final fallbackUri = Uri.parse('$fallbackUrl/latest?device_id=$deviceId');
      final response = await http.get(fallbackUri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(utf8.decode(response.bodyBytes));
        return SoilData.fromJson(data);
      } else {
        throw Exception('Server phản hồi lỗi (Mã ${response.statusCode})');
      }
    } catch (e) {
      throw Exception('Không thể kết nối tới máy chủ VPS: $e');
    }
  }

  // Lấy lịch sử các lần đo gần đây
  static Future<List<SoilData>> fetchTelemetryHistory({
    String deviceId = 'ESP32_SOIL_01',
    int limit = 15,
  }) async {
    try {
      final uri = Uri.parse('$primaryUrl/history?device_id=$deviceId&limit=$limit');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final List<dynamic> list = json.decode(utf8.decode(response.bodyBytes));
        return list.map((item) => SoilData.fromJson(item)).toList();
      }
    } catch (_) {
      // Fallback
    }

    try {
      final fallbackUri = Uri.parse('$fallbackUrl/history?device_id=$deviceId&limit=$limit');
      final response = await http.get(fallbackUri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final List<dynamic> list = json.decode(utf8.decode(response.bodyBytes));
        return list.map((item) => SoilData.fromJson(item)).toList();
      } else {
        throw Exception('Không thể tải lịch sử (Mã ${response.statusCode})');
      }
    } catch (e) {
      throw Exception('Lỗi kết nối lịch sử: $e');
    }
  }
}
