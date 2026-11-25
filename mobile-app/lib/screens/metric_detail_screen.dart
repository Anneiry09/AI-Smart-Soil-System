import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/soil_data.dart';

class MetricDetailScreen extends StatelessWidget {
  final String title;
  final IconData icon;
  final String unit;
  final double currentValue;
  final double minRange;
  final double maxRange;
  final double optimalMin;
  final double optimalMax;
  final String statusText;
  final Color statusColor;
  final String selectedNode;
  final List<SoilData> history;
  final double Function(SoilData) valueExtractor;
  final int decimalPlaces;

  const MetricDetailScreen({
    super.key,
    required this.title,
    required this.icon,
    required this.unit,
    required this.currentValue,
    required this.minRange,
    required this.maxRange,
    required this.optimalMin,
    required this.optimalMax,
    required this.statusText,
    required this.statusColor,
    required this.selectedNode,
    required this.history,
    required this.valueExtractor,
    this.decimalPlaces = 1,
  });

  String _formatVal(double v) => v.toStringAsFixed(decimalPlaces);

  String _getNodeLocationDesc(String nodeId) {
    if (nodeId.contains('01')) return 'Lô A2 - Vườn Sầu Riêng Monthong';
    if (nodeId.contains('02')) return 'Lô B1 - Vườn Sầu Riêng Ri6';
    if (nodeId.contains('03')) return 'Lô C - Vườn Ươm Cây Giống';
    return 'Khu vực quan trắc tự động';
  }

  @override
  Widget build(BuildContext context) {
    final timeFormat = DateFormat('dd/MM - HH:mm');
    // history thường sắp xếp mới nhất ở index 0
    final orderedHistory = history.isNotEmpty ? history : <SoilData>[];
    final values = orderedHistory.map(valueExtractor).toList();

    final double minVal = values.isNotEmpty ? values.reduce(math.min) : currentValue;
    final double maxVal = values.isNotEmpty ? values.reduce(math.max) : currentValue;
    final double avgVal = values.isNotEmpty
        ? values.reduce((a, b) => a + b) / values.length
        : currentValue;

    // Tính biến động so với đợt đo ngay trước đó
    double? delta;
    double? deltaPct;
    if (values.length >= 2) {
      final latest = values[0];
      final prev = values[1];
      delta = latest - prev;
      if (prev.abs() > 1e-6) {
        deltaPct = (delta / prev) * 100;
      }
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      appBar: AppBar(
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
        elevation: 0,
        title: Text(
          title,
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. THẺ TỔNG QUAN & VỊ TRÍ ĐO ĐẠC
            _buildSummaryHeaderCard(
              orderedHistory.isNotEmpty ? timeFormat.format(orderedHistory.first.createdAt) : '--',
              delta,
              deltaPct,
            ),
            const SizedBox(height: 14),

            // 2. THỐNG KÊ MIN - AVG - MAX & NGƯỠNG TỐI ƯU
            _buildStatsRow(minVal, avgVal, maxVal),
            const SizedBox(height: 14),

            // 3. BIỂU ĐỒ XU HƯỚNG QUA CÁC ĐỢT ĐO
            _buildTrendChartCard(orderedHistory),
            const SizedBox(height: 14),

            // 4. DANH SÁCH DỮ LIỆU ĐO TỪNG ĐỢT
            _buildBatchHistoryCard(orderedHistory, timeFormat),
            const SizedBox(height: 14),

            // 5. KHUYẾN NGHỊ XỬ LÝ RIÊNG
            _buildRecommendationBox(),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryHeaderCard(String lastTime, double? delta, double? deltaPct) {
    final bool isUp = (delta ?? 0) > 0;
    final bool isDown = (delta ?? 0) < 0;
    final Color deltaColor = isUp
        ? const Color(0xFF2E7D32)
        : (isDown ? Colors.deepOrange : Colors.grey.shade600);
    final String deltaSign = isUp ? '+' : '';
    final String deltaText = delta != null
        ? '${isUp ? "▲" : (isDown ? "▼" : "•")} $deltaSign${_formatVal(delta)} $unit${deltaPct != null ? " ($deltaSign${deltaPct.toStringAsFixed(1)}%)" : ""}'
        : 'Chưa có dữ liệu so sánh trước đó';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 1))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: statusColor.withAlpha(25),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: statusColor, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: [
                        Text(
                          _formatVal(currentValue),
                          style: TextStyle(
                            fontSize: 30,
                            fontWeight: FontWeight.w900,
                            color: statusColor,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          unit,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: Colors.grey.shade700,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      deltaText,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: deltaColor,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const Divider(height: 22),
          Row(
            children: [
              const Icon(Icons.location_on_outlined, size: 16, color: Color(0xFFF57C00)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Vị trí: $selectedNode • ${_getNodeLocationDesc(selectedNode)}',
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF0F172A)),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 2,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Icon(Icons.access_time, size: 15, color: Colors.grey.shade600),
              const SizedBox(width: 6),
              Text(
                'Đợt đo mới nhất: $lastTime',
                style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatsRow(double minVal, double avgVal, double maxVal) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 1))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Thống kê chuỗi đo',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF2E7D32).withAlpha(20),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  'Chuẩn: ${_formatVal(optimalMin)} – ${_formatVal(optimalMax)} $unit',
                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildStatBox('Thấp nhất', '${_formatVal(minVal)} $unit', Colors.blue.shade700),
              const SizedBox(width: 8),
              _buildStatBox('Trung bình', '${_formatVal(avgVal)} $unit', const Color(0xFF2E7D32)),
              const SizedBox(width: 8),
              _buildStatBox('Cao nhất', '${_formatVal(maxVal)} $unit', Colors.deepOrange),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatBox(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withAlpha(14),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withAlpha(45)),
        ),
        child: Column(
          children: [
            Text(label, style: TextStyle(fontSize: 11, color: Colors.grey.shade700)),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: color),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTrendChartCard(List<SoilData> orderedHistory) {
    // Đảo ngược để vẽ từ cũ (trái) sang mới (phải)
    final chartItems = orderedHistory.reversed.toList();
    final chartValues = chartItems.map(valueExtractor).toList();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 1))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Biểu đồ diễn biến theo đợt',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
              ),
              Text(
                '${chartValues.length} đợt gần nhất',
                style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
              ),
            ],
          ),
          const SizedBox(height: 14),
          SizedBox(
            height: 150,
            width: double.infinity,
            child: chartValues.length < 2
                ? Center(
                    child: Text(
                      'Cần ít nhất 2 đợt đo để vẽ biểu đồ xu hướng',
                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                    ),
                  )
                : CustomPaint(
                    painter: _MetricLineChartPainter(
                      values: chartValues,
                      minRange: minRange,
                      maxRange: maxRange,
                      optimalMin: optimalMin,
                      optimalMax: optimalMax,
                      lineColor: statusColor,
                    ),
                  ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Container(width: 14, height: 3, color: const Color(0xFF2E7D32).withAlpha(110)),
              const SizedBox(width: 6),
              Text(
                'Vùng xanh nhạt: Ngưỡng tối ưu (${_formatVal(optimalMin)} – ${_formatVal(optimalMax)} $unit)',
                style: TextStyle(fontSize: 11, color: Colors.grey.shade700),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBatchHistoryCard(List<SoilData> orderedHistory, DateFormat timeFormat) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 1))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Dữ liệu đo từng đợt',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
          ),
          const SizedBox(height: 10),
          if (orderedHistory.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text('Chưa có lịch sử đo đạc.', style: TextStyle(color: Colors.grey)),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: orderedHistory.length,
              separatorBuilder: (context, index) => const Divider(height: 14),
              itemBuilder: (context, index) {
                final item = orderedHistory[index];
                final val = valueExtractor(item);
                double? stepDelta;
                if (index + 1 < orderedHistory.length) {
                  stepDelta = val - valueExtractor(orderedHistory[index + 1]);
                }

                final bool inOptimal = val >= optimalMin && val <= optimalMax;
                final Color badgeColor = inOptimal ? const Color(0xFF2E7D32) : Colors.deepOrange;

                String deltaLabel = '—';
                Color deltaColor = Colors.grey;
                if (stepDelta != null) {
                  if (stepDelta > 0) {
                    deltaLabel = '+${_formatVal(stepDelta)}';
                    deltaColor = const Color(0xFF2E7D32);
                  } else if (stepDelta < 0) {
                    deltaLabel = _formatVal(stepDelta);
                    deltaColor = Colors.deepOrange;
                  } else {
                    deltaLabel = '0';
                  }
                }

                return Row(
                  children: [
                    Container(
                      width: 28,
                      height: 28,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '#${index + 1}',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.grey.shade700),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            timeFormat.format(item.createdAt),
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF0F172A)),
                          ),
                          Text(
                            inOptimal ? 'Trong ngưỡng an toàn' : 'Ngoài ngưỡng tối ưu',
                            style: TextStyle(fontSize: 11, color: badgeColor),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${_formatVal(val)} $unit',
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                        ),
                        Text(
                          deltaLabel,
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: deltaColor),
                        ),
                      ],
                    ),
                  ],
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildRecommendationBox() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF3E0),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFFFCC80)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.tips_and_updates_outlined, color: statusColor, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Đánh giá & Khuyến nghị xử lý',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                ),
                const SizedBox(height: 4),
                Text(
                  statusText,
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade800, height: 1.4),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricLineChartPainter extends CustomPainter {
  final List<double> values;
  final double minRange;
  final double maxRange;
  final double optimalMin;
  final double optimalMax;
  final Color lineColor;

  _MetricLineChartPainter({
    required this.values,
    required this.minRange,
    required this.maxRange,
    required this.optimalMin,
    required this.optimalMax,
    required this.lineColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;

    final double dataMin = values.reduce(math.min);
    final double dataMax = values.reduce(math.max);
    final double lowerBound = math.min(dataMin, optimalMin);
    final double upperBound = math.max(dataMax, optimalMax);
    final double span = math.max(upperBound - lowerBound, 1e-3);
    final double yMin = math.max(minRange, lowerBound - span * 0.2);
    final double yMax = math.min(maxRange, upperBound + span * 0.2);
    final double ySpan = math.max(yMax - yMin, 1e-3);

    double toY(double v) {
      final norm = ((v - yMin) / ySpan).clamp(0.0, 1.0);
      return size.height - norm * (size.height - 16) - 8;
    }

    // Vẽ vùng tối ưu màu xanh nhạt
    final double optTop = toY(optimalMax);
    final double optBottom = toY(optimalMin);
    final optPaint = Paint()..color = const Color(0xFF2E7D32).withAlpha(24);
    canvas.drawRect(
      Rect.fromLTRB(0, math.min(optTop, optBottom), size.width, math.max(optTop, optBottom)),
      optPaint,
    );

    // Đường lưới ngang nhẹ
    final gridPaint = Paint()
      ..color = Colors.grey.withAlpha(45)
      ..strokeWidth = 1;
    for (int i = 0; i <= 2; i++) {
      final y = (size.height - 16) * (i / 2) + 8;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // Tạo đường nối các điểm đo
    final path = Path();
    final points = <Offset>[];
    final double dxStep = values.length > 1 ? size.width / (values.length - 1) : size.width;

    for (int i = 0; i < values.length; i++) {
      final x = i * dxStep;
      final y = toY(values[i]);
      points.add(Offset(x, y));
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    final linePaint = Paint()
      ..color = lineColor
      ..strokeWidth = 2.6
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(path, linePaint);

    // Vẽ chấm tròn tại từng đợt đo
    final dotFill = Paint()..color = Colors.white;
    final dotStroke = Paint()
      ..color = lineColor
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    for (final p in points) {
      canvas.drawCircle(p, 4.0, dotFill);
      canvas.drawCircle(p, 4.0, dotStroke);
    }
  }

  @override
  bool shouldRepaint(covariant _MetricLineChartPainter oldDelegate) => true;
}
