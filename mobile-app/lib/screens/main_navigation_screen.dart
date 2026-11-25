import 'dart:async';
import 'package:flutter/material.dart';
import '../models/soil_data.dart';
import '../services/api_service.dart';
import 'home_screen.dart';
import 'measurement_screen.dart';
import 'recommendation_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 1; // Mặc định mở ngay màn hình Đo (Arc Gauge) theo phong cách ảnh mẫu
  SoilData? _latestData;
  List<SoilData> _history = [];
  bool _isLoading = true;
  Timer? _timer;
  String _selectedNode = 'ESP32_SOIL_01';

  @override
  void initState() {
    super.initState();
    _fetchData();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _fetchData(silent: true));
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchData({bool silent = false}) async {
    if (!silent) {
      setState(() => _isLoading = true);
    }
    try {
      final latest = await ApiService.fetchLatestTelemetry(deviceId: _selectedNode);
      final history = await ApiService.fetchTelemetryHistory(deviceId: _selectedNode, limit: 12);
      if (mounted) {
        setState(() {
          _latestData = latest;
          _history = history;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          // Tab 0: Trang chủ (Bảng thông tin số liệu đo đạc)
          HomeScreen(
            latestData: _latestData,
            history: _history,
            isLoading: _isLoading,
            onRefresh: () => _fetchData(),
            onNavigateToMeasurement: () => setState(() => _currentIndex = 1),
          ),

          // Tab 1: Đo Đạc (Đồng hồ vòng cung Arc Gauge giống mẫu)
          MeasurementScreen(
            latestData: _latestData,
            history: _history,
            isLoading: _isLoading,
            onRefresh: () => _fetchData(),
            selectedNode: _selectedNode,
            onNodeChanged: (newNode) {
              setState(() => _selectedNode = newNode);
              _fetchData();
            },
          ),

          // Tab 2: Khuyến nghị
          RecommendationScreen(
            latestData: _latestData,
          ),
        ],
      ),

      // BOTTOM NAVIGATION BAR THEO PHONG CÁCH ENFARM
      bottomNavigationBar: _buildEnfarmBottomBar(),
    );
  }

  Widget _buildEnfarmBottomBar() {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
        boxShadow: [
          BoxShadow(color: Colors.black12, blurRadius: 10, offset: Offset(0, -2)),
        ],
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 68,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              // 1. Tab Trang chủ (Nông trại / Tổng quan)
              Expanded(
                child: InkWell(
                  onTap: () => setState(() => _currentIndex = 0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.grid_view_rounded,
                        color: _currentIndex == 0 ? const Color(0xFF2E7D32) : Colors.grey.shade400,
                        size: 24,
                      ),
                      const SizedBox(height: 3),
                      Text(
                        'Trang chủ',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: _currentIndex == 0 ? FontWeight.bold : FontWeight.w500,
                          color: _currentIndex == 0 ? const Color(0xFF2E7D32) : Colors.grey.shade500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // 2. Nút Đo Nổi Bật Ở Giữa (Center Floating Action Button)
              GestureDetector(
                onTap: () => setState(() => _currentIndex = 1),
                child: Container(
                  width: 58,
                  height: 58,
                  decoration: BoxDecoration(
                    color: const Color(0xFF2E7D32),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2E7D32).withAlpha(90),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                    border: Border.all(color: Colors.white, width: 3),
                  ),
                  child: const Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.wifi_tethering, color: Colors.white, size: 24),
                      Text(
                        'Đo',
                        style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ),

              // 3. Tab Khuyến nghị
              Expanded(
                child: InkWell(
                  onTap: () => setState(() => _currentIndex = 2),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.eco_rounded,
                        color: _currentIndex == 2 ? const Color(0xFF2E7D32) : Colors.grey.shade400,
                        size: 24,
                      ),
                      const SizedBox(height: 3),
                      Text(
                        'Khuyến nghị',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: _currentIndex == 2 ? FontWeight.bold : FontWeight.w500,
                          color: _currentIndex == 2 ? const Color(0xFF2E7D32) : Colors.grey.shade500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
