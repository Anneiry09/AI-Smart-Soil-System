import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/soil_data.dart';
import '../widgets/arc_gauge.dart';
import 'metric_detail_screen.dart';

class MeasurementScreen extends StatefulWidget {
  final SoilData? latestData;
  final List<SoilData> history;
  final bool isLoading;
  final VoidCallback onRefresh;
  final String selectedNode;
  final Function(String) onNodeChanged;

  const MeasurementScreen({
    super.key,
    required this.latestData,
    required this.history,
    required this.isLoading,
    required this.onRefresh,
    required this.selectedNode,
    required this.onNodeChanged,
  });

  @override
  State<MeasurementScreen> createState() => _MeasurementScreenState();
}

class _MeasurementScreenState extends State<MeasurementScreen> with SingleTickerProviderStateMixin {
  int _selectedTab = 0; // 0: Giá trị tức thời, 1: Quá trình
  late final AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final d = widget.latestData;
    final timeFormat = DateFormat('dd/MM/yyyy - HH:mm');

    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      body: SafeArea(
        top: false,
        child: RefreshIndicator(
          onRefresh: () async => widget.onRefresh(),
          color: const Color(0xFF2E7D32),
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            slivers: [
              // 1. TOP GREEN APP BAR (Sóng cong + 3 chip mini)
              SliverToBoxAdapter(
                child: _buildTopHeader(d, timeFormat),
              ),

              // 2. THANH CHỌN ĐIỂM ĐO NẰM NGOÀI KHUNG XANH
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                  child: _buildNodeSelectorBar(),
                ),
              ),

              // 3. SEGMENTED TABS (Giá trị tức thời / Quá trình)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10.0),
                  child: _buildSegmentedSwitcher(),
                ),
              ),

              // 3. TAB CONTENT
              if (_selectedTab == 0) ...[
                if (widget.isLoading && d == null)
                  const SliverFillRemaining(
                    child: Center(
                      child: CircularProgressIndicator(color: Color(0xFF2E7D32)),
                    ),
                  )
                else if (d == null)
                  SliverFillRemaining(
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.cloud_off, size: 54, color: Colors.grey),
                          const SizedBox(height: 12),
                          const Text('Không có dữ liệu cảm biến!', style: TextStyle(color: Colors.grey)),
                          const SizedBox(height: 12),
                          ElevatedButton.icon(
                            onPressed: widget.onRefresh,
                            icon: const Icon(Icons.refresh),
                            label: const Text('Thử lại'),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  SliverPadding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0),
                    sliver: SliverList(
                      delegate: SliverChildListDelegate([
                        // Card 1: Tổng đạm dễ tiêu
                        _buildArcMetricCard(
                          title: 'Tổng đạm dễ tiêu',
                          icon: Icons.eco,
                          value: d.nitrogen,
                          min: 0,
                          max: 300,
                          optimalMin: 40,
                          optimalMax: 90,
                          unit: 'mg/kg',
                          statusText: _getNStatus(d.nitrogen),
                          statusColor: _getNColor(d.nitrogen),
                          valueExtractor: (s) => s.nitrogen,
                          decimalPlaces: 0,
                        ),

                        // Card 2: Lân P2O5 dễ tiêu
                        _buildArcMetricCard(
                          title: 'Lân P2O5 dễ tiêu',
                          icon: Icons.grass,
                          value: d.phosphorus,
                          min: 0,
                          max: 100,
                          optimalMin: 20,
                          optimalMax: 55,
                          unit: 'mg/kg',
                          statusText: _getPStatus(d.phosphorus),
                          statusColor: _getPColor(d.phosphorus),
                          valueExtractor: (s) => s.phosphorus,
                          decimalPlaces: 0,
                        ),

                        // Card 3: Kali K2O dễ tiêu
                        _buildArcMetricCard(
                          title: 'Kali K2O dễ tiêu',
                          icon: Icons.diamond_outlined,
                          value: d.potassium,
                          min: 0,
                          max: 300,
                          optimalMin: 75,
                          optimalMax: 140,
                          unit: 'mg/kg',
                          statusText: _getKStatus(d.potassium),
                          statusColor: _getKColor(d.potassium),
                          valueExtractor: (s) => s.potassium,
                          decimalPlaces: 0,
                        ),

                        // Card 4: Độ dẫn điện EC
                        _buildArcMetricCard(
                          title: 'Độ dẫn điện EC',
                          icon: Icons.bolt,
                          value: d.ec,
                          min: 0,
                          max: 1600,
                          optimalMin: 300,
                          optimalMax: 1000,
                          unit: 'µS/cm',
                          statusText: d.ecStatus,
                          statusColor: d.ecColor,
                          valueExtractor: (s) => s.ec,
                          decimalPlaces: 0,
                        ),

                        // Card 5: Độ chua pH
                        _buildArcMetricCard(
                          title: 'Độ chua của đất (pH)',
                          icon: Icons.science_outlined,
                          value: d.ph,
                          min: 3.0,
                          max: 9.0,
                          optimalMin: 5.8,
                          optimalMax: 6.8,
                          unit: 'pH',
                          statusText: d.phStatus,
                          statusColor: d.phColor,
                          valueExtractor: (s) => s.ph,
                          decimalPlaces: 1,
                        ),

                        // Card 6: Độ ẩm đất
                        _buildArcMetricCard(
                          title: 'Độ ẩm tầng rễ mặt',
                          icon: Icons.water_drop_outlined,
                          value: d.moisture,
                          min: 0,
                          max: 100,
                          optimalMin: 40,
                          optimalMax: 65,
                          unit: '%',
                          statusText: d.moistureStatus,
                          statusColor: d.moistureColor,
                          valueExtractor: (s) => s.moisture,
                          decimalPlaces: 1,
                        ),

                        // Card 7: Nhiệt độ đất
                        _buildArcMetricCard(
                          title: 'Nhiệt độ đất vùng rễ',
                          icon: Icons.thermostat_outlined,
                          value: d.temperature,
                          min: 15,
                          max: 45,
                          optimalMin: 22,
                          optimalMax: 32,
                          unit: '°C',
                          statusText: d.tempStatus,
                          statusColor: d.tempColor,
                          valueExtractor: (s) => s.temperature,
                          decimalPlaces: 1,
                        ),

                        const SizedBox(height: 80), // Padding cho BottomBar
                      ]),
                    ),
                  ),
              ] else ...[
                // QUÁ TRÌNH (LỊCH SỬ ĐO ĐẠC)
                SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        if (widget.history.isEmpty) {
                          return const Center(
                            child: Padding(
                              padding: EdgeInsets.all(32.0),
                              child: Text('Chưa có dữ liệu chuỗi thời gian', style: TextStyle(color: Colors.grey)),
                            ),
                          );
                        }
                        final item = widget.history[index];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 10),
                          elevation: 0.5,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          child: Padding(
                            padding: const EdgeInsets.all(14.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      timeFormat.format(item.createdAt),
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: item.phColor.withAlpha(25),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        'pH ${item.ph.toStringAsFixed(1)}',
                                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: item.phColor),
                                      ),
                                    ),
                                  ],
                                ),
                                const Divider(height: 16),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    _buildMiniStat('Độ ẩm', '${item.moisture.toStringAsFixed(1)}%'),
                                    _buildMiniStat('Nhiệt độ', '${item.temperature.toStringAsFixed(1)}°C'),
                                    _buildMiniStat('EC', '${item.ec.toInt()} µS'),
                                    _buildMiniStat('NPK', '${item.nitrogen.toInt()}-${item.phosphorus.toInt()}-${item.potassium.toInt()}'),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                      childCount: widget.history.isEmpty ? 1 : widget.history.length,
                    ),
                  ),
                ),
                const SliverToBoxAdapter(child: SizedBox(height: 80)),
              ],
            ],
          ),
        ),
      ),
    );
  }

  // HEADER PHONG CÁCH XANH LÁ SÓNG CONG + 3 CHIP MINI
  Widget _buildTopHeader(SoilData? d, DateFormat timeFormat) {
    final isOnline = d != null;
    final statusColor = isOnline ? Colors.lightGreenAccent : Colors.orangeAccent;

    return ClipPath(
      clipper: _HeaderWaveClipper(),
      child: Container(
        padding: EdgeInsets.only(
          top: MediaQuery.of(context).padding.top + 14,
          left: 20,
          right: 20,
          bottom: 34,
        ),
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF2E7D32), Color(0xFF1B5E20)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    final scale = 1.0 + (_pulseController.value * 0.14);
                    final opacity = 0.65 + (_pulseController.value * 0.35);
                    return Transform.scale(
                      scale: scale,
                      child: Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withAlpha(35),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          isOnline ? Icons.wifi_tethering : Icons.portable_wifi_off,
                          color: statusColor.withValues(alpha: opacity),
                          size: 20,
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Điểm đo: ${widget.selectedNode}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        d != null
                            ? 'Cập nhật: ${timeFormat.format(d.createdAt)}'
                            : 'Đang đợi tín hiệu cảm biến...',
                        style: TextStyle(
                          color: Colors.white.withAlpha(220),
                          fontSize: 12,
                        ),
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
                    color: Colors.white.withAlpha(32),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      FadeTransition(
                        opacity: Tween<double>(begin: 0.45, end: 1.0).animate(_pulseController),
                        child: Icon(Icons.circle, size: 8, color: statusColor),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        isOnline ? 'Trực tuyến' : 'Ngoại tuyến',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // 3 CHIP MINI REALTIME (pH / Độ ẩm / Nhiệt độ)
            Row(
              children: [
                _buildHeaderMiniChip(
                  icon: Icons.science_outlined,
                  label: 'pH đất',
                  value: d != null ? d.ph.toStringAsFixed(1) : '--',
                ),
                const SizedBox(width: 8),
                _buildHeaderMiniChip(
                  icon: Icons.water_drop_outlined,
                  label: 'Độ ẩm',
                  value: d != null ? '${d.moisture.toStringAsFixed(1)}%' : '--%',
                ),
                const SizedBox(width: 8),
                _buildHeaderMiniChip(
                  icon: Icons.thermostat_outlined,
                  label: 'Nhiệt độ',
                  value: d != null ? '${d.temperature.toStringAsFixed(1)}°C' : '--°C',
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderMiniChip({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(32),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white.withAlpha(55)),
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.white, size: 16),
            const SizedBox(width: 6),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(fontSize: 10, color: Colors.white.withAlpha(200)),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                  Text(
                    value,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // THANH CHỌN ĐIỂM ĐO NẰM NGOÀI KHUNG XANH
  Widget _buildNodeSelectorBar() {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      elevation: 1.5,
      shadowColor: Colors.black12,
      child: InkWell(
        onTap: _showSelectNodeBottomSheet,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE2E8E4)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF3E0),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.location_on_outlined, color: Color(0xFFF57C00), size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Điểm đo đang chọn',
                      style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                    ),
                    Text(
                      widget.selectedNode,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF0F172A),
                      ),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: const Color(0xFFF57C00),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Chọn điểm đo',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(width: 2),
                    Icon(Icons.arrow_drop_down, color: Colors.white, size: 18),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // THANH CHUYỂN TAB DẠNG VIÊN THUỐC
  Widget _buildSegmentedSwitcher() {
    return Container(
      height: 44,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFFE2E8E4),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _selectedTab = 0),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  color: _selectedTab == 0 ? Colors.white : Colors.transparent,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: _selectedTab == 0
                      ? const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))]
                      : null,
                ),
                alignment: Alignment.center,
                child: Text(
                  'Giá trị tức thời',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: _selectedTab == 0 ? FontWeight.bold : FontWeight.w500,
                    color: _selectedTab == 0 ? const Color(0xFF2E7D32) : Colors.black54,
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _selectedTab = 1),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  color: _selectedTab == 1 ? Colors.white : Colors.transparent,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: _selectedTab == 1
                      ? const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))]
                      : null,
                ),
                alignment: Alignment.center,
                child: Text(
                  'Quá trình',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: _selectedTab == 1 ? FontWeight.bold : FontWeight.w500,
                    color: _selectedTab == 1 ? const Color(0xFF2E7D32) : Colors.black54,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // THẺ ĐO ĐẠC VỚI ĐỒNG HỒ VÒNG CUNG (ARC GAUGE)
  Widget _buildArcMetricCard({
    required String title,
    required IconData icon,
    required double value,
    required double min,
    required double max,
    required double optimalMin,
    required double optimalMax,
    required String unit,
    required String statusText,
    required Color statusColor,
    required double Function(SoilData) valueExtractor,
    int decimalPlaces = 1,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 0.8,
      color: Colors.white,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: InkWell(
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder: (_) => MetricDetailScreen(
                title: title,
                icon: icon,
                unit: unit,
                currentValue: value,
                minRange: min,
                maxRange: max,
                optimalMin: optimalMin,
                optimalMax: optimalMax,
                statusText: statusText,
                statusColor: statusColor,
                selectedNode: widget.selectedNode,
                history: widget.history,
                valueExtractor: valueExtractor,
                decimalPlaces: decimalPlaces,
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(18.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Tiêu đề thẻ & Icon
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        Flexible(
                          child: Text(
                            title,
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w800,
                              color: Color(0xFF1E293B),
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(icon, size: 16, color: const Color(0xFF2E7D32)),
                      ],
                    ),
                  ),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '${value % 1 == 0 ? value.toInt() : value.toStringAsFixed(1)} $unit',
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w900,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(Icons.chevron_right, size: 20, color: Colors.grey.shade500),
                    ],
                  ),
                ],
              ),
            const SizedBox(height: 14),

            // Đồng hồ vòng cung Arc Gauge nằm ở giữa
            Center(
              child: ArcGauge(
                value: value,
                min: min,
                max: max,
                unit: unit,
                size: 175,
              ),
            ),
            const SizedBox(height: 14),

            // Hộp trạng thái màu kem (giống mẫu ảnh Enfarm)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF3E0), // Nền kem đào dịu mắt
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFFFE0B2)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      statusText,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: statusColor.withAlpha(230),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      ),
    );
  }

  Widget _buildMiniStat(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
      ],
    );
  }

  // ĐÁNH GIÁ CHỈ SỐ NPK
  String _getNStatus(double n) {
    if (n < 40) return 'Nghèo đạm • Cần bón thúc đạm hòa tan';
    if (n <= 80) return 'Trung bình / Đủ đạm phát triển đọt non';
    return 'Dư thừa đạm • Giảm phân để chống vóng lá';
  }

  Color _getNColor(double n) {
    if (n < 40) return Colors.deepOrange;
    if (n <= 80) return const Color(0xFF2E7D32);
    return Colors.amber.shade800;
  }

  String _getPStatus(double p) {
    if (p < 20) return 'Thiếu hụt lân • Rễ non phát triển chậm';
    if (p <= 55) return 'Trung bình • Kích rễ & phân hóa mầm hoa tốt';
    return 'Dư thừa lân trong đất';
  }

  Color _getPColor(double p) {
    if (p < 20) return Colors.deepOrange;
    if (p <= 55) return const Color(0xFF2E7D32);
    return Colors.amber.shade800;
  }

  String _getKStatus(double k) {
    if (k < 75) return 'Nghèo • Cần bổ sung phân bón Kali';
    if (k <= 140) return 'Đầy đủ • Giúp cứng cây & nuôi quả ngọt';
    return 'Dư thừa Kali';
  }

  Color _getKColor(double k) {
    if (k < 75) return Colors.deepOrange;
    if (k <= 140) return const Color(0xFF2E7D32);
    return Colors.amber.shade800;
  }

  // BOTTOM SHEET CHỌN ĐIỂM ĐO
  void _showSelectNodeBottomSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(22.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Chọn Điểm Cảm Biến', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
              const SizedBox(height: 12),
              _buildNodeOption('ESP32_SOIL_01', 'Lô A2 - Vườn Sầu Riêng Monthong', true),
              _buildNodeOption('ESP32_SOIL_02', 'Lô B1 - Vườn Sầu Riêng Ri6', false),
              _buildNodeOption('ESP32_SOIL_03', 'Lô C - Vườn Ươm Cây Giống', false),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  Widget _buildNodeOption(String nodeId, String desc, bool isLive) {
    final isSelected = widget.selectedNode.contains(nodeId);
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF2E7D32).withAlpha(30) : Colors.grey.shade100,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(Icons.sensors, color: isSelected ? const Color(0xFF2E7D32) : Colors.grey),
      ),
      title: Text(nodeId, style: TextStyle(fontWeight: isSelected ? FontWeight.bold : FontWeight.w500)),
      subtitle: Text(desc, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      trailing: isSelected
          ? const Icon(Icons.check_circle, color: Color(0xFF2E7D32))
          : const Icon(Icons.radio_button_unchecked, color: Colors.grey),
      onTap: () {
        widget.onNodeChanged(nodeId);
        Navigator.pop(context);
      },
    );
  }
}

class _HeaderWaveClipper extends CustomClipper<Path> {
  @override
  Path getClip(Size size) {
    final path = Path();
    path.lineTo(0, size.height - 20);
    path.quadraticBezierTo(
      size.width * 0.25,
      size.height,
      size.width * 0.5,
      size.height - 14,
    );
    path.quadraticBezierTo(
      size.width * 0.75,
      size.height - 28,
      size.width,
      size.height - 10,
    );
    path.lineTo(size.width, 0);
    path.close();
    return path;
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}
