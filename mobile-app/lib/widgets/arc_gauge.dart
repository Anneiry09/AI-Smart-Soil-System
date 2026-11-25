import 'dart:math' as math;
import 'package:flutter/material.dart';

class ArcGauge extends StatelessWidget {
  final double value;
  final double min;
  final double max;
  final String unit;
  final List<Color>? gradientColors;
  final double size;
  final String? customValueDisplay;

  const ArcGauge({
    super.key,
    required this.value,
    required this.min,
    required this.max,
    required this.unit,
    this.gradientColors,
    this.size = 150,
    this.customValueDisplay,
  });

  @override
  Widget build(BuildContext context) {
    final colors = gradientColors ??
        const [
          Color(0xFFE53935), // Đỏ (Thấp / Chua / Nghèo)
          Color(0xFFFDD835), // Vàng (Trung bình / Hơi thấp)
          Color(0xFF43A047), // Xanh lá (Lý tưởng / Đủ)
          Color(0xFFFB8C00), // Cam (Hơi cao)
          Color(0xFFD32F2F), // Đỏ đậm (Quá cao / Ngộ độc)
        ];

    final displayVal = customValueDisplay ?? (value % 1 == 0 ? value.toInt().toString() : value.toStringAsFixed(1));

    return SizedBox(
      width: size,
      height: size * 0.65,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size * 0.65),
            painter: _ArcGaugePainter(
              value: value,
              min: min,
              max: max,
              colors: colors,
            ),
          ),
          Positioned(
            bottom: 4,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  displayVal,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w900,
                    color: Color(0xFF1B5E20),
                    letterSpacing: -0.5,
                  ),
                ),
                Text(
                  unit,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey.shade600,
                  ),
                ),
              ],
            ),
          ),
          Positioned(
            left: 12,
            bottom: 2,
            child: Text(
              min % 1 == 0 ? min.toInt().toString() : min.toStringAsFixed(1),
              style: TextStyle(fontSize: 10, color: Colors.grey.shade500, fontWeight: FontWeight.bold),
            ),
          ),
          Positioned(
            right: 12,
            bottom: 2,
            child: Text(
              max % 1 == 0 ? max.toInt().toString() : max.toStringAsFixed(1),
              style: TextStyle(fontSize: 10, color: Colors.grey.shade500, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }
}

class _ArcGaugePainter extends CustomPainter {
  final double value;
  final double min;
  final double max;
  final List<Color> colors;

  _ArcGaugePainter({
    required this.value,
    required this.min,
    required this.max,
    required this.colors,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final strokeWidth = size.width * 0.085;
    final center = Offset(size.width / 2, size.height * 0.95);
    final radius = (size.width - strokeWidth) / 2 - 4;

    const startAngle = math.pi; // 180 degrees (9 o'clock)
    const sweepAngle = math.pi; // 180 degrees sweep to (3 o'clock)

    // 1. Draw Background Track (Màu nền mờ)
    final bgPaint = Paint()
      ..color = const Color(0xFFECEFF1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      bgPaint,
    );

    // 2. Draw Multi-color Gradient Arc (Dải màu vòng cung)
    final rect = Rect.fromCircle(center: center, radius: radius);
    final gradient = SweepGradient(
      startAngle: startAngle,
      endAngle: startAngle + sweepAngle,
      colors: colors,
    );

    final activePaint = Paint()
      ..shader = gradient.createShader(rect)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      rect,
      startAngle,
      sweepAngle,
      false,
      activePaint,
    );

    // 3. Draw Indicator Thumb (Con trỏ vị trí đo hiện tại)
    final clampedVal = value.clamp(min, max);
    final progress = (max == min) ? 0.0 : (clampedVal - min) / (max - min);
    final thumbAngle = startAngle + (progress * sweepAngle);

    final thumbX = center.dx + radius * math.cos(thumbAngle);
    final thumbY = center.dy + radius * math.sin(thumbAngle);

    // Vòng tròn ngoài màu trắng
    final thumbPaintOuter = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    // Vòng tròn đổ bóng nhẹ
    final shadowPaint = Paint()
      ..color = Colors.black26
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2);

    canvas.drawCircle(Offset(thumbX, thumbY + 1), strokeWidth * 0.7, shadowPaint);
    canvas.drawCircle(Offset(thumbX, thumbY), strokeWidth * 0.7, thumbPaintOuter);

    // Vòng tròn trong màu xanh đậm/màu nhấn
    final thumbPaintInner = Paint()
      ..color = const Color(0xFF1B5E20)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(Offset(thumbX, thumbY), strokeWidth * 0.38, thumbPaintInner);
  }

  @override
  bool shouldRepaint(covariant _ArcGaugePainter oldDelegate) {
    return oldDelegate.value != value ||
        oldDelegate.min != min ||
        oldDelegate.max != max;
  }
}
