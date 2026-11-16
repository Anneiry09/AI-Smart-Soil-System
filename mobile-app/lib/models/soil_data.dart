class SoilData {
  final double moisture;
  final double temperature;
  final double ec;
  final double ph;
  final double nitrogen;
  final double phosphorus;
  final double potassium;
  final DateTime timestamp;

  SoilData({
    required this.moisture,
    required this.temperature,
    required this.ec,
    required this.ph,
    required this.nitrogen,
    required this.phosphorus,
    required this.potassium,
    required this.timestamp,
  });

  factory SoilData.fromJson(Map<String, dynamic> json) {
    return SoilData(
      moisture: (json['moisture'] ?? 0.0).toDouble(),
      temperature: (json['temperature'] ?? 0.0).toDouble(),
      ec: (json['ec'] ?? 0.0).toDouble(),
      ph: (json['ph'] ?? 0.0).toDouble(),
      nitrogen: (json['nitrogen'] ?? 0.0).toDouble(),
      phosphorus: (json['phosphorus'] ?? 0.0).toDouble(),
      potassium: (json['potassium'] ?? 0.0).toDouble(),
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'])
          : DateTime.now(),
    );
  }
}
