import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/soil_data.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  SoilData? _latestData;
  List<SoilData> _history = [];
  bool _isLoading = true;
  String? _errorMessage;
  Timer? _autoRefreshTimer;
  bool _isAutoRefresh = true;

  @override
  void initState() {
    super.initState();
    _loadData();
    _startTimer();
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    super.dispose();
  }

  void _startTimer() {
    _autoRefreshTimer?.cancel();
    if (_isAutoRefresh) {
      _autoRefreshTimer = Timer.periodic(const Duration(seconds: 5), (_) {
        _loadData(silent: true);
      });
    }
  }

  void _toggleAutoRefresh() {
    setState(() {
      _isAutoRefresh = !_isAutoRefresh;
      _startTimer();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_isAutoRefresh ? 'Đã bật tự động làm mới mỗi 5s' : 'Đã tắt tự động làm mới'),
        duration: const Duration(seconds: 1),
      ),
    );
  }

  Future<void> _loadData({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });
    }

    try {
      final latest = await ApiService.fetchLatestTelemetry();
      final history = await ApiService.fetchTelemetryHistory(limit: 10);
      if (mounted) {
        setState(() {
          _latestData = latest;
          _history = history;
          _isLoading = false;
          _errorMessage = null;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          if (_latestData == null) {
            _errorMessage = e.toString().replaceAll('Exception: ', '');
          }
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final timeFormat = DateFormat('HH:mm:ss - dd/MM/yyyy');

    return Scaffold(
      backgroundColor: const Color(0xFFF4F7F5),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'AI Smart Soil System',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            Text(
              'Hệ Thống Giám Sát Nông Nghiệp Thời Gian Thực',
              style: TextStyle(fontSize: 12, color: Colors.green.shade100),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        elevation: 2,
        actions: [
          IconButton(
            tooltip: _isAutoRefresh ? 'Đang tự làm mới (5s)' : 'Tự làm mới đang tắt',
            icon: Icon(
              _isAutoRefresh ? Icons.sync : Icons.sync_disabled,
              color: _isAutoRefresh ? Colors.lightGreenAccent : Colors.white60,
            ),
            onPressed: _toggleAutoRefresh,
          ),
          IconButton(
            tooltip: 'Làm mới ngay',
            icon: const Icon(Icons.refresh),
            onPressed: () => _loadData(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => _loadData(),
        color: const Color(0xFF1B5E20),
        child: _isLoading && _latestData == null
            ? const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(color: Color(0xFF1B5E20)),
                    SizedBox(height: 16),
                    Text('Đang kết nối tới máy chủ VPS...'),
                  ],
                ),
              )
            : _errorMessage != null && _latestData == null
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.cloud_off, size: 64, color: Colors.redAccent),
                          const SizedBox(height: 16),
                          Text(
                            _errorMessage!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.redAccent, fontSize: 15),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF1B5E20),
                              foregroundColor: Colors.white,
                            ),
                            icon: const Icon(Icons.refresh),
                            label: const Text('Thử kết nối lại'),
                            onPressed: () => _loadData(),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView(
                    padding: const EdgeInsets.all(16.0),
                    children: [
                      // Card trạng thái thiết bị & Thời gian
                      _buildHeaderCard(_latestData!, timeFormat),
                      const SizedBox(height: 16),

                      // Tiêu đề nhóm thông số
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Chỉ số Môi trường Đất',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: const Color(0xFF2E3E33),
                            ),
                          ),
                          if (_isAutoRefresh)
                            Row(
                              children: [
                                Container(
                                  width: 8,
                                  height: 8,
                                  decoration: const BoxDecoration(
                                    color: Colors.green,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 6),
                                const Text(
                                  'Live 5s',
                                  style: TextStyle(fontSize: 12, color: Colors.green, fontWeight: FontWeight.w600),
                                ),
                              ],
                            ),
                        ],
                      ),
                      const SizedBox(height: 10),

                      // Grid 4 chỉ số chính: Độ ẩm, Nhiệt độ, EC, pH
                      GridView.count(
                        crossAxisCount: 2,
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        childAspectRatio: 1.15,
                        children: [
                          _buildMetricCard(
                            title: 'Độ ẩm đất',
                            value: '${_latestData!.moisture.toStringAsFixed(1)}%',
                            status: _latestData!.moistureStatus,
                            statusColor: _latestData!.moistureColor,
                            icon: Icons.water_drop,
                            iconColor: Colors.blue,
                          ),
                          _buildMetricCard(
                            title: 'Nhiệt độ đất',
                            value: '${_latestData!.temperature.toStringAsFixed(1)}°C',
                            status: _latestData!.tempStatus,
                            statusColor: _latestData!.tempColor,
                            icon: Icons.thermostat,
                            iconColor: Colors.orange,
                          ),
                          _buildMetricCard(
                            title: 'Độ dẫn điện EC',
                            value: '${_latestData!.ec.toStringAsFixed(0)} µS/cm',
                            status: _latestData!.ecStatus,
                            statusColor: _latestData!.ecColor,
                            icon: Icons.bolt,
                            iconColor: Colors.amber.shade700,
                          ),
                          _buildMetricCard(
                            title: 'Độ chua pH',
                            value: _latestData!.ph.toStringAsFixed(1),
                            status: _latestData!.phStatus,
                            statusColor: _latestData!.phColor,
                            icon: Icons.science,
                            iconColor: Colors.purple,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Nhóm chỉ số dinh dưỡng NPK
                      _buildNpkSection(_latestData!),
                      const SizedBox(height: 16),

                      // Danh sách lịch sử đo đạc gần đây
                      _buildHistorySection(_history, timeFormat),
                    ],
                  ),
      ),
    );
  }

  // Widget Header: Thông tin thiết bị & Thời gian đo
  Widget _buildHeaderCard(SoilData data, DateFormat formatter) {
    final isOnline = data.isOnline;
    final isFault = data.isFault;

    return Card(
      elevation: 1.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(Icons.sensors, color: isOnline ? const Color(0xFF1B5E20) : Colors.red, size: 26),
                    const SizedBox(width: 8),
                    Text(
                      data.deviceId,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: isOnline ? Colors.green.shade50 : Colors.red.shade50,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: isOnline ? Colors.green.shade400 : Colors.red.shade400),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          color: isOnline ? Colors.green : Colors.red,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        isOnline ? 'TRỰC TUYẾN' : 'NGOẠI TUYẾN',
                        style: TextStyle(
                          fontSize: 11,
                          color: isOnline ? Colors.green.shade800 : Colors.red.shade800,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 18),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.access_time, size: 15, color: Colors.grey),
                    const SizedBox(width: 6),
                    Text(
                      'Bản ghi #${data.id ?? '---'} (${formatter.format(data.createdAt)})',
                      style: const TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                  ],
                ),
              ],
            ),
            if (!isOnline) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.amber.shade300),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, size: 18, color: Colors.amber.shade900),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'ESP32 đang tắt hoặc mất sóng. Đang hiển thị bản ghi lưu trữ cuối cùng.',
                        style: TextStyle(fontSize: 11, color: Colors.amber.shade900, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (isFault) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade300),
                ),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, size: 18, color: Colors.red.shade900),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Cảnh báo: Tín hiệu cảm biến bất thường (-40°C, 20.000 µS/cm). Hãy kiểm tra dây RS485 và nguồn 12V.',
                        style: TextStyle(fontSize: 11, color: Colors.red.shade900, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // Widget hiển thị thẻ chỉ số từng ô
  Widget _buildMetricCard({
    required String title,
    required String value,
    required String status,
    required Color statusColor,
    required IconData icon,
    required Color iconColor,
  }) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontSize: 13, color: Colors.black87, fontWeight: FontWeight.w500),
                ),
                Icon(icon, color: iconColor, size: 22),
              ],
            ),
            Text(
              value,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF1B2E23)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
              decoration: BoxDecoration(
                color: statusColor.withAlpha(30),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                status,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 11, color: statusColor, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Widget Khối Dinh Dưỡng Đa Lượng N-P-K
  Widget _buildNpkSection(SoilData data) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.grass, color: Colors.green, size: 20),
                SizedBox(width: 8),
                Text(
                  'Dinh dưỡng đa lượng N - P - K',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildNpkItem('Nitơ (N)', '${data.nitrogen.toStringAsFixed(0)} mg/kg', Colors.blue.shade700),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildNpkItem('Photpho (P)', '${data.phosphorus.toStringAsFixed(0)} mg/kg', Colors.amber.shade800),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildNpkItem('Kali (K)', '${data.potassium.toStringAsFixed(0)} mg/kg', Colors.purple.shade700),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              '* Chỉ số NPK được nội suy dựa trên độ dẫn điện EC và độ ẩm của mẫu đất.',
              style: TextStyle(fontSize: 11, color: Colors.grey, fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNpkItem(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Column(
        children: [
          Text(label, style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color),
          ),
        ],
      ),
    );
  }

  // Widget hiển thị Lịch sử các lần đo gần đây
  Widget _buildHistorySection(List<SoilData> list, DateFormat formatter) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Lịch sử đo đạc gần đây',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                ),
                Text(
                  '${list.length} bản ghi',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
            const Divider(height: 18),
            if (list.isEmpty)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(12.0),
                  child: Text('Chưa có lịch sử đo đạc', style: TextStyle(color: Colors.grey)),
                ),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: list.length,
                separatorBuilder: (context, index) => const Divider(height: 12),
                itemBuilder: (context, index) {
                  final item = list[index];
                  return Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            formatter.format(item.createdAt),
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                          ),
                          Text(
                            'Ẩm: ${item.moisture.toStringAsFixed(1)}% | Nhiệt: ${item.temperature.toStringAsFixed(1)}°C',
                            style: const TextStyle(fontSize: 11, color: Colors.black54),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          _buildMiniBadge('pH ${item.ph.toStringAsFixed(1)}', item.phColor),
                          const SizedBox(width: 4),
                          _buildMiniBadge('${item.ec.toStringAsFixed(0)} µS', item.ecColor),
                        ],
                      ),
                    ],
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildMiniBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.bold),
      ),
    );
  }
}
