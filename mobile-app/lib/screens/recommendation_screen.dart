import 'package:flutter/material.dart';
import '../models/soil_data.dart';

class RecommendationScreen extends StatelessWidget {
  final SoilData? latestData;

  const RecommendationScreen({super.key, required this.latestData});

  @override
  Widget build(BuildContext context) {
    final d = latestData;

    return Scaffold(
      backgroundColor: const Color(0xFFF3F6F4),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'Khuyến nghị',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 16.0),
        child: Column(
          children: [
            // Thẻ Dinh Dưỡng (giống Enfarm 100%)
            _buildEnfarmCard(
              context: context,
              icon: Icons.eco,
              iconColor: const Color(0xFF2E7D32),
              title: 'Dinh dưỡng',
              subtitle: 'Thông tin dữ liệu đất và các khuyến nghị',
              onTap: () => _showNutritionDetail(context, d),
            ),
            const SizedBox(height: 14),

            // Thẻ Điều Khiển Tưới Tiêu
            _buildEnfarmCard(
              context: context,
              icon: Icons.water_drop,
              iconColor: Colors.blue.shade700,
              title: 'Tưới tiêu & Vi khí hậu',
              subtitle: 'Chu kỳ tưới xung - nghỉ và điều hòa nhiệt tầng rễ',
              onTap: () => _showIrrigationDetail(context, d),
            ),
            const SizedBox(height: 14),

            // Thẻ Bệnh Lý Vùng Rễ (XGBoost AI)
            _buildEnfarmCard(
              context: context,
              icon: Icons.biotech,
              iconColor: Colors.purple.shade700,
              title: 'Chẩn đoán sinh lý rễ (XGBoost)',
              subtitle: 'Nhận diện bệnh lý rễ non, nén chặt và bó lân',
              onTap: () => _showPathologyDetail(context, d),
            ),
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Widget _buildEnfarmCard({
    required BuildContext context,
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 1))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: iconColor.withAlpha(20),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: iconColor, size: 24),
          ),
          const SizedBox(height: 14),
          Text(
            title,
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
          ),
          const SizedBox(height: 6),
          Text(
            subtitle,
            style: const TextStyle(fontSize: 13, color: Colors.black54, height: 1.3),
          ),
          const SizedBox(height: 16),
          InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(24),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF1B5E20),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Xem chi tiết',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  SizedBox(width: 8),
                  Icon(Icons.arrow_forward, color: Colors.white, size: 16),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showNutritionDetail(BuildContext context, SoilData? d) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) {
        return Padding(
          padding: EdgeInsets.only(
            top: 20,
            left: 20,
            right: 20,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Phác Đồ Dinh Dưỡng Chi Tiết', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
              const Divider(),
              _buildDetailItem('1. Tinh vôi sữa Nano Nông Thịnh', 'Liều lượng: 150ml/gốc • Nâng pH lên ngưỡng an toàn 6.5 để chống nghẹt rễ.', Colors.amber.shade800),
              const SizedBox(height: 10),
              _buildDetailItem('2. Humic Acid hoạt hóa Mỹ', 'Liều lượng: 50ml/gốc • Kích thích nhú rễ tơ & giải độc phèn nhôm sắt.', const Color(0xFF2E7D32)),
              const SizedBox(height: 10),
              _buildDetailItem('3. Phân bón NPK 20-20-15 hòa tan', 'TẠM DỪNG BƠM nếu pH < 6.0 để tránh xót rễ non.', Colors.red.shade700),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  void _showIrrigationDetail(BuildContext context, SoilData? d) {
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
              const Text('Chế Độ Tưới Fuzzy Logic AI', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              const Text('• Độ ẩm hiện tại: Đang được kiểm soát tối ưu.'),
              const SizedBox(height: 6),
              const Text('• Chu kỳ khuyến nghị: Bật 15 giây, nghỉ 45 giây để nước ngấm sâu và rễ thở thoáng khí.'),
              const SizedBox(height: 6),
              const Text('• Khóa an toàn: Tự động ngắt khẩn cấp nếu cảm biến tuột khỏi mô đất.'),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  void _showPathologyDetail(BuildContext context, SoilData? d) {
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
              const Text('Kết Quả Phân Loại Bệnh Lý (XGBoost)', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              const Text('• Bó rễ khóa dinh dưỡng: 4%'),
              const SizedBox(height: 6),
              const Text('• Sốc muối EC cao: 1%'),
              const SizedBox(height: 6),
              const Text('• Nén chặt bí khí tầng mặt: 1%'),
              const SizedBox(height: 6),
              const Text('• Độ chua phèn: Phụ thuộc giá trị pH thực tế.'),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  Widget _buildDetailItem(String title, String desc, Color color) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withAlpha(50)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 4),
          Text(desc, style: const TextStyle(fontSize: 12, color: Colors.black87)),
        ],
      ),
    );
  }
}
