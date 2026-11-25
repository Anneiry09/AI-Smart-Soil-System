import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/soil_data.dart';

class HomeScreen extends StatelessWidget {
  final SoilData? latestData;
  final List<SoilData> history;
  final bool isLoading;
  final VoidCallback onRefresh;
  final VoidCallback onNavigateToMeasurement;

  const HomeScreen({
    super.key,
    required this.latestData,
    required this.history,
    required this.isLoading,
    required this.onRefresh,
    required this.onNavigateToMeasurement,
  });

  @override
  Widget build(BuildContext context) {
    final d = latestData;
    final timeFormat = DateFormat('HH:mm:ss - dd/MM/yyyy');

    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: const Color(0xFF2E7D32).withAlpha(25),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.eco, color: Color(0xFF2E7D32), size: 22),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'AI SMART SOIL SYSTEM',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: Color(0xFF1B5E20)),
                ),
                Text(
                  'Hệ thống quan trắc thổ nhưỡng',
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF2E7D32)),
            onPressed: onRefresh,
            tooltip: 'Làm mới',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => onRefresh(),
        color: const Color(0xFF2E7D32),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. BANNER LỜI CHÀO & TRẠM ĐO
              _buildGreetingBanner(d, timeFormat),
              const SizedBox(height: 16),

              // 2. KHUYẾN NGHỊ NÔNG HỌC TỨC THỜI (AI ADVISORY)
              if (d != null) ...[
                _buildAdvisoryCard(d),
                const SizedBox(height: 16),
              ],

              // 3. TIÊU ĐỀ BẢNG THÔNG TIN SỐ LIỆU ĐO ĐẠC
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Expanded(
                    child: Text(
                      'Bảng Số Liệu Đo Đạc Hiện Tại',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  ),
                  const SizedBox(width: 8),
                  TextButton.icon(
                    onPressed: onNavigateToMeasurement,
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    icon: const Icon(Icons.speed, size: 16, color: Color(0xFF2E7D32)),
                    label: const Text('Xem vòng cung', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // 4. LƯỚI THẺ 7 CHỈ SỐ ĐẤT THỜI GIAN THỰC
              if (isLoading && d == null)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32.0),
                    child: CircularProgressIndicator(color: Color(0xFF2E7D32)),
                  ),
                )
              else if (d == null)
                _buildEmptyState()
              else ...[
                _buildTelemetryGrid(d),
                const SizedBox(height: 18),
              ],

              // 5. BANNER HƯỚNG DẪN BẤM NÚT ĐO
              _buildMeasureGuideBanner(),
              const SizedBox(height: 18),

              // 6. BẢNG NHẬT KÝ THU THẬP GẦN ĐÂY
              _buildRecentHistorySection(history, timeFormat),
              const SizedBox(height: 80),
            ],
          ),
        ),
      ),
    );
  }

  // BANNER LỜI CHÀO
  Widget _buildGreetingBanner(SoilData? d, DateFormat timeFormat) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18.0),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2E7D32), Color(0xFF1B5E20)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: const [
          BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 3)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Xin chào, Trí Phan 👋',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Trạm quan trắc thổ nhưỡng sầu riêng',
                      style: TextStyle(fontSize: 12, color: Colors.white70),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(35),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white24),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.circle, size: 8, color: Colors.lightGreenAccent),
                    SizedBox(width: 6),
                    Text('Trực tuyến', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white)),
                  ],
                ),
              ),
            ],
          ),
          const Divider(color: Colors.white24, height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Text(
                  'Node: ESP32_SOIL_01',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white.withAlpha(230)),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 1,
                ),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  d != null ? timeFormat.format(d.createdAt) : '--:--:--',
                  style: TextStyle(fontSize: 11, color: Colors.white.withAlpha(190)),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 1,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // KHUYẾN NGHỊ NÔNG HỌC TỨC THỜI
  Widget _buildAdvisoryCard(SoilData d) {
    String message;
    IconData icon;
    Color color;

    if (d.ph < 5.8) {
      message = 'Độ chua pH thấp (${d.ph.toStringAsFixed(1)}). Đất có nguy cơ bị bó rễ và khóa lân; khuyến nghị kích hoạt bơm vôi sữa Nano để nâng pH.';
      icon = Icons.warning_amber_rounded;
      color = Colors.orange.shade800;
    } else if (d.moisture < 40) {
      message = 'Độ ẩm đất thấp (${d.moisture.toStringAsFixed(1)}%). Đất đang thiếu nước, khuyến nghị bật tưới nhỏ giọt.';
      icon = Icons.water_drop_outlined;
      color = Colors.blue.shade700;
    } else {
      message = 'Thổ nhưỡng đạt trạng thái lý tưởng! Độ ẩm ${d.moisture.toStringAsFixed(1)}%, pH ${d.ph.toStringAsFixed(1)} rất thuận lợi cho cây phát triển rễ tơ.';
      icon = Icons.check_circle_outline;
      color = const Color(0xFF2E7D32);
    }

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Khuyến nghị nông học tự động',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color),
                ),
                const SizedBox(height: 2),
                Text(
                  message,
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade800, height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // LƯỚI THẺ 7 CHỈ SỐ
  Widget _buildTelemetryGrid(SoilData d) {
    return Column(
      children: [
        // Hàng 1: 4 chỉ số môi trường đất
        Row(
          children: [
            Expanded(child: _buildMetricTile('Độ ẩm đất', '${d.moisture.toStringAsFixed(1)}%', Icons.water_drop, Colors.blue.shade700, d.moistureStatus)),
            const SizedBox(width: 10),
            Expanded(child: _buildMetricTile('Nhiệt độ đất', '${d.temperature.toStringAsFixed(1)}°C', Icons.thermostat, Colors.orange.shade800, d.tempStatus)),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: _buildMetricTile('Độ chua (pH)', d.ph.toStringAsFixed(1), Icons.science, d.phColor, d.phStatus)),
            const SizedBox(width: 10),
            Expanded(child: _buildMetricTile('Độ dẫn điện EC', '${d.ec.toInt()} µS', Icons.bolt, d.ecColor, d.ecStatus)),
          ],
        ),
        const SizedBox(height: 10),

        // Hàng 2: 3 chỉ số dinh dưỡng đa lượng N-P-K
        Row(
          children: [
            Expanded(child: _buildNpkTile('Đạm (N)', '${d.nitrogen.toInt()}', 'mg/kg', const Color(0xFF2E7D32))),
            const SizedBox(width: 8),
            Expanded(child: _buildNpkTile('Lân (P)', '${d.phosphorus.toInt()}', 'mg/kg', Colors.amber.shade800)),
            const SizedBox(width: 8),
            Expanded(child: _buildNpkTile('Kali (K)', '${d.potassium.toInt()}', 'mg/kg', Colors.purple.shade700)),
          ],
        ),
      ],
    );
  }

  Widget _buildMetricTile(String label, String value, IconData icon, Color color, String status) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 1))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.black54)),
              Icon(icon, size: 18, color: color),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: color),
          ),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(color: color.withAlpha(20), borderRadius: BorderRadius.circular(4)),
            child: Text(
              status,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNpkTile(String label, String value, String unit, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withAlpha(50)),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 3, offset: Offset(0, 1))],
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: color)),
          Text(unit, style: const TextStyle(fontSize: 9, color: Colors.grey)),
        ],
      ),
    );
  }

  // BANNER HƯỚNG DẪN BẤM ĐO
  Widget _buildMeasureGuideBanner() {
    return InkWell(
      onTap: onNavigateToMeasurement,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFFE8F5E9),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFA5D6A7)),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: Color(0xFF2E7D32),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.wifi_tethering, color: Colors.white, size: 24),
            ),
            const SizedBox(width: 14),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Đồng Hồ Đo Vòng Cung Chi Tiết',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'Bấm nút [Đo] ở giữa hoặc bấm vào đây để xem trực quan',
                    style: TextStyle(fontSize: 11, color: Colors.black54),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Color(0xFF2E7D32)),
          ],
        ),
      ),
    );
  }

  // LỊCH SỬ THU THẬP GẦN ĐÂY
  Widget _buildRecentHistorySection(List<SoilData> list, DateFormat timeFormat) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 1))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Nhật Ký Dữ Liệu Gần Nhất',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
              ),
              Text('${list.length} bản ghi', style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ),
          const Divider(height: 18),
          if (list.isEmpty)
            const Padding(
              padding: EdgeInsets.all(12.0),
              child: Center(child: Text('Chưa có lịch sử dữ liệu', style: TextStyle(color: Colors.grey, fontSize: 12))),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: list.take(5).length,
              separatorBuilder: (context, index) => const Divider(height: 10),
              itemBuilder: (context, index) {
                final item = list[index];
                return Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          timeFormat.format(item.createdAt),
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                        Text(
                          'Ẩm: ${item.moisture.toStringAsFixed(1)}% • Nhiệt: ${item.temperature.toStringAsFixed(1)}°C • EC: ${item.ec.toInt()} µS',
                          style: const TextStyle(fontSize: 10, color: Colors.black54),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                      decoration: BoxDecoration(
                        color: item.phColor.withAlpha(25),
                        borderRadius: BorderRadius.circular(5),
                      ),
                      child: Text(
                        'pH ${item.ph.toStringAsFixed(1)}',
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: item.phColor),
                      ),
                    ),
                  ],
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            const Text('Chưa kết nối được máy chủ', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: onRefresh, child: const Text('Tải lại')),
          ],
        ),
      ),
    );
  }
}
