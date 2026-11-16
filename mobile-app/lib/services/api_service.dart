import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/soil_data.dart';

class ApiService {
  static const String baseUrl = 'http://221.121.4.208/api/v1/telemetry';

  // Lấy bản ghi đo đạc mới nhất từ VPS
  static Future<SoilData> fetchLatestTelemetry({String deviceId = 'ESP32_SOIL_01'}) async {
    final uri = Uri.parse('$baseUrl/latest?device_id=$deviceId');
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 6));
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
    final uri = Uri.parse('$baseUrl/history?device_id=$deviceId&limit=$limit');
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 6));
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
