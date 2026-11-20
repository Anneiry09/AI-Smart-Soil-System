import 'package:flutter/material.dart';

class SoilData {
  final int? id;
  final String deviceId;
  final double moisture;
  final double temperature;
  final double ec;
  final double ph;
  final double nitrogen;
  final double phosphorus;
  final double potassium;
  final DateTime createdAt;

  SoilData({
    this.id,
    required this.deviceId,
    required this.moisture,
    required this.temperature,
    required this.ec,
    required this.ph,
    required this.nitrogen,
    required this.phosphorus,
    required this.potassium,
    required this.createdAt,
  });

  factory SoilData.fromJson(Map<String, dynamic> json) {
    DateTime parsedDate = DateTime.now();
    if (json['created_at'] != null) {
      final rawStr = json['created_at'].toString();
      final cleanStr = rawStr.endsWith('Z') ? rawStr : '${rawStr}Z';
      parsedDate = DateTime.tryParse(cleanStr)?.toLocal() ?? DateTime.now();
    }

    return SoilData(
      id: json['id'],
      deviceId: json['device_id'] ?? 'ESP32_SOIL_01',
      moisture: (json['moisture'] as num?)?.toDouble() ?? 0.0,
      temperature: (json['temperature'] as num?)?.toDouble() ?? 0.0,
      ec: (json['ec'] as num?)?.toDouble() ?? 0.0,
      ph: (json['ph'] as num?)?.toDouble() ?? 0.0,
      nitrogen: (json['nitrogen'] as num?)?.toDouble() ?? 0.0,
      phosphorus: (json['phosphorus'] as num?)?.toDouble() ?? 0.0,
      potassium: (json['potassium'] as num?)?.toDouble() ?? 0.0,
      createdAt: parsedDate,
    );
  }

  // Phát hiện lỗi cảm biến cực trị
  bool get isFault => temperature <= -35 || ec >= 19999 || (moisture >= 99 && ph >= 13.9);

  // Kiểm tra thiết bị có đang hoạt động trong vòng 30 giây không
  bool get isOnline => DateTime.now().difference(createdAt).inSeconds < 30;

  // --- ĐÁNH GIÁ NÔNG HỌC & MÀU SẮC TRỰC QUAN ---

  // Đánh giá Độ pH
  String get phStatus {
    if (ph < 5.0) return 'Đất chua nặng (Nhiễm phèn)';
    if (ph < 6.0) return 'Hơi chua (Phù hợp cây có múi/sầu riêng)';
    if (ph <= 7.2) return 'Lý tưởng (Độ pH trung tính)';
    return 'Đất kiềm';
  }

  Color get phColor {
    if (ph < 5.0) return Colors.deepOrange;
    if (ph < 6.0) return Colors.orange;
    if (ph <= 7.2) return Colors.green;
    return Colors.purple;
  }

  // Đánh giá Độ dẫn điện EC
  String get ecStatus {
    if (ec < 300) return 'Nghèo dinh dưỡng / Thiếu phân';
    if (ec <= 1500) return 'Nồng độ khoáng lý tưởng';
    if (ec <= 2500) return 'Nồng độ cao (Cân nhắc giảm phân)';
    return 'Ngộ độc phân / Nguy cơ cháy rễ';
  }

  Color get ecColor {
    if (ec < 300) return Colors.amber.shade800;
    if (ec <= 1500) return Colors.green;
    if (ec <= 2500) return Colors.orange;
    return Colors.red;
  }

  // Đánh giá Độ ẩm
  String get moistureStatus {
    if (moisture < 30) return 'Đất khô hạn (Cần tưới nước)';
    if (moisture <= 75) return 'Độ ẩm đất tối ưu';
    return 'Đất thừa nước (Nguy cơ úng rễ)';
  }

  Color get moistureColor {
    if (moisture < 30) return Colors.orange;
    if (moisture <= 75) return Colors.blue.shade600;
    return Colors.indigo;
  }

  // Đánh giá Nhiệt độ đất
  String get tempStatus {
    if (temperature < 20) return 'Nhiệt độ rễ thấp';
    if (temperature <= 32) return 'Nhiệt độ tối ưu';
    return 'Sốc nhiệt rễ (Cần phủ gốc che mát)';
  }

  Color get tempColor {
    if (temperature < 20) return Colors.cyan;
    if (temperature <= 32) return Colors.teal;
    return Colors.redAccent;
  }
}
